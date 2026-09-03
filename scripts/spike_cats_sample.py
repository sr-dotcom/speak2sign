"""Spike 1: sample the CATS "ASL Dictionary" collection on archive.org.

Queries the advancedsearch API for items by the Center for Accessible Technology in
Sign, records the rights field, checks for letter/digit entries, and downloads a
small sample of MP4s so signer quality can be eyeballed.

Usage: python scripts/spike_cats_sample.py [out_dir] [n_download]
Writes: <out_dir>/cats_sample.json and <out_dir>/*.mp4
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://archive.org/advancedsearch.php"
CREATOR = 'creator:("Center for Accessible Technology in Sign")'
UA = {"User-Agent": "speak2sign-spike/0.1 (university project; contact via repo)"}


def search(query: str, rows: int, fields=("identifier", "title", "rights", "licenseurl")) -> dict:
    url = API + "?" + urllib.parse.urlencode({"q": query, "output": "json", "rows": rows}) + "".join(f"&fl[]={f}" for f in fields)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def metadata(identifier: str) -> dict:
    url = f"https://archive.org/metadata/{identifier}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def main() -> None:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "spike_out")
    n_download = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    out.mkdir(parents=True, exist_ok=True)

    total = search(CREATOR, 0)["response"]["numFound"]
    sample = search(CREATOR, 50)["response"]["docs"]
    rights = {}
    for d in sample:
        rights[d.get("rights", "MISSING")] = rights.get(d.get("rights", "MISSING"), 0) + 1

    # Letters, digits, and a few news words: does the collection have them?
    probes = ["A", "B", "Z", "1", "5", "rain", "storm", "president", "government", "election", "police", "weather"]
    probe_hits = {}
    for p in probes:
        q = f'{CREATOR} AND title:("{p}")'
        docs = search(q, 5)["response"]["docs"]
        probe_hits[p] = [d["identifier"] for d in docs]
        time.sleep(0.5)

    downloaded = []
    for d in sample[:n_download]:
        ident = d["identifier"]
        md = metadata(ident)
        mp4s = [f for f in md.get("files", []) if f["name"].lower().endswith(".mp4")]
        if not mp4s:
            downloaded.append({"identifier": ident, "mp4": None})
            continue
        f = mp4s[0]
        url = f"https://archive.org/download/{ident}/{urllib.parse.quote(f['name'])}"
        dest = out / f"{ident}.mp4"
        urllib.request.urlretrieve(url, dest)
        downloaded.append({"identifier": ident, "mp4": f["name"], "bytes": dest.stat().st_size,
                           "rights": md.get("metadata", {}).get("rights"),
                           "creator": md.get("metadata", {}).get("creator")})
        time.sleep(0.5)

    result = {"numFound": total, "rights_in_first_50": rights, "probe_hits": probe_hits, "downloaded": downloaded,
              "sample_titles": [d.get("title") for d in sample[:50]]}
    (out / "cats_sample.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "sample_titles"}, indent=2))


if __name__ == "__main__":
    main()
