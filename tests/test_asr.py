import base64
import io
import wave
from pathlib import Path

import numpy as np
import pytest

from speak2sign import asr, timeline

ROOT = Path(__file__).resolve().parents[1]
WAV = ROOT / "static" / "news" / "sichuan-landslide.wav"
needs_model = pytest.mark.skipif(not (asr.MODEL_DIR / "model.bin").exists() or not WAV.exists(), reason="whisper model or fixture audio not present")


def hyp(*pairs):
    return [{"text": t, "start": s, "end": s + 0.3} for t, s in pairs]


def test_align_reference_interpolates_missing_words():
    onsets, ends, matched = asr.align_reference(["Rain", "is", "likely", "tonight."], hyp(("rain", 0.0), ("tonight", 1.0)))
    assert matched == 2
    assert onsets == [0.0, pytest.approx(0.333, abs=0.01), pytest.approx(0.667, abs=0.01), 1.0]
    assert ends[0] == 0.3 and ends[1] is None


def test_align_reference_extrapolates_at_both_ends_and_without_any_match():
    onsets, _, matched = asr.align_reference(["a", "b", "rain", "c", "d"], hyp(("rain", 2.0)))
    assert matched == 1 and onsets == [pytest.approx(2.0 - 2 * asr.FALLBACK_GAP_S), pytest.approx(2.0 - asr.FALLBACK_GAP_S), 2.0,
                                       pytest.approx(2.3), pytest.approx(2.3 + asr.FALLBACK_GAP_S)]
    onsets, ends, matched = asr.align_reference(["x", "y", "z"], hyp(("rain", 0.0)))
    assert matched == 0 and onsets == [0.0, pytest.approx(asr.FALLBACK_GAP_S), pytest.approx(2 * asr.FALLBACK_GAP_S)] and ends == [None] * 3
    assert asr.align_reference([], hyp(("rain", 0.0))) == ([], [], 0)


def test_wav_data_url_is_a_real_16k_mono_pcm_wav():
    samples = np.zeros(1600, dtype="float32")
    samples[10] = 0.5
    url = asr.wav_data_url(samples)
    head, b64 = url.split(",", 1)
    assert head == "data:audio/wav;base64"
    with wave.open(io.BytesIO(base64.b64decode(b64)), "rb") as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()) == (1, 2, 16000, 1600)
        pcm = np.frombuffer(w.readframes(1600), dtype="<i2")
    assert pcm[10] == int(0.5 * 32767) and pcm[0] == 0


@pytest.mark.parametrize("seconds,ok", [(1, True), (60, True), (60.5, False)])
def test_duration_cap_is_exactly_sixty_seconds(seconds, ok):
    url = asr.wav_data_url(np.zeros(int(asr.SR * seconds), dtype="float32"))
    wav_bytes = base64.b64decode(url.split(",", 1)[1])
    if ok:
        assert len(asr.decode(wav_bytes)) == int(asr.SR * seconds)
    else:
        with pytest.raises(ValueError, match="limit is 60"):
            asr.decode(wav_bytes)


def test_garbage_upload_raises_not_hangs():
    with pytest.raises(Exception):
        asr.decode(b"not audio at all")


def test_upload_timeline_is_valid_and_edits_cannot_run_past_the_audio(lexicon, check):
    audio = np.zeros(asr.SR * 2, dtype="float32")   # 2 s of silence stands in for the decoded clip
    words = hyp(("rain", 0.2), ("likely", 0.8), ("tonight", 1.4))
    t = asr.upload_transcript("Rain is likely tonight. Extra words typed in later by the user. And a third sentence.", words, audio)
    assert t.lane == "upload" and t.media_url.startswith("data:audio/wav") and t.duration_s == 2.0
    assert all(0 <= w.onset_s <= t.duration_s for w in t.words)
    tl = timeline.build(t, lexicon)
    check(tl)
    assert tl["media"]["kind"] == "audio" and len(tl["sentences"]) == 3 and tl["sentences"][-1]["t_end"] == 2.0
    # the appended sentences collapse onto the end of the recording, but every caption still belongs to its own sentence
    assert [c["sentence"] for c in tl["captions"]] == [0] * 4 + [1] * 8 + [2] * 4
    assert {e["sentence"] for e in tl["entries"]} == {0, 1, 2}


@needs_model
def test_transcribe_real_clip(lexicon, check):
    audio = asr.decode(WAV.read_bytes())
    words = asr.transcribe(audio)
    text = " ".join(w["text"] for w in words).lower()
    assert "landslide" in text and len(words) > 30
    t = asr.upload_transcript("Chinese rescuers are searching for some 30 people after a landslide.", words, audio)
    check(timeline.build(t, lexicon))
