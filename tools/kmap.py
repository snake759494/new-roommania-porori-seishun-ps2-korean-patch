"""한글 2,350자(KS X 1001) ↔ SJIS 1수준 한자 슬롯(0x889F~, JIS 16구~ 순서) 대응과 문자열 인코딩"""
def hangul2350():
    return [bytes([hi, lo]).decode('euc-kr') for hi in range(0xb0, 0xc9) for lo in range(0xa1, 0xff)]
def jis2sjis(r, c):
    lead = ((r - 1) >> 1) + (0x81 if r <= 62 else 0xC1)
    t = (c + 0x3f + (1 if c >= 64 else 0)) if r % 2 else c + 0x9e
    return lead << 8 | t
def slot(i):
    """i번째 1수준 한자 슬롯의 SJIS 코드"""
    return jis2sjis(16 + i // 94, i % 94 + 1)
HANGUL = hangul2350()
CM = {h: slot(i) for i, h in enumerate(HANGUL)}
RM = {v: k for k, v in CM.items()}
def f22_index(code):
    """F22 파일 번호, 파일 안 글자 순번"""
    hi, lo = code >> 8, code & 0xff
    r = (hi - 0x81) * 2 + 1 if hi < 0xa0 else (hi - 0xc1) * 2 + 1
    if lo >= 0x9f: r += 1; c = lo - 0x9e
    else: c = lo - 0x3f - (1 if lo >= 0x80 else 0)
    if r < 16: return 0, (r - 1) * 94 + c - 1
    if r < 48: return 1, (r - 16) * 94 + c - 1
    return 2, (r - 48) * 94 + c - 1
FW = str.maketrans({'!': '！', '?': '？', '(': '（', ')': '）'})
def encode(s, fw=False):
    out = bytearray()
    for c in s:
        if c in CM: out += CM[c].to_bytes(2, 'big')
        elif ord(c) < 0x80 and not fw: out.append(ord(c))
        else: out += c.encode('cp932')
    return bytes(out)
def decode(b):
    out = []; i = 0
    while i < len(b):
        c = b[i]
        if (0x81 <= c <= 0x9f or 0xe0 <= c <= 0xfc) and i + 1 < len(b):
            code = c << 8 | b[i + 1]
            out.append(RM.get(code) or b[i:i + 2].decode('cp932', 'replace')); i += 2
        else:
            out.append(chr(c) if c < 0x80 else b[i:i+1].decode('cp932', 'replace')); i += 1
    return ''.join(out)
if __name__ == '__main__':
    assert slot(0) == 0x889f and f22_index(0x889f) == (1, 0)
    print(len(CM), hex(slot(2349)), f22_index(slot(2349)), f22_index(0x989f), f22_index(0x8140), f22_index(0x839f))

NARROW = 0x81B0   # 좁은 띄어쓰기(빈 글리프, F22 렌더러에서 전진폭 절반)
_FW = {c: chr(c + 0xFEE0) for c in range(0x21, 0x7F)}
_FW.update({ord('-'): '－', ord('~'): '～', ord("'"): '’', ord('"'): '”', 0x5C: '＼'})


def encode_game(s, narrow=True):
    """번역문 → 게임 바이트(모두 2바이트). 반각 공백→좁은 공백, 반각 문자→전각."""
    out = bytearray()
    for c in s:
        if ord(c) < 0x20:
            out.append(ord(c)); continue
        if c == ' ':
            out += (NARROW if narrow else 0x8140).to_bytes(2, 'big')
        elif c in CM:
            out += CM[c].to_bytes(2, 'big')
        else:
            if ord(c) < 0x7F: c = _FW[ord(c)]
            b = c.encode('cp932')
            assert len(b) == 2, c
            out += b
    return bytes(out)
