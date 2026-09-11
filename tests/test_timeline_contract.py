"""timeline.build against contracts/timeline.schema.json plus the cross-field invariants in conftest.check_timeline."""
import json
from pathlib import Path

import jsonschema
import pytest

from speak2sign import timeline
from speak2sign.gloss import lexicon as lex
from speak2sign.transcript import TimedTranscript, Word, from_text

ROOT = Path(__file__).resolve().parents[1]
EXCERPTS = json.loads((ROOT / "data" / "demo" / "excerpts.json").read_text(encoding="utf-8"))["items"]


def test_names_are_spelled_once_then_shown_as_text(lexicon, check):
    text = "Rain hit Samoa on Sunday. Officials in Samoa said Samoa is safe."
    tl = timeline.build(from_text(text, item_id="n"), lexicon)
    check(tl)
    samoa = [e for e in tl["entries"] if e["word"] == "samoa"]
    assert [e["badge"] for e in samoa] == ["fingerspelled", "name", "name"]
    assert tl["stats"]["names"] == 2


def test_signing_time_counts_active_spans_rates_and_text_holds(lexicon, check):
    tl = timeline.build(from_text("Rain in Samoa. Samoa flooded."), lexicon)   # sign, fingerspell, name, sign
    check(tl)
    expected = 0.0
    for e in tl["entries"]:
        expected += sum((c["out_s"] - c["in_s"]) / c["rate"] for c in e["clips"]) or tl["playback"]["text_hold_s"]
    assert abs(tl["stats"]["signing_s"] - expected) < 1e-2
    assert [c["rate"] for c in tl["entries"][0]["clips"]] == [1.25]


@pytest.mark.parametrize("item", EXCERPTS, ids=[i["id"] for i in EXCERPTS])
def test_curated_excerpts_validate(item, lexicon, check):
    t = from_text(item["text"], item_id=item["id"], lane="curated", media_kind="audio", media_url=f"app/static/news/{item['id']}.wav",
                  title=item["id"], source="VOA newscast", broadcast_date=item["broadcast_date"])
    check(timeline.build(t, lexicon))


def test_audio_without_a_url_is_rejected_by_the_contract(lexicon, check):
    with pytest.raises(jsonschema.ValidationError, match="url"):
        check(timeline.build(from_text("Rain.", media_kind="audio"), lexicon))


def test_partly_without_missing_is_rejected_by_the_contract(lexicon, check):
    tl = timeline.build(from_text("Rain."), lexicon)
    tl["captions"][0]["partly"] = True   # the panel renders missing; the contract must not let it be absent
    with pytest.raises(jsonschema.ValidationError, match="missing"):
        check(tl)
    tl["captions"][0]["missing"] = ["x"]
    tl["captions"][0]["dropped"] = True
    with pytest.raises(jsonschema.ValidationError):
        check(tl)


def test_typed_and_weather_lanes_validate(lexicon, check):
    check(timeline.build(from_text("Rain is likely tonight, with a low around 62."), lexicon))
    check(timeline.build(from_text("Sunny, with a high near 97.", item_id="nws", lane="weather", media_kind="tts"), lexicon))


def test_recorded_timings_and_fronting(lexicon, check):
    words = (Word("Rain", 0.0, 0.4), Word("is", 0.4, 0.6), Word("likely", 0.6, 1.0), Word("tonight.", 1.0, 1.5))
    tl = timeline.build(TimedTranscript("x", "curated", words, "audio", "app/static/news/x.wav", 1.5), lexicon)
    check(tl)
    assert tl["entries"][0]["gloss"] == "TONIGHT" and tl["entries"][0]["onset_s"] == 0.0   # fronted to sentence start
    assert [e["word"] for e in tl["entries"]] == ["tonight", "rain", "likely"]
    assert [c["text"] for c in tl["captions"]] == ["Rain", "is", "likely", "tonight."]   # source words verbatim
    assert [c.get("dropped", False) for c in tl["captions"]] == [False, True, False, False]
    assert tl["stats"]["speech_s"] == 1.5 and tl["stats"]["signing_s"] > 0


def test_every_source_word_has_a_caption_even_inside_phrases_and_contractions(lexicon, check):
    text = "It's raining. The prime minister resigned on Sunday."
    tl = timeline.build(from_text(text), lexicon)
    check(tl)
    assert [c["text"] for c in tl["captions"]] == text.split()
    dropped = {c["text"] for c in tl["captions"] if c.get("dropped")}
    assert dropped == {"It's", "The", "on"}
    assert any(e["word"] == "prime minister" and e["badge"] == "validated" for e in tl["entries"])


