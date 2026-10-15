"""번역 검사: python tools/check_ko.py <원문 jp.tsv> <번역 ko.tsv>
- 원문 키가 모두 번역되었는지(빈 번역 금지, 원문이 공백뿐이면 예외)
- 표시 가능한 글자인지: KS X 1001 한글 2,350자, ASCII, 전각 기호/영숫자(SJIS 1~8구), 원문에 있던 가나(이모티콘)만 허용
- 한자 금지, 원문에 없던 가나 금지, `/ < >` 금지(원문에 있던 제어 표기는 허용)
- 길이: elf 는 '종류:최대글자수', extend 25, mail hdr 제목 12 (경고)
출력이 비어 있으면 통과."""
import sys, os, re, unicodedata
sys.path.insert(0, os.path.dirname(__file__))
from kmap import CM

FW = {chr(c): chr(c + 0xFEE0) for c in range(0x21, 0x7f)}
FW[' '] = '　'


def unesc(s): return s.replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')


def load(p):
    rows = {}
    for l in open(p, encoding='utf-8'):
        l = l.rstrip('\n')
        if not l or l.startswith('#'): continue
        parts = l.split('\t')
        rows[parts[0]] = parts[1:]
    return rows


def sjis_ok(ch):
    try:
        b = ch.encode('cp932')
    except UnicodeEncodeError:
        return False
    if len(b) == 1: return True
    hi = b[0]
    return 0x81 <= hi <= 0x84 or hi == 0x87   # 1~8구(기호·영숫자·가나·그리스·키릴·괘선)


ASCII_KEEP = re.compile(r'%[-0-9]*[dsx]|/[0-9a-fA-F]{8}/')


def elf_bytes(t):
    """ELF 문자열 인코딩 길이: 서식(%d 등)·색 태그(/RRGGBBAA/)는 반각 그대로, 나머지는 2바이트"""
    n = 0; p = 0
    for m in ASCII_KEEP.finditer(t):
        n += 2 * len(t[p:m.start()].replace('\n', '')) + len(m.group()); p = m.end()
    return n + 2 * len(t[p:])


def width(s):
    return sum(0.5 if c == ' ' else 1 for c in s)


def check(jp_path, ko_path):
    jp = load(jp_path); ko = load(ko_path); errs = []
    kind = os.path.basename(jp_path)
    for k, v in jp.items():
        src = unesc(v[-1])
        if k not in ko:
            errs.append('누락 %s' % k); continue
        t = unesc(ko[k][-1])
        if not t.strip() and src.strip():
            errs.append('빈 번역 %s' % k); continue
        kana_src = set(c for c in src if '぀' <= c <= 'ヿ')
        bad = []
        for c in t:
            if c in CM or c in '\n': continue
            if '가' <= c <= '힣': bad.append(c); continue        # 2350자 밖 한글
            if '一' <= c <= '鿿' or '㐀' <= c <= '䶿': bad.append(c); continue
            if '぀' <= c <= 'ヿ' and c not in kana_src and c not in 'ー・ヽヾ': bad.append(c); continue
            if c in '/<>' and c not in src: bad.append(c); continue
            if not sjis_ok(c): bad.append(c)
        if bad: errs.append('글자 %s: %s  | %s' % (k, ''.join(sorted(set(bad))), t))
        for fmt in re.findall(r'%[0-9]*[ds]', src):
            if t.count(fmt) != src.count(fmt): errs.append('서식 %s: %s' % (k, fmt))
        lim = None
        if re.fullmatch(r'[a-z0-9]+:\d+', v[0]): lim = int(v[0].split(':')[1])
        elif kind.lower().startswith('extend'): lim = 25
        if lim is not None:
            n = elf_bytes(t) if re.fullmatch(r'[a-z0-9]+:\d+', v[0]) else len(t) * 2
            if n > lim * 2 + 1:
                errs.append('길이 %s: %d바이트 > %d  | %s' % (k, n, lim * 2 + 1, t))
    for k in ko:
        if k not in jp: errs.append('원문에 없는 키 %s' % k)
    return errs


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    e = check(sys.argv[1], sys.argv[2])
    print('\n'.join(e) if e else 'OK')
