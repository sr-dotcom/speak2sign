"""Mount the interpreter panel (components v2) with a timeline. The browser side is panel.html/css/js."""
from pathlib import Path

import streamlit as st

HERE = Path(__file__).resolve().parent


def _component():
    # Declared on every run: the registration lives in the current script run (caching it breaks AppTest and reruns)
    return st.components.v2.component(
        "s2s_panel",
        html=(HERE / "panel.html").read_text(encoding="utf-8"),
        css=(HERE / "panel.css").read_text(encoding="utf-8"),
        js=(HERE / "panel.js").read_text(encoding="utf-8"),
    )


def mount(timeline, key):
    return _component()(data=timeline, key=key)
