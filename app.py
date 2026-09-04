"""Speak2Sign v2 — Streamlit entry point. Thin: layout and calls into src/speak2sign."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from speak2sign import __version__, asr, provenance, timeline  # noqa: E402
from speak2sign.gloss import lexicon as lex  # noqa: E402
from speak2sign.gloss import t5  # noqa: E402
from speak2sign.ingest import demo_set, nws  # noqa: E402
from speak2sign.transcript import from_text  # noqa: E402
from speak2sign.ui import panel, ribbon  # noqa: E402

st.set_page_config(page_title="Speak2Sign", page_icon="📺", layout="wide")


@st.cache_resource
def lexicon():
    return lex.load()


@st.cache_data(ttl=300, show_spinner="Fetching the Charlotte forecast…")
def forecast():
    return nws.fetch_forecast()


def show(tl, key):
    panel.mount(tl, key=f"panel-{key}")
    st.markdown(ribbon.ribbon_html(tl), unsafe_allow_html=True)
    st.caption(ribbon.stats_line(tl))
    with st.expander("Sources for this item"):
        for a in tl["provenance"]["attributions"]:
            st.markdown(f"- {a['text']} — {a['licence']} — {a['url']}")


st.title("Speak2Sign — news with an ASL interpreter panel")
st.info(provenance.DISCLAIMER, icon="ℹ️")

with st.sidebar:
    st.markdown("**Gloss engine**")
    if t5.available():
        ENGINE = st.radio("Engine", ["rules", "t5"], label_visibility="collapsed", horizontal=True,
                          help="rules: inspectable stdlib pass (default). t5: T5-small fine-tuned on ASLG-PC12, served by CTranslate2; timing is approximate.")
    else:
        ENGINE = "rules"
        st.caption("rules (T5 export not present on this host)")
    st.caption("Either engine resolves through the same validated lexicon; neither can invent a sign.")


def build(transcript):
    return timeline.build(transcript, lexicon(), gloss_engine=ENGINE)

news, typed, weather, upload = st.tabs(["News items", "Type text", "Live weather (Charlotte)", "Upload a clip"])

with news:
    items = demo_set.items()
    if not items:
        st.caption("No curated items built yet (scripts/build_demo_set.py).")
    else:
        labels = {f"{i['broadcast_date']} · {i['title']} ({i['topic']})": i for i in items}
        choice = st.selectbox("Pick a news item", list(labels), label_visibility="collapsed")
        item = labels[choice]
        st.caption(f"{item['source']} · {item['duration_s']:.0f} s of anchor-read audio · [archive item]({item['archive_item']})")
        show(build(demo_set.transcript(item)), key=item["id"])

with typed:
    text = st.text_area("English text", "Rain is likely tonight, with a low around 62. The prime minister resigned on Sunday.", height=100)
    if st.button("Gloss it", type="primary") and text.strip():
        show(build(from_text(text, media_kind="tts")), key="typed")

with weather:
    st.caption("Forecast text from the US National Weather Service, public domain, no key. Cached five minutes.")
    if st.button("Fetch the forecast and gloss it", type="primary"):
        try:
            tl = build(nws.transcript(forecast()))
        except Exception as e:  # network or API shape; the demo must never show a traceback
            st.error(f"Forecast unavailable right now ({e.__class__.__name__}). The curated items do not depend on it.")
        else:
            st.markdown(f"**{tl['item']['title']}** — {tl['item']['source']}")
            show(tl, key="weather")

with upload:
    st.caption("Audio or video up to 60 seconds. Transcribed on this server with faster-whisper; the clip is kept in memory for "
               "this session only, never stored, never sent anywhere else. Check the transcript before signing it.")
    up = st.file_uploader("Clip", type=["wav", "mp3", "m4a", "mp4", "ogg", "webm"], label_visibility="collapsed")
    if up is not None:
        key = f"{up.name}:{up.size}"
        if st.session_state.get("upload_key") != key:
            try:
                with st.spinner("Transcribing…"):
                    audio = asr.decode(up.getvalue())
                    words = asr.transcribe(audio)
            except ValueError as e:
                st.error(str(e))
                audio, words = None, None
            except Exception as e:  # decoder or model failure; never a traceback
                st.error(f"Could not transcribe this file ({e.__class__.__name__}). Try a WAV or MP3 under 60 seconds.")
                audio, words = None, None
            st.session_state.update(upload_key=key, upload_audio=audio, upload_words=words,
                                    upload_text=" ".join(w["text"] for w in words) if words else "")
        if st.session_state.get("upload_words"):
            text = st.text_area("Transcript (edit before signing)", st.session_state["upload_text"], height=120, key="upload_text")
            if st.button("Sign this clip", type="primary") and text.strip():
                t = asr.upload_transcript(text, st.session_state["upload_words"], st.session_state["upload_audio"])
                show(build(t), key="upload")

st.caption(f"Speak2Sign v{__version__} · lexicon {len(lexicon())} concepts · Python {sys.version.split()[0]} · streamlit {st.__version__}")
