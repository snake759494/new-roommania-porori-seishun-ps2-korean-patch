"""한글판 ISO 빌드: python tools/build.py
번역(translation/ko) → 스크립트·ELF·EXTEND·물체 이름·글꼴·이미지 → 원본 ISO 복사본에 기록"""
import sys, os, re, struct, json, glob
sys.path.insert(0, os.path.dirname(__file__))
import ads, kmap, cvm, elfpatch, build_f22, build_vfs, build_mozi
from extract_text import chat_groups
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EX = os.path.join(ROOT, 'extract', 'ROOM2')
KO = os.path.join(ROOT, 'translation', 'ko')
JP = os.path.join(ROOT, 'translation', 'jp')
MAIL_W = 21.0        # 메일 한 줄 최대 폭(전각=1, 좁은 공백=0.5)
CHAT_W = 14.0        # 채팅 본문 폭(이름 칸 6 뒤)
WIDE = '　'
CHAT_NAMES = {'ネジ': '네지', 'ねじ': '네지', 'さやか': '사야카', 'つよしっち': '츠요싯치', 'かなぴー': '카나피',
              'でんぞう': '덴조', '管理': '관리자', '': ''}
KEEP = re.compile(r'/n|/[0-9a-fA-F]{8}/|%[-0-9]*[dsx]|[<>]')
warn = []


def unesc(s): return s.replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')


def load_tsv(p, col=-1):
    out = {}
    for l in open(p, encoding='utf-8'):
        l = l.rstrip('\n')
        if not l: continue
        a = l.split('\t'); out[a[0]] = unesc(a[col])
    return out


def enc(s):
    """번역문 → 게임 바이트. 제어 표기(/n, 색 태그, 서식)는 반각 그대로."""
    out = bytearray(); p = 0
    for m in KEEP.finditer(s):
        out += kmap.encode_game(s[p:m.start()]); out += m.group().encode('ascii'); p = m.end()
    return bytes(out + kmap.encode_game(s[p:]))


def width(s): return sum(0.5 if c == ' ' else 1 for c in s)


def wrap(s, w):
    """공백 기준 줄 나눔(넘치는 단어는 글자 단위로 자름)"""
    lines = []
    for para in s.split('\n'):
        cur = ''
        for word in para.split(' '):
            cand = word if not cur else cur + ' ' + word
            if width(cand) <= w: cur = cand; continue
            if cur: lines.append(cur)
            while width(word) > w:
                k = 0
                while width(word[:k + 1]) <= w: k += 1
                lines.append(word[:k]); word = word[k:]
            cur = word
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- 번역 모으기
def gather():
    tr = {}
    for p in glob.glob(os.path.join(KO, 'parts', '*.tsv')):
        name = os.path.basename(p)[:-4]
        rows = load_tsv(p)
        if name.startswith(('MAILKK', 'DIARYNEJI', 'PCNEJI')):
            f = name.split('_')[0] if not name.startswith('PCNEJI') else 'PCNEJI'
            tr.setdefault('scn:' + f, {}).update(rows)
        elif name == 'PC_ETC':
            for k, v in rows.items():
                f, kk = k.split(':', 1); tr.setdefault('scn:' + f, {})[kk] = v
        elif name.startswith('EXTEND'):
            tr.setdefault('extend', {}).update(rows)
        elif name.startswith(('ELF', 'MOTION')):
            tr.setdefault('elf', {}).update(rows)
    tr['names'] = load_tsv(os.path.join(KO, 'names.tsv'))
    tr['small'] = load_tsv(os.path.join(KO, 'scn_small.tsv'))
    for f in glob.glob(os.path.join(KO, 'fix', '*.tsv')):   # 수동 수정(나중에 덮어씀)
        sec = os.path.basename(f)[:-4]
        tr.setdefault(sec, {}).update(load_tsv(f))
    return tr


# ---------------------------------------------------------------- 스크립트
def clone(o, args, uid):
    return ads.Op(-1000000 - uid, o.op, o.cls, b'', args)


