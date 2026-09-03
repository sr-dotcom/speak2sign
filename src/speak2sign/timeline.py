"""Timed transcript + gloss entries -> timeline JSON (contracts/timeline.schema.json).

The last server-side stage. The browser panel reads only this file. Pacing policy is ADR 0008:
the media plays one sentence and waits for the panel; clips play their active span at fixed
rates; a capitalised word with no sign is fingerspelled once, then shown as text ('name').
"""
from speak2sign import provenance
from speak2sign.gloss.rules import TIME_CONCEPTS, gloss_sentence, stats, tokenize

STATIC_URL = "app/static/"   # Streamlit static serving root
SIGN_RATE = 1.25             # playback rate for sign clips
LETTER_RATE = 2.0            # playback rate for letter and digit clips
MODE = "interpreter-paced"


def _tokens_with_onsets(transcript):
    """Tokenise word by word so every token keeps the onset and the original text of its word."""
    tokens, onsets, originals, starts = [], [], [], [0]
    for w in transcript.words:
        for t in tokenize(w.text):
            tokens.append(t)
            onsets.append(w.onset_s)
            originals.append(w.text)
        if w.text.rstrip().rstrip("\"'”’)]").endswith((".", "!", "?")) and len(tokens) > starts[-1]:
            starts.append(len(tokens))
    if starts[-1] != len(tokens):
        starts.append(len(tokens))
    return tokens, onsets, originals, starts


def _capitalised(original):
    core = original.strip("\"'“”‘’(),.;:!?")
    return bool(core) and core[0].isupper()


def _is_name(original, sentence_initial, known_names, token):
    """Capitalised mid-sentence, or sentence-initial but seen capitalised mid-sentence elsewhere in the item."""
    return _capitalised(original) and (not sentence_initial or token in known_names)


def gloss_transcript(transcript, lexicon):
    """Run the rule pass sentence by sentence. Returns (entries with onset and sentence index, sentence spans)."""
    tokens, onsets, originals, starts = _tokens_with_onsets(transcript)
    known_names = {tokens[i] for i in range(len(tokens)) if i not in starts and _capitalised(originals[i])}
    entries, spans, seen_names = [], [], set()
    for si, (a, b) in enumerate(zip(starts, starts[1:])):
        chunk = gloss_sentence(tokens[a:b], lexicon, offset=a)
        for e in chunk:
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
    return entries, spans, onsets


def _clips(entry, lexicon):
    if entry.kind == "sign":
        c = lexicon.get(entry.concept)
        return [c] if c else []
    if entry.kind in ("number", "fingerspell"):
        return [lexicon.get(cid) for cid in entry.letters]
    return []


def build(transcript, lexicon, gloss_engine="rules"):
    triples, spans, onsets = gloss_transcript(transcript, lexicon)
    entries, captions, sources, signing_s = [], [], set(), 0.0
    for e, onset, si in triples:
        spoken_t = onsets[e.token_index]   # captions keep spoken order even when the sign was fronted
        if e.kind == "dropped":
            captions.append({"t": spoken_t, "text": e.word, "dropped": True})
            continue
        captions.append({"t": spoken_t, "text": e.word})
        concepts = _clips(e, lexicon)
        rate = SIGN_RATE if e.kind == "sign" else LETTER_RATE
        clips = []
        for c in concepts:
            clips.append({"url": STATIC_URL + c.clip_file, "duration_s": c.duration_s, "in_s": c.in_s, "out_s": c.out_s or c.duration_s,
                          "rate": rate, "source": c.source, "attribution_url": c.attribution_url})
            sources.add(c.source)
            signing_s += c.active_s / rate
        gloss_label = concepts[0].gloss if e.kind == "sign" and concepts else e.word.upper()
        entry = {"onset_s": onset, "sentence": si, "word": e.word, "gloss": gloss_label, "badge": provenance.badge(e.kind), "clips": clips}
        n = provenance.note(e, concepts[0] if e.kind == "sign" and concepts else None)
        if n:
            entry["note"] = n
        entries.append(entry)
    entries.sort(key=lambda x: x["onset_s"])   # stable: fronted time signs stay at the sentence start
    captions.sort(key=lambda x: x["t"])
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
    return {"version": 1, "item": item, "media": media, "playback": {"mode": MODE, "sign_rate": SIGN_RATE, "letter_rate": LETTER_RATE},
            "sentences": spans, "captions": captions, "entries": entries, "stats": s,
            "provenance": {"disclaimer": provenance.DISCLAIMER, "attributions": provenance.attributions(sorted(sources), transcript.lane)}}
