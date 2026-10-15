"""소형 글꼴 MOZI.SVR(가나, 텍스처0)/MOZI2.SVR(ASCII, 텍스처1) 256x256(16x16 칸)의 빈 칸에 한글 등을 그린다.
게임 매핑(0x291500): 히라가나·가타카나 → 텍스처0 칸(코드 계산), 0x36A4C0 의 94자 → 텍스처1 칸,
그 외 → (elfpatch 후크) 우리 표 [u16 코드, u8 칸, u8 텍스처].
칸 배정 순서: 텍스처1 94~255 → 텍스처0 170~255 → 텍스처0 가나 칸 0~169(■ 칸 146 제외; 번역된 행동 이름에는 가나가 없음)."""
import sys, os, struct, numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
import twiddle, kmap
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TTF = os.path.join(ROOT, 'NanumSquareNeo-bRg.ttf'); SIZE = 15
CELLS = [(1, c) for c in range(94, 256)] + [(0, c) for c in range(170, 256)] + [(0, c) for c in range(0, 170) if c != 146]
_ft = None


def glyph(ch):
    global _ft
    _ft = _ft or ImageFont.truetype(TTF, SIZE * 4)
    if ch in (' ', '　'): return np.zeros((16, 16), np.uint8)
    im = Image.new('L', (64 * 2, 64 * 2))
    ImageDraw.Draw(im).text((64, 64), ch, font=_ft, fill=255, anchor='mm')
    a = np.array(im); ys, xs = np.nonzero(a > 40)
    cx = (xs.min() + xs.max()) / 2 / 4; cy = (ys.min() + ys.max()) / 2 / 4
    im = im.resize((32, 32), Image.BOX); a = np.array(im, float)
    dx = int(round(7.5 - cx)); dy = int(round(7.5 - cy))
    out = np.zeros((16, 16))
    for y in range(16):
        for x in range(16):
            sy, sx = y - dy, x - dx
            if 0 <= sy < 32 and 0 <= sx < 32: out[y, x] = a[sy, sx]
    return np.clip(out / 255 * 15 + 0.5, 0, 15).astype(np.uint8)


def code_of(ch):
    if ch == ' ': return kmap.NARROW
    if ch in kmap.CM: return kmap.CM[ch]
    return int.from_bytes(ch.encode('cp932'), 'big')


def build(chars):
    """chars: 표에 넣을 글자 목록 → ({경로: 바이트}, 표 bytes)"""
    assert len(chars) <= len(CELLS), (len(chars), len(CELLS))
    tex = []
    for f in ('MOZI.SVR', 'MOZI2.SVR'):
        d = open(os.path.join(ROOT, 'extract', 'ROOM2', f), 'rb').read()
        tex.append((d, twiddle.untwiddle4(d[32:32 + 32768], 256, 256).copy()))
    table = b''
    for ch, (t, cell) in zip(chars, CELLS):
        y, x = divmod(cell, 16)
        tex[t][1][y * 16:y * 16 + 16, x * 16:x * 16 + 16] = glyph(ch)
        table += struct.pack('<HBB', code_of(ch), cell, t)
    out = {}
    for f, (d, a) in zip(('MOZI.SVR', 'MOZI2.SVR'), tex):
        out['/' + f] = d[:32] + twiddle.twiddle4(a) + d[32 + 32768:]
    return out, table


if __name__ == '__main__':
    out, t = build(list('한글패치 테스트…'))
    a = twiddle.untwiddle4(out['/MOZI2.SVR'][32:32 + 32768], 256, 256)
    Image.fromarray(a[64:128] * 17).resize((512, 128), Image.NEAREST).save(os.path.join(ROOT, 'work', 'mozi_ko.png'))
