"""Regenerate contracts/example.timeline.json from one curated item, so the example always matches the schema and the builder.

Usage: python scripts/example_timeline.py   (run after any change to timeline.py or the schema)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from speak2sign import timeline  # noqa: E402
from speak2sign.gloss import lexicon as lex  # noqa: E402
from speak2sign.ingest import demo_set  # noqa: E402

ITEM = "california-fire-warning"
OUT = ROOT / "contracts" / "example.timeline.json"


def main():
    item = next(i for i in demo_set.items() if i["id"] == ITEM)
    tl = timeline.build(demo_set.transcript(item), lex.load())
    OUT.write_text(json.dumps(tl, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(tl['entries'])} entries, {len(tl['sentences'])} sentences")


if __name__ == "__main__":
    main()
