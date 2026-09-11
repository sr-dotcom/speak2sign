# scripts/

Build steps, dev tools and report generators. Nothing here is imported by the deployed app. Run from the repo root with the environment named in the table. Every generated file carries a header naming its producer.

| Script | Runs when | Environment | Reads | Writes |
|---|---|---|---|---|
| `seed_vocab.py` | Once, to seed the vocabulary; re-run after editing its word blocks | dev | ASL-LEX `signdata.csv` (optional) | `data/lexicon/target_vocab.csv` |
| `build_lexicon.py plan` | After the vocabulary or `overrides.json` changes | dev | `target_vocab.csv`, `overrides.json`, archive.org and Signbank APIs (1 request/s) | `data/lexicon/candidates.json` |
| `build_lexicon.py fetch` | After `plan` | dev | `candidates.json` | `static/clips/`, `static/letters/`, `data/lexicon/concepts.json`, `attribution.json`; exit 1 if any fetch failed |
| `make_contact_sheets.py` | After `fetch`, before marking clips attested | build (opencv) | `concepts.json`, `static/` | `docs/research/clip-review-*.jpg` (old sheets removed first) |
| `measure_clip_spans.py` | After `fetch` | build (opencv) | `concepts.json`, `static/` | `duration_s`, `in_s`, `out_s` into `concepts.json` |
| `build_demo_set.py` | After `data/demo/excerpts.json` changes | dev (faster-whisper) | `excerpts.json`, Internet Archive MP3s | `static/news/*.wav`, `data/demo/<id>.json` |
| `example_timeline.py` | After `timeline.py` or the schema changes | dev | one curated item, lexicon | `contracts/example.timeline.json` |
| `measure_rss.py` | Every CI run; locally before dependency changes | dev | `static/news/california-fire-warning.wav`, whisper model, T5 export if present | exit 1 over budget |
| `coverage_report.py` | After lexicon or rule changes | dev | curated items, `tests/fixtures/nws_forecast.json`, lexicon | `docs/04-testing/coverage-rules.md` (generated) |
| `evaluate_gloss.py` | After T5 training or rule changes | dev (+ T5 export for the T5 column) | curated items, the same forecast fixture, `training/results/results.json` | `docs/04-testing/evaluation.md` (generated) |
| `codex_review.sh [commit]` | Before every commit (work policy rule 5) | Codex CLI, logged in | the diff, `AGENTS.md`, `CLAUDE.md` | review to stdout, recorded in the delivery block |
| `spike_cats_sample.py` | Once (spike 1, 2026-09-03); kept so the spike is reproducible | dev | archive.org API | `spike_out/` under the current directory (git-ignored) |

Environments: dev = `requirements-dev.txt` (includes the runtime set: faster-whisper, psutil; Playwright for `tests/browser/`, plus `python -m playwright install chromium` once); build = `requirements-build.txt` (dev plus opencv). Training scripts live in `training/`.
