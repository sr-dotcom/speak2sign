# Test strategy

**Date:** 2026-09-04, revised 2026-09-10 after the whole-codebase Codex audit · **Status:** Accepted (describes what exists; nothing here is planned-but-unbuilt)
**Reads with:** [PRD](../01-requirements/prd.md) · [System design §14](../02-design/system-design.md) · [evaluation.md](evaluation.md) · [accessibility.md](accessibility.md) · [coverage-rules.md](coverage-rules.md)

## 1. What is being protected

Three things can go wrong in this system, in order of harm:

1. **Dishonesty**: a sign shown that was not retrieved from a validated clip, a badge that lies, a dropped word that is hidden, a number on screen that does not match what plays.
2. **A broken viva**: the deployed app fails to boot, runs out of memory, or a curated item does not play.
3. **Ordinary bugs**: wrong sense, wrong timing, wrong stats.

The strategy weights effort in that order. The contract checker, the honesty tests in `test_rules.py`, `test_t5.py` and `test_timeline_contract.py`, and the provenance test exist for (1); the memory gate and the smoke tests exist for (2); the unit tests exist for (3).

## 2. Layers, as built

| Layer | Tool | Count | Runs where | What it proves |
|---|---|---|---|---|
| Unit | pytest | 51 | local + CI | Tokeniser (numbers, abbreviations, contractions, Unicode letters and marks, signed and decimal forms), phrases, senses, drops, stems without false friends, antonyms never share a sign, numbers refused whole when not whole, time-fronting, stats arithmetic (`test_rules.py`); badge mapping total and strict, a note for every non-validated kind, attributions deduplicated and complete, unknown sources an error (`test_provenance.py`); ribbon chip text per badge and HTML escaping (`test_ribbon.py`); transcript estimation (`test_transcript.py`); NWS script, gridpoint fallback, failure propagation (`test_nws.py`); alignment at both ends and with no match, WAV bytes decoded by the standard library, the 60 s cap on both sides (`test_asr.py`) |
| Honesty, engine level | pytest | 13 | local + CI | The T5 path with the model replaced by a function: fabricated or compound glosses never borrow a sign, omitted words are struck through, a gloss covers one occurrence, phrases and synonyms count as covered, a same-word-other-sense gloss does not, a number the source never said is refused, an incomplete export is not installed (`test_t5.py`) |
| Data integrity | pytest over the committed data | 10 | local + CI | Concept ids unique; every clip file exists with licence and attribution URL; no keyword collision without a sense rule; no concept lists its own negation; sense targets are attested; `lexicon.load` refuses a sense rule without a clip, duplicate ids and unplayable spans (`test_lexicon.py`); the six curated items are present with readable 16 kHz mono audio of the recorded duration and monotonic timings (`test_demo_set.py`) |
| Contract | pytest + jsonschema + `conftest.check_timeline` | 26 | local + CI | Every lane's timeline validates against `contracts/timeline.schema.json`, then the cross-field invariants the schema cannot state: entries sorted, stats arithmetic, sentences contiguous, every entry and caption inside its sentence, every clip resolved to the lexicon record it claims (source, licence, attribution, span), the clip sequence exactly the digits or letters of the entry's word, captions verbatim with `dropped` / `partly` + `missing`; plus negative cases the contract must reject (audio without url, partly without missing) |
| Integration with real models | pytest, skipped when the model is absent | 2 | local (models present) | faster-whisper transcribes a real news clip and the upload path builds a valid timeline; the CTranslate2 T5 export translates a sentence |
| App smoke | `streamlit.testing.v1.AppTest` | 6 | local + CI | The page runs and shows the disclaimer and a curated ribbon; the typed lane renders and its result survives a rerun; a forecast failure and an engine failure render as messages, not tracebacks |
| Review tooling | pytest with a stub `codex` | 5 | local + CI | `scripts/codex_review.sh` collects staged, unstaged and untracked changes, rejects anything that is not exactly one commit, takes the answer between the CLI's marker and its token count, and reports a CLI failure instead of hiding it |
| Build scripts | pytest, offline | 7 | local + CI | Excerpt location (both ends must match, short excerpts), whole-file downloads, the lexicon CLI refusing unknown commands, footage replacement keeping the published clip until the new one is complete and recovering from an interrupted run (`test_scripts.py`) |
| Memory budget | `scripts/measure_rss.py` | 1 gate | CI, every push | OS high-water RSS with lexicon + whisper + one transcription + a rules timeline, and a T5 timeline where the export exists, ≤ 1800 MB (measured 334 MB on Windows and 386 MB on the CI runner, both with T5, 2026-09-10) |
| Static analysis | ruff | gate | CI | Lint clean |
| Browser | pytest + Playwright (headless Chromium) against a Streamlit server the fixture starts | 26 | local + CI (skips when Chromium is not installed) | Playback recorded by the browser: the whole first sentence plays in the prescribed order, each clip on its own span, on screen; Pause cancels clips and narration, Replay starts the sentence over, Restart; a failed clip or a failed digit inside a number falls back to text and nothing plays under the wrong label; `partly` and dropped words visibly struck; the poster frame carries its label; the item card's numbers match the timeline; Space/R shortcuts with autorepeat and modifier guards; the sign-speed control changes the clip rate; narrow screens pin the signer while the spoken word is kept below it, a manual scroll up (wheel, scrollbar, Space) opts out, no pin when the panel would swallow the screen; playback estimate and progress bar; remounts release their hooks; layout fits at 375, 740×360, 800×600 and 1440 px (`tests/browser/`) |
| Browser checks by hand | the browser pane, through the panel's shadow root | per deploy | live URL | The same paths at the deployed URL after each deploy; recorded in the deploy log |
| Evaluation | `scripts/evaluate_gloss.py`, `scripts/coverage_report.py` | reports | local | Rules vs T5 on the ASLG-PC12 test split and on the curated items plus one recorded forecast (the same fixture in both reports) |
| Accessibility | axe-core in the browser + computed contrast | report | local | 0 WCAG 2.2 AA violations; all pairs ≥ 4.8:1 |

