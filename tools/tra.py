"""TRA 텍스처 묶음: 헤더 = (u32 오프셋, u32 0, u32 크기) 반복(0 오프셋에서 끝), 각 항목 = GBIX + PVRT"""
import struct
def entries(d):
    out = []; p = 0
    while p + 12 <= len(d):
        o, z, s = struct.unpack_from('<III', d, p)
        if o == 0 or o >= len(d): break
        out.append((o, s)); p += 12
    return out
def pvr(d, o):
    """(픽셀포맷, 데이터포맷, w, h, 데이터 오프셋)"""
    q = o
    if d[q:q+4] == b'GBIX': q += 8 + struct.unpack_from('<I', d, q+4)[0]
    assert d[q:q+4] == b'PVRT', d[q:q+4]
    size, pf, df, _, w, h = struct.unpack_from('<IBBHHH', d, q+4)
    return pf, df, w, h, q + 16, size
