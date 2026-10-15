"""이미지 확대 + 8px 격자 + 좌표 눈금: python tools/gridview.py 이름 [배율] [x0,y0,x1,y1]"""
import sys
from PIL import Image, ImageDraw
n = sys.argv[1]; s = int(sys.argv[2]) if len(sys.argv) > 2 else 3
im = Image.open('work/img/%s.png' % n if not n.endswith('.png') else n).convert('RGBA')
if len(sys.argv) > 3: im = im.crop(tuple(int(v) for v in sys.argv[3].split(','))); off = [int(v) for v in sys.argv[3].split(',')][:2]
else: off = [0, 0]
bg = Image.new('RGBA', im.size, (255, 0, 255, 255)); bg.alpha_composite(im)
big = bg.resize((im.width * s, im.height * s), Image.NEAREST); dr = ImageDraw.Draw(big)
for x in range(0, im.width, 8):
    dr.line([(x * s, 0), (x * s, big.height)], fill=(0, 255, 0, 255) if (x + off[0]) % 32 == 0 else (0, 160, 0, 255))
    if (x + off[0]) % 32 == 0: dr.text((x * s + 2, 2), str(x + off[0]), fill=(255, 255, 0))
for y in range(0, im.height, 8):
    dr.line([(0, y * s), (big.width, y * s)], fill=(0, 255, 0, 255) if (y + off[1]) % 32 == 0 else (0, 160, 0, 255))
    if (y + off[1]) % 32 == 0: dr.text((2, y * s + 2), str(y + off[1]), fill=(255, 255, 0))
big.save('work/grid.png')
