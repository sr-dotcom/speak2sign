"""Timed transcript + gloss entries -> timeline JSON (contracts/timeline.schema.json).

The last server-side stage. The browser panel reads only this file. Pacing policy is ADR 0008:
the media plays one sentence and waits for the panel; within a sentence the entries play in order,
one after another (onset_s records when the word was spoken; it is not a schedule); clips play
their active span at fixed rates; a capitalised word with no sign is fingerspelled once, then
shown as text ('name'). Captions are the source words verbatim, so nothing an engine drops or
omits can disappear from the screen.
"""
import bisect
import re

from speak2sign import provenance
from speak2sign.gloss.rules import TIME_CONCEPTS, gloss_sentence, stats, tokenize

STATIC_URL = "app/static/"   # Streamlit static serving root
SIGN_RATE = 1.25             # playback rate for sign clips
LETTER_RATE = 2.0            # playback rate for letter and digit clips
TEXT_HOLD_S = 0.9            # how long the panel shows a name or an unavailable word as text
MODE = "interpreter-paced"
ENGINES = ("rules", "t5")
# A trailing full stop on these is not a sentence end: U.S., U.N., Dr., Mr. ...
ABBREVIATION = re.compile(r"^\W*(?:(?:[^\W\d_]\.)+[^\W\d_]?|Mr|Mrs|Ms|Dr|St|Jr|Sr|Gen|Sen|Gov|Rep|Lt|Col|No|vs)\.\W*$")


def _ends_sentence(word):
    core = word.rstrip().rstrip("\"'”’)]")
    return core.endswith((".", "!", "?")) and not ABBREVIATION.match(word.strip())


def _tokens_with_onsets(transcript):
    """Tokenise word by word so every token keeps the onset, the original text and the index of its word."""
    tokens, onsets, originals, word_of, starts = [], [], [], [], [0]
    words = transcript.words
    sign = ""   # a lone "-" / "+" / "−" word before a number: carried into the number's own word so "- 5" is refused as "-5"
    for wi, w in enumerate(words):
        if w.text.strip("()") in ("-", "+", "−") and wi + 1 < len(words) and words[wi + 1].text[:1].isdigit():
            sign = w.text.strip("()")
            continue
        for t in tokenize(sign + w.text):
            tokens.append(t)
            onsets.append(w.onset_s)
            originals.append(w.text)
            word_of.append(wi)
        sign = ""
        if _ends_sentence(w.text) and len(tokens) > starts[-1]:
            starts.append(len(tokens))
    if starts[-1] != len(tokens):
        starts.append(len(tokens))
    return tokens, onsets, originals, word_of, starts


def _capitalised(original):
    core = original.strip("\"'“”‘’(),.;:!?")
    return bool(core) and core[0].isupper()


def _is_name(original, sentence_initial, known_names, token):
    """Capitalised mid-sentence, or sentence-initial but seen capitalised mid-sentence elsewhere in the item."""
    return _capitalised(original) and (not sentence_initial or token in known_names)


def _engine(name):
    if name not in ENGINES:
        raise ValueError(f"unknown gloss engine {name!r}; expected one of {ENGINES}")
    if name == "t5":
        from speak2sign.gloss import t5   # lazy: ctranslate2/sentencepiece load only when chosen
        return t5.gloss_sentence
    return gloss_sentence


def _uncovered(tokens, chunk, lexicon):
    """Source token indices no T5 entry of this sentence accounts for (T5 output carries no alignment). The rule
    pass says what each source span means (phrases, sense rules, stems included); each T5 entry can account for one
    such span, by the span's text or its concept. Function words the rule pass drops count as unsigned too."""
    budget = [(e.word, e.concept) for e in chunk if e.kind != "dropped"]

    def consume(word, concept):
        """A span that means a concept is covered only by an entry signing that concept (same word, other sense: no);
        a span with no concept (a spelled word) is covered by an entry with the same text."""
        for i, (w, c) in enumerate(budget):
            if (c == concept) if concept else (w == word):
                del budget[i]
                return True
        return False

    out = set()
    for r in gloss_sentence(tokens, lexicon):
        if r.kind == "dropped" or not consume(r.word, r.concept):
            out.update(range(r.token_index, r.token_index + r.n_tokens))
    return out


def gloss_transcript(transcript, lexicon, gloss_engine="rules"):
    """Run the chosen gloss engine sentence by sentence.
    Returns (entries with onset and sentence index, sentence spans, source) where source carries the tokens, onsets,
    word index per token and, for T5, the token indices no entry accounts for."""
    tokens, onsets, originals, word_of, starts = _tokens_with_onsets(transcript)
    known_names = {tokens[i] for i in range(len(tokens)) if i not in starts and _capitalised(originals[i])}
    entries, spans, seen_names, uncovered = [], [], set(), set()
    engine = _engine(gloss_engine)
    for si, (a, b) in enumerate(zip(starts, starts[1:])):
        chunk = engine(tokens[a:b], lexicon, offset=a)
        if gloss_engine == "t5":
            uncovered |= {a + ti for ti in _uncovered(tokens[a:b], chunk, lexicon)}
        for e in chunk:
            if e.kind == "sign" and lexicon.get(e.concept) is None:   # fail closed: never a validated badge without a clip
                e.why, e.kind, e.concept = f"concept '{e.concept}' has no attested clip", "none", None
            fronted = e.kind == "sign" and e.concept in TIME_CONCEPTS and e.token_index != a
            onset = onsets[a] if fronted else onsets[e.token_index]
            if e.kind == "fingerspell" and _is_name(originals[e.token_index], e.token_index == a, known_names, e.word):
                if e.word in seen_names:
                    e.kind = "name"
                    e.why = "name already fingerspelled once; shown as text"
                else:
                    seen_names.add(e.word)
                    e.why = "name, fingerspelled on first mention"
            entries.append((e, onset, si))
        end = onsets[b] if b < len(onsets) else (transcript.duration_s if transcript.duration_s is not None else onsets[b - 1])
        spans.append({"index": si, "t_start": onsets[a], "t_end": end})
    if not spans and transcript.words:   # words but no tokens ("!!!"): one empty sentence so every caption has an owner
        t0 = transcript.words[0].onset_s
        spans.append({"index": 0, "t_start": t0, "t_end": transcript.duration_s if transcript.duration_s is not None else t0})
    if spans:   # leading words without tokens ("!!! Rain.") belong to the first sentence, so it starts where they do
        spans[0]["t_start"] = min(spans[0]["t_start"], transcript.words[0].onset_s)
    return entries, spans, {"tokens": tokens, "onsets": onsets, "word_of": word_of, "starts": starts, "uncovered": uncovered}


