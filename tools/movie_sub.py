"""TV 드라마 동영상(ROOM2TV/ADX/TV/ROOM_0x.SFD)에 한국어 자막을 입힌다 (지옥소녀·블랙 한글패치와 같은 방식).

python tools/movie_sub.py [이름 ...]   입력 movie/orig/<이름>.SFD + movie/subs/<이름>.tsv → movie/enc/<이름>.SFD

원본: Sofdec(MPEG-1 팩, 2048바이트 섹터), 비디오 MPEG-2 640x448 29.97fps(시퀀스 헤더 1개, GOP 헤더 + 불규칙 I/P/B),
      음성 ADX. 영상 섹터는 PES 2030바이트.
방법: 자막이 걸린 GOP 구간만 다시 인코딩. 픽처 유형(I/P/B)을 프레임마다 강제해 원본과 똑같은 복호 순서 배치를 만들고,
      각 픽처가 원본과 같은 바이트 위치에서 시작하도록 0으로 채운다(시작 코드 앞 0 채움은 규격상 허용).
      비디오 ES 길이·픽처 위치가 원본과 같으므로 영상 섹터 PES 헤더(타임스탬프 포함)는 원본 그대로, 페이로드만 바꿔 쓴다.
      음성 섹터·팩 헤더·파일 크기는 원본과 같다. 구간 앞 GOP 를 함께 인코딩해 열린 GOP 의 앞 B 참조를 준비한다.
자막: 게임 대사 글꼴(나눔스퀘어네오 Bold), 대사 글자 크기(22px), 흰 글자 + 검은 외곽선, 화면 아래 가운데.
tsv: 시작초 <TAB> 끝초 <TAB> 한국어 (줄바꿈은 \\n), # 줄은 주석
"""
import os, sys, io, struct, fractions
import numpy as np
import av
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = os.path.join(ROOT, 'movie')
FONT = os.path.join(ROOT, 'NanumSquareNeo-cBd.ttf')
SIZE = 22; STROKE = 2; LINE_H = 27
W, H = 640, 448
BOTTOM = H - 34
FPS = 30000 / 1001
SECTOR = 2048; PACK = 12
SC = bytes([0, 0, 1])
_font = ImageFont.truetype(FONT, SIZE)


# ------------------------------------------------------------------ SFD 영상 페이로드
def video_slots(sfd):
    """[(페이로드 시작 오프셋, 길이)] (영상 섹터 순서)"""
    out = []
    for base in range(0, len(sfd), SECTOR):
        if sfd[base:base + 4] != SC + b'\xba': continue
        c = base + PACK
        if sfd[c:c + 4] != SC + b'\xe0': continue
        ln = struct.unpack_from('>H', sfd, c + 4)[0]; end = c + 6 + ln
        p = c + 6
        while sfd[p] == 0xFF: p += 1
        if sfd[p] >> 6 == 1: p += 2
        f = sfd[p]
        p += 1 if f == 0x0F else 5 if f >> 4 == 2 else 10
        out.append((p, end - p))
    return out


def video_es(sfd):
    return b''.join(sfd[p:p + n] for p, n in video_slots(sfd))


def put_video_es(sfd, es):
    out = bytearray(sfd); q = 0
    for p, n in video_slots(sfd):
        out[p:p + n] = es[q:q + n]; q += n
    assert q == len(es)
    return bytes(out)


