"""테스트 전용 가상 패드(배포 안 함): PINE 으로 VPAD 에 버튼 마스크를 쓰면 게임이 눌린 것으로 인식.
후크: 0x16c390 (xori a0,a0,0xffff → 눌림=1 마스크) 직후 VPAD 를 OR, VANA 가 0 이 아니면 아날로그 4바이트 덮어씀.
마스크: SELECT=0x100 START=0x800 U=0x1000 R=0x2000 D=0x4000 L=0x8000 L2=1 R2=2 L1=4 R1=8 T=0x10 O=0x20 X=0x40 S=0x80
PINE 포트 28235 (work/emu/inis/PCSX2.ini)"""
import socket, struct, sys, time, os
VPAD = 0x000ff000; VANA = VPAD + 4; CAVE = 0x000ff100
BTN = dict(SELECT=0x100, START=0x800, U=0x1000, R=0x2000, D=0x4000, L=0x8000, L2=1, R2=2, L1=4, R1=8, T=0x10, O=0x20, X=0x40, S=0x80)
PORT = 28235
def j(a): return (2 << 26) | (a >> 2)
def section():
    code = [
        0x3c010000 | ((VPAD + 0x8000) >> 16),                 # lui at,hi
        0x8c210000 | (VPAD & 0xffff),              # lw at,lo(at)
        0x00812025,                                 # or a0,a0,at
        0xae040008,                                 # sw a0,8(s0)
        0x3c010000 | ((VANA + 0x8000) >> 16),
        0x8c210000 | (VANA & 0xffff),              # lw at,VANA
        0x10200002,                                 # beqz at,+2
        0x00000000,
        0xae210004,                                 # sw at,4(s1)
        j(0x16c398), 0x00000000]
    out = ["gametitle=New Roommania (dev vpad)"]
    out += ['patch=1,EE,%08x,word,%08x' % (CAVE + 4*i, c) for i, c in enumerate(code)]
    out += ['patch=1,EE,0016c390,word,%08x' % j(CAVE), 'patch=1,EE,0016c394,word,3884ffff']
    return '\n'.join(out) + '\n'
def pine(payload):
    s = socket.create_connection(('127.0.0.1', PORT), timeout=10)
    s.sendall(struct.pack('<I', len(payload) + 4) + payload)
    def rv(n):
        b = b''
        while len(b) < n:
            c = s.recv(n - len(b))
            if not c: raise EOFError
            b += c
        return b
    n = struct.unpack('<I', rv(4))[0]; body = rv(n - 4); s.close(); return body
def w32(a, v): return pine(struct.pack('<BII', 6, a, v))
def r32(a): return struct.unpack_from('<I', pine(struct.pack('<BI', 2, a)), 1)[0]
def rd(a, n):
    out = bytearray()
    for k in range(0, n, 8): out += pine(struct.pack('<BI', 3, a + k))[1:9]
    return bytes(out[:n])
def press(names, ms=300):
    m = 0
    for n in names.split('+'): m |= BTN[n]
    w32(VPAD, m); time.sleep(ms / 1000); w32(VPAD, 0); time.sleep(0.15)
def stick(lx, ly, rx=0x80, ry=0x80):   # 4(s1)=rx,ry,lx,ly
    w32(VANA, rx | ry << 8 | lx << 16 | ly << 24)
if __name__ == '__main__':
    c = sys.argv[1]
    if c == 'section': print(section(), end='')
    elif c == 'press':
        for k in sys.argv[2:]:
            try: time.sleep(float(k))
            except ValueError: press(k)
    elif c == 'hold': press(sys.argv[2], int(sys.argv[3]))
    elif c == 'stick': stick(*[int(x, 0) for x in sys.argv[2:]])
    elif c == 'save': print(pine(struct.pack('<BB', 9, int(sys.argv[2]))))
    elif c == 'load': print(pine(struct.pack('<BB', 0xa, int(sys.argv[2]))))
    elif c == 'status': print(pine(struct.pack('<B', 0xf)))
