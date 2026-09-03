import pytest

from speak2sign import provenance
from speak2sign.gloss.rules import Entry


def test_badge_mapping_is_total_and_strict():
    assert provenance.badge("sign") == "validated"
    assert provenance.badge("number") == "validated"
    assert provenance.badge("fingerspell") == "fingerspelled"
    assert provenance.badge("none") == "not_available"
    assert provenance.badge("name") == "name"
    with pytest.raises(ValueError):
        provenance.badge("dropped")


def test_notes_explain_every_non_validated_entry():
    assert provenance.note(Entry("samoa", 0, kind="fingerspell", why=""), None) == "no established sign in this system"
    assert "digit" in provenance.note(Entry("97", 0, kind="number"), None)
    assert provenance.note(Entry("x", 0, kind="none", why="cannot fingerspell 'x'"), None).startswith("cannot")


def test_attributions_include_lane_source_once():
    a = provenance.attributions(["cats", "signbank"], "curated")
    assert [x["source"] for x in a] == ["cats", "signbank", "voa"]
    assert all(x["licence"] and x["url"] for x in a)
