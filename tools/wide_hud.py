"""16:9 와이드용 2D(HUD) 가로 보정 코드.
게임의 GIF 패킷 전송 함수(0x1a1c30) 앞에 끼어들어, 패킷 속 PACKED/A+D 의 XYZ2·XYZF2·XYZ3·XYZF3 X 좌표를
화면 가운데(GS 12.4 고정소수 0x8000 = 화면 x 320)를 기준으로 3/4 로 줄인다(4:3 그림을 16:9 화면 가운데에 그대로 보이게).
python tools/wide_hud.py            → pnach 줄 출력
python tools/wide_hud.py live       → 실행 중인 PCSX2(PINE)에 바로 써 넣기(시험용)"""
import sys, os
CAVE = 0x000F0000
HOOK = 0x001A1C30
R = {n: i for i, n in enumerate('zero at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra'.split())}


def I(op, rs, rt, imm): return op << 26 | R[rs] << 21 | R[rt] << 16 | imm & 0xffff
def Rr(fn, rs, rt, rd, sa=0): return R[rs] << 21 | R[rt] << 16 | R[rd] << 11 | sa << 6 | fn


def assemble(src, base):
    lines = [l.split(';')[0].strip() for l in src.strip().splitlines()]
    lines = [l for l in lines if l]
    labels, pc = {}, base
    for l in lines:
        if l.endswith(':'): labels[l[:-1]] = pc
        else: pc += 4
    out, pc = [], base
    for l in lines:
        if l.endswith(':'): continue
        op, *a = l.replace(',', ' ').split()
        br = lambda t: ((labels[t] - pc - 4) >> 2) & 0xffff
        m = lambda s: (int(s.split('(')[0], 0), s.split('(')[1].rstrip(')'))
        if op == 'nop': w = 0
        elif op in ('addiu', 'andi', 'ori', 'xori', 'sltiu'):
            w = I({'addiu': 9, 'andi': 12, 'ori': 13, 'xori': 14, 'sltiu': 11}[op], a[1], a[0], int(a[2], 0))
        elif op in ('lw', 'lhu', 'lbu', 'sh', 'sw'):
            o, b = m(a[1]); w = I({'lw': 0x23, 'lhu': 0x25, 'lbu': 0x24, 'sh': 0x29, 'sw': 0x2b}[op], b, a[0], o)
        elif op == 'lui': w = I(0xf, 'zero', a[0], int(a[1], 0))
        elif op in ('addu', 'subu', 'sltu', 'and'):
            w = Rr({'addu': 0x21, 'subu': 0x23, 'sltu': 0x2b, 'and': 0x24}[op], a[1], a[2], a[0])
        elif op in ('srlv',): w = Rr(6, a[2], a[1], a[0])
        elif op in ('sll', 'srl', 'sra'): w = Rr({'sll': 0, 'srl': 2, 'sra': 3}[op], 'zero', a[1], a[0], int(a[2], 0))
        elif op == 'multu': w = Rr(0x19, a[0], a[1], 'zero')
        elif op == 'mflo': w = Rr(0x12, 'zero', 'zero', a[0])
        elif op == 'beq': w = I(4, a[0], a[1], br(a[2]))
        elif op == 'bne': w = I(5, a[0], a[1], br(a[2]))
        elif op == 'b': w = I(4, 'zero', 'zero', br(a[0]))
        elif op == 'j': w = 2 << 26 | (int(a[0], 0) >> 2) & 0x3ffffff
        else: raise ValueError(l)
        out.append(w); pc += 4
    return out


