"""Build the concept lexicon from the target vocabulary.

Two modes, run in order:

  python scripts/build_lexicon.py plan    # search CATS (archive.org) and ASL Signbank; write candidates.json + report
  python scripts/build_lexicon.py fetch   # download the chosen clip per concept into static/; write concepts.json + attribution.json

Sources and rules (ADR 0007):
- CATS "The ASL Dictionary" on archive.org: public domain; primary. Matched by item title.
- ASL Signbank: CC BY-NC-SA 4.0; secondary (letters, digits, gaps). Matched by ECV keyword.
  Each Signbank clip records its entry weblink, as the conditions page asks.
- Requests are rate-limited to one per second with a User-Agent naming the project.
- Nothing is downloaded in `plan`. `fetch` skips files that already exist, so it is resumable.
"""
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOCAB = ROOT / "data" / "lexicon" / "target_vocab.csv"
CANDIDATES = ROOT / "data" / "lexicon" / "candidates.json"
CONCEPTS = ROOT / "data" / "lexicon" / "concepts.json"
ATTRIBUTION = ROOT / "data" / "lexicon" / "attribution.json"
STATIC = ROOT / "static"

UA = {"User-Agent": "speak2sign-v2 lexicon builder (university project; https://github.com/sr-dotcom/speak2sign)"}
CATS_CREATOR = 'creator:("Center for Accessible Technology in Sign")'
SIGNBANK_ECV = "https://aslsignbank.com/static/ecv/asl.ecv"
SIGNBANK_ENTRY = "https://aslsignbank.com/dictionary/gloss/{id}.html"
SIGNBANK_VIDEO = "https://aslsignbank.com/dictionary/protected_media/glossvideo/ASL/{prefix}/{gloss}-{id}.mp4"
SIGNBANK_CITATION = "Hochgesang, J. A., Crasborn, O., & Lillo-Martin, D. (2017-2026). ASL Signbank. https://aslsignbank.com"
DELAY_S = 1.0

DIGIT_GLOSS = {"0": "ZERO", "1": "ONE", "2": "TWO", "3": "THREE", "4": "FOUR", "5": "FIVE", "6": "SIX", "7": "SEVEN", "8": "EIGHT", "9": "NINE"}


def get(url, binary=False, tries=3):
    """Rate-limited GET with a short retry: archive.org drops connections now and then."""
    for attempt in range(tries):
        time.sleep(DELAY_S * (attempt + 1))
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                data = r.read()
            return data if binary else data.decode("utf-8", "replace")
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
            if isinstance(e, urllib.error.HTTPError) and 400 <= e.code < 500:
                raise
            if attempt == tries - 1:
                raise
            print(f"  retry {attempt + 1} after {e.__class__.__name__}: {url[:80]}", flush=True)


def keywords_of(row):
    # keywords are "word, word (note), ..."; drop parenthetical notes and symbols
    out = []
    for k in row["keywords"].split(","):
        k = re.sub(r"\(.*?\)", "", k).strip().lower()
        if k and re.match(r"^[a-z][a-z .'-]*$", k):
            out.append(k)
    return out or [row["concept_id"].replace("-", " ")]


# ---------- CATS ----------

def cats_search(keywords):
    """One request per concept: title matches any of the first four keywords."""
    terms = " OR ".join(f'"{k}"' for k in keywords[:4])
    q = f"{CATS_CREATOR} AND title:({terms})"
    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode({"q": q, "output": "json", "rows": 25}) + "&fl[]=identifier&fl[]=title&fl[]=rights"
    try:
        docs = json.loads(get(url))["response"]["docs"]
    except Exception as e:  # network or JSON; recorded, not fatal
        return [], f"search error: {e}"
    return docs, None


def cats_score(title, keywords):
    """3 = title is exactly a keyword; 2 = keyword is one of the comma-separated title parts; 1 = keyword starts a part; 0 = no."""
    t = title.lower().strip()
    parts = [p.strip() for p in re.split(r"[,/;]", t)]
    best = 0
    for k in keywords:
        if t == k:
            return 3
        if k in parts:
            best = max(best, 2)
        elif any(p.startswith(k + " ") or p.startswith(k + "-") for p in parts):
            best = max(best, 1)
    return best


def cats_pick(docs, keywords):
    scored = [(cats_score(d.get("title", ""), keywords), d) for d in docs if d.get("rights", "") == "Public Domain"]
    scored = [s for s in scored if s[0] > 0]
    if not scored:
        return None
    scored.sort(key=lambda s: (-s[0], len(s[1].get("title", ""))))
    score, d = scored[0]
    return {"source": "cats", "score": score, "identifier": d["identifier"], "title": d.get("title", ""),
            "attribution_url": f"https://archive.org/details/{d['identifier']}", "licence": "Public Domain"}


# ---------- Signbank ----------

