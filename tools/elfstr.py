"""ELF(SLPM_652.35) 의 SJIS 문자열 목록화: 주소, 바이트 길이, 다음 문자열까지의 여유, 참조(데이터 포인터/코드 lui+addiu)"""
import sys, os, re, struct, json, bisect
sys.path.insert(0, os.path.dirname(__file__))
from mips import d, BASE, OFF, TEXT_END, w

DATA_LO, DATA_HI = 0x2c0000, 0x305e00   # 파일 오프셋 (rodata/data)
JP = re.compile(rb'[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]')


def scan():
    out = []
    p = DATA_LO
    while p < DATA_HI:
        e = d.find(b'\0', p)
        s = d[p:e]
        if s and JP.search(s):
            try:
                t = s.decode('cp932')
                if all(ch >= ' ' or ch in '\n\t' for ch in t): out.append((p, s))
            except UnicodeDecodeError:
                pass
        p = e + 1
    return out


def refs(addrs):
    """addrs(va) 에 대한 데이터 포인터와 코드 참조"""
    want = set(addrs); ptr = {}
    for i in range(0, len(d) - 3, 4):
        v = struct.unpack_from('<I', d, i)[0]
        if v in want: ptr.setdefault(v, []).append(i - OFF + BASE)
    code = {}
    his = {}
    for a in want: his.setdefault((a + 0x8000) >> 16, []).append(a)
    for a in range(BASE, TEXT_END, 4):
        x = w(a)
        if x >> 26 == 0xf and (x & 0xffff) in his:
            rt = (x >> 16) & 31
            for b in range(a + 4, min(a + 80, TEXT_END), 4):
                y = w(b)
                if y >> 26 in (9, 0x19) and (y >> 21) & 31 == rt:
                    t = (((x & 0xffff) << 16) + (y & 0xffff if y & 0x8000 == 0 else (y & 0xffff) - 0x10000)) & 0xffffffff
                    if t in want: code.setdefault(t, []).append((a, b))
                    break
    return ptr, code


if __name__ == '__main__':
    ss = scan()
    va = [p - OFF + BASE for p, s in ss]
    ptr, code = refs(va)
    rows = []
    for (p, s), v in zip(ss, va):
        e = d.find(b'\0', p); q = e + 1
        while q < len(d) and d[q] == 0: q += 1
        rows.append(dict(off=p, va=v, len=len(s), room=q - p - 1, ptr=ptr.get(v, []), code=[list(c) for c in code.get(v, [])],
                         text=s.decode('cp932')))
    json.dump(rows, open(os.path.join(os.path.dirname(__file__), '..', 'work', 'elfstr.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(len(rows), sum(1 for r in rows if not r['ptr'] and not r['code']), 'unreferenced')