SRC = """
    lui t9, 0x16           ; 마우스 커서(+따라다니는 이름표)는 3D 위를 가리키므로 보정하지 않음:
    ori t9, t9, 0xe1e8     ;   스프라이트 함수 0x16d650(복귀 0x16e1e8) ← 0x12e160(복귀 0x12e1dc) 경로에서
    bne ra, t9, scale      ;   객체 깊이(z)가 -1.1 인 것
    nop
    lw t9, 176(sp)
    lui t8, 0x12
    ori t8, t8, 0xe1dc
    bne t9, t8, scale
    nop
    lw t9, 48(sp)          ; 객체 포인터(호출자 s1)
    lw t9, 44(t9)
    lui t8, 0xbf8c
    ori t8, t8, 0xcccd
    beq t9, t8, done
    nop
scale:
    lhu t0, 0(a0)          ; DMA 태그 QWC
    addiu t1, a0, 16       ; 데이터 시작
    sll t0, t0, 4
    addu t0, t1, t0        ; 끝
loop:
    sltu t2, t1, t0
    beq t2, zero, done
    nop
    lw t2, 0(t1)
    lw t3, 4(t1)
    lw t4, 8(t1)
    lw t5, 12(t1)
    addiu t1, t1, 16
    andi t2, t2, 0x7fff    ; NLOOP
    srl t6, t3, 28         ; NREG
    bne t6, zero, nr_ok
    nop
    addiu t6, zero, 16
nr_ok:
    srl t3, t3, 26
    andi t3, t3, 3         ; FLG
    bne t3, zero, notpacked
    nop
pl:
    beq t2, zero, loop
    nop
    addiu a2, zero, 0
rl:
    beq a2, t6, rdone
    nop
    sltiu v0, a2, 8
    beq v0, zero, hi
    sll v1, a2, 2
    srlv v0, t4, v1
    b got
    nop
hi:
    addiu v1, v1, -32
    srlv v0, t5, v1
got:
    andi v0, v0, 15
    xori v1, v0, 14        ; A+D 이면 주소 바이트
    bne v1, zero, chk
    nop
    lbu v0, 8(t1)
chk:
    andi v1, v0, 0xf6      ; 4,5,12,13 = XYZF2,XYZ2,XYZF3,XYZ3
    xori v1, v1, 4
    bne v1, zero, next
    nop
    lhu v0, 0(t1)
    addiu v0, v0, -32768
    sll v1, v0, 16
    sra v0, v1, 16         ; 부호 있는 (X - 0x8000)
    sll v1, v0, 1
    addu v0, v0, v1
    sra v0, v0, 2          ; x 3/4
    addiu v0, v0, -32768   ; + 0x8000 (하위 16비트)
    sh v0, 0(t1)
next:
    addiu t1, t1, 16
    addiu a2, a2, 1
    b rl
    nop
rdone:
    addiu t2, t2, -1
    b pl
    nop
notpacked:
    addiu v1, zero, 1
    bne t3, v1, img
    nop
    multu t2, t6
    mflo v0
    sll v0, v0, 3
    addiu v0, v0, 15
    srl v0, v0, 4
    sll v0, v0, 4
    b adv
    nop
img:
    sll v0, t2, 4
adv:
    addu t1, t1, v0
    b loop
    nop
done:
    lw v1, -28136(gp)      ; 덮어쓴 원래 명령 2개
    j 0x1a1c38
    addiu a2, zero, 1
"""


def words():
    code = assemble(SRC, CAVE)
    hook = [2 << 26 | (CAVE >> 2), 0]   # j CAVE ; nop
    return code, hook


def pnach():
    code, hook = words()
    ls = ['patch=1,EE,%08X,extended,%08X' % (0x20000000 | CAVE + 4 * i, w) for i, w in enumerate(code)]
    ls += ['patch=1,EE,%08X,extended,%08X' % (0x20000000 | HOOK + 4 * i, w) for i, w in enumerate(hook)]
    return '\n'.join(ls)


if __name__ == '__main__':
    if sys.argv[1:] == ['live']:
        sys.path.insert(0, os.path.dirname(__file__)); import vpad
        code, hook = words()
        for i, w in enumerate(code): vpad.w32(CAVE + 4 * i, w)
        vpad.w32(HOOK + 4, hook[1]); vpad.w32(HOOK, hook[0])
        print('ok', len(code))
    else:
        print(pnach())
