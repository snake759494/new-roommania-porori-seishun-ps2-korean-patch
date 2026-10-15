"""이미지 한글화: 명세(SPECS)대로 원본 텍스처를 고쳐 같은 형식으로 다시 넣는다.
명세 키 = work/img 의 이름(경로__파일[_항목번호]). 함수는 PIL RGBA 이미지를 받아 고친 이미지를 돌려준다."""
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import pvrimg
from imgdraw import clear, put, fill_like, fill_row, text_layer, ink_color
from dump_img import all_textures
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WHITE = (255, 255, 255, 255)
SPECS = {}


def spec(*names):
    def deco(f):
        for n in names: SPECS[n] = f
        return f
    return deco


# ------------------------------------------------------------------ 타이틀 메뉴
def _menu(im, y0):
    im = clear(im, (0, y0, 200, y0 + 97))
    for i, t in enumerate(['시작하기', '튜토리얼', '사운드 컬렉션', '옵션']):
        im = put(im, t, (0, y0 + 2 + i * 24, 196, y0 + 2 + i * 24 + 22), w='H', size=19, color=WHITE)
    return im


@spec('TITLE__M_SELECT.SVR', 'TITLE__TITLEPAC.TRA_00')
def m_select(im): return _menu(im, 159)


NAVY = (1, 56, 98, 255); NAVYT = (1, 47, 83, 255); PALE = (217, 217, 217, 255)


def _outlined(im, text, box, size, fill=PALE, edge=NAVY, w='H', stroke=2, **kw):
    return put(im, text, box, w=w, size=size, color=fill, stroke=stroke, stroke_color=edge, **kw)


def _option01(im, x0=0, y0=0):
    # 탭 글자 'オプション' (연청 글자 + 남색 테두리, 격자무늬 바탕) → 바탕을 아래 빈 칸 무늬로 복원
    box = (x0 + 20, y0 + 12, x0 + 128, y0 + 34)
    im = fill_like(im, box, (x0 + 20, y0 + 44, x0 + 128, y0 + 66))
    im = put(im, '옵션', box, w='H', size=19, color=(176, 208, 232, 255), stroke=2, stroke_color=(10, 48, 90, 255), align='l')
    return im


@spec('TITLE__OPTION01.SVR', 'TITLE__TITLEPAC.TRA_01')
def option01(im): return _option01(im)


def _option02(im, x0=0, y0=0):
    rows = [((166, 4, 252, 28), '사운드'), ((166, 35, 252, 60), '진동'), ((162, 66, 256, 93), '자동 저장'),
            ((162, 98, 256, 125), '화면 조정'), ((166, 131, 252, 157), '돌아가기'),
            ((96, 162, 154, 189), '켜기'), ((96, 194, 154, 221), '끄기'),
            ((168, 162, 256, 189), '스테레오'), ((168, 194, 256, 221), '모노'), ((168, 226, 256, 253), '서라운드')]
    for (a, b, c, d), t in rows:
        box = (x0 + a, y0 + b, x0 + c, y0 + d)
        im = clear(im, box); im = put(im, t, box, w='H', size=19, color=WHITE)
    return im


@spec('TITLE__OPTION02.SVR', 'TITLE__TITLEPAC.TRA_02')
def option02(im): return _option02(im)


def _save02(im, x0=0, y0=0):
    # 'データ選択' 큰 글자 (밝은 회색 + 남색 테두리)
    box = (x0 + 47, y0 + 22, x0 + 222, y0 + 66)
    im = clear(im, box); im = _outlined(im, '데이터 선택', box, 30, stroke=3)
    # NO DATA → 데이터 없음
    box = (x0 + 64, y0 + 76, x0 + 210, y0 + 102)
    im = clear(im, box, (1, 67, 117, 255)); im = _outlined(im, '데이터 없음', box, 20, fill=(200, 198, 198, 255), edge=(1, 56, 98, 255), stroke=1)
    # 'ネジ' 'カカト' 라벨 (숫자 앞)
    box = (x0 + 50, y0 + 113, x0 + 102, y0 + 137); im = clear(im, box)
    im = put(im, '네지', box, w='H', size=19, color=NAVYT)
    box = (x0 + 48, y0 + 137, x0 + 102, y0 + 161); im = clear(im, box)
    im = put(im, '카카토', box, w='H', size=17, color=NAVYT)
    return im


# 데이터 선택 칸: 「クリアシナリオ ＋ 本」「ナビ達成」, 날짜 글자 「年」「月」「日」「の」
@spec('TITLE__SAVE01.SVR', 'TITLE__TITLEPAC.TRA_03')
def save01(im):
    a = np.array(im); bg = tuple(int(v) for v in a[172, 98])
    for box, t, sz, al in [((8, 163, 88, 183), '클리어 시나리오', 15, 'l'), ((144, 163, 170, 183), '편', 16, 'c'),
                           ((60, 184, 150, 203), '내비 달성', 17, 'c')]:
        im = clear(im, box, bg); im = put(im, t, box, w='H', size=sz, color=NAVYT, align=al)
    for box, t in [((226, 188, 252, 207), '년'), ((226, 210, 252, 229), '년'), ((180, 234, 202, 256), '월'),
                   ((208, 234, 229, 256), '일'), ((229, 234, 252, 256), '의')]:
        im = clear(im, box); im = put(im, t, box, w='H', size=19, color=NAVYT)
    return im


@spec('TITLE__SAVE02.SVR', 'TITLE__TITLEPAC.TRA_04')
def save02(im): return _save02(im)


# ------------------------------------------------------------------ 일시정지·뇌·메모리카드
@spec('ROOM__PAUSE_KK.SVR', 'ROOM__PAUSE_NJ.SVR')
def pause(im):
    rows = [((20, 98, 160, 118), '이대로 계속'), ((20, 122, 160, 142), '엿보기 그만'), ((20, 146, 160, 166), '가택수색 그만'),
            ((176, 120, 250, 144), '예'), ((176, 146, 250, 170), '아니요')]
    for box, t in rows:
        im = clear(im, box); im = put(im, t, box, w='H', size=16, color=WHITE)
    return im


def _brain(im):
    dark = (86, 8, 73, 255); fill = (204, 179, 146, 255)
    for box, t in [((196, 150, 256, 172), '취소'), ((92, 180, 160, 204), '앞으로'), ((192, 180, 256, 204), '갱신')]:
        im = clear(im, box); im = put(im, t, box, w='H', size=15, color=fill, stroke=2, stroke_color=dark, align='l')
    return im


@spec('ROOM__BRAIN_KK.SVR', 'ROOM__BRAIN_NJ.SVR')
def brain(im): return _brain(im)


