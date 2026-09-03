from pathlib import Path

import pytest

from speak2sign import asr

ROOT = Path(__file__).resolve().parents[1]
WAV = ROOT / "static" / "news" / "sichuan-landslide.wav"
needs_model = pytest.mark.skipif(not (asr.MODEL_DIR / "model.bin").exists() or not WAV.exists(), reason="whisper model or fixture audio not present")


def test_align_reference_interpolates_missing_words():
    hyp = [{"text": "rain", "start": 0.0, "end": 0.3}, {"text": "tonight", "start": 1.0, "end": 1.4}]
    onsets, ends, matched = asr.align_reference(["Rain", "is", "likely", "tonight."], hyp)
    assert matched == 2
    assert onsets == [0.0, pytest.approx(0.333, abs=0.01), pytest.approx(0.667, abs=0.01), 1.0]
    assert ends[0] == 0.3 and ends[1] is None


def test_wav_data_url_round_trips_header():
    import numpy as np
    url = asr.wav_data_url(np.zeros(1600, dtype="float32"))
    assert url.startswith("data:audio/wav;base64,UklGR")


@needs_model
def test_transcribe_real_clip_and_cap():
    audio = asr.decode(WAV.read_bytes())
    words = asr.transcribe(audio)
    text = " ".join(w["text"] for w in words).lower()
    assert "landslide" in text and len(words) > 30
    t = asr.upload_transcript("Chinese rescuers are searching for some 30 people after a landslide.", words, audio)
    assert t.lane == "upload" and t.media_url.startswith("data:audio/wav")


def test_clips_over_sixty_seconds_are_refused():
    import base64
    import numpy as np
    url = asr.wav_data_url(np.zeros(int(asr.SR * 61), dtype="float32"))
    wav_bytes = base64.b64decode(url.split(",", 1)[1])
    with pytest.raises(ValueError, match="limit is 60"):
        asr.decode(wav_bytes)
