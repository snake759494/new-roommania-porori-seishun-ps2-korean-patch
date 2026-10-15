"""시험용: 커서 좌표(0xFF3A64/68, float)를 직접 지정하며 물체 이름표 탐색 → work/probe.png"""
import sys, os, time, struct, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import vpad, emu
from PIL import Image, ImageDraw
CX, CY = 0xFF3A64, 0xFF3A68
def getc():
    f = lambda a: struct.unpack('<f', struct.pack('<I', vpad.r32(a)))[0]
    return f(CX), f(CY)
def setc(x, y):
    for _ in range(40):
        cx, cy = getc(); dx, dy = x - cx, y - cy
        if abs(dx) < 8 and abs(dy) < 8: return
        g = lambda v: int((1 if v > 0 else -1) * max(45, min(127, abs(v) * 1.2)))
        sx = 0x80 + g(dx); sy = 0x80 + g(dy)
        if abs(dx) < 8: sx = 0x80
        if abs(dy) < 8: sy = 0x80
        vpad.stick(max(0, min(255, sx)), max(0, min(255, sy))); time.sleep(0.05); vpad.w32(vpad.VANA, 0); time.sleep(0.04)
if __name__ == '__main__':
    if sys.argv[1] == 'set': setc(float(sys.argv[2]), float(sys.argv[3])); sys.exit()
    x0, y0, x1, y1, st = [float(v) for v in sys.argv[1:6]]
    hits = []; seen = set()
    y = y0
    while y <= y1:
        x = x0
        while x <= x1:
            setc(x, y); time.sleep(0.4)
            emu.snap('pr'); im = Image.open(os.path.join(emu.R, 'work', 'shot_pr.png')).convert('RGB')
            a = np.array(im).astype(int)
            g = (a[..., 1] > 130) & (a[..., 0] < 30) & (a[..., 2] > 70) & (a[..., 2] < 115)
            g[400:] = False
            if g.sum() > 200:
                ys, xs = np.nonzero(g); cr = im.crop((xs.min(), ys.min(), xs.max(), ys.max()))
                key = (xs.max() - xs.min(),)
                if key not in seen: seen.add(key); hits.append(((x, y), cr))
            x += st
        y += st
    out = Image.new('RGB', (640, 28 * max(1, len(hits)))); d = ImageDraw.Draw(out)
    for k, ((x, y), cr) in enumerate(hits):
        out.paste(cr, (90, k * 28)); d.text((2, k * 28 + 6), '%d,%d' % (x, y), fill=(255, 255, 0))
    out.save(os.path.join(emu.R, 'work', 'probe.png')); print(len(hits))