_uid = [0]


def new_op(o, args):
    _uid[0] += 1
    return clone(o, args, _uid[0])


def build_scn(fname, rows, small, path=None):
    d = open(path or os.path.join(EX, 'SCNSCR', fname + '.BIN'), 'rb').read()
    h, ops = ads.parse(d)
    targets = set()
    for o in ops:
        if (o.op, o.cls) in ads.JUMPS: targets.add(struct.unpack_from('<I', o.raw)[0] + 16)
    insert_after = {}; drop = set(); repl = {}
    if fname.startswith('PC'):
        for k, idx, name, msg in chat_groups(ops):
            ko = rows.get(str(k))
            if ko is None: continue
            nm = CHAT_NAMES.get(name)
            if nm is None: warn.append('채팅 화자 %s %s' % (fname, name)); nm = name
            lines = wrap(ko, CHAT_W)
            first = ops[idx[0]]
            news = []
            for n, ln in enumerate(lines):
                pre = (nm + WIDE * (6 - len(nm))) if n == 0 else WIDE * 6
                flag = (16 if n == len(lines) - 1 else 0).to_bytes(4, 'little')
                news.append([[0, flag], [0, first.args[1][1]], [2, enc(pre) + enc(ln), True]])
            # 원래 줄 + 뒤따르는 대기 명령 제거, 첫 줄 자리에 새 줄들
            for i in idx:
                if ops[i].off in targets and i != idx[0]: warn.append('점프 대상 채팅줄 %s %d' % (fname, i))
                drop.add(i)
                if i + 1 < len(ops) and (ops[i + 1].op, ops[i + 1].cls) == (2, 0) and i != idx[-1]: drop.add(i + 1)
            wait = ops[idx[-1] + 1] if idx[-1] + 1 < len(ops) and (ops[idx[-1] + 1].op, ops[idx[-1] + 1].cls) == (2, 0) else None
            seq = []
            for n, a in enumerate(news):
                if n == 0:
                    first.args = a; seq.append(first)
                else:
                    if wait is not None: seq.append(new_op(wait, [list(x) for x in wait.args]))
                    seq.append(new_op(first, a))
            drop.discard(idx[0]); repl[idx[0]] = seq
            # 마지막 줄 뒤 대기 명령(원래 idx[-1]+1)은 그대로 유지
            if idx[-1] != idx[0] and wait is not None: drop.discard(idx[-1] + 1)
        for i, o in enumerate(ops):
            if (o.op, o.cls) == (0x13, 0x10) and str(i) in rows:
                b = enc(rows[str(i)]); o.args[0][1] = b; o.args[1][1] = b
    for i, o in enumerate(ops):
        if not o.args or (o.op, o.cls) in ((0x12, 0x10), (0x13, 0x10)) and fname.startswith('PC'): continue
        for j, a in enumerate(o.args):
            if a[0] != 2: continue
            src = a[1].decode('cp932', 'replace')
            key = '%d.%d' % (i, j)
            ko = rows.get(key) if rows else None
            if ko is None and small is not None: ko = small.get(src)
            if ko is None: continue
            if ko == src: continue
            if (o.op, o.cls) == (2, 0x10) and fname.startswith('MAIL'):
                lines = wrap(ko, MAIL_W)
                a[1] = enc(lines[0])
                if len(lines) > 1:
                    insert_after.setdefault(i, []).extend(new_op(o, [[2, enc(l), True]]) for l in lines[1:])
            else:
                a[1] = enc(ko)
    out = []
    for i, o in enumerate(ops):
        if i in drop: continue
        if i in repl: out += repl[i]
        else: out.append(o)
        out += insert_after.get(i, [])
    return ads.build(h, out)


