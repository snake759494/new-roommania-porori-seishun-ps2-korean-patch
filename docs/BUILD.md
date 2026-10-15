# 재빌드

## 준비
- Python 3.11 이상 + `numpy Pillow scipy opencv-python fontTools pycdlib av imageio-ffmpeg zstandard`
- 저장소 최상위에 원본 `New Roommania - Porori Seishun (Japan).iso` (MD5 `79ecbd45bed6b44c45a7b79933b2fc8e`)
- 저장소 최상위에 글꼴 `NanumSquareNeo-aLt/bRg/cBd/dEb/eHv.ttf`, `SeoulHangangB.ttf` (`docs/FONT_CREDITS.md`)
- 번역 대본 `translation/` (저장소에 포함하지 않음: `translation/ko/parts/*.tsv`, `names.tsv`, `scn_small.tsv`, `fix/*.tsv`)
- 동영상 자막 대본 `movie/subs/ROOM_01~03.tsv` (저장소에 포함하지 않음)

## 순서
```
python tools/extract.py        # 원본 ISO → extract/ (CVM 내부 파일, 실행 파일)
python tools/elfstr.py         # 실행 파일 문자열 목록 (work/elfstr.json)
python tools/extract_text.py   # 원문 표 translation/jp
python tools/dump_img.py       # 텍스처 목록 (work/img)
python tools/movie_sub.py      # 동영상 자막: movie/orig/*.SFD → movie/enc/*.SFD (원본 SFD 는 tools/cvm.py 의 read 로 추출)
python tools/build.py          # → New Roommania - Porori Seishun (Korean).iso
python tools/qa_all.py         # 결과 ISO 전수 잔존 가나 검사
python tools/qa_leftover.py    # 스크립트·표시 문자열 잔존 일본어 검사
xdelta3 -0 -f -e -s "New Roommania - Porori Seishun (Japan).iso" "New Roommania - Porori Seishun (Korean).iso" New_Roommania_Porori_Seishun_KO.xdelta
```
- 빌드할 부분만 고르기: 환경 변수 `PARTS` (예: `PARTS=img,elf`), 실행 파일 문자열 분류는 `ELFCATS`.

## 와이드 패치
```
python tools/wide_hud.py       # 2D HUD 보정 코드 → pnach 줄 출력
```
`widescreen/SLPM-65235_<한글판 CRC>.pnach` 는 3D 시야각 줄 + 위 출력으로 구성합니다. 한글판 CRC 는 `tools/emu.py` 의 `elf_crc()` 로 구합니다(실행 파일이 바뀌면 CRC·파일명도 바뀜).

## 실기(에뮬레이터) 확인 도구
`tools/emu.py`(백그라운드 PCSX2 실행·상태 저장 스크린샷), `vpad.py`(pnach 가상 패드 + PINE), `nav.py`, `seq.sh`, `probe.py` — 포터블 PCSX2 를 `work/emu` 에 두고 PINE 포트 28235, 치트 사용으로 설정합니다.
