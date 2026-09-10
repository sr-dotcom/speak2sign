import json
from pathlib import Path

import pytest

from speak2sign.ingest import nws

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "nws_forecast.json").read_text(encoding="utf-8"))
PERIODS = FIXTURE["properties"]["periods"]


def test_script_is_exactly_the_first_n_periods_as_sentences():
    s = nws.script(FIXTURE, periods=2)
    assert s == " ".join(f"{p['name']}. {p['detailedForecast'].strip()}" for p in PERIODS[:2])
    assert PERIODS[2]["name"] not in s
    assert nws.script({"properties": {"periods": [{"name": "Tonight", "detailedForecast": "Clear"}]}}) == "Tonight. Clear."


def test_transcript_is_weather_lane_with_source_and_estimated_onsets():
    t = nws.transcript(FIXTURE)
    assert t.lane == "weather" and t.media_kind == "tts"
    assert "National Weather Service" in t.source
    assert t.words[0].onset_s == 0.0 and t.words[1].onset_s > 0


def test_fetch_falls_back_to_resolving_the_gridpoint(monkeypatch):
    calls = []

    def fake_get(url):
        calls.append(url)
        if url == nws.FORECAST_URL:
            raise OSError("gridpoint moved")
        if url.startswith("https://api.weather.gov/points/"):
            return {"properties": {"forecast": "https://api.weather.gov/gridpoints/GSP/1,1/forecast"}}
        return FIXTURE

    monkeypatch.setattr(nws, "_get", fake_get)
    assert nws.fetch_forecast() == FIXTURE
    assert calls == [nws.FORECAST_URL, f"https://api.weather.gov/points/{nws.CHARLOTTE[0]},{nws.CHARLOTTE[1]}", "https://api.weather.gov/gridpoints/GSP/1,1/forecast"]


def test_fetch_failure_propagates_for_the_app_to_report(monkeypatch):
    def fake_get(url):
        raise TimeoutError("no network")

    monkeypatch.setattr(nws, "_get", fake_get)
    with pytest.raises(TimeoutError):
        nws.fetch_forecast()
