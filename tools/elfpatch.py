"""SLPM_652.35 코드 패치.
- 코드 동굴: 비어 있던 두 번째 PT_LOAD(vaddr 0x66FD00 = 원래 _end)를 파일 끝 섹션 정보 자리(0x305E80~)에 실어 사용.
  섹션 헤더는 로딩에 쓰이지 않으므로 e_shoff/e_shnum 을 0 으로 지운다.
- 힙 시작을 동굴 뒤로: SetupHeap 인자(0x100188), sbrk 초기 break(0x33B414).
- 좁은 띄어쓰기: F22 렌더러(0x12D110)의 글자 전진(0x12D57C)에서 코드 NARROW(0x81B0)이면 전진폭 절반."""
import struct

BASE = 0x100000; OFF = 0x80
CAVE_VA = 0x66FD00; CAVE_OFF = 0x305E80
NARROW = 0x81B0


def va2off(a): return a - BASE + OFF


def j(a): return 0x08000000 | ((a >> 2) & 0x3FFFFFF)


def cave_code(base):
    """F22 전진폭 후크. base = 이 코드가 놓일 주소"""
    c = [
        0xC600000C,                         # lwc1  f0,12(s0)
        0x90E80000,                         # lbu   t0,0(a3)
        0x24090000 | (NARROW >> 8),         # addiu t1,zero,0x81
        0x15090006,                         # bne   t0,t1,L1  (+6)
        0x90E80001,                         # lbu   t0,1(a3)
        0x24090000 | (NARROW & 0xFF),       # addiu t1,zero,0xB0
        0x15090003,                         # bne   t0,t1,L1  (+3)
        0x3C0A3F00,                         # lui   t2,0x3f00   (0.5)
        0x448A0800,                         # mtc1  t2,f1
        0x46010002,                         # mul.s f0,f0,f1
        # L1:
        0x4600AD40,                         # add.s f21,f21,f0
        0xC6000010,                         # lwc1  f0,16(s0)
        0x4600B580,                         # add.s f22,f22,f0
        j(0x12D590),
        0x00000000,
    ]
    # bne 오프셋 검증: 3번째(인덱스3) → L1(인덱스10): 10-4=6, 인덱스6 → 10-7=3
    return b''.join(struct.pack('<I', x) for x in c)


MAX_FILE = 1549 * 2048     # 바깥 ISO 에서 ELF 에 할당된 섹터 끝(다음 파일 직전)
MOZI_FREE1 = 512 - 94      # build_mozi.FREE1 과 같아야 함


def mozi_code(base, table_va, n):
    """소형 글꼴 매핑(0x291500)의 '없는 글자' 경로: a1=SJIS 코드 → 우리 표(u16 코드, u8 칸, u8 텍스처)에서 찾아
    v0=텍스처, a1=칸. 없으면 원래대로 텍스처0 칸 146(■)."""
    hi = (table_va + 0x8000) >> 16; lo = table_va & 0xFFFF
    c = [
        0x3C080000 | hi,                    # 0  lui   t0,hi
        0x25080000 | lo,                    # 1  addiu t0,t0,lo
        0x24090000 | n,                     # 2  addiu t1,zero,n
        0x950A0000,                         # 3  loop: lhu t2,0(t0)
        0x11450000 | 7,                     # 4  beq   t2,a1,found(12)
        0x00000000,                         # 5  nop
        0x2529FFFF,                         # 6  addiu t1,t1,-1
        0x1D20FFFB,                         # 7  bgtz  t1,loop
        0x25080004,                         # 8  addiu t0,t0,4
        0x24050092,                         # 9  addiu a1,zero,146
        j(0x2916A8),                        # 10 j     back
        0x0000102D,                         # 11 move  v0,zero
        0x91050002,                         # 12 found: lbu a1,2(t0)
        j(0x2916A8),                        # 13 j     back
        0x91020003,                         # 14 lbu   v0,3(t0)
    ]
    return b''.join(struct.pack('<I', x & 0xFFFFFFFF) for x in c)