# ---------------------------------------------------------------- EXTEND / 물체 이름
def build_extend(tr):
    files = {}
    for k, v in tr.items():
        f, n = k.split(':'); files.setdefault(f, {})[int(n)] = v
    out = {}
    for f, rows in files.items():
        p = os.path.join(EX, 'EXTEND', f + '_TEXT.BIN')
        d = bytearray(open(p, 'rb').read())
        for n, ko in rows.items():
            b = enc(ko)
            if len(b) > 50: warn.append('EXTEND 길이 %s:%d' % (f, n)); b = b[:50]
            b += '　'.encode('cp932') * ((50 - len(b)) // 2)
            d[n * 51:n * 51 + 51] = b + b'\0'
        out['/EXTEND/%s_TEXT.BIN' % f] = bytes(d)
    return out


def build_scrdat(names):
    out = {}
    pat = re.compile(rb'(MODEL_CLICK_NAME\s+\S+ )([^\r\n]*?)( ?)(\r?)$', re.M)
    for r, ds, fs in os.walk(os.path.join(EX, 'SCRDAT')):
        for f in fs:
            p = os.path.join(r, f); d = open(p, 'rb').read()
            if b'MODEL_CLICK_NAME' not in d: continue
            def sub(m):
                s = m.group(2).decode('cp932')
                ko = names.get(s)
                if ko is None:
                    if re.search('[぀-ヿ一-鿿]', s): warn.append('이름 없음 %s' % s)
                    return m.group(0)
                return m.group(1) + enc(ko.strip()) + m.group(3) + m.group(4)
            nd = pat.sub(sub, d)
            if nd != d: out['/' + os.path.relpath(p, EX).replace('\\', '/')] = nd
    return out


# ---------------------------------------------------------------- ELF
def build_elf(tr, mozi_table=None):
    e = bytearray(open(os.path.join(ROOT, 'extract', 'SLPM_652.35'), 'rb').read())
    rows = {r['off']: r for r in json.load(open(os.path.join(ROOT, 'work', 'elfstr.json'), encoding='utf-8'))}
    reloc = []; used = 0
    cats = {l.split('	')[0]: l.split('	')[1].split(':')[0] for l in open(os.path.join(JP, 'elf.tsv'), encoding='utf-8') if l.strip()}
    only = os.environ.get('ELFCATS')
    for k, ko in sorted(tr.items()):
        if only and cats.get(k) not in only.split(','): continue
        off = int(k, 16); r = rows[off]
        r['room'] = min(r['room'], ((off + r['len'] + 16) & ~15) - off - 1)   # 16바이트 경계 너머 0 은 데이터일 수 있음
        if ko == r['text']: continue
        b = enc(ko)
        if len(b) > r['room']:
            if not (r['ptr'] or r['code']):
                warn.append('ELF 길이 초과(참조 모름) %06x %d>%d %s' % (off, len(b), r['room'], ko)); continue
            codes = [tuple(c) for c in r['code']]
            reloc.append((b + b'\0', r['ptr'], codes)); used += len(b) + 4
            e[off:off + r['room'] + 1] = b'\0' * (r['room'] + 1)
            continue
        e[off:off + r['room'] + 1] = b + b'\0' * (r['room'] + 1 - len(b))
    if reloc: print('ELF 문자열 재배치 %d개 (%d바이트)' % (len(reloc), used))
    return elfpatch.patch(bytes(e), reloc, mozi_table)


# ---------------------------------------------------------------- 소형 글꼴(MOZI)
def mozi_chars(tr):
    """소형 글꼴(MOZI)로 그려지는 번역(행동 이름: ELF 행동 표·스크립트 05/13, 꼬마 찾기 카운터)에 쓰인 글자 중 원래 글꼴에 없는 것"""
    cats = {l.split('	')[0]: l.split('	')[1].split(':')[0] for l in open(os.path.join(JP, 'elf.tsv'), encoding='utf-8') if l.strip()}
    chibi = {'2e9370', '2e9390', '2e93b0', '2e93c0', '2e93d0', '2e93f0', '2e9410', '2e9430', '2e9450', '2e9470'}
    texts = [v for k, v in tr.get('elf', {}).items() if cats.get(k) == 'action' or k in chibi]
    acts = [l.split('	')[0] for l in open(os.path.join(JP, 'scn_small.tsv'), encoding='utf-8') if '	act' in l]
    texts += [tr['small'][k] for k in acts if k in tr['small']]
    from mips import d as elfd, va2off
    t94 = set(elfd[va2off(0x36A4C0) + 2 * i:va2off(0x36A4C0) + 2 * i + 2][::-1].decode('cp932', 'replace') for i in range(94))
    s = set()
    for t in texts:
        for c in t:
            if c == ' ': s.add(' '); continue
            if ord(c) < 0x7F: c = kmap._FW[ord(c)]
            if c in t94: continue
            s.add(c)
    return sorted(s, key=build_mozi.code_of)


# ---------------------------------------------------------------- 전체
def main():
    tr = gather()
    files = {}
    comp = set(os.environ.get('PARTS', 'scn,extend,names,elf,f22,vfs,img,movie').split(','))
    small = tr['small']
    for p in sorted(glob.glob(os.path.join(EX, 'SCNSCR', '*.BIN'))):
        f = os.path.basename(p)[:-4]
        rows = tr.get('scn:' + f)
        b = build_scn(f, rows or {}, small if not rows else None)
        if b != open(p, 'rb').read() and 'scn' in comp: files[('ROOM2', '/SCNSCR/%s.BIN' % f)] = b
    for p in sorted(glob.glob(os.path.join(EX, 'SCNSCR', 'INIT', '*.BIN'))):
        f = os.path.basename(p)[:-4]
        b = build_scn(f, {}, small, p)
        if b != open(p, 'rb').read() and 'scn' in comp: files[('ROOM2', '/SCNSCR/INIT/%s.BIN' % f)] = b
    if 'extend' in comp:
        for k, v in build_extend(tr.get('extend', {})).items(): files[('ROOM2', k)] = v
    if 'names' in comp:
        for k, v in build_scrdat(tr['names']).items(): files[('ROOM2', k)] = v
    mozi_table = None
    if 'mozi' in comp or 'elf' in comp:
        mc = mozi_chars(tr)
        mf, mozi_table = build_mozi.build(mc)
        print('소형 글꼴 추가 글자 %d개' % len(mc))
        for k, v in mf.items(): files[('ROOM2', k)] = v
    if 'elf' in comp: files[('ISO', '/SLPM_652.35')] = build_elf(tr.get('elf', {}), mozi_table)
    elif 'elfpatch' in comp:
        files[('ISO', '/SLPM_652.35')] = elfpatch.patch(open(os.path.join(ROOT, 'extract', 'SLPM_652.35'), 'rb').read())
    if 'f22' in comp:
        f1, _ = build_f22.build(os.path.join(EX, 'FONT'))
        files[('ROOM2', '/FONT/F22_001.TRA')] = f1
        files[('ROOM2', '/FONT/F22_000.TRA')] = build_f22.build000(os.path.join(EX, 'FONT'))
    if 'vfs' in comp:
        vi, vs = build_vfs.build(kmap.HANGUL)
        files[('ROOM2', '/TTF/ROOM2.VFI')] = vi; files[('ROOM2', '/TTF/ROOM2.VFS')] = vs
    if 'movie' in comp:
        for f in sorted(glob.glob(os.path.join(ROOT, 'movie', 'enc', '*.SFD'))):
            files[('ROOM2TV', '/ADX/TV/' + os.path.basename(f))] = open(f, 'rb').read()
    try:
        if 'img' not in comp: raise ImportError
        import build_img
        for k, v in build_img.build().items(): files[('ROOM2', k)] = v
    except ImportError:
        pass
    print('파일 %d개 교체' % len(files))
    if warn:
        print('경고 %d건' % len(warn)); open(os.path.join(ROOT, 'work', 'build_warn.txt'), 'w', encoding='utf-8').write('\n'.join(warn))
        for w in warn[:20]: print(' ', w)
    cvm.build(files)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
