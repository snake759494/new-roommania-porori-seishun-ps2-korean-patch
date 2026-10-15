"""시험용: 시점을 돌려가며 커서 격자 탐색, 물체 이름표 수집 → work/hunt.png"""
import sys, time, numpy as np, os
sys.path.insert(0, os.path.dirname(__file__))
import probe, vpad, emu
from PIL import Image, ImageDraw
slot = int(sys.argv[1]); views = [float(v) for v in sys.argv[2].split(',')]
found = []; seen = set()
for vi, rot in enumerate(views):
    vpad.pine(bytes([0xa, slot])); time.sleep(3)
    if rot:
        vpad.stick(0x80, 0x80, 0xff if rot > 0 else 0x00, 0x80); time.sleep(abs(rot)); vpad.w32(vpad.VANA, 0); time.sleep(0.6)
    for y in range(150, 321, 34):
        for x in range(150, 491, 34):
            probe.setc(x, y); time.sleep(1.8); emu.snap('pr')
            im = Image.open(os.path.join(emu.R, 'work', 'shot_pr.png')).convert('RGB'); a = np.array(im).astype(int)
            g = ((a[..., 1] > 130) & (a[..., 0] < 45) & (a[..., 2] > 70) & (a[..., 2] < 120)); g[395:] = False
            if g.sum() > 200:
                ys, xs = np.nonzero(g); w = xs.max() - xs.min()
                if w not in seen: seen.add(w); found.append((rot, x, y, im.crop((xs.min(), ys.min(), xs.max(), ys.max()))))
out = Image.new('RGB', (420, 26 * max(1, len(found)))); d = ImageDraw.Draw(out)
for k, (r, x, y, c) in enumerate(found): out.paste(c, (110, k * 26)); d.text((2, k * 26 + 6), '%.2f %d,%d' % (r, x, y), fill=(255, 255, 0))
out.save(os.path.join(emu.R, 'work', 'hunt.png')); print(len(found))
