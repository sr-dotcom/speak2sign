"""Upload lane speech-to-text: faster-whisper base.en int8, lazy-loaded, capped at 60 s.

The demo path (curated items) never calls this. Uploaded audio is decoded in memory, transcribed,
and handed back as a TimedTranscript plus a WAV data URL for the panel; nothing is written to disk
and nothing leaves the server (ADR 0002 memory rules; TRD §12 privacy).
"""
import base64
import difflib
import io
import re
import urllib.request
import wave
from pathlib import Path

import numpy as np

from speak2sign.transcript import TimedTranscript, Word

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "models" / "faster-whisper-base.en"
MODEL_REPO = "https://huggingface.co/Systran/faster-whisper-base.en/resolve/main/"
MODEL_FILES = ("config.json", "model.bin", "tokenizer.json", "vocabulary.txt")
UA = {"User-Agent": "speak2sign-v2 (university project; https://github.com/sr-dotcom/speak2sign)"}
SR = 16000
MAX_S = 60.0
FALLBACK_GAP_S = 0.38
_model = None


def ensure_model():
    """Fetch the CTranslate2 files once with urllib (works behind TLS-inspecting proxies where the HF client does not)."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for name in MODEL_FILES:
        dest = MODEL_DIR / name
        if not dest.exists():
            with urllib.request.urlopen(urllib.request.Request(MODEL_REPO + name, headers=UA), timeout=300) as r:
                dest.write_bytes(r.read())
    return MODEL_DIR


def model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel  # imported here so the demo path never pays for it
        _model = WhisperModel(str(ensure_model()), device="cpu", compute_type="int8")
    return _model


def decode(data: bytes):
    """Any container/codec PyAV can read -> float32 mono at 16 kHz. Raises ValueError over the cap."""
    from faster_whisper.audio import decode_audio
    audio = decode_audio(io.BytesIO(data), sampling_rate=SR)
    if len(audio) / SR > MAX_S:
        raise ValueError(f"clip is {len(audio) / SR:.0f} s; the limit is {MAX_S:.0f} s")
    return audio


def transcribe(audio):
    """Word-level transcript of decoded audio."""
    segments, _ = model().transcribe(audio, word_timestamps=True, language="en", beam_size=1)
    words = []
    for seg in segments:
        for w in seg.words or []:
            words.append({"text": w.word.strip(), "start": round(float(w.start), 3), "end": round(float(w.end), 3)})
    return words


def wav_bytes(audio):
    """16 kHz mono 16-bit WAV bytes from float32 samples."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
    return buf.getvalue()


def wav_data_url(audio):
    return "data:audio/wav;base64," + base64.b64encode(wav_bytes(audio)).decode("ascii")


def _norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def align_reference(ref_tokens, hyp_words, t0=0.0):
    """Onset per reference word from whisper words (difflib), gaps interpolated. Returns (onsets, ends, matched)."""
    ref = [_norm(t) for t in ref_tokens]
    hyp = [_norm(w["text"]) for w in hyp_words]
    onsets, ends = [None] * len(ref), [None] * len(ref)
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ref, hyp, autojunk=False).get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                onsets[i1 + k] = hyp_words[j1 + k]["start"] - t0
                ends[i1 + k] = hyp_words[j1 + k]["end"] - t0
    matched = sum(1 for o in onsets if o is not None)
    known = [i for i, o in enumerate(onsets) if o is not None]
    for i in range(len(ref)):
        if onsets[i] is None:
            prev = max([k for k in known if k < i], default=None)
            nxt = min([k for k in known if k > i], default=None)
            if prev is None and nxt is None:
                onsets[i] = i * FALLBACK_GAP_S
            elif prev is None:
                onsets[i] = max(0.0, onsets[nxt] - (nxt - i) * FALLBACK_GAP_S)
            elif nxt is None:
                onsets[i] = (ends[prev] or onsets[prev]) + (i - prev - 1) * FALLBACK_GAP_S
            else:
                onsets[i] = onsets[prev] + (onsets[nxt] - onsets[prev]) * (i - prev) / (nxt - prev)
    return [round(max(0.0, o), 3) for o in onsets], [round(e, 3) if e is not None else None for e in ends], matched


def upload_transcript(text, hyp_words, audio):
    """Build the upload lane's transcript from the (possibly edited) text and whisper's word timings."""
    tokens = text.split()
    onsets, ends, _ = align_reference(tokens, hyp_words)
    words = tuple(Word(t, o, e) for t, o, e in zip(tokens, onsets, ends))
    return TimedTranscript("upload", "upload", words, "audio", wav_data_url(audio), round(len(audio) / SR, 3),
                           title="Uploaded clip", source="Your uploaded clip, transcribed on the server with faster-whisper base.en; not stored")
