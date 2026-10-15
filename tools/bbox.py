"""이미지에서 글자 덩어리(연결된 불투명/전경 영역)의 경계 상자 목록: python tools/bbox.py 이미지이름 [배경판정]"""
import sys, os, numpy as np
from PIL import Image
from scipy import ndimage
def boxes(path, mode='alpha', thr=40, dil=3, bgcol=None):
    a = np.array(Image.open(path).convert('RGBA')).astype(int)
    if mode == 'alpha': m = a[..., 3] > thr
    else:
        bg = np.array(bgcol); m = (np.abs(a[..., :3] - bg).sum(2) > thr) & (a[..., 3] > 0)
    m2 = ndimage.binary_dilation(m, iterations=dil)
    lab, n = ndimage.label(m2)
    out = []
    for s in ndimage.find_objects(lab):
        y, x = s; out.append((x.start, y.start, x.stop, y.stop))
    return sorted(out, key=lambda b: (b[1] // 8, b[0]))
if __name__ == '__main__':
    p = 'work/img/%s.png' % sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else 'alpha'
    bg = tuple(int(x) for x in sys.argv[3].split(',')) if len(sys.argv) > 3 else None
    for b in boxes(p, mode, bgcol=bg): print(b, b[2]-b[0], b[3]-b[1])
