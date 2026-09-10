"""Shared fixtures: the lexicon and the timeline invariants every lane must satisfy (the cross-field half of the contract)."""
import json
import sys
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from speak2sign.gloss import lexicon as lex  # noqa: E402

SCHEMA = json.loads((ROOT / "contracts" / "timeline.schema.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def lexicon():
    return lex.load()


def check_timeline(tl, lexicon):
    """Schema, then what the schema cannot say: ordering, sentence membership, every clip is the lexicon's own record."""
    jsonschema.validate(tl, SCHEMA)
    by_file = {c.clip_file: c for c in lexicon.concepts.values()}
    onsets = [e["onset_s"] for e in tl["entries"]]
    assert onsets == sorted(onsets)
    s = tl["stats"]
    assert s["validated"] + s["fingerspelled"] + s["names"] + s["not_available"] == len(tl["entries"]) == s["tokens"]
    spans = tl["sentences"]
    assert [x["index"] for x in spans] == list(range(len(spans)))
    for a, b in zip(spans, spans[1:]):
        assert a["t_start"] <= a["t_end"] == b["t_start"]
    if spans:
        assert spans[-1]["t_start"] <= spans[-1]["t_end"] <= s["speech_s"] + 1e-6
    for e in tl["entries"]:
        assert (len(e["clips"]) >= 1) == (e["badge"] in ("validated", "fingerspelled")), e
        span = spans[e["sentence"]]
        assert span["t_start"] <= e["onset_s"] <= span["t_end"], e
        concepts = [by_file[c["url"].removeprefix("app/static/")] for c in e["clips"]]   # a clip the lexicon does not own is a KeyError
        # the clip sequence is exactly what the entry says it is: one sign, or one clip per character in order
        if e["badge"] == "fingerspelled" or (e["badge"] == "validated" and e["word"].isdigit()):
            chars = [ch for ch in e["word"] if ch.isalnum()]
            assert [k.concept_id for k in concepts] == [f"digit-{ch}" if ch.isdigit() else f"letter-{ch.lower()}" for ch in chars], e
        elif e["badge"] == "validated":
            assert len(concepts) == 1 and concepts[0].gloss == e["gloss"], e
        for c, concept in zip(e["clips"], concepts):
            assert (c["source"], c["licence"], c["attribution_url"]) == (concept.source, concept.licence, concept.attribution_url)
            assert (c["in_s"], c["out_s"], c["duration_s"]) == (concept.in_s, concept.out_s or concept.duration_s, concept.duration_s)
            assert (ROOT / "static" / concept.clip_file).exists()
            assert 0 <= c["in_s"] < c["out_s"] <= c["duration_s"] + 1e-6
    times = [c["t"] for c in tl["captions"]]
    assert times == sorted(times)
    owners = [c["sentence"] for c in tl["captions"]]
    assert owners == sorted(owners)
    for c in tl["captions"]:
        span = spans[c["sentence"]]
        assert span["t_start"] <= c["t"] <= span["t_end"], c
        assert not (c.get("dropped") and c.get("partly")), c
    assert tl["playback"]["mode"] == "interpreter-paced"


@pytest.fixture
def check(lexicon):
    return lambda tl: check_timeline(tl, lexicon)
