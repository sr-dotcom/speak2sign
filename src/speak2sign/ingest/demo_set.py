"""Curated news items: pre-built audio excerpts and word timings under data/demo/ (built by scripts/build_demo_set.py)."""
import json
from pathlib import Path

from speak2sign.transcript import TimedTranscript, Word

ROOT = Path(__file__).resolve().parents[3]
DEMO = ROOT / "data" / "demo"


def items():
    """All built items, oldest broadcast first. An item exists only if its JSON and audio are both present."""
    out = []
    for p in sorted(DEMO.glob("*.json")):
        if p.name == "excerpts.json":
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        if (ROOT / "static" / d["media"]).exists():
            out.append(d)
    return sorted(out, key=lambda d: d["broadcast_date"])


def transcript(item):
    words = tuple(Word(w["text"], w["onset_s"], w.get("end_s")) for w in item["words"])
    return TimedTranscript(item["id"], "curated", words, "audio", "app/static/" + item["media"], item["duration_s"],
                           title=item["title"], source=item["source"], broadcast_date=item["broadcast_date"])
