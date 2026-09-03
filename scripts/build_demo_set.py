"""Build the curated news items: audio excerpt + word timings for each entry in data/demo/excerpts.json.

For each item: download the day's VOA newscast MP3 (public domain, Internet Archive), transcribe it with
faster-whisper base.en int8 (word timestamps), locate the excerpt by matching its reference text to the
whisper words, cut that span to a 16 kHz mono WAV under static/news/, align the reference text (the
archive's own transcript) to the whisper words for onsets, and write data/demo/<id>.json.

The deployed app never runs whisper: it reads the JSON. Speech-to-text and alignment live in
speak2sign.asr, shared with the upload lane.

Usage: python scripts/build_demo_set.py [work_dir]   (build env: requirements-build.txt)
"""
import difflib
import json
import sys
import time
import urllib.request
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from faster_whisper.audio import decode_audio  # noqa: E402

from speak2sign import asr  # noqa: E402

EXCERPTS = ROOT / "data" / "demo" / "excerpts.json"
OUT_AUDIO = ROOT / "static" / "news"
OUT_JSON = ROOT / "data" / "demo"
PAD_BEFORE, PAD_AFTER = 0.25, 0.6


def download(url, dest):
    if not dest.exists():
        with urllib.request.urlopen(urllib.request.Request(url, headers=asr.UA), timeout=120) as r:
            dest.write_bytes(r.read())
    return dest


def locate(ref_tokens, hyp_words):
    """Hyp word index range covering the reference text: best match for its first and last 8 tokens."""
    hyp = [asr._norm(w["text"]) for w in hyp_words]
    ref = [asr._norm(t) for t in ref_tokens]

    def find(chunk, lo, hi):
        best, best_i = 0.0, None
        for i in range(lo, max(lo, hi - len(chunk)) + 1):
            r = difflib.SequenceMatcher(None, chunk, hyp[i : i + len(chunk)]).ratio()
            if r > best:
                best, best_i = r, i
        return best_i, best

    head, hs = find(ref[:8], 0, len(hyp))
    tail, ts = find(ref[-8:], head, min(len(hyp), head + int(len(ref) * 1.6) + 20))
    if head is None or tail is None or hs < 0.5:
        raise RuntimeError(f"could not locate excerpt (head score {hs:.2f})")
    return head, tail + 8, hs, ts


def main():
    work = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "spike_out" / "voa")
    work.mkdir(parents=True, exist_ok=True)
    OUT_AUDIO.mkdir(parents=True, exist_ok=True)
    proc = psutil.Process()
    t = time.time()
    asr.model()
    print(f"model loaded in {time.time() - t:.1f}s; RSS {proc.memory_info().rss / 1e6:.0f} MB")
    for it in json.loads(EXCERPTS.read_text(encoding="utf-8"))["items"]:
        mp3 = download(it["mp3"], work / f"{it['broadcast_date']}.mp3")
        audio = decode_audio(str(mp3), sampling_rate=asr.SR)
        t = time.time()
        words = asr.transcribe(audio)
        secs = time.time() - t
        ref_tokens = it["text"].split()
        a, b, hs, ts = locate(ref_tokens, words)
        t0 = max(0.0, words[a]["start"] - PAD_BEFORE)
        t1 = min(len(audio) / asr.SR, words[b - 1]["end"] + PAD_AFTER)
        onsets, ends, matched = asr.align_reference(ref_tokens, words[a:b], t0)
        (OUT_AUDIO / f"{it['id']}.wav").write_bytes(asr.wav_bytes(audio[int(t0 * asr.SR) : int(t1 * asr.SR)]))
        out = {"id": it["id"], "title": it["id"].replace("-", " ").capitalize(), "broadcast_date": it["broadcast_date"], "topic": it["topic"],
               "source": f"VOA newscast {it['broadcast_date']} via Internet Archive (public domain)", "archive_item": it["archive_item"],
               "media": f"news/{it['id']}.wav", "duration_s": round(t1 - t0, 3), "text": it["text"],
               "words": [{"text": w, "onset_s": o, "end_s": e} for w, o, e in zip(ref_tokens, onsets, ends)],
               "alignment": {"whisper_model": "base.en int8", "matched_words": matched, "total_words": len(ref_tokens),
                             "locate_scores": [round(hs, 2), round(ts, 2)], "newscast_span_s": [round(t0, 2), round(t1, 2)]}}
        (OUT_JSON / f"{it['id']}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"{it['id']:26} span {t0:6.1f}-{t1:6.1f}s ({t1 - t0:4.1f}s)  aligned {matched}/{len(ref_tokens)}  "
              f"locate {hs:.2f}/{ts:.2f}  whisper {secs:.0f}s for {len(audio) / asr.SR:.0f}s audio")
    print(f"RSS {proc.memory_info().rss / 1e6:.0f} MB")


if __name__ == "__main__":
    main()
