"""ADS 스크립트(SCNSCR/*.BIN) 파서/재조립기.
헤더 16바이트('ADS\\0', u32 ver, u32 본문크기(=파일크기-16), u32 ?) + 명령열 [u8 op][u8 cls][u16 len(헤더 포함)] + 0 패딩(4배수).
cls 0x02 명령은 원시 바이트(점프 1a/02, 1b/02 의 +4 = 코드(0x10) 기준 오프셋).
그 외 명령 본문 = 인자열: 0/1/3 = 타입+u32, 2 = 문자열(02 n 0×n 문자열\\0, 문자열 시작이 4바이트 정렬; 일부는 패딩 없음)."""
import struct

JUMPS = {(0x1a, 2), (0x1b, 2)}


class Op:
    __slots__ = ('off', 'op', 'cls', 'raw', 'args')

    def __init__(s, off, op, cls, raw, args):
        s.off, s.op, s.cls, s.raw, s.args = off, op, cls, raw, args


def _args(d, p, end):
    out = []
    while p < end:
        t = d[p]
        if t in (0, 1, 3):
            if p + 5 > end: return None
            out.append([t, d[p + 1:p + 5]]); p += 5
        elif t == 2:
            n = d[p + 1]
            if 1 <= n <= 4 and not any(d[p + 2:p + 2 + n]) and (p + 2 + n) % 4 == 0:
                s = p + 2 + n; pad = True
            else:
                s = p + 1; pad = False
            e = d.find(b'\0', s)
            if e < 0 or e >= end: return None
            out.append([2, d[s:e], pad]); p = e + 1
        else:
            return None
    return out


def parse(d):
    assert d[:4] == b'ADS\0'
    p = 16; ops = []
    while p + 4 <= len(d):
        op, cls, ln = struct.unpack_from('<BBH', d, p)
        if ln < 4 or p + ln > len(d): break
        a = None if cls == 2 else _args(d, p + 4, p + ln)
        ops.append(Op(p, op, cls, d[p + 4:p + ln], a))
        p += ln
    return d[:16] + d[p:], ops   # 헤더 뒤에 원래 끝 패딩(쓰레기 값)을 붙여 보관


def strings(ops):
    """[(명령 번호, 인자 번호, bytes)]"""
    out = []
    for i, o in enumerate(ops):
        if o.args:
            for j, a in enumerate(o.args):
                if a[0] == 2: out.append((i, j, a[1]))
    return out


def build(hdr, ops):
    tail = hdr[16:]; hdr = hdr[:16]
    out = bytearray(hdr); newoff = {}
    for o in ops:
        p = len(out); newoff[o.off] = p
        if o.args is None:
            body = bytearray(o.raw)
        else:
            body = bytearray()
            for a in o.args:
                if a[0] == 2:
                    q = p + 4 + len(body)
                    if a[2]:
                        n = (-(q + 2)) % 4 or 4
                        body += bytes([2, n]) + b'\0' * n
                    else:
                        body.append(2)
                    body += a[1] + b'\0'
                else:
                    body += bytes([a[0]]) + a[1]
        ln = len(body) + 4
        assert ln < 0x10000
        out += struct.pack('<BBH', o.op, o.cls, ln) + body
    # 점프 재배치
    for o in ops:
        if (o.op, o.cls) in JUMPS:
            p = newoff[o.off]
            t = struct.unpack_from('<I', out, p + 4)[0]
            struct.pack_into('<I', out, p + 4, newoff[t + 16] - 16)
    out += tail if (len(out) + len(tail)) % 4 == 0 else b'\0' * ((-len(out)) % 4)
    struct.pack_into('<I', out, 8, len(out) - 16)
    return bytes(out)


if __name__ == '__main__':
    import os
    D = 'extract/ROOM2/SCNSCR/'; bad = 0; n = 0
    for f in sorted(os.listdir(D)):
        if not f.endswith('.BIN'): continue
        d = open(D + f, 'rb').read()
        h, ops = parse(d)
        if any(o.args is None and o.cls != 2 for o in ops): print('unparsed', f); bad += 1
        n += len(strings(ops))
        if build(h, ops) != d: print('roundtrip FAIL', f, len(build(h, ops)), len(d)); bad += 1
    print('files bad', bad, 'strings', n)
