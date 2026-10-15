"""시험용 자동 조작: python tools/nav.py tutorial|newgame → 타이틀 메뉴까지 가서 선택"""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
import vpad, emu
from PIL import Image
def shot():
    emu.snap('nav'); return Image.open(os.path.join(emu.R, 'work', 'shot_nav.png')).convert('RGB')
def menu_visible(im):
    r, g, b = im.getpixel((100, 300)); return abs(r - 127) < 25 and abs(g - 159) < 25 and abs(b - 160) < 25
def to_menu(limit=25):
    for _ in range(limit):
        im = shot()
        if menu_visible(im): return True
        vpad.press('START' if _ % 2 else 'O'); time.sleep(2.5)
    return False
if __name__ == '__main__':
    ok = to_menu(); print('menu', ok)
    if ok and sys.argv[1] == 'tutorial': vpad.press('D'); time.sleep(1); vpad.press('O'); time.sleep(14); vpad.press('O'); time.sleep(6)
    if ok and sys.argv[1] == 'newgame': vpad.press('O'); time.sleep(5)
    emu.snap(sys.argv[2] if len(sys.argv) > 2 else 'nav2')
