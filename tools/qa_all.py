"""결과 ISO 전수 검사: CVM 내부 모든 파일 + ELF 에서 가나(히라가나·가타카나)가 들어간 SJIS 문자열을 찾는다.
한자 슬롯은 한글로 덮였으므로 한자는 '한글로 보임' → 가나만 잔존 일본어로 판정. 결과 work/qa_all.tsv"""
import sys, os, re, struct, collections
sys.path.insert(0, os.path.dirname(__file__))
import cvm, kmap
OUT = cvm.OUT
SJ = re.compile(rb'(?:[\x81-\x84\x88-\x9f\xe0-\xea][\x40-\x7e\x80-\xfc]){2,}')
KANA = re.compile('[\u3041-\u3093\u30a1-\u30f6]')
SKIP = ('.ADX', '.TV', '.BD', '.HD', '.SFD', '.SVR', '.TRA', '.PVR', '.RT', '.RO', '.RMS', '.RMD', '.VAG', '.PROG', '.SSET', '.VFS')
f = open(OUT, 'rb'); res = collections.Counter(); ex = {}
def read_cvm(cv, path, l, sz):
    f.seek(cvm.CVMS[cv] * 2048 + cvm.HDR + l * 2048); return f.read(sz)
def scan(name, d):
    for m in SJ.finditer(d):
        try: t = kmap.decode(m.group())
        except Exception: continue
        k = sum(1 for c in t if KANA.match(c))
        if k >= 2 and k * 2 >= len(t) * 0.3:
            res[name] += 1; ex.setdefault(name, []).append(t)
for cv, s in cvm.CVMS.items():
    for n, l, sz, rp in cvm.walk(f, s * 2048):
        if n.upper().endswith(SKIP): continue
        scan(cv + n, read_cvm(cv, n, l, sz))
r = cvm.outer_records(f)['/SLPM_652.35']; f.seek(r[0] * 2048); scan('ELF', f.read(r[1]))
sys.stdout.reconfigure(encoding='utf-8')
with open(os.path.join(cvm.ROOT, 'work', 'qa_all.tsv'), 'w', encoding='utf-8') as o:
    for k, v in res.most_common():
        print(v, k, ' | '.join(ex[k][:4])[:150])
        for t in ex[k]: o.write('%s\t%s\n' % (k, t))
print('총', sum(res.values()))
