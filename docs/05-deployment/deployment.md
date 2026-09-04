# Deployment record

| Item | Value |
|---|---|
| Repository | https://github.com/sr-dotcom/speak2sign-v2 (public, `main`) |
| First push | 2026-09-03, nine commits `c7081c4..701a6bd` |
| CI | GitHub Actions `ci.yml`: ruff, pytest, `scripts/measure_rss.py` (1800 MB budget) on every push and PR |
| Host | Streamlit Community Cloud (ADR 0002) |
| Live URL | **not yet deployed** — see steps below |
| Entry point | `app.py`, Python 3.12 (`runtime.txt`), runtime deps `requirements.txt` only |

## Deploy steps (Community Cloud, once)

1. Sign in at https://share.streamlit.io with the GitHub account that owns the repo.
2. New app → repository `sr-dotcom/speak2sign-v2`, branch `main`, main file `app.py`, custom subdomain `speak2sign` (6–63 chars).
3. Advanced settings: Python 3.12. No secrets are needed for the MVP (the Guardian key, Phase 4 headline lane, would go in Secrets as `GUARDIAN_API_KEY`).
4. Deploy. First boot installs `streamlit` and `faster-whisper`; the whisper model (145 MB) is fetched on the first upload, not at boot.
5. Record the URL and commit hash in the table above and in `README.md`; run the spike 4 remote check (`docs/research/spikes.md`) at the URL: static clips served, panel plays, Play/Pause/Restart, one curated item end to end in Chrome, Edge, Firefox, Safari.

## Release procedure

- Merge to `main` (CI green) → Community Cloud redeploys automatically.
- Tag phase exits: `git tag -a v0.4.0 -m "phases 0–4"` etc. `v1.0.0` at hand-in.
- After each deploy: open the URL, play one curated item, note date, commit, and result in the log below.

## Runbook (short)

| Symptom | Action |
|---|---|
| App asleep (12 h idle) | Open the URL; wait for the wake-up; open it again the morning of the viva |
| "Forecast unavailable" | NWS API down or rate-limited; curated items and typed text still work |
| Upload transcription fails | Check the app log for the model download (first use); a WAV under 60 s is the safe format |
| Clip missing in the panel | `pytest tests/test_lexicon.py` locally: every concept's clip must exist; rebuild with `scripts/build_lexicon.py fetch` |
| Over memory | `scripts/measure_rss.py` locally; the only large resident is whisper (measured 334 MB) |

## Deploy log

| Date | Commit | Result |
|---|---|---|
| 2026-09-03 | 701a6bd | Pushed to GitHub; CI run pending; Community Cloud deploy pending (needs the owner's sign-in) |
