"""시험용: 커서를 격자로 움직이며 물체 이름표(초록 띠)가 뜨는 위치를 모은다 → work/scan.png"""
import sys, os, time, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import vpad, emu
from PIL import Image
def ls(x, y, t): vpad.stick(x, y); time.sleep(t); vpad.w32(vpad.VANA, 0); time.sleep(0.15)
step = float(sys.argv[1]) if len(sys.argv) > 1 else 0.1
cols = int(sys.argv[2]) if len(sys.argv) > 2 else 8; rows = int(sys.argv[3]) if len(sys.argv) > 3 else 6
ls(0x00, 0x00, 2.0)
hits = []
for r in range(rows):
    for c in range(cols):
        emu.snap('sc'); im = Image.open(os.path.join(emu.R, 'work', 'shot_sc.png')).convert('RGB')
        a = np.array(im).astype(int)
        g = (a[..., 1] > 130) & (a[..., 0] < 30) & (a[..., 2] > 70) & (a[..., 2] < 115)
        if g[:400].sum() > 300:
            ys, xs = np.nonzero(g[:400]); hits.append((r, c, im.crop((max(0, xs.min() - 30), ys.min() - 4, xs.max() + 4, ys.max() + 4))))
        ls(0xff, 0x80, step)
    ls(0x00, 0x80, step * cols); ls(0x80, 0xff, step * 0.8)
print(len(hits))
W = 640; out = Image.new('RGB', (W, 30 * max(1, len(hits))))
for k, (r, c, cr) in enumerate(hits): out.paste(cr.resize((min(cr.width, 560), cr.height)), (60, k * 30)); 
from PIL import ImageDraw
d = ImageDraw.Draw(out)
for k, (r, c, cr) in enumerate(hits): d.text((2, k * 30 + 8), '%d,%d' % (r, c), fill=(255, 255, 0))
out.save(os.path.join(emu.R, 'work', 'scan.png'))