def test_partly_signed_words_are_marked_not_hidden(lexicon, check):
    tl = timeline.build(from_text("Don't panic. It's fine."), lexicon)   # do dropped + NOT signed; it + is both dropped
    check(tl)
    flags = {c["text"]: ("dropped" if c.get("dropped") else "partly" if c.get("partly") else "signed") for c in tl["captions"]}
    assert flags == {"Don't": "partly", "panic.": "signed", "It's": "dropped", "fine.": "signed"}
    assert tl["captions"][0]["missing"] == ["do"]   # the unsigned part is named, so the strike-through is explicit
    assert [c["sentence"] for c in tl["captions"]] == [0, 0, 1, 1]


def test_leading_punctuation_belongs_to_the_first_sentence(lexicon, check):
    tl = timeline.build(from_text("!!! Rain. Snow."), lexicon)
    check(tl)
    assert [c["sentence"] for c in tl["captions"]] == [0, 0, 1] and tl["sentences"][0]["t_start"] == 0.0


def test_punctuation_only_input_still_has_a_sentence_for_its_caption(lexicon, check):
    tl = timeline.build(from_text("!!!"), lexicon)
    check(tl)
    assert len(tl["sentences"]) == 1 and tl["entries"] == [] and [c["text"] for c in tl["captions"]] == ["!!!"]


def test_accented_name_is_refused_whole_in_either_unicode_form(lexicon, check):
    for form in ("José", "José"):
        tl = timeline.build(from_text(f"Officials met {form} today."), lexicon)
        check(tl)
        e = [e for e in tl["entries"] if e["word"] == "josé"][0]
        assert e["badge"] == "not_available" and "é" in e["note"]
        assert not any(c.get("dropped") for c in tl["captions"] if c["text"] == form)


def test_abbreviations_do_not_end_a_sentence(lexicon):
    tl = timeline.build(from_text("The U.S. navy left. Dr. Smith said hello. Bye."), lexicon)
    assert len(tl["sentences"]) == 3


def test_numbers_are_signed_digit_by_digit_and_displayed_as_typed(lexicon, check):
    tl = timeline.build(from_text("A high near 97 and 1,000 people."), lexicon)
    check(tl)
    by_word = {e["word"]: e for e in tl["entries"]}
    assert by_word["97"]["badge"] == "validated" and by_word["97"]["gloss"] == "97"
    assert [c["url"].rsplit("/", 1)[1] for c in by_word["97"]["clips"]] == ["digit-9.mp4", "digit-7.mp4"]
    assert [c["url"].rsplit("/", 1)[1] for c in by_word["1000"]["clips"]] == ["digit-1.mp4", "digit-0.mp4", "digit-0.mp4", "digit-0.mp4"]


def test_non_whole_numbers_are_refused_whole_not_signed_in_pieces(lexicon, check):
    text = "Low around (-5), up 12.5 percent, 1/2 inch, winds 20–30 mph at 10:30, .5 more, −7 wind chill, 1.5e-3 units."
    tl = timeline.build(from_text(text), lexicon)
    check(tl)
    refused = {e["word"]: e for e in tl["entries"] if e["badge"] == "not_available"}
    assert set(refused) == {"-5", "12.5", "1/2", "20-30", "10:30", ".5", "-7", "1.5e-3"}
    assert "whole number" in refused["12.5"]["note"]
    assert not any(e["badge"] == "validated" and e["word"].isdigit() for e in tl["entries"])   # no stray digit signs
    assert [c["text"] for c in tl["captions"]] == text.split()


def test_a_sign_written_as_its_own_word_still_belongs_to_the_number(lexicon, check):
    for text in ("Low around - 5 tonight.", "Low around − 5 tonight.", "Low around (-) 5 tonight."):
        tl = timeline.build(from_text(text), lexicon)
        check(tl)
        refused = [e for e in tl["entries"] if e["badge"] == "not_available"]
        assert [e["word"] for e in refused] == ["-5"], text
        assert not any(e["badge"] == "validated" and e["word"] == "5" for e in tl["entries"])
        assert [c["text"] for c in tl["captions"]] == text.split()


