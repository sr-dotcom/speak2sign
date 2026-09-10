"""The T5 path with the model replaced by a function: whatever it returns, no sign can be invented and no source word lost."""
import pytest

from speak2sign import timeline
from speak2sign.gloss import t5
from speak2sign.gloss.rules import stats
from speak2sign.transcript import from_text


def cooperative(text):
    # what a fine-tuned model typically returns for "rain is likely tonight in samoa"
    return ["TONIGHT", "RAIN", "DESC-LIKELY", "X-IN", "SAMOA"]


def test_t5_glosses_resolve_through_the_lexicon(lexicon):
    entries = t5.gloss("Rain is likely tonight in Samoa.", lexicon, translate_fn=cooperative)
    kinds = [(e.word, e.kind, e.concept) for e in entries]
    assert ("tonight", "sign", "tonight") in kinds
    assert ("rain", "sign", "rain") in kinds
    assert ("likely", "sign", "chance") in kinds            # DESC- prefix stripped before lookup and display
    assert any(w == "in" and k == "dropped" for w, k, _ in kinds)   # X- marker stripped, preposition dropped
    samoa = [e for e in entries if e.word == "samoa"][0]
    assert samoa.kind == "fingerspell" and samoa.letters[0] == "letter-s"
    s = stats(entries)
    assert s["validated"] == 3 and s["fingerspelled"] == 1


def test_fabricated_or_compound_glosses_never_borrow_a_sign(lexicon):
    entries = t5.gloss("Rain fell.", lexicon, translate_fn=lambda t: ["RAIN-COAT", "ZORBLAX", "12.5", "SUNDAY"])
    by_word = {e.word: e for e in entries}
    assert by_word["rain-coat"].kind == "fingerspell" and by_word["rain-coat"].concept is None   # not RAIN
    assert by_word["zorblax"].kind == "fingerspell"
    assert by_word["12.5"].kind == "none"
    assert by_word["sunday"].kind == "sign" and by_word["sunday"].concept == "sunday"
    assert not any(e.concept == "rain" for e in entries)


def test_a_number_the_source_never_said_is_refused_and_bare_markers_are_ignored(lexicon, check, monkeypatch):
    monkeypatch.setattr(t5, "translate", lambda _: ["X-", "72", "DESC-", "PEOPLE", "27"])
    tl = timeline.build(from_text("27 people."), lexicon, gloss_engine="t5")
    check(tl)
    by_word = {e["word"]: e for e in tl["entries"]}
    assert by_word["72"]["badge"] == "not_available" and "changed a number" in by_word["72"]["note"]
    assert by_word["27"]["badge"] == "validated" and [c["url"][-11:] for c in by_word["27"]["clips"]] == ["digit-2.mp4", "digit-7.mp4"]
    assert "" not in by_word and len(tl["entries"]) == 3
    monkeypatch.setattr(t5, "translate", lambda _: ["TWO", "HUNDRED", "PEOPLE"])   # a spelled-out quantity the source never said
    tl = timeline.build(from_text("27 people."), lexicon, gloss_engine="t5")
    assert {e["word"]: e["badge"] for e in tl["entries"]} == {"two": "not_available", "hundred": "not_available", "people": "validated"}


def test_words_the_model_omits_stay_in_the_captions(lexicon, check, monkeypatch):
    monkeypatch.setattr(t5, "translate", lambda text: ["RAIN"])
    text = "Rain is likely tonight in Samoa."
    tl = timeline.build(from_text(text), lexicon, gloss_engine="t5")
    check(tl)
    assert [c["text"] for c in tl["captions"]] == text.split()
    assert [c["text"] for c in tl["captions"] if c.get("dropped")] == ["is", "likely", "tonight", "in", "Samoa."]   # every omitted word is struck
    assert [e["word"] for e in tl["entries"]] == ["rain"]
    assert tl["stats"]["gloss_engine"] == "t5"
    assert {"t5", "aslg_pc12"} <= {a["source"] for a in tl["provenance"]["attributions"]}


def dropped_captions(text, glosses, lexicon, monkeypatch):
    monkeypatch.setattr(t5, "translate", lambda _: glosses)
    return [c["text"] for c in timeline.build(from_text(text), lexicon, gloss_engine="t5")["captions"] if c.get("dropped")]


