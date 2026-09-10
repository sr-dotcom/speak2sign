"""The ribbon shows exactly what the panel will play, escaped."""
from speak2sign import timeline
from speak2sign.transcript import from_text
from speak2sign.ui import ribbon


def entry(badge, word, gloss=None, note=None):
    e = {"badge": badge, "word": word, "gloss": gloss or word.upper(), "clips": [], "onset_s": 0.0, "sentence": 0}
    if note:
        e["note"] = note
    return e


def test_chip_text_per_badge():
    assert ribbon.chip_text(entry("validated", "prime minister", "LEADERb")) == "LEADER"   # variant suffix hidden
    assert ribbon.chip_text(entry("validated", "97", "97")) == "97"                        # numbers untouched
    assert ribbon.chip_text(entry("fingerspelled", "o'neil")) == "O-N-E-I-L"                # only characters with clips
    assert ribbon.chip_text(entry("name", "Samoa")) == "Samoa"
    assert ribbon.chip_text(entry("not_available", "12.5")) == "12.5"


def test_ribbon_html_escapes_user_text_and_shows_the_badge_label():
    tl = {"entries": [entry("fingerspelled", "<b>x"), entry("not_available", "a&b", note='why "not"')]}
    html = ribbon.ribbon_html(tl)
    assert "<b>" not in html and ">B-X<" in html and 'title="&lt;b&gt;x' in html   # tag characters never reach the DOM unescaped
    assert "a&amp;b" in html and 'title="why &quot;not&quot;"' in html
    assert html.count('class="s2s-chip"') == 2 and "fingerspelled</small>" in html and "not available</small>" in html


def test_stats_line_names_the_engine_and_counts(lexicon):
    tl = timeline.build(from_text("Rain in Samoa."), lexicon)
    line = ribbon.stats_line(tl)
    assert "engine: rules" in line and "1 fingerspelled" in line and "Coverage" in line
