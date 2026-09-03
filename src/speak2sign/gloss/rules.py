"""Rule-based English -> gloss pass. Standard library only. Every decision is visible in the output.

gloss(text, lexicon) -> list[Entry]. Each Entry covers one or more source tokens and says what
happened to them: a concept was found, the word will be fingerspelled, the word was dropped (a
function word, shown struck through in the caption), or nothing honest can be shown.

Steps per sentence: tokenise -> match multi-word phrases -> per-token sense rules and keyword
lookup -> numbers to digit sequences -> function words dropped -> time expressions moved to the
front (the one ASL reordering that is safe without a signer).
"""
import re
from dataclasses import dataclass, field

FUNCTION_WORDS = set("""
a an the is am are was were be been being do does did has have had will would shall should
can could may might must of to in on at by for with from as that this these those it its
there their they them he she his her him his i me my we our you your than then so such
""".split())
CONTRACTIONS = {"it's": "it is", "that's": "that is", "there's": "there is", "he's": "he is", "she's": "she is",
                "i'm": "i am", "we're": "we are", "they're": "they are", "you're": "you are", "don't": "do not",
                "doesn't": "does not", "didn't": "did not", "won't": "will not", "can't": "can not", "isn't": "is not",
                "aren't": "are not", "wasn't": "was not", "weren't": "were not", "hasn't": "has not", "haven't": "have not",
                "who's": "who is", "what's": "what is", "let's": "let us", "wanna": "want to", "gonna": "going to"}
CONTRACTION_RE = re.compile(r"\b(" + "|".join(re.escape(k) for k in CONTRACTIONS) + r")\b")
TIME_CONCEPTS = {"today", "tonight", "tomorrow", "morning", "afternoon", "night", "day", "week", "weekend", "month", "year",
                 "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "now", "last", "next"}
STEM_SUFFIXES = ("ies", "ing", "ed", "es", "s", "ly", "er", "est")
MAX_FINGERSPELL = 12


@dataclass
class Entry:
    word: str                 # the source text this entry covers
    token_index: int          # index of the first source token (for timing)
    n_tokens: int = 1
    kind: str = "none"        # sign | number | fingerspell | dropped | none
    concept: str | None = None
    letters: tuple = field(default_factory=tuple)   # for fingerspell: letters/digits in order
    why: str = ""


def tokenize(text):
    """Lowercase tokens. Keeps 'u.s.' style abbreviations and hyphenated words; expands contractions."""
    text = text.lower().replace("’", "'")
    text = re.sub(r"(\d),(\d)", r"\1\2", text)          # 10,000 -> 10000
    text = re.sub(r"(\d)%", r"\1 percent", text)        # 30% -> 30 percent
    text = re.sub(r"\$(\d+(?:\.\d+)?)", r"\1 dollar", text)  # $160 -> 160 dollar
    text = CONTRACTION_RE.sub(lambda m: CONTRACTIONS[m.group(0)], text)
    text = re.sub(r"(\w)'s\b", r"\1", text)             # possessive: samoa's -> samoa
    return re.findall(r"[a-z]+(?:\.[a-z]+)+\.?|[a-z]+(?:[-'][a-z]+)*|\d+(?:\.\d+)?", text)


def sentences(text):
    return [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]


def _stem(word, lexicon):
    for suf in STEM_SUFFIXES:
        if word.endswith(suf) and len(word) - len(suf) >= 3:
            base = word[: -len(suf)] + ("y" if suf == "ies" else "")
            if base in lexicon.words:
                return base
            if suf in ("ed", "ing", "es", "er", "est") and base + "e" in lexicon.words:
                return base + "e"
    return None


def _apply_sense(word, prev, nxt, rules):
    """Returns (target, consume_next). target is a concept id, 'fingerspell', or None (no rule matched)."""
    for rule in rules:
        if "default" in rule:
            return rule["default"], False
        if "if_prev_in" in rule and prev in rule["if_prev_in"]:
            return rule["concept"], rule.get("consume_next", False)
        if "if_next_in" in rule and nxt in rule["if_next_in"]:
            return rule["concept"], rule.get("consume_next", False)
    return None, False


def _fingerspell(word, lexicon, index, n=1, why="no established sign in this system"):
    chars = [c for c in word if c.isalnum()]
    if not chars or len(chars) > MAX_FINGERSPELL:
        return Entry(word, index, n, "none", why=f"cannot fingerspell '{word}'")
    letters = []
    for ch in chars:
        c = lexicon.digit(ch) if ch.isdigit() else lexicon.letter(ch)
        if c is None:
            return Entry(word, index, n, "none", why=f"no clip for character '{ch}'")
        letters.append(c.concept_id)
    return Entry(word, index, n, "fingerspell", letters=tuple(letters), why=why)


def gloss_sentence(tokens, lexicon, offset=0):
    entries = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        # 1. multi-word phrase
        matched = False
        for parts, cid in lexicon.phrases:
            if tuple(tokens[i : i + len(parts)]) == parts:
                entries.append(Entry(" ".join(parts), offset + i, len(parts), "sign", cid))
                i += len(parts)
                matched = True
                break
        if matched:
            continue
        prev = tokens[i - 1] if i > 0 else ""
        nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
        # 2. sense rule
        if tok in lexicon.senses:
            target, consume = _apply_sense(tok, prev, nxt, lexicon.senses[tok])
            if target is not None:
                n = 2 if consume else 1
                word = " ".join(tokens[i : i + n])
                if target == "fingerspell":
                    entries.append(_fingerspell(word, lexicon, offset + i, n))
                else:
                    entries.append(Entry(word, offset + i, n, "sign", target, why="sense rule"))
                i += n
                continue
        # 3. function word
        if tok in FUNCTION_WORDS:
            entries.append(Entry(tok, offset + i, 1, "dropped", why="function word"))
            i += 1
            continue
        # 4. keyword, then stem
        cid = lexicon.words.get(tok)
        if cid is None:
            base = _stem(tok, lexicon)
            cid = lexicon.words.get(base) if base else None
        if cid:
            entries.append(Entry(tok, offset + i, 1, "sign", cid))
            i += 1
            continue
        # 5. numbers -> digit sequence; each digit is a validated sign, so this counts as 'number', not fingerspelling
        if re.fullmatch(r"\d+(\.\d+)?", tok):
            e = _fingerspell(tok, lexicon, offset + i, why="number, signed digit by digit")
            if e.kind == "fingerspell":
                e.kind = "number"
            entries.append(e)
            i += 1
            continue
        # 6. fingerspell or refuse
        entries.append(_fingerspell(tok, lexicon, offset + i))
        i += 1
    # 7. time expressions to the front of the sentence
    time_first = [e for e in entries if e.kind == "sign" and e.concept in TIME_CONCEPTS]
    rest = [e for e in entries if not (e.kind == "sign" and e.concept in TIME_CONCEPTS)]
    return time_first + rest


def gloss(text, lexicon):
    out, offset = [], 0
    for s in sentences(text):
        toks = tokenize(s)
        out.extend(gloss_sentence(toks, lexicon, offset))
        offset += len(toks)
    return out


def stats(entries):
    content = [e for e in entries if e.kind != "dropped"]
    n = len(content) or 1
    signed = sum(1 for e in content if e.kind in ("sign", "number"))
    spelled = sum(1 for e in content if e.kind == "fingerspell")
    names = sum(1 for e in content if e.kind == "name")
    return {"tokens": len(content), "validated": signed, "fingerspelled": spelled, "names": names,
            "not_available": len(content) - signed - spelled - names,
            "coverage": round(signed / n, 3), "fingerspelling_rate": round(spelled / n, 3)}
