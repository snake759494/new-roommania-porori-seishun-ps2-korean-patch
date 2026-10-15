"""ELF 디스어셈블/참조 검색 도우미"""
import struct
from r5900 import dis1, s16
ELF = 'extract/SLPM_652.35'
d = open(ELF, 'rb').read()
BASE = 0x100000; OFF = 0x80
def va2off(a): return a - BASE + OFF
def w(a): return struct.unpack_from('<I', d, va2off(a))[0]
def dis(a, n, out=print):
    for k in range(n):
        x = a + 4*k
        out('%08x: %08x %s' % (x, w(x), dis1(x, w(x))))
TEXT_END = 0x100000 + 3169792
def xref_addr(target):
    """lui/addiu 또는 lui/ori 조합으로 target 을 만드는 위치"""
    hi = (target + 0x8000) >> 16; lo = target & 0xffff; res = []
    for a in range(BASE, TEXT_END, 4):
        x = w(a)
        if x >> 26 == 0xf and x & 0xffff == hi:
            rt = (x >> 16) & 31
            for b in range(a + 4, min(a + 64, TEXT_END), 4):
                y = w(b)
                if (y >> 21) & 31 == rt and y & 0xffff == lo and y >> 26 in (9, 0x23, 0x2b, 0x25, 0x24, 0x21, 0x20, 0x28, 0x29, 0x31, 0x39): res.append(b); break
        if x >> 26 == 0xf and x & 0xffff == target >> 16:
            rt = (x >> 16) & 31
            for b in range(a + 4, min(a + 64, TEXT_END), 4):
                y = w(b)
                if y >> 26 == 0xd and (y >> 21) & 31 == rt and y & 0xffff == lo: res.append(b); break
    return res
def callers(fn):
    t = 0x0c000000 | (fn >> 2) & 0x3ffffff
    return [a for a in range(BASE, TEXT_END, 4) if w(a) == t]
def func_start(a):
    while a > BASE:
        a -= 4; x = w(a)
        if x >> 16 == 0x27bd and (x & 0x8000): return a
    return None
GP = 0x40d070
def gp_refs(lo, hi):
    out = []
    for a in range(BASE, TEXT_END, 4):
        x = w(a)
        if (x >> 21) & 31 == 28 and x >> 26 in (9,0x23,0x2b,0x24,0x25,0x21,0x20,0x28,0x29,0x37,0x3f,0x31,0x39):
            t = GP + s16(x & 0xffff)
            if lo <= t < hi: out.append((a, t))
    return out
