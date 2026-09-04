# Test strategy

**Date:** 2026-09-04 · **Status:** Accepted (describes what exists; nothing here is planned-but-unbuilt)
**Reads with:** [PRD](../01-requirements/prd.md) · [System design §14](../02-design/system-design.md) · [evaluation.md](evaluation.md) · [accessibility.md](accessibility.md) · [coverage-rules.md](coverage-rules.md)

## 1. What is being protected

Three things can go wrong in this system, in order of harm:

1. **Dishonesty**: a sign shown that was not retrieved from a validated clip, a badge that lies, a dropped word that is hidden, a number on screen that does not match what plays.
2. **A broken viva**: the deployed app fails to boot, runs out of memory, or a curated item does not play.
3. **Ordinary bugs**: wrong sense, wrong timing, wrong stats.

The strategy weights effort in that order. The contract test and the provenance test exist for (1); the memory budget and the smoke test exist for (2); the unit tests exist for (3).

## 2. Layers, as built

| Layer | Tool | Count | Runs where | What it proves |
|---|---|---|---|---|
| Unit | pytest | 27 | local + CI | Tokeniser, phrases, senses, drops, numbers, time-fronting, stats arithmetic (`test_rules.py`); badge mapping is total and strict, notes explain every non-validated entry, attributions include the lane source once (`test_provenance.py`); alignment interpolation, WAV encoding, the 60 s cap (`test_asr.py`); T5 glosses resolve only through the lexicon and never invent a sign, token positions in range (`test_t5.py`); vocabulary ids well-formed, sense rules point at real concepts (`test_lexicon.py`); forecast script shape (`test_nws.py`) |
| Data integrity | pytest over the committed data | 4 | local + CI | Every attested concept's clip file exists with a licence and attribution URL; no English keyword is owned by two concepts without a sense rule; every curated item has monotonic timings, audio on disk, and ≥ 60 % whisper alignment |
| Contract | pytest + jsonschema | 6 | local + CI | Every lane's timeline validates against `contracts/timeline.schema.json`; entries sorted by onset; stats arithmetic (`validated + fingerspelled + names + not_available == entries == tokens`); every clip URL resolves to a file; fronting, dropped captions, names-once, signing time at recorded rates, provenance completeness |
| Integration with real models | pytest, skipped when the model is absent | 2 | local (models present) | faster-whisper transcribes a real news clip and the upload path builds a valid timeline; the CTranslate2 T5 export translates a sentence |
| App smoke | `streamlit.testing.v1.AppTest` | 2 | local + CI | The app runs without exception, shows the disclaimer, and the typed lane renders a ribbon with the rules engine |
| Memory budget | `scripts/measure_rss.py` | 1 gate | CI, every push | Peak RSS with lexicon + whisper + one transcription + timeline ≤ 1800 MB (measured 316 MB on the CI runner, 334 MB on Windows) |
| Static analysis | ruff | gate | CI | Lint clean |
| Browser checks | scripted DOM checks in the browser pane, screenshots | per change | local and at the live URL | Panel plays clips, captions highlight, waiting state fires, static files served (206), engine toggle works; recorded in the dev log and `spikes.md` |
| Evaluation | `scripts/evaluate_gloss.py`, `scripts/coverage_report.py` | reports | local | Rules vs T5 on the ASLG-PC12 test split and on the curated items; coverage and fingerspelling per item |
| Accessibility | axe-core in the browser + computed contrast | report | local | 0 WCAG 2.2 AA violations; all pairs ≥ 4.8:1 |

Total automated: **43 tests**, 94 % line coverage of `src/speak2sign` (`pytest --cov`). The uncovered lines are network error branches in `nws.py`, the model-download branch in `asr.py` and `t5.py`, and the real-model call in `t5.py` when the export is absent.

## 3. Requirement traceability

