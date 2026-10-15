"""ROOM2 의 모든 텍스처를 work/img/*.png 로, 목록은 work/img_list.json, 일람표 work/sheet_*.png"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import pvrimg
from tra import entries
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EX = os.path.join(ROOT, 'extract', 'ROOM2')


def offsets(d):
    return [0] if d[:4] in (b'GBIX', b'PVRT') else [o for o, s in entries(d)]


def all_textures():
    for r, ds, fs in os.walk(EX):
        for f in sorted(fs):
            if not f.upper().endswith(('.SVR', '.TRA')): continue
            p = os.path.join(r, f); d = open(p, 'rb').read()
            offs = offsets(d)
            rel = os.path.relpath(p, EX).replace(os.sep, '/')
            for k, o in enumerate(offs):
                name = rel.replace('/', '__') + ('' if len(offs) == 1 else '_%02d' % k)
                yield name, rel, o, d


if __name__ == '__main__':
    os.makedirs(os.path.join(ROOT, 'work', 'img'), exist_ok=True)
    lst = []
    for name, rel, o, d in all_textures():
        try:
            rgba, info = pvrimg.decode(d, o)
        except Exception:
            continue
        Image.fromarray(rgba).save(os.path.join(ROOT, 'work', 'img', name + '.png'))
        lst.append((name, rel, o, rgba.shape[1], rgba.shape[0]))
    json.dump(lst, open(os.path.join(ROOT, 'work', 'img_list.json'), 'w'))
    # 일람표: 썸네일 200px, 6x4 장
    T = 200; per = 24
    for s in range(0, len(lst), per):
        sheet = Image.new('RGB', (T * 6, (T + 14) * 4), (40, 40, 60)); dr = ImageDraw.Draw(sheet)
        for i, (name, rel, o, w, h) in enumerate(lst[s:s + per]):
            im = Image.open(os.path.join(ROOT, 'work', 'img', name + '.png')).convert('RGBA')
            bg = Image.new('RGBA', im.size, (90, 90, 120, 255)); bg.alpha_composite(im)
            bg.thumbnail((T, T)); x, y = (i % 6) * T, (i // 6) * (T + 14)
            sheet.paste(bg.convert('RGB'), (x, y + 14)); dr.text((x + 2, y), '%d %s' % (s + i, name[-28:]), fill=(255, 255, 0))
        sheet.save(os.path.join(ROOT, 'work', 'sheet_%03d.png' % (s // per)))
    print(len(lst))
