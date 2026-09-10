from speak2sign.transcript import WORDS_PER_SECOND, TimedTranscript, Word, from_text


def test_from_text_estimates_a_steady_clock_and_keeps_words_verbatim():
    t = from_text("It's raining in Samoa.", item_id="x", lane="typed", media_kind="none", title="T")
    assert [w.text for w in t.words] == ["It's", "raining", "in", "Samoa."]
    assert [w.onset_s for w in t.words] == [round(i / WORDS_PER_SECOND, 3) for i in range(4)]
    assert t.words[0].end_s == t.words[1].onset_s
    assert t.duration_s == round(4 / WORDS_PER_SECOND, 3) and t.text == "It's raining in Samoa."
    assert (t.item_id, t.lane, t.media_kind, t.title, t.media_url) == ("x", "typed", "none", "T", None)


def test_from_text_with_nothing_to_say():
    t = from_text("   ")
    assert t.words == () and t.duration_s == 0.0 and t.text == ""


def test_transcripts_are_immutable_records():
    t = TimedTranscript("i", "curated", (Word("Rain", 0.0),))
    try:
        t.lane = "typed"
    except AttributeError:
        pass
    else:
        raise AssertionError("TimedTranscript should be frozen")