def signbank_index():
    root = ET.fromstring(get(SIGNBANK_ECV).encode("utf-8"))
    rows = []
    for e in root.iter():
        if e.tag.endswith("CV_ENTRY_ML"):
            v = e.find("{*}CVE_VALUE")
            if v is None or not v.text:
                continue
            desc = [d.strip().lower() for d in (v.get("DESCRIPTION") or "").split(",")]
            rows.append({"id": e.get("CVE_ID"), "gloss": v.text.strip(), "keywords": desc})
    return rows


def signbank_pick(index, concept, keywords):
    if concept.startswith("letter-"):
        want = concept.split("-")[1].upper()
        hits = [r for r in index if r["gloss"].upper() == f"LETTER-{want}"]
    elif concept.startswith("digit-"):
        want = DIGIT_GLOSS[concept.split("-")[1]]
        hits = [r for r in index if r["gloss"].upper() == want]
    else:
        hits = []
        for k in keywords:
            hits += [r for r in index if k in r["keywords"] and not r["gloss"].startswith("~")]
    if not hits:
        return None
    # prefer a gloss whose base form (variant suffix stripped) is one of our keywords, then the shortest gloss
    def base(g):
        m = re.match(r"^[A-Z][A-Z-]*", g)
        return (m.group(0) if m else g).rstrip("-").lower().replace("-", " ")
    hits.sort(key=lambda r: (0 if base(r["gloss"]) in keywords else 1, len(r["gloss"])))
    return signbank_record(hits[0], score=2)


def signbank_record(r, score):
    prefix = re.sub(r"[^A-Z]", "", r["gloss"].upper())[:2]
    return {"source": "signbank", "score": score, "id": r["id"], "gloss": r["gloss"],
            "attribution_url": SIGNBANK_ENTRY.format(id=r["id"]),
            "video_url": SIGNBANK_VIDEO.format(prefix=prefix, gloss=urllib.parse.quote(r["gloss"]), id=r["id"]),
            "licence": "CC BY-NC-SA 4.0", "citation": SIGNBANK_CITATION}


def signbank_video_url(s):
    """The video file is named after the lemma, not the variant gloss (SAYstr -> SAY-536.mp4).
    Read the entry page and take the .mp4 it references; fall back to the guessed URL."""
    try:
        html = get(s["attribution_url"])
        m = re.search(r'(?:src|href)="(/dictionary/protected_media/glossvideo/[^"]+\.mp4)"', html)
        if m:
            return "https://aslsignbank.com" + m.group(1)
    except Exception as e:
        print(f"  entry page unreadable ({e.__class__.__name__}); guessing video URL")
    return s["video_url"]


# ---------- modes ----------

OVERRIDES = ROOT / "data" / "lexicon" / "overrides.json"


def apply_override(rec, ov, index):
    """A reviewed override: {"source": "signbank", "gloss": "PEOPLE"} or {"source": "cats", "identifier": "..."}."""
    if ov["source"] == "signbank":
        hit = [r for r in index if r["gloss"] == ov["gloss"]]
        if not hit:
            rec["note"] = f"override gloss {ov['gloss']} not in ECV"
            return
        rec["signbank"] = signbank_record(hit[0], score=3)
        rec["chosen"] = "signbank"
    else:
        rec["cats"] = {"source": "cats", "score": 3, "identifier": ov["identifier"], "title": ov.get("title", ""),
                       "attribution_url": f"https://archive.org/details/{ov['identifier']}", "licence": "Public Domain"}
        rec["chosen"] = "cats"
    rec["note"] = "reviewed override: " + ov.get("why", "")


def plan(only=None):
    vocab = list(csv.DictReader(open(VOCAB, encoding="utf-8")))
    index = signbank_index()
    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8")) if OVERRIDES.exists() else {}
    overrides = {k: v for k, v in overrides.items() if not k.startswith("_")}
    out = json.loads(CANDIDATES.read_text(encoding="utf-8")) if (only and CANDIDATES.exists()) else {}
    print(f"Signbank ECV: {len(index)} entries; vocabulary: {len(vocab)} rows; overrides: {len(overrides)}")
    for i, row in enumerate(vocab, 1):
        cid = row["concept_id"]
        if only and cid not in only:
            continue
        kws = keywords_of(row)
        if cid in overrides:
            rec = {"concept_id": cid, "source_block": row["source"], "keywords": kws, "cats": None, "signbank": None, "chosen": None, "note": None}
            apply_override(rec, overrides[cid], index)
            out[cid] = rec
            continue
        rec = {"concept_id": cid, "source_block": row["source"], "keywords": kws, "cats": None, "signbank": None, "chosen": None, "note": None}
        if row["source"] in ("letter", "digit"):
            rec["signbank"] = signbank_pick(index, cid, kws)
        else:
            docs, err = cats_search(kws)
            rec["cats"] = cats_pick(docs, kws)
            rec["signbank"] = signbank_pick(index, cid, kws)
            if err:
                rec["note"] = err
        if rec["cats"] and rec["cats"]["score"] >= 2:
            rec["chosen"] = "cats"
        elif rec["signbank"]:
            rec["chosen"] = "signbank"
        elif rec["cats"]:
            rec["chosen"] = "cats"  # weak title match; flag for review
            rec["note"] = (rec["note"] or "") + " weak CATS title match, review"
        out[cid] = rec
        if i % 20 == 0:
            print(f"  {i}/{len(vocab)} …", flush=True)
    CANDIDATES.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    report(out)


