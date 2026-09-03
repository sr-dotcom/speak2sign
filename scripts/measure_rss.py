"""Memory budget check: peak RSS with the lexicon and faster-whisper loaded and one transcription done.

Fails (exit 1) over BUDGET_MB. Run in CI and before any dependency change.
Usage: python scripts/measure_rss.py [budget_mb]
"""
import sys
import time
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from speak2sign import asr, timeline  # noqa: E402
from speak2sign.gloss import lexicon as lex  # noqa: E402

BUDGET_MB = float(sys.argv[1]) if len(sys.argv) > 1 else 1800.0
FIXTURE = ROOT / "static" / "news" / "california-fire-warning.wav"


def rss_mb(proc):
    info = proc.memory_info()
    return max(getattr(info, "peak_wset", 0), info.rss) / 1e6


def main():
    proc = psutil.Process()
    L = lex.load()
    print(f"lexicon loaded ({len(L)} concepts): {rss_mb(proc):.0f} MB")
    t = time.time()
    asr.model()
    print(f"whisper loaded in {time.time() - t:.1f}s: {rss_mb(proc):.0f} MB")
    audio = asr.decode(FIXTURE.read_bytes())
    t = time.time()
    words = asr.transcribe(audio)
    print(f"transcribed {len(audio) / asr.SR:.0f}s of audio in {time.time() - t:.1f}s ({len(words)} words): {rss_mb(proc):.0f} MB")
    tl = timeline.build(asr.upload_transcript(" ".join(w["text"] for w in words), words, audio), L)
    peak = rss_mb(proc)
    print(f"timeline built ({len(tl['entries'])} entries); peak RSS {peak:.0f} MB; budget {BUDGET_MB:.0f} MB")
    if peak > BUDGET_MB:
        print("OVER BUDGET")
        sys.exit(1)


if __name__ == "__main__":
    main()
