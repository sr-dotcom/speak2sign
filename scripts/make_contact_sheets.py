"""Make contact sheets of the fetched clips so a human can eyeball every sign once.

Reads data/lexicon/concepts.json, grabs the middle frame of each clip, tiles them 6 per row with the
concept id, and writes docs/research/clip-review-<n>.jpg (48 clips per sheet). A middle frame shows
the signer and the handshape, not the whole movement; the clip itself is what plays.
Old sheets are removed first so the set on disk is always the current lexicon. Exits 1 if any clip
is unreadable or a sheet could not be written.

Build tool: needs opencv-python-headless (requirements-build.txt).
Usage: python scripts/make_contact_sheets.py
"""
import json
import sys
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
    for old in OUT.glob("clip-review-*.jpg"):
        old.unlink()
    failed = []
    for s in range(0, len(tiles), PER_SHEET):
        chunk = tiles[s : s + PER_SHEET]
        while len(chunk) % COLS:
            chunk.append(np.full((TILE_H, TILE_W, 3), 245, np.uint8))
        rows = [np.hstack(chunk[i : i + COLS]) for i in range(0, len(chunk), COLS)]
        out = OUT / f"clip-review-{s // PER_SHEET + 1}.jpg"
        if cv2.imwrite(str(out), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 80]):
            print("wrote", out.relative_to(ROOT))
        else:
            failed.append(out.name)
    print(f"{len(tiles)} clips, {len(bad)} unreadable: {bad}; {len(failed)} sheets not written: {failed}")
    if bad or failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