def report(out):
    by = {}
    for r in out.values():
        by[r["chosen"] or "none"] = by.get(r["chosen"] or "none", 0) + 1
    print("\nPLAN REPORT")
    print(f"  chosen: {by}")
    missing = [c for c, r in out.items() if not r["chosen"]]
    weak = [c for c, r in out.items() if r["chosen"] == "cats" and r["cats"]["score"] < 2]
    print(f"  no clip found ({len(missing)}): {', '.join(missing)}")
    print(f"  weak CATS matches to review ({len(weak)}): {', '.join(weak)}")


def fetch():
    cands = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    previous = {c["concept_id"]: c for c in json.loads(CONCEPTS.read_text(encoding="utf-8"))} if CONCEPTS.exists() else {}
    concepts, attributions = [], []
    failures = {}
    for cid, rec in cands.items():
        src = rec["chosen"]
        if not src:
            continue
        sub = "letters" if rec["source_block"] in ("letter", "digit") else "clips"
        dest = STATIC / sub / f"{cid}.mp4"
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            if src == "cats":
                c = rec["cats"]
                if not dest.exists():
                    md = json.loads(get(f"https://archive.org/metadata/{c['identifier']}"))
                    mp4s = [f["name"] for f in md.get("files", []) if f["name"].lower().endswith(".mp4")]
                    mp4s.sort(key=lambda n: 0 if n.lower().endswith(".ia.mp4") else 1)  # small derivative first
                    if not mp4s:
                        raise RuntimeError(f"no mp4 in item {c['identifier']}")
                    data = None
                    for name in mp4s[:2]:
                        try:
                            data = get(f"https://archive.org/download/{c['identifier']}/{urllib.parse.quote(name)}", binary=True)
                            break
                        except Exception as e:  # try the other derivative before giving up
                            print(f"  {cid}: {name} failed ({e.__class__.__name__}), trying next")
                    if data is None:
                        raise RuntimeError("all mp4 derivatives failed")
                    dest.write_bytes(data)
                clip = {"file": f"{sub}/{cid}.mp4", "source": "cats", "source_id": c["identifier"], "attribution_url": c["attribution_url"], "licence": c["licence"]}
            else:
                s = rec["signbank"]
                if not dest.exists():
                    dest.write_bytes(get(signbank_video_url(s), binary=True))
                clip = {"file": f"{sub}/{cid}.mp4", "source": "signbank", "source_id": s["id"], "gloss": s["gloss"],
                        "attribution_url": s["attribution_url"], "licence": s["licence"], "citation": s["citation"]}
        except Exception as e:
            failures[cid] = f"{e.__class__.__name__}: {e}"[:160]
            print(f"  {cid}: FAILED {failures[cid]}")
            continue
        prev = previous.get(cid, {})
        measured = ("duration_s", "in_s", "out_s")
        same_clip = {k: v for k, v in prev.get("clip", {}).items() if k not in measured} == clip
        if same_clip:
            clip.update({k: prev["clip"][k] for k in measured if k in prev["clip"]})
        record = {"concept_id": cid, "gloss": (rec["signbank"] or {}).get("gloss") if src == "signbank" else cid.upper().replace("-", " "),
                  "keywords": rec["keywords"], "clip": clip, "badge": "validated",
                  "status": prev.get("status", "review") if same_clip else "review"}
        if prev.get("note"):
            record["note"] = prev["note"]
        concepts.append(record)
        attributions.append({"concept_id": cid, **clip})
        print(f"  {cid}: {src} -> {clip['file']}")
    CONCEPTS.write_text(json.dumps(concepts, indent=1, ensure_ascii=False), encoding="utf-8")
    ATTRIBUTION.write_text(json.dumps(attributions, indent=1, ensure_ascii=False), encoding="utf-8")
    (ROOT / "data" / "lexicon" / "fetch_failures.json").write_text(json.dumps(failures, indent=1), encoding="utf-8")
    total = sum(p.stat().st_size for p in STATIC.rglob("*.mp4"))
    print(f"\nwrote {len(concepts)} concepts; {len(failures)} failures (fetch_failures.json); static/ holds {total/1e6:.1f} MB of clips")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "plan"
    if mode == "plan":
        plan(only=set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None)
    else:
        fetch()
