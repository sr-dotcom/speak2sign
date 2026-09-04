import pytest

from speak2sign.gloss import lexicon as lex
from speak2sign.gloss import t5
from speak2sign.gloss.rules import stats

L = lex.load()


def fake_translate(text):
    # what a fine-tuned model typically returns for "rain is likely tonight in samoa"
    return ["TONIGHT", "RAIN", "DESC-LIKELY", "X-IN", "SAMOA"]


def test_t5_glosses_resolve_through_the_lexicon_never_inventing_signs():
    entries = t5.gloss("Rain is likely tonight in Samoa.", L, translate_fn=fake_translate)
    kinds = [(e.word, e.kind, e.concept) for e in entries]
    assert ("tonight", "sign", "tonight") in kinds
    assert ("rain", "sign", "rain") in kinds
    assert ("desc-likely", "sign", "chance") in kinds            # DESC- prefix stripped before lookup
    assert any(w == "x-in" and k == "dropped" for w, k, _ in kinds)   # pronoun/preposition marker dropped
    samoa = [e for e in entries if e.word == "samoa"][0]
    assert samoa.kind == "fingerspell" and samoa.letters[0] == "letter-s"
    s = stats(entries)
    assert s["validated"] == 3 and s["fingerspelled"] == 1


def test_t5_entries_carry_token_positions_in_range():
    entries = t5.gloss("The prime minister resigned on Sunday. Rain is likely.", L, translate_fn=lambda t: t.upper().split())
    assert all(0 <= e.token_index < 11 for e in entries)


@pytest.mark.skipif(not (t5.MODEL_DIR / "model.bin").exists(), reason="T5 export not present")
def test_real_model_translates_one_sentence():
    out = t5.translate("The prime minister resigned on Sunday.")
    assert out and all(isinstance(g, str) for g in out)
