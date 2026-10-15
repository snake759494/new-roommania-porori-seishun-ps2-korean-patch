import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from cvm import ISO, CVMS, walk, HDR
SKIP = ('.ADX', '.TV', '.BD', '.HD', '.SFD')
f = open(ISO, 'rb')
for k, s in CVMS.items():
    for n, l, sz, _ in walk(f, s*2048):
        if n.upper().endswith(SKIP): continue
        out = os.path.join('extract', k + n)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        f.seek(s*2048 + HDR + l*2048); open(out, 'wb').write(f.read(sz))
# ELF
import pycdlib
