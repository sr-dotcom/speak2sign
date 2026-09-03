"""Concept lexicon: the only place the system knows what a sign looks like.

Loads data/lexicon/concepts.json (built by scripts/build_lexicon.py) and senses.json.
Keyed on concept ids, never on English strings alone; English keywords are an index into it.
"""
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LEX_DIR = ROOT / "data" / "lexicon"


@dataclass(frozen=True)
class Concept:
    concept_id: str
    gloss: str
    keywords: tuple
    clip_file: str        # relative to static/
    source: str           # cats | signbank
    licence: str
    attribution_url: str
    note: str | None
    duration_s: float = 0.0
    in_s: float = 0.0
    out_s: float = 0.0

    @property
    def active_s(self):
        return round(max(0.0, (self.out_s or self.duration_s) - self.in_s), 3)


class Lexicon:
    def __init__(self, concepts, senses):
        self.concepts = {c.concept_id: c for c in concepts}
        self.senses = senses
        self.words = {}     # single-word keyword -> concept_id
        self.phrases = []   # (tuple of words, concept_id), longest first
        for c in concepts:
            for k in c.keywords:
                parts = tuple(k.split())
                if len(parts) == 1:
                    self.words.setdefault(k, c.concept_id)
                else:
                    self.phrases.append((parts, c.concept_id))
        self.phrases.sort(key=lambda p: -len(p[0]))

    def get(self, concept_id):
        return self.concepts.get(concept_id)

    def letter(self, ch):
        return self.concepts.get(f"letter-{ch.lower()}")

    def digit(self, ch):
        return self.concepts.get(f"digit-{ch}")

    def __len__(self):
        return len(self.concepts)


@lru_cache(maxsize=1)
def load(lex_dir=LEX_DIR):
    raw = json.loads((Path(lex_dir) / "concepts.json").read_text(encoding="utf-8"))
    concepts = [
        Concept(r["concept_id"], r["gloss"], tuple(r["keywords"]), r["clip"]["file"], r["clip"]["source"],
                r["clip"]["licence"], r["clip"]["attribution_url"], r.get("note"), r["clip"].get("duration_s") or 0.0,
                r["clip"].get("in_s") or 0.0, r["clip"].get("out_s") or r["clip"].get("duration_s") or 0.0)
        for r in raw if r.get("status") == "attested"
    ]
    senses = json.loads((Path(lex_dir) / "senses.json").read_text(encoding="utf-8"))
    senses = {k: v for k, v in senses.items() if not k.startswith("_")}
    return Lexicon(concepts, senses)