Total automated: **146 tests** (2 skip without local models, 26 without Chromium), **98 % line coverage** of `src/speak2sign` (`pytest --cov`, commit of 2026-09-10). Uncovered: the model-download branch in `asr.py`, the network error branch in `nws.py`, and three defensive lines in `rules.py` and `t5.py`.

## 3. Requirement traceability

| Requirement | Evidence |
|---|---|
| FR-01 pick an item and play | `test_demo_set.py`, `test_smoke_app.py`, `tests/browser/test_panel.py` |
| FR-02 captions synchronised | timings validated in `test_demo_set.py`; captions owned by sentence in the contract checker; highlight observed at the live URL |
| FR-03 clip per entry | contract checker: clip count per badge, every clip the lexicon's own record, exact digit/letter sequence |
| FR-04 badge on every entry | `test_provenance.py`, contract (badge enum, badge-dependent clip rule) |
| FR-05 fingerspelled letters in order | `test_rules.py` (full letter sequence), contract checker (clip sequence = characters) |
| FR-06 overrun shown, nothing skipped | ADR 0008 replaced this with interpreter pacing; `sentences[]` and rates in the contract; waiting state observed in browser checks |
| FR-07 disclaimer and attribution first | `test_smoke_app.py`, `test_timeline_contract.py::test_provenance_lists_every_source_used`, `test_provenance.py` |
| FR-08 weather lane | `test_nws.py` (offline fixture, fallback, failure), smoke test for the failure message |
| FR-09 typed text | `test_smoke_app.py`, contract tests |
| FR-10 coverage and rate shown | `test_ribbon.py::test_stats_line_names_the_engine_and_counts` |
| FR-11 dropped words struck through | contract tests (`dropped`, `partly` + `missing`), T5 omission tests, `tests/browser/test_panel.py::test_typed_lane_marks_partly_and_dropped_words_visibly` |
| FR-12 engine toggle | `test_t5.py`; engine failure message in `test_smoke_app.py`; toggle checked in the browser |
| FR-13 upload ≤ 60 s with editable transcript | `test_asr.py` (cap at exactly 60 s, alignment, upload timeline without the model, edited text clamped to the recording, real transcription when the model is present); file upload itself not automated |
| FR-14 headline lane | not built (optional) |
| FR-15 keyboard operation | `accessibility.md` §3 |
| FR-16 disclaimer content | `provenance.DISCLAIMER` asserted in the contract test |
| FR-17 uploads never stored | `asr.py` decodes in memory and returns a data URL to the uploader's own browser; no disk write exists in the module (code review); the caption in the app states exactly this boundary |
| NFR-02 memory | `measure_rss.py` in CI |
| NFR-05 licences | `test_lexicon.py`, clip `licence` carried in every timeline clip (contract) |
| NFR-06 reproducibility | pinned requirements; `training/README.md` states the unpinned parts of the recorded run; `results.json` and split indices committed |

## 4. How to run

```bash
.venv/Scripts/python -m pytest -q                       # 146 tests, ~9 min with the browser tests (several play items to the end)
.venv/Scripts/python -m playwright install chromium     # once, for tests/browser/
.venv/Scripts/python -m pytest -q --cov=src/speak2sign  # coverage
.venv/Scripts/ruff check .
.venv/Scripts/python scripts/measure_rss.py 1800        # memory gate (downloads whisper on first run)
.venv/Scripts/python scripts/evaluate_gloss.py          # rules vs T5 report
.venv/Scripts/python scripts/coverage_report.py         # rule-pass coverage per item
scripts/codex_review.sh                                 # independent review of the uncommitted change (work policy rule 5)
```

CI (`.github/workflows/ci.yml`) runs lint, tests and the memory gate on every push and pull request. A red run is visible on the PR and in the Actions history; no branch protection is configured (sole developer, trunk-based), so the gate is a signal, not a lock.

## 5. Known gaps and why they are accepted

| Gap | Why accepted | Mitigation |
|---|---|---|
| The panel's browser tests cover playback paths, not pixel layout | Screenshots drift with fonts and themes | Layout is checked with a scroll-width assertion at two viewports and by eye at the live URL |
| File upload is not driven end to end by a test | Streamlit's uploader is not scriptable from AppTest | The whole path below the widget is tested without the model (`test_upload_timeline_is_valid_and_edits_cannot_run_past_the_audio`) and with it when present |
| Intermediate commits are not individually green | The history was rebuilt in SDLC order; the pipeline commit's contract test needs the curated items from a later commit | `main` is green at every push; tags mark releasable states |
| `AppTest` takes 5–10 s per test | Streamlit component registration on first run | Timeout set to 20 s |
| No human screen-reader session | Time | Marked UNVERIFIED in `accessibility.md` |
| Safari and Firefox | No macOS available; Firefox untested | Marked UNVERIFIED in `spikes.md` |
| Deployed Python version | The host reported 3.14.7 while `runtime.txt` says 3.12 | Marked UNVERIFIED in `deployment.md` until the app's Advanced settings are confirmed |

## 6. Definition of done for any change

Code + test + docs in the same change; `ruff` and `pytest` green; memory gate green if dependencies or models changed; checked at the live URL after deploy; the delivery note states what, why, the trade-off, the ponytail review and the Codex review (work policy in `CLAUDE.md`).
