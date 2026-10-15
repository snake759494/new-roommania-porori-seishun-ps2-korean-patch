# 사용: seq.sh 접두어 "키 대기" ... → 각 단계 후 스냅, 4장씩 합친 이미지 work/<접두어>_N.png
P=$1; shift; i=0; L=""
for st in "$@"; do python tools/vpad.py press $st >/dev/null; python tools/emu.py snap ${P}$i >/dev/null; L="$L work/shot_${P}$i.png"; i=$((i+1)); done
python - $P $L <<'PY'
import sys,os
from PIL import Image
P=sys.argv[1]; fs=sys.argv[2:]
for k in range(0,len(fs),4):
    im=Image.new('RGB',(1280,960))
    for i,f in enumerate(fs[k:k+4]): im.paste(Image.open(f).convert('RGB').resize((640,480)),((i%2)*640,(i//2)*480))
    im.save('work/%s_%d.png'%(P,k//4))
for f in fs: os.remove(f)
PY
