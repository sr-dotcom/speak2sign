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


@pytest.mark.parametrize("kind", ["fingerspell", "name", "none"])
def test_every_non_validated_kind_gets_a_note_even_without_a_why(kind):
    assert provenance.note(Entry("samoa", 0, kind=kind, why=""), None)


def test_notes_carry_the_engine_reason_and_number_explanation():
    assert provenance.note(Entry("samoa", 0, kind="fingerspell", why=""), None) == "no established sign in this system"
    assert "digit" in provenance.note(Entry("97", 0, kind="number"), None)
    assert provenance.note(Entry("x", 0, kind="none", why="cannot fingerspell 'x'"), None).startswith("cannot")
    assert provenance.note(Entry("rain", 0, kind="sign", concept="rain"), None) is None


def test_attributions_are_deduplicated_and_complete():
    a = provenance.attributions(["cats", "signbank", "cats", "voa"], "curated")
    assert [x["source"] for x in a] == ["cats", "signbank", "voa"]
    assert all(x["licence"] and x["url"] and x["text"] for x in a)
    assert [x["source"] for x in provenance.attributions([], "typed")] == []
    assert [x["source"] for x in provenance.attributions(["cats"], "weather", "t5")] == ["cats", "nws", "t5", "aslg_pc12"]


def test_unknown_source_is_an_error_not_a_silent_drop():
    with pytest.raises(ValueError, match="wikimedia"):
        provenance.attributions(["wikimedia"], "typed")
    with pytest.raises(KeyError):
        provenance.attributions([], "typed", "llm")
