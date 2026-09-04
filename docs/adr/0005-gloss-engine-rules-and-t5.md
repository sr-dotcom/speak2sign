# ADR 0005 — Gloss engine: rule pass by default, T5-small via CTranslate2 behind a toggle

**Date:** 2026-09-03 · **Status:** Accepted
**Retires:** the Keras 16-class intent classifier and TensorFlow (previous iteration, decision B)

## Context

The module marks a deep-learning component (⚑A2). The previous iteration's 16-class intent classifier cannot generalise beyond 16 phrases. The system needs English → gloss for open text, and the deployed app must stay torch-free within 1.8 GB (ADR 0002).

## Decision

- **Default: a rule pass** (`src/speak2sign/gloss/rules.py`, stdlib only): phrases first, sense table, function-word drops recorded for the caption, numbers as digit sequences, time expressions fronted. Every decision is a visible Entry.
- **Deep-learning path: t5-small fine-tuned on ASLG-PC12** (87,710 English→gloss pairs, CC BY-NC 4.0) on Kaggle (`training/train_t5_gloss.py`), exported to **CTranslate2 int8** (`training/export_ct2.py`) and served at runtime with `ctranslate2` + `sentencepiece` only (`src/speak2sign/gloss/t5.py`). Behind a user toggle; hidden when the export is absent.
- **Both paths resolve through the same lexicon**: a T5 gloss with no validated clip is fingerspelled or refused. T5 can never invent a sign form.
- **Evaluation** (`docs/04-testing/evaluation.md`, Phase 5): BLEU/chrF on the held-out ASLG-PC12 split, and coverage, fingerspelling rate and a manual 30-sentence gloss review on the curated news items, rules vs T5. The default changes only if T5 wins on the news items.

## Consequences

- Runtime gains `sentencepiece` (2 MB) and uses the `ctranslate2` already required by faster-whisper; the export is ~60 MB, fetched from a GitHub Release on first use.
- Timing for the T5 path is approximate: model output carries no word alignment, so glosses are mapped to source positions proportionally. Acceptable under interpreter pacing (ADR 0008); stated in the UI.
- Known limitation stated up front: ASLG-PC12 glosses were rule-generated from parliamentary text, so a high test-split score does not imply good news glossing.

## Alternatives rejected

- Keras intent classifier (16 phrases, no generalisation); LLM APIs (cost, rate limits, not reproducible); sentence-transformers (needs torch); training on ASL Citizen or PHOENIX-2014T (German Sign Language; and EUD Principle 7 discourages data from interpreted broadcasts).
