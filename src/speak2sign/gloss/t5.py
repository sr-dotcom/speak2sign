"""T5 gloss path: the fine-tuned t5-small served by CTranslate2 int8 (no torch at runtime). Behind a toggle.

Produces the same Entry list as the rule pass so the timeline builder treats both alike. A T5 gloss is
resolved through the lexicon exactly like a rule-pass keyword, so T5 can never invent a sign form:
unknown glosses fingerspell, or are refused. T5 output carries no alignment, so each gloss is mapped
back to a source token position proportionally; the timeline keeps captions from the source text.

Model files live in models/t5_gloss_ct2 (git-ignored): model.bin, config.json, spiece.model. They are
fetched from the project's GitHub Release on first use if T5_RELEASE_URL is set.
"""
import io
import os
import re
import shutil
import threading
import urllib.request
import zipfile
from pathlib import Path

from speak2sign.gloss.rules import FUNCTION_WORDS, NUMBER_RE, Entry, _fingerspell, number_entry, sentences, tokenize

ROOT = Path(__file__).resolve().parents[3]
MODEL_DIR = ROOT / "models" / "t5_gloss_ct2"
RELEASE_URL = os.environ.get("T5_RELEASE_URL", "")
PREFIX = "translate English to ASL gloss: "
MAX_LEN = 64
GLOSS_PREFIXES = ("DESC-", "X-")   # ASLG-PC12 marks adjectives/adverbs and pronouns; strip for lookup
REQUIRED_FILES = ("model.bin", "config.json", "spiece.model")
_model = None                      # (translator, sentencepiece) once both loaded
_lock = threading.Lock()           # Streamlit serves sessions on threads: load once, never twice


def _complete(d):
    return all((d / f).exists() for f in REQUIRED_FILES)


def available():
    return _complete(MODEL_DIR) or bool(RELEASE_URL)


def _ensure():
    """Download and unpack the export once. Unpacked into a staging folder, checked for every required file, then
    renamed into place, so a failed or interrupted download never leaves a half-export that passes for complete;
    an incomplete folder counts as absent and is downloaded again."""
    if not _complete(MODEL_DIR):
        if not RELEASE_URL:
            raise FileNotFoundError("T5 model not present or incomplete, and T5_RELEASE_URL not set")
        staging = MODEL_DIR.with_name(MODEL_DIR.name + ".part")
        shutil.rmtree(staging, ignore_errors=True)
        with urllib.request.urlopen(urllib.request.Request(RELEASE_URL, headers={"User-Agent": "speak2sign"}), timeout=600) as r:
            zipfile.ZipFile(io.BytesIO(r.read())).extractall(staging)
        missing = [f for f in REQUIRED_FILES if not (staging / f).exists()]
        if missing:
            shutil.rmtree(staging, ignore_errors=True)
            raise FileNotFoundError(f"release zip is missing {missing} ({RELEASE_URL})")
        shutil.rmtree(MODEL_DIR, ignore_errors=True)
        staging.rename(MODEL_DIR)
    return MODEL_DIR


def _load():
    global _model
    with _lock:
        if _model is None:
            import ctranslate2
            import sentencepiece as spm
            d = _ensure()
            translator = ctranslate2.Translator(str(d), device="cpu", compute_type="int8")
            sp = spm.SentencePieceProcessor(model_file=str(d / "spiece.model"))
            _model = (translator, sp)   # published only once both exist
    return _model


def translate(text):
    """English sentence -> list of gloss tokens (uppercase strings) from the model."""
    tr, sp = _load()
    pieces = sp.encode(PREFIX + text, out_type=str) + ["</s>"]
    out = tr.translate_batch([pieces], beam_size=2, max_decoding_length=MAX_LEN)[0].hypotheses[0]
    return sp.decode(out).split()


def _strip(gloss):
    for p in GLOSS_PREFIXES:
        if gloss.startswith(p):
            return gloss[len(p):]
    return gloss


SCALE_CONCEPTS = {"hundred", "thousand", "million", "billion"}


def _numeric(cid):
    """A concept that states a quantity: a digit sign or a scale word."""
    return cid.startswith("digit-") or cid in SCALE_CONCEPTS


def _lookup(gloss, lexicon):
    """Exact keyword or exact phrase only. A compound like RAIN-COAT must not resolve to RAIN."""
    g = _strip(gloss).lower().replace("-", " ")
    return lexicon.words.get(g) or lexicon.words.get(g.replace(" ", "-")) or lexicon.phrase_ids.get(tuple(g.split()))


def gloss_sentence(tokens, lexicon, offset=0, translate_fn=None):
    """Same contract as rules.gloss_sentence. Gloss order comes from the model."""
    text = " ".join(tokens)
    glosses = [g for g in (translate_fn or translate)(text) if re.search(r"[A-Za-z0-9]", g)]
    entries = []
    n_src = max(1, len(tokens))
    for i, g in enumerate(glosses):
        ti = offset + min(n_src - 1, round(i * n_src / max(1, len(glosses))))
        word = _strip(g).lower()
        if not word:   # a bare marker such as "X-"
            continue
        cid = _lookup(g, lexicon)
        if cid and _numeric(cid) and word not in tokens:   # TWO for a source that says 27: a changed quantity, refused
            entries.append(Entry(word, ti, 1, "none", why=f"'{word}' is not in the source text; the model changed a number"))
        elif cid:
            entries.append(Entry(word, ti, 1, "sign", cid, why="t5"))
        elif word in FUNCTION_WORDS:
            entries.append(Entry(word, ti, 1, "dropped", why="function word (t5)"))
        elif word[0].isdigit() or NUMBER_RE.fullmatch(word):
            if word not in tokens:   # a number the source never said (27 -> 72) must not play as validated digits
                entries.append(Entry(word, ti, 1, "none", why=f"'{word}' is not in the source text; the model changed a number"))
            else:
                entries.append(number_entry(word, lexicon, ti))
        else:
            entries.append(_fingerspell(word, lexicon, ti, why="t5 gloss with no validated sign"))
    return entries


def gloss(text, lexicon, translate_fn=None):
    out, offset = [], 0
    for s in sentences(text):
        toks = tokenize(s)
        out.extend(gloss_sentence(toks, lexicon, offset, translate_fn))
        offset += len(toks)
    return out