@spec('MC__MEMORY_MSG.SVR')
def memory(im):
    t = (0, 47, 83, 255)
    for box, s, wt in [((140, 26, 230, 48), '아니요', 'B'), ((140, 50, 230, 74), '예', 'B'),
                       ((168, 74, 230, 98), '확인', 'H'), ((160, 98, 230, 122), '취소', 'H')]:
        im = clear(im, box); im = put(im, s, box, w=wt, size=18, color=t, align='l' if box[0] > 150 else 'c')
    return im


# ------------------------------------------------------------------ 여러 장을 가로로 이어 붙여 그리는 명세
GROUPS = {}   # 키 = 이름 튜플(왼→오), 값 = 함수(이어 붙인 이미지) → 이미지


def group(*names):
    def deco(f):
        GROUPS[names] = f
        return f
    return deco


def _auto_dup(tex):
    """같은 그림이 다른 파일에도 들어 있으면(PC 화면 등) 같은 명세를 자동으로 적용"""
    import hashlib
    h = {}
    for n, (rel, o, d) in tex.items():
        try: a = pvrimg.decode(d, o)[0]
        except Exception: continue
        h.setdefault(hashlib.md5(np.ascontiguousarray(a).tobytes() + bytes(str(a.shape), 'ascii')).hexdigest(), []).append(n)
    added = 0
    for same in h.values():
        src = [n for n in same if n in SPECS]
        if not src: continue
        for n in same:
            if n not in SPECS: SPECS[n] = SPECS[src[0]]; added += 1
    print('같은 그림 자동 적용', added)


def build(only=None):
    out = {}; files = {}
    tex = {name: (rel, o, d) for name, rel, o, d in all_textures()}
    _auto_dup(tex)
    _add_web_side(tex)
    done = {}
    for names, f in GROUPS.items():
        if isinstance(f, tuple) and only and not any(l[0] in only for l in f[1]): continue
        if not isinstance(f, tuple) and only and not any(n in only for n in names): continue
        if isinstance(f, tuple):     # (함수, [(이름, 원본 잘라낼 상자, 큰 그림 위치)...], 큰 그림 크기)
            f, lay, size = f
            big = Image.new('RGBA', size); srcs = {}
            for n, cb, pos in lay:
                srcs.setdefault(n, Image.fromarray(pvrimg.decode(tex[n][2], tex[n][1])[0]))
                big.paste(srcs[n].crop(cb), pos)
            big = f(big)
            for n, cb, pos in lay:
                im = done.get(n, srcs[n]).copy()
                im.paste(big.crop((pos[0], pos[1], pos[0] + cb[2] - cb[0], pos[1] + cb[3] - cb[1])), cb[:2]); done[n] = im
            continue
        ims = [Image.fromarray(pvrimg.decode(tex[n][2], tex[n][1])[0]) for n in names]
        W = sum(i.width for i in ims); H = max(i.height for i in ims)
        big = Image.new('RGBA', (W, H)); x = 0
        for i in ims: big.paste(i, (x, 0)); x += i.width
        big = f(big); x = 0
        for n, i in zip(names, ims):
            done[n] = big.crop((x, 0, x + i.width, i.height)); x += i.width
    for dup, src in getattr(__import__('manga'), 'DUP', {}).items():
        if src in done and dup in tex: done[dup] = done[src]
    for name, (rel, o, d) in tex.items():
        if name not in SPECS and name not in done: continue
        if only and name not in only and name not in done: continue
        im = done.get(name) or Image.fromarray(pvrimg.decode(d, o)[0])
        if name in SPECS: im = SPECS[name](im)
        new = np.array(im.convert('RGBA'))
        buf = files.setdefault(rel, bytearray(d))
        enc = pvrimg.encode(bytes(buf), o, rgba=new)
        buf[o:o + len(enc)] = enc
        if only: Image.fromarray(new).save(os.path.join(ROOT, 'work', 'ko_%s.png' % name))
    for rel, b in files.items(): out['/' + rel] = bytes(b)
    return out


# 화면 조정 하단 안내: TRA_03 오른쪽 끝(x 224~256)과 TRA_04 왼쪽(x 128~) 이 화면에서 이어진다.
@spec('TITLE__TITLE03.TRA_03')
def screen_adj3(im):
    t = (0, 46, 81, 255)
    im = fill_row(im, (114, 152, 186, 174), 111)
    im = put(im, '기본값', (114, 152, 186, 174), w='H', size=15, color=t, align='l')
    im = fill_row(im, (214, 152, 256, 174), 212)
    im = put(im, '결정', (218, 152, 256, 174), w='H', size=15, color=t, align='l')
    return im


@spec('TITLE__TITLE03.TRA_04')
def screen_adj4(im):
    t = (0, 46, 81, 255)
    im = fill_row(im, (128, 152, 156, 174), 157)
    im = fill_row(im, (186, 152, 240, 174), 241)
    im = put(im, '돌아가기', (186, 152, 240, 174), w='H', size=15, color=t, align='l')
    return im


# ------------------------------------------------------------------ 달력(카카토=붉은색, 네지=녹색)
KK_INK = (107, 0, 14, 255); NJ_INK = (2, 59, 58, 255)


def _end(im, ink):
    for box, t, sz in [((92, 6, 150, 30), '예', 21), ((160, 6, 236, 30), '아니요', 21),
                       ((40, 126, 220, 152), '게임 그만둘래?', 18), ((30, 158, 230, 184), '저장 못 하는데?', 18)]:
        im = clear(im, box); im = put(im, t, box, w='H', size=sz, color=ink)
    return im


@spec('CALENDER__C_END_KK.SVR', 'CALENDER__C_KK.TRA_07')
def end_kk(im): return _end(im, KK_INK)


@spec('CALENDER__C_END_NJ.SVR', 'CALENDER__C_NJ.TRA_07')
def end_nj(im): return _end(im, NJ_INK)


def _dotchi(im, ink, bgsrc):
    box = (36, 124, 160, 142)
    bg = tuple(int(v) for v in np.array(im)[126, 30])
    im = clear(im, box, bg)
    return put(im, '어느 쪽으로 할래?', box, w='H', size=16, color=ink)


@spec('CALENDER__C_KK.TRA_01', 'CALENDER__C_KK01.SVR')
def dotchi_kk(im): return _dotchi(im, (126, 0, 18, 255), (36, 152, 160, 176))


@spec('CALENDER__C_NJ.TRA_01', 'CALENDER__C_NJ01.SVR')
def dotchi_nj(im): return _dotchi(im, (39, 62, 52, 255), (36, 152, 160, 176))


