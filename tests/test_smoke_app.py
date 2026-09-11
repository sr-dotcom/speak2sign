"""The Streamlit page end to end with AppTest: every lane renders, and every failure becomes a message, never a traceback."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def run_app():
    return AppTest.from_file(str(APP), default_timeout=20).run()


def test_app_loads_with_disclaimer_and_a_curated_item():
    at = run_app()
    assert not at.exception
    assert any("not a substitute for a human interpreter" in i.value for i in at.info)
    assert any("s2s-chip" in m.value for m in at.markdown)   # the first curated item is mounted with its ribbon
    assert any(c.value.startswith("Badges:") for c in at.caption)   # and the legend under it
    # the item card above the panel: each metric carries exactly the timeline's own number for the first curated item
    from speak2sign import timeline
    from speak2sign.gloss import lexicon as lex
    from speak2sign.ingest import demo_set

    tl = timeline.build(demo_set.transcript(demo_set.items()[0]), lex.load())
    s = tl["stats"]
    assert {m.label: m.value for m in at.metric[:4]} == {"Validated signs": f"{s['coverage']:.0%}", "Fingerspelled": f"{s['fingerspelling_rate']:.0%}",
                                                        "Signing time": f"~{s['signing_s']:.0f} s", "Sentences": str(len(tl["sentences"]))}


def test_typed_lane_renders_and_survives_a_rerun():
    at = run_app()
    at.text_area(key="typed_text").set_value("Rain is likely tonight. Don't panic.").run()
    at.button(key="typed_go").click().run()
    assert not at.exception
    html = " ".join(m.value for m in at.markdown)
    assert "TONIGHT" in html and "validated</small>" in html and "fingerspelled</small>" in html
    at.text_area(key="typed_text").set_value("changed but not submitted").run()   # a rerun without the button
    assert not at.exception and "TONIGHT" in " ".join(m.value for m in at.markdown)   # the result is still there


def test_weather_failure_is_a_message_not_a_traceback(monkeypatch):
    from speak2sign.ingest import nws

    def down(*a, **k):
        raise TimeoutError("api.weather.gov unreachable")

    monkeypatch.setattr(nws, "fetch_forecast", down)
    at = run_app()
    at.button(key="weather_go").click().run()
    assert not at.exception
    assert any("Forecast unavailable" in e.value and "TimeoutError" in e.value for e in at.error)


def test_lexicon_failure_is_a_message_everywhere_including_the_footer(monkeypatch):
    import streamlit as st

    from speak2sign.gloss import lexicon as lex

    def broken(*a, **k):
        raise ValueError("concepts.json corrupt")

    monkeypatch.setattr(lex, "load", broken)
    st.cache_resource.clear()   # the lexicon is cached across AppTest runs in this process
    try:
        at = run_app()
        assert not at.exception
        assert any("Could not build the signing plan" in e.value for e in at.error)
        assert any("lexicon unavailable (ValueError)" in c.value for c in at.caption)
    finally:
        st.cache_resource.clear()


def test_engine_failure_is_a_message_not_a_traceback(monkeypatch):
    from speak2sign import timeline

    def broken(*a, **k):
        raise RuntimeError("model exploded")

    monkeypatch.setattr(timeline, "build", broken)
    at = run_app()
    assert not at.exception
    assert any("Could not build the signing plan" in e.value for e in at.error)
