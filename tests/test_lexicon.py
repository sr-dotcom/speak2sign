import csv
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LEX = ROOT / "data" / "lexicon"
CONCEPTS = LEX / "concepts.json"
needs_concepts = pytest.mark.skipif(not CONCEPTS.exists(), reason="concepts.json not built yet (run build_lexicon.py fetch)")


def test_vocab_ids_unique_and_wellformed():
    rows = list(csv.DictReader(open(LEX / "target_vocab.csv", encoding="utf-8")))
    ids = [r["concept_id"] for r in rows]
    assert len(ids) == len(set(ids))
    assert all(i == i.lower() and " " not in i for i in ids)


def test_senses_point_at_known_concepts():
    rows = list(csv.DictReader(open(LEX / "target_vocab.csv", encoding="utf-8")))
    ids = {r["concept_id"] for r in rows}
    senses = json.load(open(LEX / "senses.json", encoding="utf-8"))
    for word, rules in senses.items():
        if word.startswith("_"):
            continue
        for rule in rules:
            target = rule.get("concept") or rule.get("default")
            assert target in ids or target == "fingerspell", f"{word}: {target} is not a concept"


@needs_concepts
def test_every_concept_has_clip_licence_and_attribution():
    concepts = json.load(open(CONCEPTS, encoding="utf-8"))
    assert concepts
    for c in concepts:
        clip = c["clip"]
        assert (ROOT / "static" / clip["file"]).exists(), c["concept_id"]
        assert clip["licence"] in ("Public Domain", "CC BY-NC-SA 4.0")
        assert clip["attribution_url"].startswith("https://")
        if clip["source"] == "signbank":
            assert "aslsignbank.com/dictionary/gloss/" in clip["attribution_url"]


@needs_concepts
def test_no_keyword_collision_without_sense_rule():
    concepts = json.load(open(CONCEPTS, encoding="utf-8"))
    senses = json.load(open(LEX / "senses.json", encoding="utf-8"))
    owners = {}
    for c in concepts:
        for k in c["keywords"]:
            owners.setdefault(k, set()).add(c["concept_id"])
    collisions = {k: v for k, v in owners.items() if len(v) > 1 and k not in senses}
    assert not collisions, collisions
