"""벡터 글꼴(ROOM2.VFI/VFS) 다시 만들기.
- 원본의 비한자 글리프(기호·숫자·영문·가나)는 그대로 두고, 한자 글리프는 버린다(코드가 한글 슬롯과 겹침).
- 주어진 한글 글자를 나눔스퀘어네오 윤곽에서 만들어 SJIS 슬롯 코드로 넣는다.
좌표: 1em=5120, x 오른쪽+, y 아래+(기준선 0), 값은 0x8000 더한 u16. 닫힌 윤곽(첫 점 반복), 바깥 윤곽 면적 +, 구멍 −."""
import sys, os, struct, math
sys.path.insert(0, os.path.dirname(__file__))
import kmap, vfs
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TTF = os.path.join(ROOT, 'NanumSquareNeo-cBd.ttf')
S = 4.95                    # TTF 단위 → 게임 단위 배율 (한글 높이 ≈ 원본 한자 높이)
CX, CY = 2560, -1940        # 원본 한자 잉크 상자 중심
REF_X, REF_Y = 485.5, 318   # '한' 잉크 상자 중심(TTF)
TOL = 12.0                  # 곡선 평탄화 허용 오차(게임 단위)


def _quad(p0, p1, p2):
    d = math.hypot(p0[0] - 2 * p1[0] + p2[0], p0[1] - 2 * p1[1] + p2[1])
    n = max(1, int(math.ceil(math.sqrt(d / (4 * TOL)))))
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (k / n for k in range(1, n + 1))]


def outline(font, ch):
    gs = font.getGlyphSet(); name = font.getBestCmap()[ord(ch)]
    pen = DecomposingRecordingPen(gs); gs[name].draw(pen)
    tf = lambda p: (S * p[0] + (CX - REF_X * S), -S * p[1] + (CY + REF_Y * S))
    conts = []; cur = []
    for op, args in pen.value:
        if op == 'moveTo':
            cur = [tf(args[0])]
        elif op == 'lineTo':
            cur.append(tf(args[0]))
        elif op == 'qCurveTo':
            pts = [tf(a) for a in args]
            # 암시적 중간점 처리
            p0 = cur[-1]
            for i in range(len(pts) - 1):
                c = pts[i]; e = pts[i + 1] if i == len(pts) - 2 else ((pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2)
                cur += _quad(p0, c, e); p0 = e
        elif op == 'curveTo':
            raise ValueError('cubic')
        elif op in ('closePath', 'endPath'):
            if len(cur) > 2:
                if cur[0] != cur[-1]: cur.append(cur[0])
                conts.append(cur)
            cur = []
    # 같은 점 연속 제거, 정수화
    out = []
    for c in conts:
        q = []
        for x, y in c:
            p = (int(round(x)), int(round(y)))
            if not q or q[-1] != p: q.append(p)
        if len(q) >= 4: out.append(q)
    return orient(out)


def area(c):
    return sum(c[i][0] * c[i + 1][1] - c[i + 1][0] * c[i][1] for i in range(len(c) - 1)) / 2


def inside(pt, c):
    x, y = pt; r = False
    for i in range(len(c) - 1):
        (x1, y1), (x2, y2) = c[i], c[i + 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: r = not r
    return r


def orient(conts):
    """포함 깊이 짝수 = 바깥(면적 +), 홀수 = 구멍(면적 −)"""
    out = []
    for i, c in enumerate(conts):
        depth = sum(1 for j, o in enumerate(conts) if j != i and inside(c[0], o))
        want = 1 if depth % 2 == 0 else -1
        if area(c) * want < 0: c = c[::-1]
        out.append(c)
    return out


def build(hangul):
    """hangul: 넣을 한글 글자 집합 → (vfi bytes, vfs bytes)"""
    src_i = open(os.path.join(ROOT, 'extract/ROOM2/TTF/ROOM2.VFI'), 'rb').read()
    src_s = open(os.path.join(ROOT, 'extract/ROOM2/TTF/ROOM2.VFS'), 'rb').read()
    n = struct.unpack_from('<I', src_i, 4)[0]
    codes = [src_i[8 + 2 * k:10 + 2 * k] for k in range(n)]
    hdr, gl = vfs.parse(src_s)
    keep = []
    for c, g in zip(codes, gl):
        if c[0] < 0x88: keep.append((c, g))          # 1~8구(기호·영숫자·가나)만 유지
    font = TTFont(TTF)
    for ch in sorted(hangul, key=lambda h: kmap.CM[h]):
        code = kmap.CM[ch].to_bytes(2, 'big')
        conts = outline(font, ch)
        pts = [[(x + 0x8000, y + 0x8000) for x, y in c] for c in conts]
        keep.append((code, pts))
    vfi = struct.pack('<II', 3, len(keep)) + b''.join(c for c, g in keep)
    return vfi, vfs.build(hdr, [g for c, g in keep])


if __name__ == '__main__':
    hs = kmap.HANGUL if len(sys.argv) < 2 else sys.argv[1]
    vi, vs = build(hs)
    print('glyphs', struct.unpack_from('<I', vi, 4)[0], 'vfs bytes', len(vs), 'per hangul', (len(vs) - 100000) / max(1, len(hs)))
