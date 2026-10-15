"""PVR(GBIX+PVRT) 텍스처 ↔ RGBA 배열.
형식(픽셀형식, 데이터형식):
  (9,104) 16색 RGBA 팔레트(64B) + 4bpp, PS2 스위즐(CT32 w/2 x h/4 → PSMT4)
  (9,108) 256색 RGBA 팔레트(1KB, CSM1 배열) + 8bpp, PS2 스위즐(CT32 w/2 x h/2 → PSMT8)
  (8,106) 256색 16비트 팔레트(512B) + 8bpp (스위즐 동일)
  (9,96)  32비트 RGBA 선형,  (8,96) 16비트 RGBA5551 선형
  (6,5)   DC 트위들 4bpp, 팔레트 외부(회색 단계로 가정)
알파는 PS2 방식(0x80=불투명) → 출력 시 0~255 로 변환."""
import struct, numpy as np, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import gsmem, twiddle


def header(d, o=0):
    q = o
    if d[q:q + 4] == b'GBIX': q += 8 + struct.unpack_from('<I', d, q + 4)[0]
    assert d[q:q + 4] == b'PVRT', d[q:q + 4]
    size, pf, df, _, w, h = struct.unpack_from('<IBBHHH', d, q + 4)
    return q, size, pf, df, w, h


def _csm1(n):
    idx = np.arange(n)
    if n == 256:
        idx = (idx & ~0x18) | ((idx & 8) << 1) | ((idx & 16) >> 1)
    return idx


def _a(x): return np.minimum(255, x.astype(np.int32) * 2).astype(np.uint8)