def patch(elf, reloc=(), mozi_table=None):
    """reloc: [(문자열 바이트(NUL 포함), [데이터 포인터 VA...], [(lui VA, addiu VA)...])] → 동굴로 옮기고 참조 수정
    mozi_table: 소형 글꼴 추가 글자 코드 표(u16 LE)"""
    e = bytearray(elf)
    assert len(e) == 0x306030
    # 앞 0x40 바이트는 비워 둔다(시작 코드의 bss 지우기 루프가 _end 바로 뒤 16바이트를 덮어씀)
    cave = bytearray(0x40) + cave_code(CAVE_VA + 0x40)
    if mozi_table:
        n = len(mozi_table) // 4
        hook = CAVE_VA + len(cave)
        code_len = len(mozi_code(0, 0, n))
        table_va = hook + code_len
        cave += mozi_code(hook, table_va, n) + mozi_table
        assert struct.unpack_from('<2I', e, va2off(0x29169C)) == (0x24050092, 0x70001628)
        struct.pack_into('<2I', e, va2off(0x29169C), j(hook), 0)
    for s, ptrs, codes in reloc:
        while len(cave) % 4: cave.append(0)
        va = CAVE_VA + len(cave); cave += s
        for p in ptrs:
            assert struct.unpack_from('<I', e, va2off(p))[0] != 0
            struct.pack_into('<I', e, va2off(p), va)
        for lui, addiu in codes:
            x = struct.unpack_from('<I', e, va2off(lui))[0]; y = struct.unpack_from('<I', e, va2off(addiu))[0]
            assert x >> 26 == 0xF and y >> 26 in (9, 0x19)
            struct.pack_into('<I', e, va2off(lui), (x & 0xFFFF0000) | ((va + 0x8000) >> 16))
            struct.pack_into('<I', e, va2off(addiu), (y & 0xFFFF0000) | (va & 0xFFFF))
    while len(cave) % 16: cave.append(0)
    room = len(cave)
    assert CAVE_OFF + room <= MAX_FILE, ('동굴 초과', CAVE_OFF + room - MAX_FILE)
    e[CAVE_OFF:] = cave
    if len(e) < 0x306030: e += b'\0' * (0x306030 - len(e))   # 원래 크기 이하면 크기 유지
    # 프로그램 헤더 2
    phoff = struct.unpack_from('<I', e, 0x1C)[0]
    p2 = phoff + 32
    assert struct.unpack_from('<I', e, p2)[0] == 1
    struct.pack_into('<8I', e, p2, 1, CAVE_OFF, CAVE_VA, CAVE_VA, room, room, 7, 0x10)
    # 섹션 헤더 제거
    struct.pack_into('<I', e, 0x20, 0)
    struct.pack_into('<HHH', e, 0x2E, 0, 0, 0)
    # 힙 시작 이동
    new_end = (CAVE_VA + room + 0xFF) & ~0xFF
    hi = (new_end + 0x8000) >> 16; lo = new_end & 0xFFFF
    assert struct.unpack_from('<I', e, va2off(0x100180))[0] == 0x3C040067
    assert struct.unpack_from('<I', e, va2off(0x100188))[0] == 0x2484FD00
    struct.pack_into('<I', e, va2off(0x100180), 0x3C040000 | hi)
    struct.pack_into('<I', e, va2off(0x100188), 0x24840000 | lo)
    assert struct.unpack_from('<I', e, va2off(0x33B414))[0] == 0x66FD00
    struct.pack_into('<I', e, va2off(0x33B414), new_end)
    # F22 전진 후크
    assert struct.unpack_from('<4I', e, va2off(0x12D57C)) == (0xC600000C, 0x4600AD40, 0xC6000010, 0x4600B580)
    struct.pack_into('<4I', e, va2off(0x12D57C), j(CAVE_VA + 0x40), 0, 0, 0)
    return bytes(e)


if __name__ == '__main__':
    import sys
    d = open(sys.argv[1] if len(sys.argv) > 1 else 'extract/SLPM_652.35', 'rb').read()
    p = patch(d); print(len(p), hex(CAVE_VA))
