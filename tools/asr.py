"""동영상 음성 받아쓰기(일본어 원문, 로컬 faster-whisper). 번역은 사람이 직접 한다."""
import json, sys
from faster_whisper import WhisperModel
m = WhisperModel('large-v3', device='cpu', compute_type='int8')
for n in sys.argv[1:]:
    seg, _ = m.transcribe('movie/asr/%s.wav' % n, language='ja', beam_size=5, vad_filter=True, word_timestamps=False)
    rows = [dict(s=round(x.start, 2), e=round(x.end, 2), t=x.text) for x in seg]
    json.dump(rows, open('movie/asr/%s.json' % n, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(n, len(rows), flush=True)
