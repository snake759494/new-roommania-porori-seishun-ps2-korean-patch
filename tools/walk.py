"""시험용: walk.py 동작... (r초=오른쪽 회전, l초=왼쪽, u초/d초=위/아래 보기, f=앞으로, s=스냅이름, mx,my초=커서 이동, o/x=버튼)"""
import sys, time, os
sys.path.insert(0, os.path.dirname(__file__))
import vpad, emu
def rs(x, y, t): vpad.stick(0x80, 0x80, x, y); time.sleep(t); vpad.w32(vpad.VANA, 0); time.sleep(0.3)
def ls(x, y, t): vpad.stick(x, y); time.sleep(t); vpad.w32(vpad.VANA, 0); time.sleep(0.2)
for a in sys.argv[1:]:
    k, v = a[0], a[1:]
    if k == 'r': rs(0xff, 0x80, float(v))
    elif k == 'l': rs(0x00, 0x80, float(v))
    elif k == 'u': rs(0x80, 0x00, float(v))
    elif k == 'd': rs(0x80, 0xff, float(v))
    elif k == 'f': vpad.press('T', 200); time.sleep(float(v or 2.5))
    elif k == 'b': vpad.press('S', 200); time.sleep(float(v or 2.5))
    elif k == 'o': vpad.press('O', 150); time.sleep(float(v or 1))
    elif k == 'x': vpad.press('X', 150); time.sleep(float(v or 1))
    elif k == 's': emu.snap(v)
    elif k == 'm':
        dx, dy, t = v.split(','); ls(int(dx, 16), int(dy, 16), float(t))
    elif k == 'w': time.sleep(float(v))