def _clips(entry, lexicon):
    if entry.kind == "sign":
        return [lexicon.get(entry.concept)]
    if entry.kind in ("number", "fingerspell"):
        return [lexicon.get(cid) for cid in entry.letters]
    return []


def _captions(transcript, triples, src, gloss_engine):
    """One caption per source word, verbatim, at its spoken time, owned by its sentence. 'dropped' when nothing signs
    it (the rule pass dropped every token, or no T5 entry accounts for any); 'partly' when some of its tokens are
    signed and some are not ("don't" -> NOT signed, "do" dropped; "30%" -> 30 signed, "percent" omitted)."""
    dropped_tokens = set(src["uncovered"])
    for e, _, _ in triples:
        if e.kind == "dropped" and (gloss_engine == "rules" or src["tokens"][e.token_index] == e.word):
            dropped_tokens.update(range(e.token_index, e.token_index + e.n_tokens))
    tokens_of = {}
    for ti, wi in enumerate(src["word_of"]):
        tokens_of.setdefault(wi, []).append(ti)
    n_sentences = max(1, len(src["starts"]) - 1)
    captions, sentence = [], 0
    for wi, w in enumerate(transcript.words):
        toks = tokens_of.get(wi, [])
        if toks:   # a word with no tokens (punctuation only) stays with the sentence before it
            sentence = min(n_sentences - 1, bisect.bisect_right(src["starts"], toks[0]) - 1)
        c = {"t": w.onset_s, "text": w.text, "sentence": sentence}
        missing = [src["tokens"][t] for t in toks if t in dropped_tokens]
        if toks and len(missing) == len(toks):
            c["dropped"] = True
        elif missing:
            c["partly"] = True
            c["missing"] = missing   # the unsigned parts, shown struck through after the word
        captions.append(c)
    return captions


def build(transcript, lexicon, gloss_engine="rules"):
    triples, spans, src = gloss_transcript(transcript, lexicon, gloss_engine)
    onsets = src["onsets"]
    entries, sources, signing_s = [], set(), 0.0
    for e, onset, si in triples:
        if e.kind == "dropped":
            continue
        concepts = _clips(e, lexicon)
        rate = SIGN_RATE if e.kind == "sign" else LETTER_RATE
        clips = []
        for c in concepts:
            clips.append({"url": STATIC_URL + c.clip_file, "duration_s": c.duration_s, "in_s": c.in_s, "out_s": c.out_s or c.duration_s,
                          "rate": rate, "source": c.source, "licence": c.licence, "attribution_url": c.attribution_url})
            sources.add(c.source)
            signing_s += c.active_s / rate
        if not clips:
            signing_s += TEXT_HOLD_S
        gloss_label = concepts[0].gloss if e.kind == "sign" else e.word.upper()
        entry = {"onset_s": onset, "sentence": si, "word": e.word, "gloss": gloss_label, "badge": provenance.badge(e.kind), "clips": clips}
        n = provenance.note(e, concepts[0] if e.kind == "sign" else None)
        if n:
            entry["note"] = n
        entries.append(entry)
    entries.sort(key=lambda x: x["onset_s"])   # stable: fronted time signs stay at the sentence start
    captions = _captions(transcript, triples, src, gloss_engine)
    s = stats([e for e, _, _ in triples])
    speech_s = transcript.duration_s if transcript.duration_s is not None else (max(onsets) if onsets else 0.0)
    s.update({"signing_s": round(signing_s, 3), "speech_s": round(speech_s, 3), "gloss_engine": gloss_engine})
    media = {"kind": transcript.media_kind}
    if transcript.media_url:
        media["url"] = transcript.media_url
    if transcript.duration_s is not None:
        media["duration_s"] = transcript.duration_s
    item = {"id": transcript.item_id, "title": transcript.title or transcript.item_id, "source": transcript.source or transcript.lane, "lane": transcript.lane}
    if transcript.broadcast_date:
        item["broadcast_date"] = transcript.broadcast_date
    return {"version": 1, "item": item, "media": media,
            "playback": {"mode": MODE, "sign_rate": SIGN_RATE, "letter_rate": LETTER_RATE, "text_hold_s": TEXT_HOLD_S},
            "sentences": spans, "captions": captions, "entries": entries, "stats": s,
            "provenance": {"disclaimer": provenance.DISCLAIMER, "attributions": provenance.attributions(sorted(sources), transcript.lane, gloss_engine)}}
