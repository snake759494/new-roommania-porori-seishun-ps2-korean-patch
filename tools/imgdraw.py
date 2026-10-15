"""이미지 재작성 도우미: 영역 지우기(배경색/주변색 채움), 한글 글자 그리기(테두리·그림자·세로쓰기·폭 맞춤)"""
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = {'L': 'NanumSquareNeo-aLt.ttf', 'R': 'NanumSquareNeo-bRg.ttf', 'B': 'NanumSquareNeo-cBd.ttf',
         'EB': 'NanumSquareNeo-dEb.ttf', 'H': 'NanumSquareNeo-eHv.ttf',
         'SB': 'SeoulHangangB.ttf', 'SEB': 'SeoulHangangEB.ttf', 'SM': 'SeoulHangangM.ttf', 'SL': 'SeoulHangangL.ttf'}
_cache = {}


def font(w, size):
    k = (w, size)
    if k not in _cache: _cache[k] = ImageFont.truetype(os.path.join(ROOT, FONTS[w]), size)
    return _cache[k]


def clear(im, box, color=None):
    """box 영역을 color(RGBA)로 채움. color 없으면 투명."""
    x0, y0, x1, y1 = box
    a = np.array(im)
    a[y0:y1, x0:x1] = color if color is not None else (0, 0, 0, 0)
    return Image.fromarray(a)


def fill_like(im, box, src_box):
    """box 영역을 src_box 영역 이미지를 늘려 채움(무늬 배경 지우기용)"""
    src = im.crop(src_box).resize((box[2] - box[0], box[3] - box[1]), Image.NEAREST)
    im = im.copy(); im.paste(src, box[:2]); return im


def fill_row(im, box, sx):
    """box 영역 각 행을 x=sx 열의 색으로 채움(가로 그라데이션 배경용)"""
    a = np.array(im); x0, y0, x1, y1 = box
    a[y0:y1, x0:x1] = a[y0:y1, sx:sx + 1]
    return Image.fromarray(a)


def text_layer(text, w='H', size=20, color=(255, 255, 255, 255), stroke=0, stroke_color=(0, 0, 0, 255),
               spacing=0, vertical=False, line_gap=0):
    """글자만 그린 RGBA 이미지(여백 없이 잘라냄)"""
    ft = font(w, size)
    pad = stroke + 4
    if vertical:
        cols = text.split('\n'); cw = size + spacing
        adv = lambda ch: int(size * 0.4) if ch == ' ' else int(size * 0.55) if ch in '.,、。' else size + spacing
        H = max(sum(adv(ch) for ch in c) for c in cols) + pad * 2
        W = len(cols) * (size + line_gap) + pad * 2
        im = Image.new('RGBA', (W, H)); dr = ImageDraw.Draw(im)
        for ci, col in enumerate(cols):
            x = W - pad - (ci + 1) * (size + line_gap) + line_gap + size // 2
            y = pad
            for k, ch in enumerate(col):
                a = adv(ch)
                if ch == ' ': y += a; continue
                if ch in 'ー－～…': ch = {'ー': '|', '－': '|', '～': '≀', '…': '︙'}.get(ch, ch)
                if ch in '.,、。':
                    dr.text((x + size // 3, y + a // 2 - size // 4), ch, font=ft, fill=color, anchor='mm', stroke_width=stroke, stroke_fill=stroke_color)
                else:
                    dr.text((x, y + a // 2), ch, font=ft, fill=color, anchor='mm', stroke_width=stroke, stroke_fill=stroke_color)
                y += a
    else:
        lines = text.split('\n')
        dummy = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
        widths = [dummy.textlength(l, font=ft) + spacing * max(0, len(l) - 1) for l in lines]
        W = int(max(widths)) + pad * 2; H = len(lines) * (size + line_gap) + pad * 2
        im = Image.new('RGBA', (W, H)); dr = ImageDraw.Draw(im)
        for li, l in enumerate(lines):
            y = pad + li * (size + line_gap) + size // 2
            x = pad + (W - pad * 2 - widths[li]) / 2
            if spacing:
                for ch in l:
                    dr.text((x, y), ch, font=ft, fill=color, anchor='lm', stroke_width=stroke, stroke_fill=stroke_color)
                    x += dummy.textlength(ch, font=ft) + spacing
            else:
                dr.text((x, y), l, font=ft, fill=color, anchor='lm', stroke_width=stroke, stroke_fill=stroke_color)
    bb = im.getbbox()
    return im.crop(bb) if bb else im


def put(im, text, box, align='c', valign='m', fit=True, shadow=None, **kw):
    """box 안에 글자를 그림. fit: 넘치면 가로로 줄여 맞춤. shadow=(dx,dy,RGBA)"""
    x0, y0, x1, y1 = box
    t = text_layer(text, **kw)
    bw, bh = x1 - x0, y1 - y0
    if fit and (t.width > bw or t.height > bh):
        sx = min(1.0, bw / t.width); sy = min(1.0, bh / t.height)
        if kw.get('vertical'): sx, sy = min(sx, sy), sy
        else: sy = min(sy, 1.0)
        t = t.resize((max(1, int(t.width * sx)), max(1, int(t.height * sy))), Image.LANCZOS)
    x = x0 + (0 if align == 'l' else (bw - t.width) if align == 'r' else (bw - t.width) // 2)
    y = y0 + (0 if valign == 't' else (bh - t.height) if valign == 'b' else (bh - t.height) // 2)
    im = im.copy()
    if shadow:
        dx, dy, sc = shadow
        a = np.array(t); s = np.zeros_like(a); s[..., :3] = sc[:3]; s[..., 3] = (a[..., 3].astype(int) * sc[3] // 255)
        im.alpha_composite(Image.fromarray(s), (x + dx, y + dy))
    im.alpha_composite(t, (x, y))
    return im


def ink_color(im, box, bg=None):
    """box 안에서 가장 많이 쓰인 불투명 색(글자색 추정)"""
    a = np.array(im.crop(box)).reshape(-1, 4)
    a = a[a[:, 3] > 200]
    if bg is not None: a = a[np.abs(a[:, :3].astype(int) - bg[:3]).sum(1) > 60]
    if len(a) == 0: return (255, 255, 255, 255)
    v, c = np.unique(a, axis=0, return_counts=True)
    return tuple(int(x) for x in v[c.argmax()])
