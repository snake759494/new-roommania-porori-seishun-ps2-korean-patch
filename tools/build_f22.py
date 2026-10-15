"""F22 비트맵 폰트에 한글 2,350자를 1수준 한자 슬롯에 그려 넣는다(나눔스퀘어네오 Bold 21px, 16단계 안티앨리어싱)."""
import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
import f22, kmap
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TTF = os.path.join(ROOT, 'NanumSquareNeo-cBd.ttf'); SIZE = 21
CX, CY = 10.5, 11.0     # 원본 한자 잉크 박스 중심(셀 22x22)
_ft = None
def render(ch, extra=None):
    global _ft
    _ft = _ft or ImageFont.truetype(TTF, SIZE * 4)
    im = Image.new('L', (88 * 3, 88 * 3))
    ImageDraw.Draw(im).text((132, 132), ch, font=_ft, fill=255, anchor='mm')
    a = np.array(im); ys, xs = np.nonzero(a > 40)
    cx = (xs.min() + xs.max()) / 2 / 4; cy = (ys.min() + ys.max()) / 2 / 4
    im = im.resize((66, 66), Image.BOX)
    a = np.array(im, float)
    # 잉크 중심을 (CX,CY) 로: 정수 이동
    dx = int(round(CX - cx)) ; dy = int(round(CY - cy))
    out = np.zeros((22, 22), float)
    for y in range(22):
        for x in range(22):
            sy, sx = y - dy, x - dx
            if 0 <= sy < 66 and 0 <= sx < 66: out[y, x] = a[sy, sx]
    return np.clip(out / 255 * 15 + 0.5, 0, 15).astype(np.uint8)
def build(src_dir):
    """F22_001.TRA 바이트(한글 적용) 반환"""
    d = bytearray(open(os.path.join(src_dir, 'F22_001.TRA'), 'rb').read())
    pages = f22.pages(bytes(d)); arrs = [p[1].copy() for p in pages]
    for ch, code in kmap.CM.items():
        fn, i = kmap.f22_index(code); assert fn == 1
        pg, k = divmod(i, 121); y, x = divmod(k, 11)
        arrs[pg][y*22:y*22+22, x*22:x*22+22] = render(ch)
    for (o, _), a in zip(pages, arrs): d[o:o+32768] = f22.encode(a)
    return bytes(d), arrs
def build000(src_dir):
    """F22_000.TRA: 좁은 띄어쓰기 코드(kmap.NARROW) 칸을 빈 글리프로"""
    d = bytearray(open(os.path.join(src_dir, 'F22_000.TRA'), 'rb').read())
    pages = f22.pages(bytes(d))
    fn, i = kmap.f22_index(kmap.NARROW); assert fn == 0
    pg, k = divmod(i, 121); y, x = divmod(k, 11)
    o, a = pages[pg]; a = a.copy()
    a[y*22:y*22+22, x*22:x*22+22] = 0
    d[o:o+32768] = f22.encode(a)
    return bytes(d)


if __name__ == '__main__':
    b, arrs = build(os.path.join(ROOT, 'extract/ROOM2/FONT'))
    Image.fromarray(np.concatenate(arrs[:3], 1) * 17).save(os.path.join(ROOT, 'work/f22_ko.png'))
