"""번역 원문 표 생성 → translation/jp/*.tsv
- scn/<파일>.tsv : 메일·일기·PC 스크립트(명령번호.인자번호 키)
- scn_small.tsv  : 그 밖의 연출 스크립트 문자열(원문 키, 중복 제거)
- elf.tsv        : ELF 표시용 문자열(파일 오프셋 키, 최대 전각 글자 수)
- extend.tsv     : EXTEND/*_TEXT.BIN 고정 레코드(25자)
- names.tsv      : SCRDAT 물체 이름(원문 키)
열: 키 \\t 종류/최대길이 \\t 원문"""
import os, re, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import ads
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EX = os.path.join(ROOT, 'extract', 'ROOM2')
OUT = os.path.join(ROOT, 'translation', 'jp')
JP = re.compile(rb'[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]')
BIG = ('MAIL', 'DIARY', 'PC')
OPNAME = {(1, 0x10): 'hdr', (2, 0x10): 'line', (3, 0x10): 'hdr3', (0x12, 0x10): 'chat', (0x13, 0x10): 'type',
          (7, 0x10): 'telop', (5, 0x13): 'act', (0x16, 0x10): 'act2'}


def esc(s): return s.replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n')


def dec(b): return b.decode('cp932')


def scn():
    os.makedirs(os.path.join(OUT, 'scn'), exist_ok=True)
    small = {}
    import glob
    for fp in sorted(glob.glob(os.path.join(EX, 'SCNSCR', '*.BIN')) + glob.glob(os.path.join(EX, 'SCNSCR', 'INIT', '*.BIN'))):
        f = os.path.basename(fp)
        h, ops = ads.parse(open(fp, 'rb').read())
        rows = []
        if f.startswith('PC'):
            rows = pc_rows(ops)
            open(os.path.join(OUT, 'scn', f[:-4] + '.tsv'), 'w', encoding='utf-8').write('\n'.join(rows) + '\n')
            continue
        for i, j, b in ads.strings(ops):
            if not JP.search(b): continue
            o = ops[i]; t = OPNAME.get((o.op, o.cls), '%02x/%02x' % (o.op, o.cls))
            if f.startswith('DIARY') and t == 'hdr': t = 'para'
            if f.startswith(BIG): rows.append('%d.%d\t%s\t%s' % (i, j, t, esc(dec(b))))
            else:
                s = dec(b)
                if s in ('囮卅',): continue
                small.setdefault(s, set()).add(t)
        if rows:
            open(os.path.join(OUT, 'scn', f[:-4] + '.tsv'), 'w', encoding='utf-8').write('\n'.join(rows) + '\n')
    open(os.path.join(OUT, 'scn_small.tsv'), 'w', encoding='utf-8').write(
        ''.join('%s\t%s\t%s\n' % (esc(s), '/'.join(sorted(t)), esc(s)) for s, t in small.items()))


def chat_groups(ops):
    """12/10 채팅 줄을 메시지 단위로 묶는다: [(첫 명령번호, [명령번호...], 화자, 본문)]. 첫 인자 0=다음 줄 이어짐, 16=끝"""
    out = []; cur = None
    for i, o in enumerate(ops):
        if (o.op, o.cls) != (0x12, 0x10): continue
        s = dec(o.args[2][1]); flag = int.from_bytes(o.args[0][1], 'little')
        if cur is None:
            name = s[:6].rstrip('　'); cur = [i, [i], name, s[6:]]
        else:
            cur[1].append(i); cur[3] += s[6:] if s[:6] == '　' * 6 else s
        if flag != 0:
            out.append(tuple(cur)); cur = None
    assert cur is None
    return out


def pc_rows(ops):
    rows = []
    for i, o in enumerate(ops):
        if (o.op, o.cls) == (0x13, 0x10):
            rows.append('%d\ttype\t%s' % (i, esc(dec(o.args[1][1]))))
        elif o.args and (o.op, o.cls) != (0x12, 0x10):
            for j, a in enumerate(o.args):
                if a[0] == 2 and JP.search(a[1]):
                    rows.append('%d.%d\t%02x/%02x\t%s' % (i, j, o.op, o.cls, esc(dec(a[1]))))
    for k, idx, name, msg in chat_groups(ops):
        rows.append('%d\tchat:%s\t%s' % (k, name, esc(msg)))
    rows.sort(key=lambda r: float(r.split('\t')[0]))
    return rows


