import json
from pathlib import Path

from speak2sign.ingest import nws

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "nws_forecast.json").read_text(encoding="utf-8"))


def test_script_is_sentences_with_period_names():
    s = nws.script(FIXTURE, periods=2)
    first = FIXTURE["properties"]["periods"][0]["name"]
    assert s.startswith(f"{first}. ") and s.count(". ") >= 3
    assert "Tonight." in s


def test_transcript_is_weather_lane_with_source_and_estimated_onsets():
    t = nws.transcript(FIXTURE)
    assert t.lane == "weather" and t.media_kind == "tts"
    assert "National Weather Service" in t.source
    assert t.words[0].onset_s == 0.0 and t.words[1].onset_s > 0
