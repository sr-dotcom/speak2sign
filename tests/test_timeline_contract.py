import json
from pathlib import Path

import jsonschema
import pytest

from speak2sign import timeline
from speak2sign.gloss import lexicon as lex
from speak2sign.transcript import TimedTranscript, Word, from_text

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "contracts" / "timeline.schema.json").read_text(encoding="utf-8"))
L = lex.load()
EXCERPTS = json.loads((ROOT / "data" / "demo" / "excerpts.json").read_text(encoding="utf-8"))["items"]


def check(tl):
    jsonschema.validate(tl, SCHEMA)
    onsets = [e["onset_s"] for e in tl["entries"]]
    assert onsets == sorted(onsets)
    s = tl["stats"]
    assert s["validated"] + s["fingerspelled"] + s["names"] + s["not_available"] == len(tl["entries"]) == s["tokens"]
    for e in tl["entries"]:
        expected = {"validated": lambda n: n >= 1, "fingerspelled": lambda n: n >= 1, "name": lambda n: n == 0, "not_available": lambda n: n == 0}[e["badge"]]
        assert expected(len(e["clips"])), e
        assert 0 <= e["sentence"] < len(tl["sentences"])
        for c in e["clips"]:
            assert (ROOT / "static" / c["url"].removeprefix("app/static/")).exists()
            assert 0 <= c["in_s"] < c["out_s"] <= c["duration_s"] + 1e-6
    assert tl["playback"]["mode"] == "interpreter-paced"
    ends = [s["t_end"] for s in tl["sentences"]]
    assert ends == sorted(ends)


def test_names_are_spelled_once_then_shown_as_text():
    text = "Rain hit Samoa on Sunday. Officials in Samoa said Samoa is safe."
    tl = timeline.build(from_text(text, item_id="n"), L)
    check(tl)
    samoa = [e for e in tl["entries"] if e["word"] == "samoa"]
    assert [e["badge"] for e in samoa] == ["fingerspelled", "name", "name"]
    assert tl["stats"]["names"] == 2  # "hit" is also fingerspelled, so fingerspelled == 2


def test_signing_time_uses_active_spans_and_rates():
    tl = timeline.build(from_text("rain"), L)
    c = tl["entries"][0]["clips"][0]
    assert c["rate"] == 1.25
    assert abs(tl["stats"]["signing_s"] - (c["out_s"] - c["in_s"]) / 1.25) < 1e-3


@pytest.mark.parametrize("item", EXCERPTS, ids=[i["id"] for i in EXCERPTS])
def test_curated_items_validate(item):
    t = from_text(item["text"], item_id=item["id"], lane="curated", media_kind="audio", title=item["id"],
                  source="VOA newscast", broadcast_date=item["broadcast_date"])
    check(timeline.build(t, L))


def test_typed_and_weather_lanes_validate():
    check(timeline.build(from_text("Rain is likely tonight, with a low around 62."), L))
    check(timeline.build(from_text("Sunny, with a high near 97.", item_id="nws", lane="weather", media_kind="tts"), L))


def test_recorded_timings_and_fronting():
    words = (Word("Rain", 0.0, 0.4), Word("is", 0.4, 0.6), Word("likely", 0.6, 1.0), Word("tonight.", 1.0, 1.5))
    tl = timeline.build(TimedTranscript("x", "curated", words, "audio", "app/static/news/x.mp3", 1.5), L)
    check(tl)
    assert tl["entries"][0]["gloss"] == "TONIGHT" and tl["entries"][0]["onset_s"] == 0.0   # fronted to sentence start
    assert [e["word"] for e in tl["entries"]] == ["tonight", "rain", "likely"]
    assert any(c.get("dropped") for c in tl["captions"] if c["text"] == "is")
    assert tl["stats"]["speech_s"] == 1.5 and tl["stats"]["signing_s"] > 0


def test_provenance_lists_every_source_used():
    tl = timeline.build(from_text("The weather is sunny in Samoa", item_id="w", lane="weather", media_kind="tts"), L)
    srcs = {a["source"] for a in tl["provenance"]["attributions"]}
    assert {"signbank", "cats", "nws"} <= srcs
    assert "not a substitute for a human interpreter" in tl["provenance"]["disclaimer"]
