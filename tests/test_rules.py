import pytest

from speak2sign.gloss import lexicon as lex
from speak2sign.gloss.rules import gloss, stats, tokenize

L = lex.load()


def kinds(text):
    return [(e.word, e.kind, e.concept) for e in gloss(text, L)]


def test_tokenize_numbers_and_abbreviations():
    assert tokenize("Chance of precipitation is 30%.") == ["chance", "of", "precipitation", "is", "30", "percent"]
    assert tokenize("The U.S. spent $160 million, 10,000 troops.") == ["the", "u.s.", "spent", "160", "dollar", "million", "10000", "troops"]
    assert tokenize("It's raining") == ["it", "is", "raining"]


def test_function_words_are_dropped_not_lost():
    out = kinds("The rain is heavy")
    assert ("the", "dropped", None) in out and ("is", "dropped", None) in out
    assert ("rain", "sign", "rain") in out and ("heavy", "sign", "heavy") in out


def test_phrase_beats_single_words():
    out = kinds("The prime minister resigned")
    assert ("prime minister", "sign", "leader") in out
    assert ("resigned", "sign", "resign") in out


def test_sense_rule_uses_context():
    assert ("red flag", "sign", "warning") in kinds("a red flag warning")
    assert ("fall", "sign", "decrease") in kinds("temperatures will fall to 60")


def test_time_words_move_to_front():
    out = gloss("Rain is likely tonight", L)
    assert out[0].concept == "tonight"
    assert [e.concept for e in out if e.kind == "sign"] == ["tonight", "rain", "chance"]


def test_numbers_become_digit_sequences():
    e = [e for e in gloss("high near 97", L) if e.word == "97"][0]
    assert e.kind == "number" and e.letters == ("digit-9", "digit-7")
    assert [e.word for e in gloss("Samoa's navy", L) if e.kind != "dropped"] == ["samoa", "navy"]


def test_unknown_word_is_fingerspelled_and_long_word_refused():
    e = [e for e in gloss("Samoa", L) if e.word == "samoa"][0]
    assert e.kind == "fingerspell" and e.letters[0] == "letter-s"
    e = [e for e in gloss("antidisestablishmentarianism", L)][0]
    assert e.kind == "none"


def test_stemming_reaches_the_lexicon():
    assert ("showers", "sign", "rain") in kinds("scattered showers")
    assert ("killed", "sign", "kill") in kinds("killed")


def test_stats_arithmetic():
    s = stats(gloss("The rain is heavy in Samoa", L))
    assert s["tokens"] == s["validated"] + s["fingerspelled"] + s["not_available"]
    assert s["validated"] == 2 and s["fingerspelled"] == 1


@pytest.mark.parametrize("text", ["", "   ", "!!!"])
def test_empty_input_is_a_noop(text):
    assert gloss(text, L) == []