def extend():
    rows = []
    for f in sorted(os.listdir(os.path.join(EX, 'EXTEND'))):
        if not f.endswith('_TEXT.BIN'): continue
        d = open(os.path.join(EX, 'EXTEND', f), 'rb').read()
        assert len(d) % 51 == 0
        for k in range(len(d) // 51):
            if d[k * 51] == 0: continue
            s = dec(d[k * 51:k * 51 + 50].split(b'\0')[0]).rstrip('\u3000')
            rows.append('%s:%d\t25\t%s' % (f[:-9], k, esc(s)))
    open(os.path.join(OUT, 'extend.tsv'), 'w', encoding='utf-8').write('\n'.join(rows) + '\n')


def names():
    seen = {}
    for r, ds, fs in os.walk(os.path.join(EX, 'SCRDAT')):
        for f in fs:
            for l in open(os.path.join(r, f), 'rb').read().split(b'\r\n'):
                if b'MODEL_CLICK_NAME' in l and JP.search(l):
                    s = dec(b' '.join(l.split()[3:]))
                    seen[s] = 1
    open(os.path.join(OUT, 'names.tsv'), 'w', encoding='utf-8').write(''.join('%s\t16\t%s\n' % (esc(s), esc(s)) for s in seen))


# ELF: 표시용으로 판단한 구간(파일 오프셋). 디버그/내부 이름 구간(모션 이름 0x2ecb60~0x2eebc0, 오류 메시지 등)은 제외.
ELF_RANGES = [(0x2d6cd0, 0x2d7a00, 'mc'), (0x2d8fb0, 0x2dc800, 'song'), (0x2dcb78, 0x2dea90, 'credit'),
              (0x2ded18, 0x2df870, 'object'), (0x2df8c0, 0x2e0300, 'action'), (0x2e8a18, 0x2e8b10, 'holiday'),
              (0x2e8b40, 0x2e9480, 'mischief'), (0x2e94c8, 0x2e94d0, 'mischief'), (0x2e9c10, 0x2e9c30, 'misc'),
              (0x2ef5a8, 0x2ef660, 'navi'), (0x2efe50, 0x2efea8, 'skip'), (0x2f0810, 0x2f14b0, 'title'),
              (0x2fbd40, 0x2fbd70, 'pc'), (0x2fbd70, 0x2fc060, 'pcdoc'), (0x2fc2d0, 0x2fc5d0, 'navi'),
              (0x2fcad8, 0x2fd670, 'title2'), (0x2fd670, 0x2fd820, 'navi'), (0x2fd8b8, 0x2fdd50, 'telop'),
              (0x2fe160, 0x2fe530, 'chibi'), (0x2fe748, 0x2fe758, 'chibi'), (0x2fe890, 0x2fe910, 'telop'),
              (0x2fed88, 0x2fee58, 'telop'), (0x2ff098, 0x2ff250, 'mail'), (0x2ff608, 0x2ff618, 'mail'),
              (0x304550, 0x304eb0, 'tutorial'), (0x304f78, 0x305080, 'telop')]


def elf():
    rows = json.load(open(os.path.join(ROOT, 'work', 'elfstr.json'), encoding='utf-8'))
    out = []
    for r in rows:
        cat = next((c for a, b, c in ELF_RANGES if a <= r['off'] < b), None)
        if not cat: continue
        t = r['text']
        if r['len'] <= 3 and r['len'] % 2: continue   # 데이터 바이트가 우연히 SJIS 로 보이는 것
        if not re.search('[\u3040-\u30ff\u4e00-\u9fff]', t): continue
        out.append('%06x\t%s:%d\t%s' % (r['off'], cat, r['room'] // 2, esc(t)))
    open(os.path.join(OUT, 'elf.tsv'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    scn(); extend(); names(); elf()
    for r, ds, fs in os.walk(OUT):
        for f in fs:
            p = os.path.join(r, f); n = sum(1 for _ in open(p, encoding='utf-8'))
            c = sum(len(l.split('\t')[-1]) for l in open(p, encoding='utf-8'))
            print('%-40s %6d줄 %7d자' % (os.path.relpath(p, OUT), n, c))