| Requirement | Evidence |
|---|---|
| FR-01 pick an item and play | `test_demo_set.py`, browser check at the live URL (2026-09-04) |
| FR-02 captions synchronised | browser check (audio-time highlight); timings validated in `test_demo_set.py` |
| FR-03 clip per entry at onset | contract test (`check()` asserts clip counts per badge and files exist) |
| FR-04 badge on every entry | `test_provenance.py`, contract test (badge enum in schema) |
| FR-05 fingerspelled letters in order | `test_rules.py::test_unknown_word_is_fingerspelled_and_long_word_refused`, `test_timeline_contract.py` clip counts |
| FR-06 overrun shown, nothing skipped | ADR 0008 replaced this with interpreter pacing; `sentences[]` and rates in the contract test; waiting state observed in browser checks |
| FR-07 disclaimer and attribution first | `test_smoke_app.py`, `test_timeline_contract.py::test_provenance_lists_every_source_used` |
| FR-08 weather lane | `test_nws.py` (offline fixture), browser check at the live URL |
| FR-09 typed text | `test_smoke_app.py`, contract test |
| FR-10 coverage and rate shown | `stats_line` in `ribbon.py` (covered), `test_rules.py::test_stats_arithmetic` |
| FR-11 dropped words struck through | `test_timeline_contract.py::test_recorded_timings_and_fronting` (caption `dropped` flag); panel CSS |
| FR-12 engine toggle | `test_t5.py`; toggle checked in the browser (`engine: t5` in the stats line) |
| FR-13 upload ≤ 60 s with editable transcript | `test_asr.py` (cap, alignment, real transcription); upload tab render checked in the browser; file upload itself not automated |
| FR-14 headline lane | not built (optional) |
| FR-15 keyboard operation | `accessibility.md` §3 |
| FR-16 disclaimer content | `provenance.DISCLAIMER` asserted in the contract test |
| FR-17 uploads never stored | by construction (`asr.py` uses memory and a data URL); code review, no test |
| NFR-02 memory | `measure_rss.py` in CI |
| NFR-05 licences | `test_lexicon.py::test_every_concept_has_clip_licence_and_attribution` |
| NFR-06 reproducibility | pinned requirements; `training/README.md`; `results.json` and split indices committed |

## 4. How to run

```bash
.venv/Scripts/python -m pytest -q                       # 43 tests, ~3 s (integration tests skip without models)
.venv/Scripts/python -m pytest -q --cov=src/speak2sign  # coverage
.venv/Scripts/ruff check .
.venv/Scripts/python scripts/measure_rss.py 1800        # memory gate (downloads whisper on first run)
.venv/Scripts/python scripts/evaluate_gloss.py          # rules vs T5 report
.venv/Scripts/python scripts/coverage_report.py         # rule-pass coverage per item
```

CI (`.github/workflows/ci.yml`) runs lint, tests and the memory gate on every push and pull request; a red run cannot be merged.

## 5. Known gaps and why they are accepted

| Gap | Why accepted | Mitigation |
|---|---|---|
| The panel's JavaScript has no unit tests | ~200 lines of DOM and media code; a JS test runner would add a toolchain for one file | Browser checks after every panel change, recorded with screenshots; the timeline contract test guards everything the panel consumes |
| File upload is not driven end to end by a test | Streamlit's uploader is not scriptable from AppTest | The whole path below the widget is tested with a real WAV in `test_asr.py` |
| Intermediate commits are not individually green | The history was rebuilt in SDLC order; the pipeline commit's contract test needs the curated items from a later commit | `main` is green at every push; tags mark releasable states |
| `AppTest` occasionally takes ~10 s | Streamlit component registration on first run | Observed once; no retry logic added until it recurs |
| No human screen-reader session | Time | Marked UNVERIFIED in `accessibility.md` |
| Safari and Firefox | No macOS available; Firefox untested | Marked UNVERIFIED in `spikes.md` |

## 6. Definition of done for any change

Code + test + docs in the same change; `ruff` and `pytest` green; memory gate green if dependencies or models changed; checked at the live URL after deploy; the delivery note states what, why, the trade-off, and the ponytail review (work policy in `CLAUDE.md`).