def test_t5_coverage_follows_concepts_not_spelling(lexicon, monkeypatch):
    assert dropped_captions("Showers likely tonight.", ["TONIGHT", "RAIN"], lexicon, monkeypatch) == ["likely"]   # 'Showers' resolves to RAIN


def test_t5_one_gloss_covers_one_occurrence(lexicon, monkeypatch):
    assert dropped_captions("Rain, rain, rain.", ["RAIN", "RAIN"], lexicon, monkeypatch) == ["rain."]


def test_t5_omitted_unit_inside_a_word_is_marked_partly(lexicon, monkeypatch):
    monkeypatch.setattr(t5, "translate", lambda _: ["30"])
    tl = timeline.build(from_text("30% chance."), lexicon, gloss_engine="t5")
    assert [(c["text"], c.get("partly", False), c.get("dropped", False)) for c in tl["captions"]] == [("30%", True, False), ("chance.", False, True)]
    assert tl["captions"][0]["missing"] == ["percent"]


def test_t5_same_word_in_another_sense_does_not_cover_the_source(lexicon, monkeypatch):
    assert t5._lookup("DEAL", lexicon) == "deal"   # a bare T5 DEAL is the agreement; the rule pass reads 'deal with' as MANAGE
    assert dropped_captions("They will deal with it.", ["DEAL"], lexicon, monkeypatch) == ["They", "will", "deal", "with", "it."]
    assert dropped_captions("They will deal with it.", ["MANAGE"], lexicon, monkeypatch) == ["They", "will", "with", "it."]


def test_t5_coverage_uses_the_rule_pass_sense_not_the_bare_keyword(lexicon, monkeypatch):
    # 'red flag' means WARNING here (sense rule); a T5 FLAG gloss does not account for it
    assert dropped_captions("A red flag warning.", ["FLAG"], lexicon, monkeypatch) == ["A", "red", "flag", "warning."]
    assert dropped_captions("A red flag warning.", ["WARNING", "WARNING"], lexicon, monkeypatch) == ["A"]


def test_t5_phrase_gloss_covers_its_words(lexicon, monkeypatch):
    assert dropped_captions("The prime minister resigned.", ["PRIME-MINISTER", "RESIGN"], lexicon, monkeypatch) == ["The"]


def test_t5_entries_carry_token_positions_in_range(lexicon):
    entries = t5.gloss("The prime minister resigned on Sunday. Rain is likely.", lexicon, translate_fn=lambda t: t.upper().split())
    assert all(0 <= e.token_index < 11 for e in entries)


@pytest.mark.skipif(not (t5.MODEL_DIR / "model.bin").exists(), reason="T5 export not present")
def test_real_model_translates_one_sentence():
    out = t5.translate("The prime minister resigned on Sunday.")
    assert out and all(isinstance(g, str) for g in out)


def test_incomplete_export_is_downloaded_again_and_a_bad_zip_is_not_installed(tmp_path, monkeypatch):
    import io
    import zipfile

    model_dir = tmp_path / "t5_gloss_ct2"
    model_dir.mkdir()
    (model_dir / "model.bin").write_bytes(b"x")   # spiece.model and config.json missing: must not count as installed
    monkeypatch.setattr(t5, "MODEL_DIR", model_dir)
    monkeypatch.setattr(t5, "RELEASE_URL", "https://example.invalid/t5.zip")
    assert t5.available()

    def zip_with(names):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for n in names:
                z.writestr(n, "data")
        return buf.getvalue()

    class Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(t5.urllib.request, "urlopen", lambda req, timeout: Resp(zip_with(["model.bin", "config.json"])))
    with pytest.raises(FileNotFoundError, match="spiece.model"):
        t5._ensure()
    assert not model_dir.with_name("t5_gloss_ct2.part").exists() and not t5._complete(model_dir)
    monkeypatch.setattr(t5.urllib.request, "urlopen", lambda req, timeout: Resp(zip_with(t5.REQUIRED_FILES)))
    assert t5._ensure() == model_dir and t5._complete(model_dir)
