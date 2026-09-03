from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_app_loads_with_disclaimer():
    at = AppTest.from_file(str(APP)).run()
    assert not at.exception
    assert any("not a substitute for a human interpreter" in i.value for i in at.info)


def test_typed_lane_renders_a_ribbon():
    at = AppTest.from_file(str(APP)).run()
    at.text_area[0].set_value("Rain is likely tonight.").run()
    at.button[0].click().run()
    assert not at.exception
    html = " ".join(m.value for m in at.markdown)
    assert "s2s-chip" in html and "TONIGHT" in html