def test_a_spaced_range_is_refused_whole_and_still_ends_its_sentence(lexicon, check, monkeypatch):
    text = "Winds 20 - 30 mph. Rain."
    tl = timeline.build(from_text(text), lexicon)
    check(tl)
    assert [e["word"] for e in tl["entries"] if e["badge"] == "not_available"] == ["20-30"]
    assert not any(e["word"] in ("20", "30", "-30") for e in tl["entries"])
    assert [c["text"] for c in tl["captions"]] == text.split() and len(tl["sentences"]) == 2
    assert [c["sentence"] for c in tl["captions"]] == [0, 0, 0, 0, 0, 1]
    assert not any(c.get("dropped") or c.get("partly") for c in tl["captions"][1:4])   # the refused range is shown as text, like any refusal
    from speak2sign.gloss import t5   # the same three words, when nothing accounts for them, are struck together
    monkeypatch.setattr(t5, "translate", lambda _: ["WIND"])
    tl = timeline.build(from_text(text), lexicon, gloss_engine="t5")
    assert [c["text"] for c in tl["captions"] if c.get("dropped")] == ["20", "-", "30", "mph.", "Rain."]
    for spaced, joined in (("Winds 20 – 30 mph.", "20-30"), ("Winds 20 + 30 mph.", "20+30"), ("Winds 20 (-) 30 mph.", "20-30")):
        tl = timeline.build(from_text(spaced), lexicon)   # en dash and plus, written as their own word, keep their meaning
        check(tl)
        assert [e["word"] for e in tl["entries"] if e["badge"] == "not_available"] == [joined], spaced
        assert not any(e["badge"] == "validated" and e["word"] in ("20", "30") for e in tl["entries"]), spaced
    # a sentence end between the numbers is not a range: two sentences, "20" signed, "-30" refused, ownership kept
    tl = timeline.build(from_text("Wind 20. - 30 people."), lexicon)
    check(tl)
    assert len(tl["sentences"]) == 2 and [c["sentence"] for c in tl["captions"]] == [0, 0, 1, 1, 1]
    assert {e["word"]: e["badge"] for e in tl["entries"] if e["word"] in ("20", "-30")} == {"20": "validated", "-30": "not_available"}


def test_sign_pointing_at_a_concept_without_a_clip_fails_closed(lexicon, check):
    broken = lex.Lexicon(list(lexicon.concepts.values()), {"rain": [{"default": "ghost"}]})
    tl = timeline.build(from_text("Rain today."), broken)
    check(tl)
    rain = [e for e in tl["entries"] if e["word"] == "rain"][0]
    assert rain["badge"] == "not_available" and "ghost" in rain["note"] and rain["clips"] == []
    assert tl["stats"]["validated"] == 1   # today


def test_sign_rate_is_a_viewer_choice_within_bounds(lexicon, check):
    slow = timeline.build(from_text("Rain in Samoa."), lexicon, sign_rate=1.0)
    fast = timeline.build(from_text("Rain in Samoa."), lexicon, sign_rate=1.5)
    check(slow)
    check(fast)
    assert slow["playback"]["sign_rate"] == 1.0 and fast["playback"]["sign_rate"] == 1.5
    assert [c["rate"] for c in slow["entries"][0]["clips"]] == [1.0] and [c["rate"] for c in fast["entries"][0]["clips"]] == [1.5]
    assert [c["rate"] for c in slow["entries"][1]["clips"]] == [2.0] * 5   # letters keep their own rate
    assert slow["stats"]["signing_s"] > fast["stats"]["signing_s"]
    with pytest.raises(ValueError, match="sign_rate"):
        timeline.build(from_text("Rain."), lexicon, sign_rate=3.0)


def test_unknown_engine_is_rejected(lexicon):
    with pytest.raises(ValueError, match="unknown gloss engine"):
        timeline.build(from_text("rain"), lexicon, gloss_engine="llm")


def test_provenance_lists_every_source_used(lexicon):
    tl = timeline.build(from_text("The weather is sunny in Samoa", item_id="w", lane="weather", media_kind="tts"), lexicon)
    srcs = {a["source"] for a in tl["provenance"]["attributions"]}
    assert {"signbank", "cats", "nws"} <= srcs
    assert "not a substitute for a human interpreter" in tl["provenance"]["disclaimer"]
    assert all(c["licence"] for e in tl["entries"] for c in e["clips"])
