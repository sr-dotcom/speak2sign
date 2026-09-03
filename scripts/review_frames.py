"""Make contact sheets of the fetched clips so a human can eyeball every sign once.

Reads data/lexicon/concepts.json, grabs the middle frame of each clip, tiles them 6 per
row with the concept id, and writes docs/research/clip-review-<n>.jpg (48 clips per sheet).
Needs opencv-python-headless (dev tool only, not a runtime dependency):
    .venv/Scripts/pip install opencv-python-headless
Usage: python scripts/review_frames.py
"""
import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CONCEPTS = ROOT / "data" / "lexicon" / "concepts.json"
OUT = ROOT / "docs" / "research"
TILE_W, TILE_H, COLS, PER_SHEET = 240, 150, 6, 48


def mid_frame(path):
    cap = cv2.VideoCapture(str(path))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, n // 2))
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return None, n
    return cv2.resize(frame, (TILE_W, TILE_H - 22)), n


def main():
    concepts = json.load(open(CONCEPTS, encoding="utf-8"))
    tiles, bad = [], []
    for c in concepts:
        path = ROOT / "static" / c["clip"]["file"]
        frame, n = mid_frame(path) if path.exists() else (None, 0)
        tile = np.full((TILE_H, TILE_W, 3), 245, np.uint8)
        if frame is None:
            bad.append(c["concept_id"])
        else:
            tile[: TILE_H - 22] = frame
        label = f"{c['concept_id']} [{c['clip']['source']}] {n}f"
        cv2.putText(tile, label[:34], (4, TILE_H - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (20, 20, 20), 1, cv2.LINE_AA)
        tiles.append(tile)
    for s in range(0, len(tiles), PER_SHEET):
        chunk = tiles[s : s + PER_SHEET]
        while len(chunk) % COLS:
            chunk.append(np.full((TILE_H, TILE_W, 3), 245, np.uint8))
        rows = [np.hstack(chunk[i : i + COLS]) for i in range(0, len(chunk), COLS)]
        sheet = np.vstack(rows)
        out = OUT / f"clip-review-{s // PER_SHEET + 1}.jpg"
        cv2.imwrite(str(out), sheet, [cv2.IMWRITE_JPEG_QUALITY, 80])
        print("wrote", out.relative_to(ROOT))
    print(f"{len(tiles)} clips, {len(bad)} unreadable: {bad}")


if __name__ == "__main__":
    main()
