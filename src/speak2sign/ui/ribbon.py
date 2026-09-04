"""Render a timeline as an HTML gloss ribbon: one chip per entry, badges by colour and text, dropped words struck through."""
import html
import re

BADGE_STYLE = {
    "validated": ("#1f6f3f", "#e3f2e8", "validated"),
    "fingerspelled": ("#8a5a00", "#fbf0d5", "fingerspelled"),
    "name": ("#3b4a5a", "#e8ecf1", "name, shown as text"),
    "not_available": ("#8a2a22", "#f9e3e0", "not available"),
}
CSS = """
<style>
.s2s-ribbon{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 10px}
.s2s-chip{border-radius:4px;padding:4px 8px;font:14px/1.3 ui-monospace,Consolas,monospace;border:1px solid rgba(0,0,0,.08)}
.s2s-chip small{display:block;font:11px/1.2 system-ui,sans-serif;letter-spacing:.04em;text-transform:uppercase;opacity:.85}
</style>
"""


def ribbon_html(timeline):
    chips = []
    for e in timeline["entries"]:
        fg, bg, label = BADGE_STYLE[e["badge"]]
        title = html.escape(e.get("note") or f"{e['word']} → {e['gloss']}")
        gloss = re.match(r"^[A-Z0-9][A-Z0-9-]*", e["gloss"])   # LEADERb -> LEADER: hide Signbank variant suffixes on screen
        text = html.escape((gloss.group(0) if gloss else e["gloss"]) if e["badge"] == "validated" else e["word"])
        if e["badge"] == "fingerspelled":
            text = "-".join(html.escape(e["word"]).upper())
        # Streamlit strips role/aria-* from both st.markdown and st.html, so the chip's accessible text is its visible text:
        # gloss + badge label. The note is a title (hover) here and a live region in the panel.
        chips.append(f'<span class="s2s-chip" style="color:{fg};background:{bg}" title="{title}">{text}<small>{label}</small></span>')
    return CSS + f'<div class="s2s-ribbon">{"".join(chips)}</div>'


def stats_line(timeline):
    s = timeline["stats"]
    return (f"Coverage {s['coverage']:.0%} · fingerspelled {s['fingerspelling_rate']:.0%} · "
            f"{s['validated']} validated, {s['fingerspelled']} fingerspelled, {s['names']} names as text, {s['not_available']} not available · "
            f"speech {s['speech_s']:.0f} s, signing about {s['signing_s']:.0f} s at {timeline['playback']['sign_rate']}× / {timeline['playback']['letter_rate']}× · engine: {s['gloss_engine']}")
