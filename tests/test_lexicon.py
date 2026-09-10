"""The committed lexicon data, and what lexicon.load refuses."""
import csv
import json
from pathlib import Path

import pytest

from speak2sign.gloss import lexicon as lex

ROOT = Path(__file__).resolve().parents[1]
LEX = ROOT / "data" / "lexicon"
CONCEPTS = json.loads((LEX / "concepts.json").read_text(encoding="utf-8"))
SENSES = json.loads((LEX / "senses.json").read_text(encoding="utf-8"))


def test_vocab_ids_unique_and_wellformed():
    rows = list(csv.DictReader(open(LEX / "target_vocab.csv", encoding="utf-8")))
    ids = [r["concept_id"] for r in rows]
    assert len(ids) == len(set(ids))
    assert all(i == i.lower() and " " not in i for i in ids)


def test_concept_ids_unique_and_every_clip_has_file_licence_and_attribution():
    assert CONCEPTS
    ids = [c["concept_id"] for c in CONCEPTS]
    assert len(ids) == len(set(ids))
    for c in CONCEPTS:
        clip = c["clip"]
        assert (ROOT / "static" / clip["file"]).exists(), c["concept_id"]
        assert clip["licence"] in ("Public Domain", "CC BY-NC-SA 4.0")
        assert clip["attribution_url"].startswith("https://")
        if clip["source"] == "signbank":
            assert "aslsignbank.com/dictionary/gloss/" in clip["attribution_url"]
        assert "badge" not in c   # the badge is decided at runtime from the entry kind, never stored


def test_senses_point_at_attested_concepts():
    attested = {c["concept_id"] for c in CONCEPTS if c["status"] == "attested"}
    for word, rules in SENSES.items():
        if word.startswith("_"):
            continue
        for rule in rules:
            target = rule.get("concept") or rule.get("default")
            assert target in attested or target == "fingerspell", f"{word}: {target} has no attested clip"


def test_no_keyword_collision_without_sense_rule():
    owners = {}
    for c in CONCEPTS:
        for k in c["keywords"]:
            owners.setdefault(k, set()).add(c["concept_id"])
    collisions = {k: v for k, v in owners.items() if len(v) > 1 and k not in SENSES}
    assert not collisions, collisions


def test_no_concept_lists_its_own_negation_as_a_keyword():
    for c in CONCEPTS:
        for k in c["keywords"]:
            for prefix in ("un", "non", "non-"):
                assert not (k.startswith(prefix) and k[len(prefix):] in c["keywords"]), (c["concept_id"], k)


def _lexicon_dir(tmp_path, concepts=CONCEPTS, senses=SENSES):
    d = tmp_path / "lexicon"
    d.mkdir(parents=True)
    (d / "concepts.json").write_text(json.dumps(concepts), encoding="utf-8")
    (d / "senses.json").write_text(json.dumps(senses), encoding="utf-8")
    return d


def test_load_refuses_a_sense_rule_with_no_clip(tmp_path):
    with pytest.raises(ValueError, match="ghost"):
        lex.load(_lexicon_dir(tmp_path, senses={"rain": [{"default": "ghost"}]}))


def test_load_refuses_duplicate_ids_and_unplayable_spans(tmp_path):
    with pytest.raises(ValueError, match="duplicate"):
        lex.load(_lexicon_dir(tmp_path, concepts=CONCEPTS + [CONCEPTS[0]]))
    broken = json.loads(json.dumps(CONCEPTS))
    broken[0]["clip"]["in_s"] = broken[0]["clip"]["out_s"] + 1
    with pytest.raises(ValueError, match="unplayable"):
        lex.load(_lexicon_dir(tmp_path / "b", concepts=broken))
