"""결과 ISO 에서 일본어(가나·한자) 잔존 검사: 스크립트·EXTEND·SCRDAT·ELF 표시 문자열"""
import sys, os, re, json, glob
sys.path.insert(0, os.path.dirname(__file__))
import cvm, ads, kmap
sys.stdout.reconfigure(encoding='utf-8')
t = cvm.table(); f = open(cvm.OUT, 'rb')
def read(path):
    l, sz, rp = t['ROOM2'][path]
    # 디렉터리 레코드는 결과 ISO 에서 다시 읽어야 함
    f.seek(rp); rec = f.read(34)
    import struct
    l = struct.unpack_from('<I', rec, 2)[0]; sz = struct.unpack_from('<I', rec, 10)[0]
    f.seek(cvm.CVMS['ROOM2'] * 2048 + cvm.HDR + l * 2048); return f.read(sz)
KANA = re.compile('[\u3041-\u30f6]')
bad = 0
for path in t['ROOM2']:
    if not (path.startswith('/SCNSCR/') and path.endswith('.BIN')): continue
    h, ops = ads.parse(read(path))
    for i, j, b in ads.strings(ops):
        s = kmap.decode(b)
        if KANA.search(s) and s not in ('デバッグ',):
            bad += 1
            if bad < 40: print(path, i, s)
print('스크립트 잔존', bad)
