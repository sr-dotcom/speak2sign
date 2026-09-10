"""Memory budget check: peak RSS with the lexicon, faster-whisper and (when its export is present) T5 loaded, one
transcription and one translation done.

Fails (exit 1) over BUDGET_MB. Run in CI and before any dependency change. Peak, not current: the process
high-water mark from the OS (ru_maxrss on Linux/macOS, peak_wset on Windows), so a spike inside a step cannot hide.
T5 is measured only where its export exists (locally, or on Cloud with T5_RELEASE_URL); CI prints that it was skipped.
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
from speak2sign.gloss import t5  # noqa: E402

BUDGET_MB = float(sys.argv[1]) if len(sys.argv) > 1 else 1800.0
FIXTURE = ROOT / "static" / "news" / "california-fire-warning.wav"


def peak_mb(proc):
    info = proc.memory_info()
    if hasattr(info, "peak_wset"):          # Windows
        return info.peak_wset / 1e6
    import resource
    maxrss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return maxrss / 1e6 if sys.platform == "darwin" else maxrss / 1e3   # bytes on macOS, kilobytes on Linux


def main():
    proc = psutil.Process()
    lexicon = lex.load()
    print(f"lexicon loaded ({len(lexicon)} concepts): {peak_mb(proc):.0f} MB")
    t = time.time()
    asr.model()
    print(f"whisper loaded in {time.time() - t:.1f}s: {peak_mb(proc):.0f} MB")
    audio = asr.decode(FIXTURE.read_bytes())
    t = time.time()
    words = asr.transcribe(audio)
    print(f"transcribed {len(audio) / asr.SR:.0f}s of audio in {time.time() - t:.1f}s ({len(words)} words): {peak_mb(proc):.0f} MB")
    transcript = asr.upload_transcript(" ".join(w["text"] for w in words), words, audio)
    tl = timeline.build(transcript, lexicon)
    print(f"timeline built with rules ({len(tl['entries'])} entries): {peak_mb(proc):.0f} MB")
    if t5.available():
        t = time.time()
        tl = timeline.build(transcript, lexicon, gloss_engine="t5")
        print(f"timeline built with t5 in {time.time() - t:.1f}s ({len(tl['entries'])} entries): {peak_mb(proc):.0f} MB")
    else:
        print("t5 export not present: not measured on this host")
    peak = peak_mb(proc)
    print(f"peak RSS {peak:.0f} MB; budget {BUDGET_MB:.0f} MB")
    if peak > BUDGET_MB:
        print("OVER BUDGET")
        sys.exit(1)


if __name__ == "__main__":
    main()
