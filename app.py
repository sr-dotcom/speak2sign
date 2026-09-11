"""Speak2Sign v2 — Streamlit entry point. Thin: layout and calls into src/speak2sign."""
import hashlib
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
def get_lexicon():
    return lex.load()


@st.cache_data(ttl=300, show_spinner="Fetching the Charlotte forecast…")
def forecast():
    return nws.fetch_forecast()


def item_card(tl):
    """What the viewer is about to watch, before Play: how much of it is validated signing and how long it will take."""
    s, n = tl["stats"], len(tl["sentences"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Validated signs", f"{s['coverage']:.0%}", help="Share of content words shown with a validated clip. The rest are fingerspelled, shown as text, or marked not available.")
    c2.metric("Fingerspelled", f"{s['fingerspelling_rate']:.0%}", help="Words spelled letter by letter with validated letter clips.")
    c3.metric("Signing time", f"~{s['signing_s']:.0f} s", help=f"Projected at {tl['playback']['sign_rate']}× for signs and {tl['playback']['letter_rate']}× for letters; the narration ({s['speech_s']:.0f} s) waits for the interpreter at each sentence end.")
    c4.metric("Sentences", str(n), help="The narration pauses after each sentence until the interpreter has signed it.")


def show_timeline(transcript, key):
    """Build and mount one item. A failure (a model that will not load, bad data) becomes a message, never a traceback."""
    try:
        tl = timeline.build(transcript, get_lexicon(), gloss_engine=ENGINE, sign_rate=SIGN_RATE)
    except Exception as e:
        hint = " Switch the engine to rules in the sidebar." if ENGINE != "rules" else ""
        st.error(f"Could not build the signing plan with the {ENGINE} engine ({e.__class__.__name__}).{hint}")
        return
    item_card(tl)
    panel.mount(tl, key=f"panel-{key}")
    st.markdown(ribbon.ribbon_html(tl), unsafe_allow_html=True)
    st.caption(ribbon.stats_line(tl))
    st.caption(ribbon.LEGEND)
    with st.expander("Sources for this item"):
        for a in tl["provenance"]["attributions"]:
            st.markdown(f"- {a['text']} — {a['licence']} — {a['url']}")


st.title("Speak2Sign")
st.caption("News with an ASL interpreter panel, signed from recorded clips of Deaf signers. Every sign carries a badge saying where it came from.")
st.info(provenance.DISCLAIMER, icon="ℹ️")

with st.sidebar:
    st.markdown("**How it works**")
    st.caption("The news text is turned into a sequence of sign concepts by a rule pass (or a small T5 model). Each concept is looked up in a "
               "lexicon of validated clips (the count is in the footer); a word with no clip is fingerspelled, and one that cannot be spelled is marked not available. "
               "The bulletin plays one sentence at a time and waits for the interpreter to finish it.")
    st.markdown("**Translation**")
    ENGINE_LABEL = {"rules": "Rule-based", "t5": "T5 model"}
    if t5.available():
        ENGINE = st.radio("Translation", ["rules", "t5"], format_func=ENGINE_LABEL.get, label_visibility="collapsed", horizontal=True, key="engine",
                          help="Rule-based: an inspectable pass over the words (default). T5 model: T5-small fine-tuned on ASLG-PC12, served by CTranslate2; timing is approximate.")
    else:
        ENGINE = "rules"
        st.caption("Rule-based (the T5 export is not present on this host)")
    st.caption("Either engine resolves through the same validated lexicon; neither can invent a sign.")
    st.markdown("**Sign speed**")
    SIGN_RATE = st.radio("Sign speed", timeline.SIGN_RATES, index=timeline.SIGN_RATES.index(timeline.SIGN_RATE), format_func=lambda r: f"{r}×",
                         horizontal=True, label_visibility="collapsed", key="sign_rate",
                         help="Playback rate of the sign clips. Letters and digits stay at 2.0×. Slower is easier to read and makes the narration wait longer at each sentence end; the signing time above the panel updates.")
    st.markdown("**Project**")
    st.caption("[Source and documentation](https://github.com/sr-dotcom/speak2sign) · MIT code; clip and data licences in NOTICE.md · UNC Charlotte capstone, 2026.")

news, typed, weather, upload = st.tabs(["News items", "Type text", "Live weather (Charlotte)", "Upload a clip"])

with news:
    items = demo_set.items()
    if not items:
        st.caption("No curated items built yet (scripts/build_demo_set.py).")
    else:
        labels = {f"{i['broadcast_date']} · {i['title']} ({i['topic']})": i for i in items}
        choice = st.selectbox("Pick a news item", list(labels), label_visibility="collapsed", key="news_item")
        item = labels[choice]
        st.caption(f"{item['source']} · {item['duration_s']:.0f} s of anchor-read audio · [archive item]({item['archive_item']})")
        show_timeline(demo_set.transcript(item), item["id"])

# The typed, weather and upload results live in session state so they survive reruns (a tab switch, an engine change).
with typed:
    text = st.text_area("English text", "Rain is likely tonight, with a low around 62. The prime minister resigned on Sunday.", height=100, key="typed_text")
    if st.button("Gloss it", type="primary", key="typed_go") and text.strip():
        st.session_state["typed_transcript"] = from_text(text, media_kind="tts")
    if "typed_transcript" in st.session_state:
        show_timeline(st.session_state["typed_transcript"], "typed")

with weather:
    st.caption("Forecast text from the US National Weather Service, public domain, no key. Cached five minutes.")
    if st.button("Fetch the forecast and gloss it", type="primary", key="weather_go"):
        try:
            st.session_state["weather_transcript"] = nws.transcript(forecast())
        except Exception as e:  # network or API shape; the demo must never show a traceback
            st.error(f"Forecast unavailable right now ({e.__class__.__name__}). The curated items do not depend on it.")
    if "weather_transcript" in st.session_state:
        t = st.session_state["weather_transcript"]
        st.markdown(f"**{t.title}** — {t.source}")
        show_timeline(t, "weather")

with upload:
    st.caption("Audio or video up to 60 seconds. Transcribed on this server with faster-whisper. The audio stays in memory for this "
               "session, is sent back only to your own browser for playback, and never goes to a third party or to disk. "
               "Check the transcript before signing it.")
    up = st.file_uploader("Clip", type=["wav", "mp3", "m4a", "mp4", "ogg", "webm"], label_visibility="collapsed", key="upload_file")
    if up is not None:
        data = up.getvalue()
        key = hashlib.sha256(data).hexdigest()   # the bytes, not the name: a different file with the same name and size is a different clip
        if st.session_state.get("upload_key") != key:
            audio, words = None, None
            try:
                with st.spinner("Transcribing…"):
                    audio = asr.decode(data)
                    words = asr.transcribe(audio)
            except ValueError as e:
                st.error(str(e))
            except Exception as e:  # decoder or model failure; never a traceback
                st.error(f"Could not transcribe this file ({e.__class__.__name__}). Try a WAV or MP3 under 60 seconds.")
            st.session_state.update(upload_key=key, upload_audio=audio, upload_words=words, upload_signed=None,
                                    upload_text=" ".join(w["text"] for w in words) if words else "")
        if st.session_state.get("upload_words"):
            text = st.text_area("Transcript (edit before signing)", height=120, key="upload_text")
            if st.button("Sign this clip", type="primary", key="upload_go") and text.strip():
                st.session_state["upload_signed"] = text
            if st.session_state.get("upload_signed"):
                show_timeline(asr.upload_transcript(st.session_state["upload_signed"], st.session_state["upload_words"], st.session_state["upload_audio"]), "upload")

try:
    lexicon_note = f"lexicon {len(get_lexicon())} concepts"
except Exception as e:   # the lanes above already reported it; the footer must not be the one place a traceback escapes
    lexicon_note = f"lexicon unavailable ({e.__class__.__name__})"
st.caption(f"Speak2Sign v{__version__} · {lexicon_note} · Python {sys.version.split()[0]} · streamlit {st.__version__}")