# ------------------------------------------------------------------ 자막
def render(text):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    lines = text.split('\\n'); y = BOTTOM - LINE_H * len(lines)
    for ln in lines:
        d.text((W // 2, y + LINE_H / 2), ln, font=_font, anchor='mm', fill=(255, 255, 255, 255),
               stroke_width=STROKE, stroke_fill=(0, 0, 0, 255))
        y += LINE_H
    return im


def load_subs(name):
    subs = []
    for ln in open(os.path.join(M, 'subs', name + '.tsv'), encoding='utf8').read().splitlines():
        if ln.strip() and not ln.startswith('#'):
            s, e, t = ln.split('\t', 2); subs.append((float(s), float(e), t))
    return subs


# ------------------------------------------------------------------ MPEG 도우미
def pic_starts(es):
    r, i = [], 0
    while True:
        i = es.find(SC + b'\x00', i)
        if i < 0: return r
        r.append(i); i += 4


def align(orig, enc, lat=0):
    """각 픽처가 원본과 같은 바이트 위치에서 시작하도록 0 채움. 넘치면 None."""
    po, pn = pic_starts(orig), pic_starts(enc)
    if len(po) != len(pn): return None
    bo, bn = po + [len(orig)], pn + [len(enc)]
    out = bytearray(enc[:pn[0]])
    if len(out) > po[0] + lat: return None
    out += b'\x00' * max(0, po[0] - len(out))
    for k in range(len(pn)):
        out += enc[bn[k]:bn[k + 1]]
        if len(out) > bo[k + 1] + (lat if k + 1 < len(pn) else 0): return None
        out += b'\x00' * max(0, bo[k + 1] - len(out))
    return bytes(out)


def display_index(types):
    """복호 순서 픽처 유형(1=I,2=P,3=B) → 표시 순서 번호"""
    idx = [0] * len(types); held = None; slot = 0
    for o, t in enumerate(types):
        if t in (1, 2):
            if held is not None: idx[held] = slot; slot += 1
            held = o
        else:
            idx[o] = slot; slot += 1
    if held is not None: idx[held] = slot
    return idx


def encode_typed(frames, dtypes, q):
    """표시 순서 프레임과 유형('I','P','B')을 그대로 강제해 MPEG-2 로 인코딩"""
    PT = av.video.frame.PictureType
    out = io.BytesIO()
    oc = av.open(out, 'w', format='mpeg2video')
    st = oc.add_stream('mpeg2video', rate=fractions.Fraction(30000, 1001))
    st.width, st.height = W, H; st.pix_fmt = 'yuv420p'
    cc = st.codec_context; cc.gop_size = 100000; cc.max_b_frames = 4
    cc.options = {'sc_threshold': '1000000000', 'b_strategy': '0', 'qscale': str(q), 'intra_vlc': '1'}
    for img, t in zip(frames, dtypes):
        fr = av.VideoFrame.from_ndarray(img, format='rgb24').reformat(format='yuv420p')
        fr.pict_type = {'I': PT.I, 'P': PT.P, 'B': PT.B}[t]
        for p in st.encode(fr): oc.mux(p)
    for p in st.encode(): oc.mux(p)
    oc.close()
    return out.getvalue()


def strip_seq(es):
    """시퀀스 헤더(+시퀀스 확장)와 종료 코드를 지운다(원본은 맨 앞 한 번뿐)"""
    out = bytearray(); p = 0
    while True:
        i = es.find(SC + b'\xb3', p)
        if i < 0: out += es[p:]; break
        out += es[p:i]
        k = es.find(SC, i + 4)
        while k >= 0 and es[k + 3] == 0xB5 and (es[k + 4] >> 4) in (1, 2):
            k = es.find(SC, k + 4)
        p = k
    return bytes(out).replace(SC + b'\xb7', b'')


# ------------------------------------------------------------------ 처리
def process(name):
    """전체 재인코딩(프레임 수 동일) + sofdec_remux(신비한 바다의 나디아 한글패치에서 PS2 실기 검증된 방식)로
    영상 섹터만 다시 채운다. 음성 섹터·팩 헤더·파일 크기는 원본 그대로, 영상 PES 타임스탬프는 원본 표시 순서표로 재계산."""
    import subprocess, imageio_ffmpeg, sofdec_remux
    FF = imageio_ffmpeg.get_ffmpeg_exe()
    src = open(os.path.join(M, 'orig', name + '.SFD'), 'rb').read()
    es = video_es(src)
    n = len(pic_starts(es))
    sub_at = [None] * n
    for s0, e0, t in load_subs(name):
        for fi in range(int(round(s0 * FPS)), min(n, int(round(e0 * FPS)))): sub_at[fi] = t
    os.makedirs(os.path.join(M, 'enc'), exist_ok=True)
    tmp = os.path.join(M, 'enc', name + '.src.m2v'); open(tmp, 'wb').write(es)
    out_m2v = os.path.join(M, 'enc', name + '.m2v')
    cap = len(sofdec_remux.analyse(src)[0]) * sofdec_remux.VIDEO_PAYLOAD
    secs = n / FPS
    rate = int(cap * 8 / secs * 0.80)                    # 정렬 여유 20%
    enc = subprocess.Popen([FF, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                            '-s', '%dx%d' % (W, H), '-r', '30000/1001', '-i', '-',
                            '-c:v', 'mpeg2video', '-pix_fmt', 'yuv420p', '-b:v', str(rate), '-maxrate', str(int(rate * 1.15)),
                            '-bufsize', '1179648', '-g', '15', '-bf', '2', '-aspect', '4:3',
                            '-f', 'mpeg2video', out_m2v], stdin=subprocess.PIPE)
    cache = {}; k = 0
    c = av.open(tmp)
    for fr in c.decode(video=0):
        if k >= n: break
        t = sub_at[k]
        if t:
            if t not in cache: cache[t] = render(t)
            base = fr.to_image().convert('RGBA'); base.alpha_composite(cache[t])
            enc.stdin.write(base.convert('RGB').tobytes())
        else:
            enc.stdin.write(fr.to_ndarray(format='rgb24').tobytes())
        k += 1
    c.close(); enc.stdin.close(); enc.wait(); os.remove(tmp)
    assert k == n, (k, n)
    video = open(out_m2v, 'rb').read()
    dst = sofdec_remux.remux(src, video)
    assert len(dst) == len(src)
    open(os.path.join(M, 'enc', name + '.SFD'), 'wb').write(dst)
    os.remove(out_m2v)
    print(name, '프레임', n, '비트레이트', rate, '영상', len(video), '/', cap, flush=True)


def preview(name, t, path):
    tmp = path + '.m2v'; open(tmp, 'wb').write(video_es(open(os.path.join(M, 'enc', name + '.SFD'), 'rb').read()))
    c = av.open(tmp)
    for i, fr in enumerate(c.decode(video=0)):
        if i == int(t * FPS): fr.to_image().save(path); break
    c.close(); os.remove(tmp)


if __name__ == '__main__':
    for n in sys.argv[1:] or ['ROOM_01', 'ROOM_02', 'ROOM_03']: process(n)
