"""Measure each clip's duration and active motion span and record them in concepts.json.

`in_s`/`out_s` bound the span where frame-to-frame change exceeds 12% of the clip's own peak
(dictionary clips start and end in a neutral pose). The panel plays only that span (ADR 0008).
Re-running overwrites the spans: they are measurements, not reviewed edits. Exits 1 if any clip
is unreadable, and writes nothing in that case.

Build tool: needs opencv-python-headless (requirements-build.txt). Run after build_lexicon.py fetch.
Usage: python scripts/measure_clip_spans.py
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CONCEPTS = ROOT / "data" / "lexicon" / "concepts.json"
THRESH = 0.12
PAD_S = 0.1   # keep a little of the neutral pose on each side


def measure(path):
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    prev, energy = None, []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.resize(f, (160, 90)), cv2.COLOR_BGR2GRAY).astype(np.float32)
        energy.append(0.0 if prev is None else float(np.abs(g - prev).mean()))
        prev = g
    cap.release()
    if not energy:
        return None
    e = np.array(energy)
    dur = len(e) / fps
    active = np.where(e > THRESH * (e.max() or 1))[0]
    if len(active) == 0:
        return {"duration_s": round(dur, 3), "in_s": 0.0, "out_s": round(dur, 3)}
    return {"duration_s": round(dur, 3), "in_s": round(max(0.0, active[0] / fps - PAD_S), 3),
            "out_s": round(min(dur, active[-1] / fps + PAD_S), 3)}


def main():
    concepts = json.loads(CONCEPTS.read_text(encoding="utf-8"))
    missing = []
    for c in concepts:
        m = measure(ROOT / "static" / c["clip"]["file"])
        if m is None:
            missing.append(c["concept_id"])
            continue
        c["clip"].update(m)
    if missing:
        print(f"unreadable clips, nothing written: {missing}")
        sys.exit(1)
    CONCEPTS.write_text(json.dumps(concepts, indent=1, ensure_ascii=False), encoding="utf-8")
    full = sum(c["clip"]["duration_s"] for c in concepts)
    act = sum(c["clip"]["out_s"] - c["clip"]["in_s"] for c in concepts)
    share = f" ({act / full:.0%})" if full else ""
    print(f"{len(concepts)} clips measured: {full:.0f}s total, {act:.0f}s active{share}")


if __name__ == "__main__":
    main()
