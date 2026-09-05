# scripts/

Build steps, dev tools and report generators. Nothing here is imported by the deployed app. Run from the repo root with the environment named in the table.

| Script | Runs when | Environment | Reads | Writes |
|---|---|---|---|---|
| `vocab_seed.py` | Once, to seed the vocabulary; re-run after editing its word blocks | dev | ASL-LEX `signdata.csv` (optional) | `data/lexicon/target_vocab.csv` |
| `build_lexicon.py plan` | After the vocabulary or `overrides.json` changes | dev | `target_vocab.csv`, `overrides.json`, archive.org and Signbank APIs (1 request/s) | `data/lexicon/candidates.json` |
| `build_lexicon.py fetch` | After `plan` | dev | `candidates.json` | `static/clips/`, `static/letters/`, `data/lexicon/concepts.json`, `attribution.json` |
| `review_frames.py` | After `fetch`, before marking clips attested | build (opencv) | `concepts.json`, `static/` | `docs/research/clip-review-*.jpg` |
| `clip_durations.py` | After `fetch` | build (opencv) | `concepts.json`, `static/` | `duration_s`, `in_s`, `out_s` into `concepts.json` |
| `build_demo_set.py` | After `data/demo/excerpts.json` changes | build (faster-whisper) | `excerpts.json`, Internet Archive MP3s | `static/news/*.wav`, `data/demo/<id>.json` |
| `measure_rss.py` | Every CI run; locally before dependency changes | dev | `static/news/california-fire-warning.wav`, whisper model | exit 1 over budget |
| `coverage_report.py` | After lexicon or rule changes | dev | curated items, lexicon | `docs/04-testing/coverage-rules.md` (generated) |
| `evaluate_gloss.py` | After T5 training or rule changes | dev (+ T5 export for the T5 column) | curated items, `training/results/results.json` | `docs/04-testing/evaluation.md` (generated) |
| `spike_cats_sample.py` | Once (spike 1, 2026-09-03); kept so the spike is reproducible | dev | archive.org API | a sample folder outside the repo |

Environments: dev = `requirements-dev.txt`; build = `requirements-build.txt` (adds opencv, faster-whisper, psutil). Training scripts live in `training/`.
