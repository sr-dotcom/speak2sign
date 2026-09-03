"""Coverage and fingerspelling rate of the rule pass on the curated excerpts and a live forecast.

Usage: python scripts/coverage_report.py   (writes docs/04-testing/coverage-rules.md)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from speak2sign.gloss import lexicon as lex  # noqa: E402
from speak2sign.gloss.rules import gloss, stats  # noqa: E402

FORECAST = ("Sunny, with a high near 97. Heat index values as high as 105. South southwest wind 1 to 5 mph. "
            "Tonight, mostly clear, with a low around 75. Saturday, a slight chance of showers and thunderstorms "
            "between 2pm and 4pm. Partly cloudy, with a low around 72. Chance of precipitation is 30%.")


def main():
    L = lex.load()
    items = json.loads((ROOT / "data" / "demo" / "excerpts.json").read_text(encoding="utf-8"))["items"]
    items = items + [{"id": "nws-forecast (sample 2026-09-03)", "text": FORECAST}]
    lines = ["# Rule-pass coverage", "", f"Lexicon: {len(L)} attested concepts. Content tokens exclude dropped function words.", "",
             "| Item | Content tokens | Validated | Fingerspelled | Not available | Coverage | Fingerspelling rate | Fingerspelled words |",
             "|---|---|---|---|---|---|---|---|"]
    tot = {"tokens": 0, "validated": 0, "fingerspelled": 0, "not_available": 0}
    for it in items:
        entries = gloss(it["text"], L)
        s = stats(entries)
        for k in tot:
            tot[k] += s[k]
        fs = " ".join(e.word for e in entries if e.kind == "fingerspell")
        lines.append(f"| {it['id']} | {s['tokens']} | {s['validated']} | {s['fingerspelled']} | {s['not_available']} | "
                     f"{s['coverage']:.0%} | {s['fingerspelling_rate']:.0%} | {fs} |")
    n = tot["tokens"] or 1
    lines.append(f"| **All** | {tot['tokens']} | {tot['validated']} | {tot['fingerspelled']} | {tot['not_available']} | "
                 f"**{tot['validated']/n:.0%}** | **{tot['fingerspelled']/n:.0%}** | |")
    out = ROOT / "docs" / "04-testing" / "coverage-rules.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
