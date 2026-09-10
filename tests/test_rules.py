import pytest

from speak2sign.gloss.rules import gloss, stats, tokenize


def kinds(text, lexicon):
    return [(e.word, e.kind, e.concept) for e in gloss(text, lexicon)]


def test_tokenize_numbers_and_abbreviations():
    assert tokenize("Chance of precipitation is 30%.") == ["chance", "of", "precipitation", "is", "30", "percent"]
    assert tokenize("The U.S. spent $160 million, 10,000 troops.") == ["the", "u.s.", "spent", "160", "dollar", "million", "10000", "troops"]
    assert tokenize("It's raining") == ["it", "is", "raining"]
    assert tokenize("1,000,000 people") == ["1000000", "people"]
    assert tokenize("a low around -5, winds 20-30 mph") == ["a", "low", "around", "-5", "winds", "20-30", "mph"]
    assert tokenize("(-5) or 1/2 or .5 at 10:30 on 2024-11-19") == ["-5", "or", "1/2", "or", ".5", "at", "10:30", "on", "2024-11-19"]
    assert tokenize("−5 and 20–30") == ["-5", "and", "20-30"]   # Unicode minus and en dash
    assert tokenize("a low of − 5 or - 7") == ["a", "low", "of", "-5", "or", "-7"]   # a separated sign still belongs to its number
    assert tokenize("between 2pm and 4pm, 1e3 and the 1st") == ["between", "2pm", "and", "4pm", "1e3", "and", "the", "1st"]
    assert tokenize("José") == tokenize("José") == ["josé"]   # precomposed and decomposed accent alike


def test_mixed_digit_letter_tokens_are_spelled_never_signed_as_numbers(lexicon):
    out = {e.word: e for e in gloss("1e3 at 2pm, 1e-3 or 1e+3", lexicon)}
    assert out["1e3"].kind == "fingerspell" and out["1e3"].letters == ("digit-1", "letter-e", "digit-3")
    assert out["2pm"].kind == "fingerspell" and out["2pm"].letters == ("digit-2", "letter-p", "letter-m")
    assert out["1e-3"].kind == "none" and out["1e+3"].kind == "none"   # a sign inside: refused whole, no fragment played
    assert [e.kind for e in gloss("1.5e3 and 1.5e-3", lexicon) if e.word != "and"] == ["none", "none"]
    assert tokenize("1.5e3 and 1.5e-3 by 10km") == ["1.5e3", "and", "1.5e-3", "by", "10km"]
    assert tokenize("$1.5e-3 and $160") == ["1.5e-3", "dollar", "and", "160", "dollar"]
    assert gloss("$1.5e-3", lexicon)[0].kind == "none"   # the amount is refused whole; no exponent digit plays


def test_combining_mark_that_nfc_cannot_fold_still_refuses_the_word(lexicon):
    e = gloss("q́x", lexicon)[0]
    assert e.word == "q́x" and e.kind == "none" and "́" in e.why


def test_function_words_are_dropped_not_lost(lexicon):
    out = kinds("The rain is heavy", lexicon)
    assert ("the", "dropped", None) in out and ("is", "dropped", None) in out
    assert ("rain", "sign", "rain") in out and ("heavy", "sign", "heavy") in out


def test_phrase_beats_single_words(lexicon):
    out = kinds("The prime minister resigned", lexicon)
    assert ("prime minister", "sign", "leader") in out
    assert ("resigned", "sign", "resign") in out


def test_sense_rule_uses_context(lexicon):
    assert ("red flag", "sign", "warning") in kinds("a red flag warning", lexicon)
    assert ("fall", "sign", "decrease") in kinds("temperatures will fall to 60", lexicon)


def test_time_words_move_to_front(lexicon):
    out = gloss("Rain is likely tonight", lexicon)
    assert out[0].concept == "tonight"
    assert [e.concept for e in out if e.kind == "sign"] == ["tonight", "rain", "chance"]


def test_whole_numbers_become_digit_sequences(lexicon):
    e = [e for e in gloss("high near 97", lexicon) if e.word == "97"][0]
    assert e.kind == "number" and e.letters == ("digit-9", "digit-7")
    assert [e.word for e in gloss("Samoa's navy", lexicon) if e.kind != "dropped"] == ["samoa", "navy"]


@pytest.mark.parametrize("tok", ["-5", "12.5"])
def test_negative_and_decimal_numbers_are_refused(tok, lexicon):
    e = [e for e in gloss(f"around {tok} now", lexicon) if e.word == tok][0]
    assert e.kind == "none" and "whole number" in e.why


def test_unknown_word_is_fingerspelled_in_full_and_long_word_refused(lexicon):
    e = [e for e in gloss("Samoa", lexicon) if e.word == "samoa"][0]
    assert e.kind == "fingerspell" and e.letters == ("letter-s", "letter-a", "letter-m", "letter-o", "letter-a")
    e = [e for e in gloss("antidisestablishmentarianism", lexicon)][0]
    assert e.kind == "none"


def test_letter_without_a_clip_refuses_the_whole_word(lexicon):
    e = gloss("José", lexicon)[0]
    assert e.word == "josé" and e.kind == "none" and "é" in e.why


def test_stemming_reaches_the_lexicon_without_false_friends(lexicon):
    assert ("showers", "sign", "rain") in kinds("scattered showers", lexicon)
    assert ("killed", "sign", "kill") in kinds("killed", lexicon)
    assert ("news", "fingerspell", None) in kinds("the news", lexicon)      # not NEW
    assert ("goods", "fingerspell", None) in kinds("goods", lexicon)        # not GOOD


def test_antonyms_never_share_a_sign(lexicon):
    assert ("uncommon", "fingerspell", None) in kinds("uncommon", lexicon)
    assert ("noncitizen", "fingerspell", None) in kinds("noncitizen", lexicon)
    assert ("common", "sign", "common") in kinds("common", lexicon)


def test_stats_arithmetic(lexicon):
    s = stats(gloss("The rain is heavy in Samoa", lexicon))
    assert s["tokens"] == s["validated"] + s["fingerspelled"] + s["not_available"]
    assert s["validated"] == 2 and s["fingerspelled"] == 1


@pytest.mark.parametrize("text", ["", "   ", "!!!"])
def test_empty_input_is_a_noop(text, lexicon):
    assert gloss(text, lexicon) == []