def _found(im, who, ink):
    box = (0, 212, 192, 238)
    im = clear(im, box)
    im = put(im, '찾은 꼬마%s:' % who, box, w='H', size=18, color=(230, 230, 230, 255), stroke=2, stroke_color=ink, align='l')
    box = (226, 212, 256, 238); im = clear(im, box)
    return put(im, '마리', box, w='H', size=15, color=(230, 230, 230, 255), stroke=2, stroke_color=ink, fit=True)


@spec('CALENDER__C_KK.TRA_04', 'CALENDER__C_KK02.SVR')
def found_kk(im): return _found(im, '카카토', (40, 60, 80, 255))


@spec('CALENDER__C_NJ.TRA_04', 'CALENDER__C_NJ02.SVR')
def found_nj(im): return _found(im, '네지', (40, 60, 80, 255))


# 월 표시: '月' 자리를 '월'로 (숫자는 그대로). 큰 글자 밝은 회색 + 남색 테두리
MONTH_FILL = (217, 217, 217, 255); MONTH_EDGE = (1, 47, 83, 255)


def _wol(im, boxes, size=30):
    for box in boxes:
        im = clear(im, box)
        im = put(im, '월', box, w='H', size=size, color=MONTH_FILL, stroke=2, stroke_color=MONTH_EDGE)
    return im


@spec('CALENDER__C_KK.TRA_02', 'CALENDER__C_NJ.TRA_02', 'CALENDER__C_MONTHS01.SVR')
def months1(im):
    boxes = [(70, 10, 106, 48), (200, 10, 236, 48), (74, 58, 110, 96), (200, 58, 236, 96), (74, 106, 110, 144),
             (200, 106, 236, 144), (74, 154, 110, 192), (200, 154, 236, 192), (74, 202, 110, 240), (212, 202, 248, 240)]
    return _wol(im, boxes)


@spec('CALENDER__C_KK.TRA_03', 'CALENDER__C_NJ.TRA_03', 'CALENDER__C_MONTHS02.SVR')
def months2(im):
    im = _wol(im, [(84, 10, 120, 48), (210, 10, 246, 48)])
    # ナビ一覧 → 내비 목록
    box = (0, 112, 144, 150); im = clear(im, box)
    im = put(im, '내비 목록', box, w='H', size=26, color=MONTH_FILL, stroke=2, stroke_color=MONTH_EDGE, align='l')
    return _months_stamps(im)


# 버튼 안내: ケッテイ/モドル/ナビ
def _dog(im, ink):
    for box, t in [((20, 208, 80, 232), '결정'), ((100, 208, 164, 232), '결정'), ((194, 208, 244, 232), '취소'),
                   ((114, 232, 176, 256), '결정'), ((206, 232, 244, 256), '내비')]:
        im = clear(im, box); im = put(im, t, box, w='H', size=17, color=ink)
    return im


@spec('CALENDER__L_DOG.SVR')
def dog(im): return _dog(im, (0, 47, 83, 255))


@spec('CALENDER__L_DOG_KK.SVR')
def dog_kk(im): return _dog(im, (86, 8, 73, 255))


@spec('CALENDER__L_DOG_NJ.SVR')
def dog_nj(im): return _dog(im, (16, 72, 68, 255))


@spec('CALENDER__NAVI_A.SVR')
def navi_a(im):
    ink = (42, 36, 32, 255)
    for box, t in [((98, 212, 156, 240), '보기'), ((180, 212, 250, 240), '돌아가기')]:
        im = clear(im, box); im = put(im, t, box, w='B', size=19, color=ink, align='l')
    return im


# 사운드 컬렉션
SC_FILL = (226, 216, 158, 255); SC_EDGE = (143, 11, 31, 255)


@spec('EXTEND__SC_TITLE.SVR')
def sc_title(im):
    rows = [((50, 6, 236, 44), '세라니 포지'), ((50, 54, 236, 92), '세라니 축제'), ((50, 102, 244, 140), '텔레비전 12'),
            ((50, 150, 166, 188), '라디오'), ((50, 198, 166, 236), '피아노')]
    for box, t in rows:
        im = clear(im, box); im = put(im, t, box, w='H', size=27, color=SC_FILL, stroke=3, stroke_color=SC_EDGE, align='l')
    return im


@spec('EXTEND__SOUND_C01.SVR')
def sound_c01(im):
    box = (0, 48, 166, 72); im = clear(im, box, (207, 160, 52, 255))
    im = put(im, '다음 상까지 앞으로', box, w='H', size=17, color=(107, 0, 14, 255), align='l')
    box = (218, 46, 246, 74); im = clear(im, box, (207, 160, 52, 255))
    return put(im, '개', box, w='H', size=19, color=(107, 0, 14, 255))


@spec('EXTEND__SOUND_C02.SVR')
def sound_c02(im):
    ink = (86, 8, 73, 255)
    im = clear(im, (26, 232, 92, 256)); im = put(im, '결정', (26, 232, 92, 256), w='H', size=17, color=ink, align='l')
    im = clear(im, (116, 232, 170, 256)); im = put(im, '취소', (118, 232, 170, 256), w='H', size=17, color=ink, align='l')
    return im


# 엿보기 점수 화면
def _score(im):
    rows = [((48, 2, 146, 26), '클릭 수', (60, 26, 103, 255)), ((148, 2, 252, 26), '세라니 지수', (107, 0, 14, 255)),
            ((48, 27, 146, 52), '유효 클릭', (16, 70, 40, 255)), ((146, 27, 252, 52), '총 클릭 수', (1, 47, 83, 255)),
            ((48, 52, 146, 76), '짜증 클릭', (191, 21, 51, 255)), ((146, 52, 252, 76), '종합 점수', (1, 47, 83, 255))]
    for box, t, c in rows:
        im = clear(im, box); im = put(im, t, box, w='H', size=19, color=c, align='l')
    for box, t in [((192, 120, 215, 150), '월'), ((216, 120, 240, 150), '일')]:
        im = clear(im, box); im = put(im, t, box, w='H', size=18, color=(226, 237, 217, 255), stroke=2, stroke_color=(1, 47, 83, 255))
    for box, t in [((28, 166, 196, 200), '당신의 엿보기'), ((24, 200, 190, 232), '지수 체크')]:
        im = clear(im, box); im = put(im, t, box, w='H', size=28, color=(226, 237, 217, 255), stroke=3, stroke_color=(1, 47, 83, 255), align='l')
    return im


@spec('INFO__SCORE_KK02.SVR', 'INFO__SCORE_NJ02.SVR')
def score(im): return _score(im)


