"""드림캐스트식 PVR 트위들(모턴 순서) 해제/적용"""
import numpy as np
def morton(w, h):
    """[h,w] 각 픽셀의 트위들 순번"""
    y, x = np.mgrid[0:h, 0:w]
    idx = np.zeros((h, w), np.int64)
    n = max(w, h).bit_length()
    for i in range(n):
        idx |= ((y >> i) & 1) << (2 * i)
        idx |= ((x >> i) & 1) << (2 * i + 1)
    return idx
def untwiddle4(px, w, h):
    lin = np.frombuffer(px, np.uint8)
    a = np.zeros(lin.size * 2, np.uint8); a[0::2] = lin & 15; a[1::2] = lin >> 4
    return a[morton(w, h)]
def twiddle4(img):
    h, w = img.shape
    a = np.zeros(w * h, np.uint8); a[morton(w, h)] = img
    return (a[0::2] | (a[1::2] << 4)).astype(np.uint8).tobytes()
def untwiddle8(px, w, h):
    return np.frombuffer(px, np.uint8)[morton(w, h)]
def twiddle8(img):
    h, w = img.shape
    a = np.zeros(w * h, np.uint8); a[morton(w, h)] = img
    return a.tobytes()


def untwiddle4_rect(px, w, h):
    """직사각형: 짧은 변 크기의 정사각 블록이 긴 변 방향으로 이어짐"""
    s = min(w, h); n = s * s // 2; out = np.zeros((h, w), np.uint8)
    for k in range(max(w, h) // s):
        blk = untwiddle4(px[k * n:(k + 1) * n], s, s)
        if h > w: out[k * s:(k + 1) * s, :] = blk
        else: out[:, k * s:(k + 1) * s] = blk
    return out


def twiddle4_rect(img):
    h, w = img.shape; s = min(w, h); out = b''
    for k in range(max(w, h) // s):
        out += twiddle4(img[k * s:(k + 1) * s, :] if h > w else img[:, k * s:(k + 1) * s])
    return out
