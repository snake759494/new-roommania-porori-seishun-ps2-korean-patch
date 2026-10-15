"""F22 비트맵 폰트(TRA 안의 256x256 PSMT4 PVR, CT32 128x64 로 스위즐) 읽기/쓰기"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from tra import entries, pvr
import gsmem
def pages(d):
    out = []
    for o, s in entries(d):
        pf, df, w, h, q, sz = pvr(d, o)
        px = d[q+64:q+64+w*h//2]
        mem = gsmem.mem_from_ct32(px, 128, 64)
        out.append((q+64, gsmem.read4(mem, 256, 256, 4).astype(np.uint8)))
    return out
def encode(a):
    """[256,256] 4비트 인덱스 → 스위즐된 32768 바이트"""
    mem = np.zeros(32768, np.uint8)
    ad = gsmem.addr4(256, 256, 4)
    lo = (ad & 1) == 0
    np.bitwise_or.at(mem, ad[lo] >> 1, a[lo] & 15)
    np.bitwise_or.at(mem, ad[~lo] >> 1, (a[~lo] & 15) << 4)
    a32 = gsmem.addr32(128, 64, 2)
    out = np.zeros((64, 128, 4), np.uint8)
    for k in range(4): out[:, :, k] = mem[a32 + k]
    return out.tobytes()