# 감정 지수(레이더 그래프) 라벨: 기울어진 세로 글자
def _tilt(im, cells, ink, size=15, angle=70):
    for (x0, y0, x1, y1), t in cells:
        im = clear(im, (x0, y0, x1, y1))
        lay = text_layer(t, w='H', size=size, color=ink).rotate(angle, expand=True, resample=Image.BICUBIC)
        lay.thumbnail((x1 - x0, y1 - y0))
        im = im.copy(); im.alpha_composite(lay, (x0 + (x1 - x0 - lay.width) // 2, y0 + (y1 - y0 - lay.height) // 2))
    return im


@spec('INFO__AFFECTIVITY01.SVR')
def aff1(im):
    ink = (76, 18, 94, 255)
    top = ['느긋도', '의욕도', '애니마도', '우봇도', '사이코도']; bot = ['러블리도', '평범도', '꿈추구도', '엉뚱도', '융단도']
    cells = [((k * 48, 2, k * 48 + 48, 90), t) for k, t in enumerate(top)] + [((k * 48, 108, k * 48 + 48, 202), t) for k, t in enumerate(bot)]
    return _tilt(im, cells, ink)


@spec('INFO__AFFECTIVITY02.SVR')
def aff2(im):
    ink = (107, 0, 14, 255)
    top = ['보은도', '신랑도', '꼬마꼬마도', '마루몬도', '꾸준도']
    im = _tilt(im, [((k * 48, 2, k * 48 + 48, 92), t) for k, t in enumerate(top)], ink)
    im = clear(im, (0, 88, 256, 100))
    rows = [((4, 104, 106, 128), '마이니도'), ((112, 104, 220, 128), '스마일리도'), ((4, 128, 106, 152), '토끼도'),
            ((112, 128, 220, 152), '가슴구멍도'), ((4, 152, 106, 176), '원룸도'), ((112, 152, 220, 176), '물고기도'),
            ((4, 176, 106, 200), '해피엔딩도'), ((4, 200, 106, 224), '러브레이도'), ((4, 224, 106, 248), '삐뽀삐뽀도')]
    for box, t in rows:
        im = clear(im, box); im = put(im, t, box, w='H', size=18, color=ink, align='l')
    return im


@spec('EXTEND__SERANI01.SVR')
def serani01(im):
    for box, t in [((48, 160, 232, 208), '네지 혼잣말'), ((48, 208, 240, 256), '카카토 혼잣말')]:
        im = clear(im, box); im = put(im, t, box, w='H', size=27, color=SC_FILL, stroke=3, stroke_color=SC_EDGE, align='l')
    return im


@spec('EXTEND__SERANI02.SVR')
def serani02(im):
    box = (50, 216, 168, 254); im = clear(im, box)
    return put(im, '전화', box, w='H', size=27, color=SC_FILL, stroke=3, stroke_color=SC_EDGE, align='l')


# 라디오·전화 메뉴의 「留」(부재중 메시지) 공 아이콘 → '부'
@spec('EXTEND__RAD_TEL.SVR')
def rad_tel(im):
    import cv2
    a = np.array(im)
    for cx, cy, ink in [(184, 168, (20, 150, 110, 255)), (184, 216, (235, 110, 40, 255))]:
        x0, y0, x1, y1 = cx - 11, cy - 11, cx + 11, cy + 11
        sub = a[y0:y1, x0:x1]; c = sub[..., :3].astype(int)
        yy, xx = np.mgrid[y0:y1, x0:x1]; r = np.hypot(xx - cx, yy - cy)
        ref = np.median(c[(r > 7) & (r < 9.5) & (sub[..., 3] > 100)], 0)
        m = (np.abs(c - ref).sum(2) > 70) & (r < 10) & (sub[..., 3] > 100)
        m = cv2.dilate(m.astype(np.uint8) * 255, np.ones((2, 2), np.uint8))
        sub[..., :3] = cv2.inpaint(np.ascontiguousarray(sub[..., :3]), m, 4, cv2.INPAINT_TELEA)
        a[y0:y1, x0:x1] = sub
        break
    yy, xx = np.mgrid[-11:11, -11:11]; disk = np.hypot(xx, yy) < 10.5   # 아래 공은 위 공의 지운 안쪽을 복사
    a[205:227, 173:195][disk] = a[157:179, 173:195][disk]
    im = Image.fromarray(a)
    for cx, cy, ink in [(184, 168, (20, 150, 110, 255)), (184, 216, (235, 110, 40, 255))]:
        im = put(im, '부', (cx - 10, cy - 10, cx + 10, cy + 10), w='H', size=18, color=ink)
    return im


# 타이틀 로고 (TITLE01.TRA: 640x448 화면을 256 조각으로)
def _title_logo(big):
    import cv2
    a = np.array(big)
    rgb = a[..., :3].astype(int)
    reg = np.zeros(a.shape[:2], bool); reg[18:118, 18:610] = True
    white = (rgb.min(2) > 225)
    red = (rgb[..., 0] > 150) & (rgb[..., 1] < 90) & (rgb[..., 2] < 110)
    dark = (rgb.sum(2) < 260)
    m = (white | red | dark) & reg
    m = cv2.dilate(m.astype(np.uint8) * 255, np.ones((5, 5), np.uint8), iterations=2)
    m[~reg] = 0
    bgr = cv2.cvtColor(a[..., :3].astype(np.uint8), cv2.COLOR_RGB2BGR)
    out = cv2.inpaint(bgr, m, 9, cv2.INPAINT_TELEA)
    a[..., :3] = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
    im = Image.fromarray(a)
    RED = (214, 20, 32, 255)
    sh = (40, 20, 40, 160)
    im = put(im, '뉴 룸매니아', (24, 24, 400, 108), w='H', size=72, color=WHITE, stroke=5, stroke_color=RED, shadow=(4, 4, sh), align='l')
    im = put(im, '또르륵 청춘', (402, 58, 600, 108), w='H', size=38, color=RED, stroke=4, stroke_color=WHITE, shadow=(3, 3, sh), align='l')
    return im


GROUPS[('TITLE01',)] = (_title_logo, [('TITLE__TITLE01.TRA_00', (0, 0, 256, 256), (0, 0)), ('TITLE__TITLE01.TRA_01', (0, 0, 256, 256), (256, 0)),
                                       ('TITLE__TITLE01.TRA_04', (0, 0, 128, 256), (512, 0))], (640, 256))


# 그림 위 글자 지우기(주변으로 메움)
def erase(im, box, pred=None, grow=2):
    import cv2
    a = np.array(im); x0, y0, x1, y1 = box
    sub = a[y0:y1, x0:x1].copy(); rgb = sub[..., :3].astype(int)
    m = pred(rgb) if pred else np.ones(sub.shape[:2], bool)
    m = cv2.dilate(m.astype(np.uint8) * 255, np.ones((3, 3), np.uint8), iterations=grow)
    bgr = cv2.cvtColor(sub[..., :3].astype(np.uint8), cv2.COLOR_RGB2BGR)
    sub[..., :3] = cv2.cvtColor(cv2.inpaint(bgr, m, 5, cv2.INPAINT_TELEA), cv2.COLOR_BGR2RGB)
    a[y0:y1, x0:x1] = sub
    return Image.fromarray(a)


# 상품(ごほうび)
GH_FILL = (254, 246, 193, 255); GH_EDGE = (149, 0, 23, 255)


def _gh(im, box, t, size=19, align='l'):
    im = clear(im, box)
    return put(im, t, box, w='H', size=size, color=GH_FILL, stroke=3, stroke_color=GH_EDGE, align=align, shadow=(2, 2, (200, 40, 60, 255)))


@spec('EXTEND__PRESENT__GOHOUBI_01.SVR')
def gh01(im):
    rows = ['모션 캡처 영상', '하로하로 나리얀스 음두', '성우 인터뷰 네지 편', '세라니 포지 애니메이션 PV',
            '성우 인터뷰 카카토 편', '비밀 이벤트 장면 A', '비밀 이벤트 장면 B', '비밀 하로하로 나리얀스 음두']
    for k, t in enumerate(rows):
        im = clear(im, (0, k * 32, 256, k * 32 + 32))
        im = _gh(im, (4, 2 + k * 32, 254, 28 + k * 32), t)
    return im


@spec('EXTEND__PRESENT__GOHOUBI_02.SVR')
def gh02(im):
    for box, t in [((2, 2, 256, 28), '세라니 축제 스파이럴 다 하이'), ((2, 32, 230, 58), '메슈 하마마츠 물웅덩이'), ((2, 62, 140, 88), '비장 VTR')]:
        im = _gh(im, box, t)
    box = (80, 146, 222, 190); im = clear(im, box)
    return put(im, '보너스', box, w='H', size=36, color=GH_FILL, stroke=4, stroke_color=GH_EDGE, shadow=(3, 3, (200, 40, 60, 255)))


def _btn(im, box, t, size=15):
    ink = (107, 0, 14, 255)
    im = erase(im, box, lambda c: (c.sum(2) < 330) | (c.min(2) > 225))
    return put(im, t, box, w='H', size=size, color=(238, 253, 215, 255), stroke=2, stroke_color=ink)


GH_BTN = {4: ['하로하로|나리얀스 음두', '세라니 축제|스파이럴|다 하이!'], 5: ['성우|인터뷰|네지 편', '세라니 포지|애니메이션 PV'],
          6: ['성우|인터뷰|카카토 편', '비밀 이벤트|장면 A'], 7: ['메슈 하마마츠|물웅덩이', '비밀 이벤트|장면 B'],
          8: ['비밀 하로하로|나리얀스 음두', '비장 VTR']}


def _ghbtn(k):
    def f(im):
        a, b = [x.replace('|', chr(10)) for x in GH_BTN[k]]
        im = _btn(im, (14, 20, 140, 84), a)
        im = _btn(im, (14, 120, 140, 192), b)
        if k == 4:
            ink = (86, 8, 73, 255)
            for box, t in [((190, 184, 256, 210), '취소'), ((66, 224, 150, 250), '확대'), ((176, 224, 256, 250), '축소')]:
                im = clear(im, box); im = put(im, t, box, w='H', size=15, color=(239, 222, 223, 255), stroke=2, stroke_color=ink, align='l')
        return im
    return f


for _k in GH_BTN: SPECS['EXTEND__PRESENT__GOHOUBI_%02d.SVR' % _k] = _ghbtn(_k)


def _seiyuu(im, who, name, ink):
    box = (46, 16, 126, 216); im = erase(im, box, lambda c: c.sum(2) < 600)
    return put(im, who + '의 목소리' + chr(10) + name, box, w='H', size=20, color=ink, vertical=True, line_gap=6)


@spec('EXTEND__PRESENT__SEIYUU_KK02.SVR')
def sy_kk(im): return _seiyuu(im, '카카토', '네모토 사오리', (114, 6, 20, 255))


@spec('EXTEND__PRESENT__SEIYUU_NJ02.SVR')
def sy_nj(im): return _seiyuu(im, '네지', '시미즈 히지리', (9, 55, 91, 255))


@spec('NAVI__NAVI_D.SVR')
def navi_d(im):
    W = (240, 240, 240, 255)
    for box, t, sz in [((0, 4, 66, 32), '꼬마카카토', 11), ((0, 34, 66, 74), '꼬마네지', 12)]:
        im = clear(im, box); im = put(im, t, box, w='R', size=sz, color=W)
    im = erase(im, (40, 100, 86, 128), lambda c: c.min(2) > 180)
    im = put(im, '마리', (40, 100, 86, 128), w='R', size=15, color=W)
    im = erase(im, (6, 146, 120, 176), lambda c: c.min(2) > 180)
    im = put(im, '잡았다', (6, 146, 120, 176), w='R', size=17, color=W, align='l')
    ink = (40, 40, 40, 255)
    for box, t in [((150, 204, 256, 230), '보기'), ((150, 232, 256, 256), '돌아가기')]:
        im = clear(im, (176, box[1] - 6, 256, box[3])); im = put(im, t, (176, box[1], 256, box[3]), w='B', size=17, color=ink, align='l')
    return im


# 점수 화면 원형 라벨(うれしい度 등): 원을 따라 글자를 돌려 그림
def _arc(im, text, cx, cy, r, ang_mid, ink, size=15, step=None):
    import math
    ft = text_layer  # noqa
    step = step or (size + 1) / r * 180 / math.pi
    bottom = 20 < ang_mid < 160
    if bottom: step = -step                       # 아래쪽은 똑바로 읽히게 왼→오(반시계)
    a0 = ang_mid - step * (len(text) - 1) / 2
    for k, ch in enumerate(text):
        deg = a0 + step * k; a = math.radians(deg)
        rot = -(deg - 90) if bottom else -(deg + 90)
        lay = text_layer(ch, w='H', size=size, color=ink).rotate(rot, expand=True, resample=Image.BICUBIC)
        x = cx + r * math.cos(a) - lay.width / 2; y = cy + r * math.sin(a) - lay.height / 2
        im = im.copy(); im.alpha_composite(lay, (int(round(x)), int(round(y))))
    return im


def _score3(im):
    import cv2
    a = np.array(im); h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]; rr = np.hypot(xx - 122, yy - 113)
    band = (rr > 84) & (rr < 102)
    rgb = a[..., :3].astype(int)
    txt = band & ~((np.abs(rgb - [231, 225, 188]).sum(2) < 22))
    m = cv2.dilate(txt.astype(np.uint8) * 255, np.ones((3, 3), np.uint8), iterations=2); m[~band] = 0
    a[..., :3][band & (m > 0)] = (231, 225, 188); m[:] = 0
    bgr = cv2.cvtColor(a[..., :3].astype(np.uint8), cv2.COLOR_RGB2BGR)
    a[..., :3] = cv2.cvtColor(cv2.inpaint(bgr, m, 4, cv2.INPAINT_TELEA), cv2.COLOR_BGR2RGB)
    im = Image.fromarray(a)
    for t, ang, ink in [('기쁨도', -90, (190, 110, 10, 255)), ('당찬도', -8, (120, 20, 110, 255)),
                        ('슬픔도', 55, (20, 140, 70, 255)), ('분노도', 126, (20, 80, 170, 255))]:
        im = _arc(im, t, 122, 113, 94, ang, ink, size=16)
    return im


@spec('INFO__SCORE_KK03.SVR', 'INFO__SCORE_NJ03.SVR')
def score3(im): return _score3(im)


@spec('INFO__SCORE_KK01.SVR', 'INFO__SCORE_NJ01.SVR')
def score1(im):
    box = (190, 230, 256, 256); im = clear(im, box)
    return put(im, '건너뛰기', box, w='H', size=16, color=(40, 20, 40, 255), align='l')


# 済/失 도장 → 완/실
def _stamp(im, cx, cy, r, ch, inner, ink, edge=None, size=None):
    a = np.array(im); h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]; m = np.hypot(xx - cx, yy - cy) < r
    a[m] = inner if inner is not None else (0, 0, 0, 0)
    im = Image.fromarray(a)
    sz = size or int(r * 1.5)
    R = max(r, sz * 0.6)
    box = (int(cx - R), int(cy - R), int(cx + R), int(cy + R))
    return put(im, ch, box, w='H', size=sz, color=ink, stroke=2 if edge else 0, stroke_color=edge or (0, 0, 0, 0))


