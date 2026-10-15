"""CRI CVM(ROFS) 내부 ISO9660 파서/패처.
원본 ISO 안 CVM 위치(섹터)를 받아 내부 파일 목록과 디렉터리 레코드 위치를 돌려준다.
CVM 크기는 바꾸지 않는다: 커진 파일은 쓰이지 않는 FONT/BACKUP 영역으로 옮긴다."""
import struct, os, json, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ISO = os.path.join(ROOT, "New Roommania - Porori Seishun (Japan).iso")
OUT = os.path.join(ROOT, "New Roommania - Porori Seishun (Korean).iso")
CVMS = {'ROOM2TV': 2399, 'ROOM2': 975672}   # 원본 ISO 섹터
HDR = 0x1800
SEC = 2048


def walk(f, cvm_off):
    """[(경로, 내부 LBA, 크기, 디렉터리 레코드의 ISO 절대 오프셋)]"""
    base = cvm_off + HDR
    f.seek(base + 16 * SEC); pvd = f.read(SEC)
    out = []

    def rd(lba, size, path):
        f.seek(base + lba * SEC); d = f.read(size)
        p = 0
        while p < len(d):
            l = d[p]
            if l == 0:
                p = (p // SEC + 1) * SEC; continue
            rec = d[p:p + l]
            elba, = struct.unpack_from('<I', rec, 2); esz, = struct.unpack_from('<I', rec, 10)
            fl = rec[25]; nl = rec[32]; name = rec[33:33 + nl]
            if name not in (b'\0', b'\1'):
                n = name.decode('ascii', 'replace').split(';')[0]
                if fl & 2: rd(elba, esz, path + n + '/')
                else: out.append((path + n, elba, esz, base + lba * SEC + p))
            p += l
    root = pvd[156:156 + 34]
    lba, = struct.unpack_from('<I', root, 2); sz, = struct.unpack_from('<I', root, 10)
    rd(lba, sz, '/')
    return out


def table():
    f = open(ISO, 'rb')
    return {k: {n: (l, sz, rp) for n, l, sz, rp in walk(f, s * SEC)} for k, s in CVMS.items()}


def read(cvm, path, t=None):
    t = t or table()
    l, sz, rp = t[cvm][path]
    with open(ISO, 'rb') as f:
        f.seek(CVMS[cvm] * SEC + HDR + l * SEC); return f.read(sz)


# 재배치용 빈 영역(내부 LBA): 게임이 참조하지 않는 FONT/BACKUP/* (F22_000~003.TRA, FPAL.SVP)
FREE = {'ROOM2': [('/FONT/BACKUP/F22_000.TRA', '/FONT/BACKUP/FPAL.SVP')]}


def outer_records(f):
    """바깥 ISO9660: {경로: (LBA, 크기, 디렉터리 레코드 절대 오프셋)}"""
    f.seek(16 * SEC); pvd = f.read(SEC); out = {}

    def rd(lba, size, path):
        f.seek(lba * SEC); d = f.read(size); p = 0
        while p < len(d):
            l = d[p]
            if l == 0: p = (p // SEC + 1) * SEC; continue
            rec = d[p:p + l]; elba, esz = struct.unpack_from('<I', rec, 2)[0], struct.unpack_from('<I', rec, 10)[0]
            nm = rec[33:33 + rec[32]]
            if nm not in (b'\0', b'\1'):
                n = nm.decode('ascii').split(';')[0]
                if rec[25] & 2: rd(elba, esz, path + n + '/')
                else: out[path + n] = (elba, esz, lba * SEC + p)
            p += l
    root = pvd[156:190]
    rd(struct.unpack_from('<I', root, 2)[0], struct.unpack_from('<I', root, 10)[0], '/')
    return out


def build(files, out=OUT):
    """files: {(cvm, 내부경로): bytes}. 원본 ISO 를 복사(최초 1회)하고, 지난 빌드에서 쓴 영역은 원본으로 되돌린 뒤 새로 쓴다."""
    t = table()
    man_path = out + '.regions.json'
    if not os.path.exists(out) or os.path.getsize(out) != os.path.getsize(ISO) or not os.path.exists(man_path):
        print('원본 ISO 복사 중...'); shutil.copyfile(ISO, out); json.dump([], open(man_path, 'w'))
    regions = json.load(open(man_path))
    src = open(ISO, 'rb'); dst = open(out, 'r+b')
    for o, n in regions:   # 되돌리기
        src.seek(o); dst.seek(o); dst.write(src.read(n))
    regions = []

    def write(o, b):
        dst.seek(o); dst.write(b); regions.append((o, len(b)))
    pools = {}
    for cvm, fr in FREE.items():
        a, b = fr[0]
        l0 = t[cvm][a][0]; lb, szb, _ = t[cvm][b]
        pools[cvm] = [l0, lb + (szb + SEC - 1) // SEC]
    for (cvm, path), data in sorted(files.items()):
        if cvm == 'ISO':   # 바깥 ISO 파일: 제자리(할당 섹터 안에서만 크기 변경, ISO9660·UDF 크기 함께 갱신)
            lba, size, rp = outer_records(src)[path]
            alloc = (size + SEC - 1) // SEC * SEC
            assert len(data) <= alloc, (path, len(data), alloc)
            write(lba * SEC, data + b'\0' * (alloc - len(data)))
            if len(data) != size:
                src.seek(rp); rec = bytearray(src.read(34))
                struct.pack_into('<I', rec, 10, len(data)); struct.pack_into('>I', rec, 14, len(data))
                write(rp, bytes(rec[:18]))
                import udf
                u = udf.UDF(src); lbn = u.files[path.upper()]
                b, tag, ad0, l_ad, adtype = u._fe(lbn)
                struct.pack_into('<Q', b, 56, len(data))
                struct.pack_into('<I', b, ad0, len(data))
                struct.pack_into('<Q', b, 64, (len(data) + SEC - 1) // SEC)
                udf.fix_tag(b)
                write((u.part_start + lbn) * SEC, bytes(b))
            continue
        l, sz, rp = t[cvm][path]
        alloc = (sz + SEC - 1) // SEC; need = (len(data) + SEC - 1) // SEC
        if need > alloc:
            p = pools[cvm]
            if p[0] + need > p[1]: raise RuntimeError('재배치 공간 부족: %s %d섹터' % (path, need))
            l = p[0]; p[0] += need
            print('  재배치 %s → LBA %d (%d섹터)' % (path, l, need))
        base = CVMS[cvm] * SEC + HDR
        write(base + l * SEC, data + b'\0' * (need * SEC - len(data)))
        src.seek(rp); rec = bytearray(src.read(34))
        struct.pack_into('<I', rec, 2, l); struct.pack_into('>I', rec, 6, l)
        struct.pack_into('<I', rec, 10, len(data)); struct.pack_into('>I', rec, 14, len(data))
        write(rp, bytes(rec[:18]))
    dst.close()
    json.dump(regions, open(man_path, 'w'))
    left = {k: v[1] - v[0] for k, v in pools.items()}
    print('ISO 기록 완료:', out, '남은 재배치 섹터', left)


if __name__ == '__main__':
    t = table()
    for k in t:
        for n, (l, sz, rp) in sorted(t[k].items(), key=lambda x: x[1][0]): print(k, l, sz, n)
