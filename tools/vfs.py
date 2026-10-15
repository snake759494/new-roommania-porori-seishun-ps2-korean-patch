"""ROOM2.VFS 벡터 폰트 파서/작성기.
구조: u32 3, u32 글리프수, f32 320.0, 글리프 반복:
  u32 윤곽수, u32 글리프바이트(이 8바이트 포함), 윤곽 반복: u32 점수, u32 윤곽바이트(=점수*4+8), (u16 x, u16 y)*점수"""
import struct


def parse(d):
    n = struct.unpack_from('<I', d, 4)[0]; p = 12; gl = []
    for i in range(n):
        nc, gb = struct.unpack_from('<II', d, p); q = p + 8; conts = []
        for c in range(nc):
            k, cb = struct.unpack_from('<II', d, q)
            conts.append(list(struct.iter_unpack('<HH', d[q + 8:q + 8 + k * 4]))); q += cb
        assert q == p + gb
        gl.append(conts); p += gb
    assert p == len(d)
    return d[:12], gl


def build(hdr, gl):
    out = [struct.pack('<I', 3), struct.pack('<I', len(gl)), hdr[8:12]]
    for conts in gl:
        body = b''.join(struct.pack('<II', len(c), len(c) * 4 + 8) + b''.join(struct.pack('<HH', *pt) for pt in c) for c in conts)
        out.append(struct.pack('<II', len(conts), len(body) + 8) + body)
    return b''.join(out)


if __name__ == '__main__':
    import sys
    d = open(sys.argv[1], 'rb').read()
    h, gl = parse(d); print(len(gl)); assert build(h, gl) == d; print('roundtrip ok')