@spec('NAVI__NAVISYS.SVR')
def navisys(im):
    return _stamp(im, 31, 31, 25, '완', (255, 0, 0, 255), (255, 216, 0, 255), (7, 8, 5, 255))


@spec('CALENDER__NAVI_B.SVR')
def navi_b(im):
    from PIL import ImageDraw
    a = np.array(im); a[134:204, 64:212] = 0; im = Image.fromarray(a); d = ImageDraw.Draw(im)
    for cx, col in [(98, (200, 30, 30, 255)), (173, (0, 120, 200, 255))]:
        d.ellipse((cx - 30, 168 - 30, cx + 30, 168 + 30), outline=(40, 0, 0, 255) if cx < 150 else (0, 30, 70, 255), width=5)
        d.ellipse((cx - 29, 168 - 29, cx + 29, 168 + 29), outline=col, width=3)
    im = _stamp(im, 98, 168, 1, '완', None, (200, 30, 30, 255), (80, 0, 0, 255), 36)
    return _stamp(im, 173, 168, 1, '실', None, (0, 120, 200, 255), (0, 40, 90, 255), 36)


def _months_stamps(im):
    a = np.array(im)
    disc = tuple(int(v) for v in a[56, 161])
    im = _stamp(im, 161, 79, 22, '완', disc, (170, 30, 20, 255), None, 30)
    return _stamp(im, 224, 79, 26, '실', None, (40, 170, 170, 255), (0, 60, 70, 255), 34)