def decode(d, o=0):
    """→ (rgba[h,w,4] uint8, info)"""
    q, size, pf, df, w, h = header(d, o); p = q + 16
    if (pf, df) == (9, 104):
        pal = np.frombuffer(d[p:p + 64], np.uint8).reshape(16, 4); px = d[p + 64:p + 64 + w * h // 2]
        idx = gsmem.read4(gsmem.mem_from_ct32(px, w // 2, h // 4), w, h, max(1, w // 64))
        rgba = pal[idx].copy(); rgba[..., 3] = _a(rgba[..., 3])
        return rgba, dict(kind='p4', pal=pal, idx=idx)
    if (pf, df) in ((9, 108), (8, 106)):
        if pf == 9:
            pal = np.frombuffer(d[p:p + 1024], np.uint8).reshape(256, 4); p2 = p + 1024
        else:
            v = np.frombuffer(d[p:p + 512], '<u2').astype(np.int32)
            pal = np.stack([(v & 31) << 3, ((v >> 5) & 31) << 3, ((v >> 10) & 31) << 3, np.where(v & 0x8000, 0x80, 0)], 1).astype(np.uint8)
            p2 = p + 512
        pal = pal[_csm1(256)]
        px = d[p2:p2 + w * h]
        idx = gsmem.ct32_to_t8(px, w // 2, h // 2, w, h)
        rgba = pal[idx].copy(); rgba[..., 3] = _a(rgba[..., 3])
        return rgba, dict(kind='p8', pal=pal, idx=idx)
    if (pf, df) == (9, 96):
        a = np.frombuffer(d[p:p + w * h * 4], np.uint8).reshape(h, w, 4).copy(); a[..., 3] = _a(a[..., 3])
        return a, dict(kind='c32')
    if (pf, df) == (8, 96):
        v = np.frombuffer(d[p:p + w * h * 2], '<u2').reshape(h, w).astype(np.int32)
        a = np.stack([(v & 31) << 3, ((v >> 5) & 31) << 3, ((v >> 10) & 31) << 3, np.where(v & 0x8000, 255, 0)], 2).astype(np.uint8)
        return a, dict(kind='c16')
    if (pf, df) == (6, 5):
        idx = twiddle.untwiddle4_rect(d[p:p + w * h // 2], w, h) if w != h else twiddle.untwiddle4(d[p:p + w * h // 2], w, h)
        g = (idx * 17).astype(np.uint8)
        return np.stack([g, g, g, np.where(idx > 0, 255, 0).astype(np.uint8)], 2), dict(kind='dc4', idx=idx)
    raise ValueError('형식 %s' % ((pf, df),))


def encode(d, o, rgba=None, idx=None, pal=None):
    """원본 텍스처 d[o:] 와 같은 형식으로 새 픽셀을 넣은 바이트(같은 길이)를 돌려준다.
    팔레트 형식은 idx(+선택 pal)를 주거나, rgba 를 주면 원래 팔레트에 가장 가까운 색으로 양자화."""
    q, size, pf, df, w, h = header(d, o); p = q + 16
    out = bytearray(d[o:q + 8 + size])
    base = p - o
    if (pf, df) == (9, 104):
        opal = np.frombuffer(d[p:p + 64], np.uint8).reshape(16, 4)
        if pal is not None: out[base:base + 64] = pal.astype(np.uint8).tobytes(); opal = pal
        if idx is None: idx = quantize(rgba, opal)
        mem = np.zeros(w * h // 2, np.uint8)
        ad = gsmem.addr4(w, h, max(1, w // 64)); lo = (ad & 1) == 0
        np.bitwise_or.at(mem, ad[lo] >> 1, idx[lo] & 15); np.bitwise_or.at(mem, ad[~lo] >> 1, (idx[~lo] & 15) << 4)
        a32 = gsmem.addr32(w // 2, h // 4, max(1, w // 128))
        ct = np.zeros((h // 4, w // 2, 4), np.uint8)
        for k in range(4): ct[:, :, k] = mem[a32 + k]
        out[base + 64:base + 64 + w * h // 2] = ct.tobytes()
        return bytes(out)
    if (pf, df) in ((9, 108), (8, 106)):
        psz = 1024 if pf == 9 else 512
        if pf == 9:
            opal = np.frombuffer(d[p:p + 1024], np.uint8).reshape(256, 4)[_csm1(256)]
        else:
            opal = decode(d, o)[1]['pal']
        if pal is not None:
            assert pf == 9
            raw = np.zeros((256, 4), np.uint8); raw[_csm1(256)] = pal
            out[base:base + 1024] = raw.tobytes(); opal = pal
        if idx is None: idx = quantize(rgba, opal)
        out[base + psz:base + psz + w * h] = gsmem.t8_to_ct32(idx.astype(np.uint8), w // 2, h // 2, w, h)
        return bytes(out)
    if (pf, df) == (9, 96):
        a = rgba.copy(); a[..., 3] = (a[..., 3].astype(np.int32) + 1) // 2
        out[base:base + w * h * 4] = a.astype(np.uint8).tobytes(); return bytes(out)
    if (pf, df) == (8, 96):
        r, g, b, al = [rgba[..., k].astype(np.int32) for k in range(4)]
        v = (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10) | np.where(al >= 128, 0x8000, 0)
        out[base:base + w * h * 2] = v.astype('<u2').tobytes(); return bytes(out)
    if (pf, df) == (6, 5):
        if idx is None: idx = np.clip((rgba[..., 0].astype(int) + 8) // 17, 0, 15)
        out[base:base + w * h // 2] = twiddle.twiddle4_rect(idx) if w != h else twiddle.twiddle4(idx.astype(np.uint8)); return bytes(out)
    raise ValueError


def quantize(rgba, pal):
    """rgba(알파 0~255) → 팔레트(PS2 알파) 최근접 색 인덱스"""
    P = pal.astype(np.int32).copy(); P[:, 3] = np.minimum(255, P[:, 3] * 2)
    X = rgba.reshape(-1, 4).astype(np.int32)
    best = np.zeros(len(X), np.int32); bd = np.full(len(X), 1 << 30)
    w = np.array([1, 1, 1, 2])
    for i, c in enumerate(P):
        dd = (((X - c) ** 2) * w).sum(1)
        m = dd < bd; bd[m] = dd[m]; best[m] = i
    return best.reshape(rgba.shape[:2])
