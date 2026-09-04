"""T5 gloss path: the fine-tuned t5-small served by CTranslate2 int8 (no torch at runtime). Behind a toggle.

Produces the same Entry list as the rule pass so the timeline builder treats both alike. A T5 gloss is
resolved through the lexicon exactly like a rule-pass keyword, so T5 can never invent a sign form:
unknown glosses fingerspell, or are refused.

Model files live in models/t5_gloss_ct2 (git-ignored): model.bin, config.json, spiece.model. They are
fetched from the project's GitHub Release on first use if T5_RELEASE_URL is set.
"""
import io
import os
import re
import urllib.request
import zipfile
from pathlib import Path

from speak2sign.gloss.rules import FUNCTION_WORDS, Entry, _fingerspell, tokenize

ROOT = Path(__file__).resolve().parents[3]
MODEL_DIR = ROOT / "models" / "t5_gloss_ct2"
RELEASE_URL = os.environ.get("T5_RELEASE_URL", "")
PREFIX = "translate English to ASL gloss: "
MAX_LEN = 64
GLOSS_PREFIXES = ("DESC-", "X-")   # ASLG-PC12 marks adjectives/adverbs and pronouns; strip for lookup
_translator = None
_sp = None


def available():
    return (MODEL_DIR / "model.bin").exists() or bool(RELEASE_URL)


def _ensure():
    if not (MODEL_DIR / "model.bin").exists():
        if not RELEASE_URL:
            raise FileNotFoundError("T5 model not present and T5_RELEASE_URL not set")
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(urllib.request.Request(RELEASE_URL, headers={"User-Agent": "speak2sign-v2"}), timeout=600) as r:
            zipfile.ZipFile(io.BytesIO(r.read())).extractall(MODEL_DIR)
    return MODEL_DIR


def _load():
    global _translator, _sp
    if _translator is None:
        import ctranslate2
        import sentencepiece as spm
        d = _ensure()
        _translator = ctranslate2.Translator(str(d), device="cpu", compute_type="int8")
        _sp = spm.SentencePieceProcessor(model_file=str(d / "spiece.model"))
    return _translator, _sp


def translate(text):
    """English sentence -> list of gloss tokens (uppercase strings) from the model."""
    tr, sp = _load()
    pieces = sp.encode(PREFIX + text, out_type=str) + ["</s>"]
    out = tr.translate_batch([pieces], beam_size=2, max_decoding_length=MAX_LEN)[0].hypotheses[0]
    return sp.decode(out).split()


def _lookup(gloss, lexicon):
    g = gloss
    for p in GLOSS_PREFIXES:
        if g.startswith(p):
            g = g[len(p):]
    g = g.lower().replace("-", " ")
    return lexicon.words.get(g) or lexicon.words.get(g.replace(" ", "-")) or lexicon.words.get(g.split()[0] if g else g)


def gloss_sentence(tokens, lexicon, offset=0, translate_fn=translate):
    """Same contract as rules.gloss_sentence. Gloss order comes from the model; each gloss is mapped
    back to a source token position proportionally, since T5 output carries no alignment."""
    text = " ".join(tokens)
    glosses = [g for g in translate_fn(text) if re.search(r"[A-Za-z0-9]", g)]
    entries = []
    n_src = max(1, len(tokens))
    for i, g in enumerate(glosses):
        ti = offset + min(n_src - 1, round(i * n_src / max(1, len(glosses))))
        word = g.lower()
        cid = _lookup(g, lexicon)
        if cid:
            entries.append(Entry(word, ti, 1, "sign", cid, why="t5"))
        elif word.lstrip("x-").lstrip("desc-") in FUNCTION_WORDS:
            entries.append(Entry(word, ti, 1, "dropped", why="function word (t5)"))
        elif re.fullmatch(r"\d+(\.\d+)?", word):
            e = _fingerspell(word, lexicon, ti, why="number, signed digit by digit")
            if e.kind == "fingerspell":
                e.kind = "number"
            entries.append(e)
        else:
            entries.append(_fingerspell(word, lexicon, ti, why="t5 gloss with no validated sign"))
    return entries


def gloss(text, lexicon, translate_fn=translate):
    out, offset = [], 0
    for s in re.split(r"(?<=[.!?])\s+", text.strip()):
        if not s:
            continue
        toks = tokenize(s)
        out.extend(gloss_sentence(toks, lexicon, offset, translate_fn))
        offset += len(toks)
    return out