@spec('EXTEND__CONGRA01.SVR', 'EXTEND__CONGRA02.SVR')
def congra(im):
    a = np.array(im)
    rib = (a[..., 3] > 200) & (np.abs(a[..., :3].astype(int) - 230).sum(2) < 30)
    # 리본 안쪽 글자(검정·빨강) 지우기: 리본 폭 안의 비흰색 픽셀을 흰색으로
    sub = a[40:215, 112:152]; rgb = sub[..., :3].astype(int)
    txt = (sub[..., 3] > 100) & ((rgb.sum(2) < 300) | ((rgb[..., 0] > 150) & (rgb[..., 1] < 80)))
    import cv2
    txt = cv2.dilate(txt.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    sub[txt] = (230, 230, 230, 255); a[40:215, 112:152] = sub
    im = Image.fromarray(a)
    im = put(im, '일단은', (116, 52, 150, 160), w='H', size=19, color=(20, 20, 20, 255), vertical=True)
    return put(im, '축하', (116, 164, 150, 212), w='H', size=17, color=(200, 20, 30, 255), vertical=True)


@spec('EXTEND__PRESENT__GOHOUBI_03.SVR')
def gh03(im):
    box = (20, 128, 150, 176)
    im = erase(im, box, lambda c: (c[..., 0] > 100) & (c[..., 1] < 90) | (c.min(2) > 200))
    return put(im, '모션 캡처' + chr(10) + '영상', box, w='H', size=17, color=(240, 230, 200, 255), stroke=2, stroke_color=(119, 12, 26, 255), line_gap=-2)


# 네지 PC 화면: 메일 프로그램 메뉴·상태줄, 왼쪽 폴더 목록 (작은 글씨)
def _tiny(im, box, t, color=(0, 0, 0, 255), bg=None, size=8, align='l', w='B'):
    im = clear(im, box, bg if bg is not None else tuple(int(v) for v in np.array(im)[box[1], box[0]]))
    return put(im, t, box, w=w, size=size, color=color, align=align)


def _pc_side(im):
    for k, t in enumerate(['받은편지', '보낸편지', '즐겨찾기', '휴지통']):
        y = 41 + k * 8
        im = _tiny(im, (10, y, 28, y + 8), t, bg=(255, 255, 255, 255), size=6)
    return im


@spec('ETC__PC_F00.TRA_03')
def pc_mail(im):
    for x0, x1, t in [(98, 116, '송신'), (118, 144, '파일'), (148, 166, '편집'), (170, 186, '첨부'), (190, 206, '기능'), (208, 230, '도움말')]:
        im = _tiny(im, (x0, 4, x1, 12), t, bg=(255, 255, 255, 255), size=7)
    im = _tiny(im, (38, 246, 108, 255), '새 메일 2통이 있습니다', bg=(223, 223, 223, 255), size=7)
    return _pc_side(im)


@spec('ETC__PC_F00.TRA_02')
def pc_web(im):
    return _pc_side(im)


def _wp(im, items):
    """웹페이지 글자 교체: (상자, 글, 크기, 색, 배경(None=주변 지우기))"""
    for it in items:
        box, t, sz, col, bg = it[:5]; al = it[5] if len(it) > 5 else 'l'
        if bg == 'p':    # 상자를 주변 평균색으로 채움
            a = np.array(im); x0, y0, x1, y1 = box
            ring = np.concatenate([a[max(0, y0 - 3):y0, x0:x1].reshape(-1, 4), a[y1:y1 + 3, x0:x1].reshape(-1, 4)])
            im = clear(im, box, tuple(int(v) for v in np.median(ring, 0)))
        elif bg is None:   # 글자(배경과 다른 픽셀)만 주변으로 메움
            a = np.array(im); x0, y0, x1, y1 = box; sub = a[y0:y1, x0:x1, :3].astype(int)
            ring = np.concatenate([a[max(0, y0 - 2):y0, x0:x1, :3].reshape(-1, 3), a[y1:y1 + 2, x0:x1, :3].reshape(-1, 3)])
            ref = np.median(ring, 0) if len(ring) else np.median(sub.reshape(-1, 3), 0)
            im = erase(im, box, lambda c, ref=ref: np.abs(c - ref).sum(2) > 60, grow=1)
        else:
            im = clear(im, box, bg)
        im = put(im, t, box, w='H', size=sz, color=col, align=al)
    return im


@spec('ETC__PC_S01.TRA_04')
def pc_s01(im):
    R = (215, 30, 40, 255); K = (30, 20, 20, 255)
    im = _wp(im, [((48, 116, 110, 127), '5월 8일', 10, K, None),
                    ((48, 128, 150, 139), '도리코시 백화점 7층', 10, K, None),
                    ((48, 139, 150, 150), '이벤트홀에서', 10, K, None),
                    ((48, 149, 236, 161), '초코피그 프리미엄 팩 세일 개최!', 10, K, None),
                    ((48, 160, 140, 169), '한정 20000세트', 8, K, None),
                    ((48, 169, 206, 178), '(1인 2세트까지 구매 가능합니다)', 8, K, None),
                    ((40, 36, 242, 46), '신작 정보  상품 안내  회사 소개  채용 안내  지도  뉴스', 7, (255, 240, 240, 255), (225, 40, 50, 255), 'c'),
                    ((40, 225, 80, 233), '톱으로', 7, (255, 240, 240, 255), (225, 40, 50, 255), 'c'),
                    ((200, 225, 240, 235), '뿌루타 제과', 8, R, None, 'c')])
    # 비스듬한 빨간 문구
    from PIL import ImageDraw
    a = np.array(im); sub = a[185:215, 70:230]; rgb = sub[..., :3].astype(int)
    red = (rgb[..., 0] > 170) & (rgb[..., 1] < 110)
    import cv2
    m = cv2.dilate(red.astype(np.uint8) * 255, np.ones((3, 3), np.uint8), iterations=1)
    bgr = cv2.cvtColor(sub[..., :3].astype(np.uint8), cv2.COLOR_RGB2BGR)
    sub[..., :3] = cv2.cvtColor(cv2.inpaint(bgr, m, 3, cv2.INPAINT_TELEA), cv2.COLOR_BGR2RGB); a[185:215, 70:230] = sub
    im = Image.fromarray(a)
    lay = text_layer('환상의 로드리게스 시리즈도 입하 예정!', w='H', size=11, color=R, stroke=1, stroke_color=(255, 255, 255, 255)).rotate(8, expand=True, resample=Image.BICUBIC)
    im = im.copy(); im.alpha_composite(lay, (72, 186))
    # 초코피그 로고
    a = np.array(im); sub = a[56:110, 54:126]; rgb = sub[..., :3].astype(int)
    logo = ((rgb[..., 0] > 180) & (rgb[..., 1] < 120)) | ((rgb[..., 0] > 200) & (rgb[..., 1] > 180) & (rgb[..., 2] < 120)) | (rgb.sum(2) < 200)
    import cv2
    m = cv2.dilate(logo.astype(np.uint8) * 255, np.ones((3, 3), np.uint8), iterations=2)
    bgr = cv2.cvtColor(sub[..., :3].astype(np.uint8), cv2.COLOR_RGB2BGR)
    sub[..., :3] = cv2.cvtColor(cv2.inpaint(bgr, m, 5, cv2.INPAINT_TELEA), cv2.COLOR_BGR2RGB); a[56:110, 54:126] = sub
    im = Image.fromarray(a)
    im = put(im, '초코', (56, 58, 98, 76), w='H', size=13, color=(230, 30, 40, 255), stroke=2, stroke_color=(255, 230, 60, 255))
    im = put(im, '피그', (56, 74, 126, 108), w='H', size=28, color=(230, 30, 40, 255), stroke=3, stroke_color=(255, 255, 255, 255))
    return im


@spec('ETC__PC_S02.TRA_06')
def pc_s02(im):
    K = (40, 40, 40, 255)
    return _wp(im, [((72, 38, 186, 59), '아동복지센터', 15, K, (250, 250, 250, 255), 'c'),
                    ((78, 89, 107, 98), '당신은', 7, K, None),
                    ((146, 89, 200, 98), '번째 방문자입니다', 7, K, None),
                    ((88, 125, 132, 135), '어린이 페이지', 7, K, None),
                    ((88, 139, 132, 149), '시설 소개', 7, K, None),
                    ((88, 153, 132, 163), '상담실', 7, K, None),
                    ((88, 167, 132, 177), '문의하기', 7, K, None),
                    ((50, 223, 166, 233), '의견·요망 사항은 이쪽으로→', 7, K, None),
                    ((178, 222, 234, 234), '센터 홈페이지로', 6, (250, 250, 250, 255), (130, 110, 200, 255), 'c')])


@spec('ETC__PC_S03.TRA_05')
def pc_s03b(im):
    K = (20, 20, 20, 255); Wt = (230, 230, 255, 255)
    return _wp(im, [((86, 32, 250, 44), '사이코 치쿠와 개발 홈페이지', 9, Wt, (148, 152, 220, 255), 'c'),
                    ((84, 46, 252, 72), '사이코 치쿠와 (가칭)', 16, K, (255, 255, 255, 255)),
                    ((38, 79, 84, 93), '기획 노트', 7, Wt, (148, 152, 220, 255)),
                    ((38, 96, 84, 110), '판촉 예정표', 7, Wt, (148, 152, 220, 255)),
                    ((38, 113, 84, 127), '연구 자료', 7, Wt, (148, 152, 220, 255)),
                    ((38, 130, 84, 144), '링크', 7, Wt, (148, 152, 220, 255)),
                    ((135, 181, 193, 191), '스케줄표로', 7, K, (210, 210, 210, 255), 'c'),
                    ((112, 213, 191, 225), '야세탄 식품 주식회사', 8, K, None)])


@spec('ETC__PC_S03.TRA_04')
def pc_s03a(im):
    K = (40, 40, 40, 255)
    im = _wp(im, [((54, 32, 224, 64), '길모퉁이 라면 워커', 17, (110, 120, 200, 255), 'p', 'c'),
                  ((52, 78, 146, 91), '역에서 20분, 세련된 가게', 8, K, 'p'),
                  ((112, 231, 162, 240), '오늘의 메뉴', 7, K, (220, 220, 220, 255), 'c')])
    return im


@spec('ETC__PC_S06_0.TRA_04', 'ETC__PC_S06_1.TRA_04')
def pc_bank(im):
    R = (200, 30, 30, 255); K = (40, 40, 40, 255)
    im = _wp(im, [((40, 33, 112, 45), '팔백팔은행', 10, K, (255, 255, 255, 255)),
                  ((88, 86, 236, 96), '인터넷 뱅킹 가입 신청은 이쪽으로', 7, R, 'p')])
    for k, t in enumerate(['종합 안내', '점포 안내', '주요 거래처', '회사 소개', '채용 안내', 'Q&A']):
        y = 92 + k * 7
        im = _wp(im, [((44, y, 82, y + 7), t, 6, R, (160, 240, 160, 255))])
    for k, t in enumerate(['서비스 안내', '종합 계좌', '신청 안내', '휴대폰 뱅킹', '복권']):
        y = 104 + k * 7
        im = _wp(im, [((103, y, 146, y + 7), t, 6, K, 'p')])
    for k, (a, b) in enumerate([('보통예금', '주택 대출'), ('정기예금', '교육 대출'), ('외화예금', '신차 대출'),
                                ('투자신탁', '다목적 대출'), ('금융채', '카드론')]):
        y = 165 + k * 7
        im = _wp(im, [((103, y, 134, y + 7), a, 6, K, 'p'), ((145, y, 194, y + 7), b, 6, K, 'p')])
    for k, t in enumerate(['대출 상환', '해외여행 보험']):
        y = 200 + k * 7
        im = _wp(im, [((145, y, 194, y + 7), t, 6, K, 'p')])
    return im


@spec('ETC__PC_F05.TRA_04')
def pc_award(im):
    K = (60, 60, 60, 255)
    return _wp(im, [((176, 32, 250, 47), '마키즈키사', 12, (255, 255, 255, 255), (235, 150, 110, 255), 'c'),
                    ((80, 70, 202, 88), '마키즈키사 만화 대상', 12, (150, 150, 150, 255), 'p', 'c'),
                    ((82, 89, 116, 102), '대상', 11, (230, 30, 30, 255), 'p'),
                    ((82, 103, 124, 146), '상금', 18, (60, 60, 60, 255), 'p'),
                    ((166, 103, 200, 146), '만엔', 16, (60, 60, 60, 255), 'p'),
                    ((86, 152, 152, 157), '소년 만화 부문', 6, K, 'p'),
                    ((86, 157, 152, 162), '청년 만화 부문', 6, K, 'p'),
                    ((86, 162, 152, 170), '소녀 만화 부문', 6, K, 'p'),
                    ((205, 49, 248, 56), '이달의 신간', 6, (150, 110, 0, 255), 'p', 'c')])


@spec('ETC__PC_S09.TRA_04')
def pc_sekizou(im):
    B = (140, 140, 230, 255)
    return _wp(im, [((80, 175, 160, 194), '수수께끼의 석상 53세', 10, B, 'p'),
                    ((180, 182, 222, 194), '최저 입찰가', 7, (60, 60, 60, 255), 'p'),
                    ((238, 178, 250, 194), '엔', 8, B, 'p')])


@spec('ETC__PC_S02.TRA_05')
def pc_gallery(im):
    Wt = (230, 230, 230, 255)
    return _wp(im, [((32, 36, 78, 49), 'TOP', 8, Wt, (0, 0, 0, 255)),
                    ((32, 49, 78, 68), '신작 정보', 7, Wt, (0, 0, 0, 255)),
                    ((32, 84, 78, 96), 'BBS', 7, Wt, (0, 0, 0, 255)),
                    ((32, 70, 78, 82), '갤러리', 7, Wt, (0, 0, 0, 255)),
                    ((32, 96, 78, 108), '링크 모음', 7, Wt, (0, 0, 0, 255))])


@spec('ETC__PC_S13.TRA_05')
def pc_iso(im):
    return _wp(im, [((88, 96, 184, 106), '이소플라본이 뭐야?', 10, (20, 20, 20, 255), 'p')])


@spec('ETC__PC_F03.TRA_05')
def pc_sekizou2(im):
    return _search(im, bid=True)


# 검색 엔진(yapoo!) 페이지: 상단 배너 「おともだち探し」, 입찰 칸 「最低入札額」
def _search(im, bid=False):
    D = (60, 60, 60, 255)
    its = [((143, 55, 187, 62), '친구 찾기', 7, D, (255, 255, 255, 255), 'c')]
    if bid: its += [((99, 196, 125, 204), '최저 입찰가', 6, D, 'p', 'r'), ((99, 211, 125, 219), '최저 입찰가', 6, D, 'p', 'r')]
    return _wp(im, its)


@spec('ETC__PC_F03.TRA_04')
def pc_search_dog(im): return _search(im)


@spec('ETC__PC_S05.TRA_06')
def pc_search_book(im): return _search(im, bid=True)


# 웹 브라우저 왼쪽 즐겨찾기 목록(웹페이지 그림마다 들어 있음)
_SIDE_REF = None


def _web_side(im):
    for k, t in enumerate(['받은편지', '보낸편지', '즐겨찾기', '휴지통']):
        y = 42 + k * 8
        im = _tiny(im, (8, y, 24, y + 8), t, bg=(255, 255, 255, 255), size=6)
    return im


def _add_web_side(tex):
    ref = pvrimg.decode(tex['ETC__PC_F03.TRA_05'][2], tex['ETC__PC_F03.TRA_05'][1])[0][40:76, 6:24].astype(int)
    n_ = 0
    for n, (rel, o, d) in tex.items():
        if not n.startswith('ETC__PC_') or n.endswith(('_00', '_01', '_02', '_03')): continue
        try: a = pvrimg.decode(d, o)[0]
        except Exception: continue
        if a.shape[0] < 76 or np.abs(a[40:76, 6:24].astype(int) - ref).mean() > 6: continue
        f = SPECS.get(n)
        SPECS[n] = (lambda f: (lambda im: _web_side(f(im) if f else im)))(f); n_ += 1
    print('웹 즐겨찾기 목록', n_)


import manga
for _p, _caps in manga.PAGES.items():
    GROUPS[('MANGA', _p)] = ((lambda caps: (lambda big: manga.render_page(big, caps)))(_caps), manga.layout(_p), (512, 768))


if __name__ == '__main__':
    r = build(sys.argv[1:] or None); print(len(r), list(r)[:5])
