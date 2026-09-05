"""Live weather lane: the National Weather Service forecast for Charlotte, NC, as a short script.

api.weather.gov needs no key. Its policy asks for an identifying User-Agent. Public domain (US government work).
The gridpoint for Charlotte was resolved once from /points/35.2271,-80.8431 (office GSP, grid 119,65);
if that URL ever fails we resolve it again.
"""
import json
import urllib.request
from datetime import datetime, timezone

from speak2sign.transcript import from_text

UA = {"User-Agent": "speak2sign (university project; https://github.com/sr-dotcom/speak2sign)", "Accept": "application/geo+json"}
CHARLOTTE = (35.2271, -80.8431)
FORECAST_URL = "https://api.weather.gov/gridpoints/GSP/119,65/forecast"
PERIODS = 4
TIMEOUT_S = 10


def _get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=TIMEOUT_S) as r:
        return json.load(r)


def fetch_forecast():
    """Raw forecast JSON from the NWS. Falls back to re-resolving the gridpoint once."""
    try:
        return _get(FORECAST_URL)
    except Exception:
        points = _get(f"https://api.weather.gov/points/{CHARLOTTE[0]},{CHARLOTTE[1]}")
        return _get(points["properties"]["forecast"])


def script(forecast, periods=PERIODS):
    """Turn the first N forecast periods into narratable sentences: 'Tonight: mostly clear, with a low around 75.'"""
    out = []
    for p in forecast["properties"]["periods"][:periods]:
        detail = p["detailedForecast"].strip()
        if not detail.endswith((".", "!", "?")):
            detail += "."
        out.append(f"{p['name']}. {detail}")
    return " ".join(out)


def transcript(forecast, fetched_at=None):
    when = (fetched_at or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M UTC")
    generated = forecast["properties"].get("generatedAt", "")[:16].replace("T", " ")
    return from_text(script(forecast), item_id="nws-charlotte", lane="weather", media_kind="tts",
                     title="Charlotte, NC forecast", source=f"National Weather Service forecast, issued {generated}, fetched {when}")


def live_transcript():
    return transcript(fetch_forecast())
