# Deployment record

| Item | Value |
|---|---|
| Repository | https://github.com/sr-dotcom/speak2sign (public, `main`) |
| First push | 2026-09-03, nine commits `c7081c4..701a6bd` |
| CI | GitHub Actions `ci.yml`: ruff, pytest, `scripts/measure_rss.py` (1800 MB budget) on every push and PR |
| Host | Streamlit Community Cloud (ADR 0002) |
| Live URL | **https://speak2sign.streamlit.app** (deployed by the owner 2026-09-04) |
| Entry point | `app.py`, runtime deps `requirements.txt` only. Python: `runtime.txt` asks for 3.12 and CI runs 3.12, but the host reported **3.14.7** on 2026-09-04 (log below); the version is set in the app's Advanced settings and has not been confirmed since. Until it is, the deployed runtime is UNVERIFIED as 3.12 |

## Deploy steps (Community Cloud, once)

1. Sign in at https://share.streamlit.io with the GitHub account that owns the repo.
2. New app → repository `sr-dotcom/speak2sign`, branch `main`, main file `app.py`, custom subdomain `speak2sign` (6–63 chars).
3. Advanced settings: Python 3.12. Secrets (Manage app → Settings → Secrets, TOML): `T5_RELEASE_URL = "https://github.com/sr-dotcom/speak2sign/releases/download/v0.5.0-t5/t5_gloss_ct2.zip"` enables the T5 toggle (53 MB download on first use). The Guardian key for the optional headline lane would be `GUARDIAN_API_KEY`.
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
| Over memory | `scripts/measure_rss.py` locally: peak with lexicon + whisper + one transcription (334 MB on Windows, 316 MB in CI) plus T5 when its export is present (+86 MB measured 2026-09-04) |

## Deploy log

| Date | Commit | Result |
|---|---|---|
| 2026-09-03 | 701a6bd | Pushed to GitHub; CI green (peak RSS 316 MB on the Linux runner) |
| 2026-09-04 | f2bcfd9 | Community Cloud deploy live at https://speak2sign.streamlit.app. Remote check in Chromium: static clips and news audio served with 206 from `/~/+/app/static/`, curated item plays with caption highlight and the waiting state, live weather lane fetched a forecast issued 2026-09-04 18:36 and rendered 153 chips. The app runs inside a same-origin iframe on the Community Cloud page. Cloud-side 403/404 on `/api/v2/user/details` are the host's own calls, not ours. |
| 2026-09-04 | 8f68c46 | CI green (T5 path). Redeploy booted with `ctranslate2` and `sentencepiece` pinned. **Observed Python 3.14.7 on the host** although `runtime.txt` says 3.12 (the Community Cloud version is chosen in the app's Advanced settings, which override the file): CI tests on 3.12, so the owner should set 3.12 in Manage app → Settings to match. Upload lane on 3.14 UNVERIFIED. |
| 2026-09-10 | 44ceab1 | CI green on the audit commits (a841c49, 326c6b3, 44ceab1). App had gone to sleep; woke in about a minute and redeployed. Live check through the panel's shadow root: Samoa item plays, captions are the source words verbatim with function words struck, sign label follows the clip (fingerspelling Q-U-O-T-E at 2.0×), waiting state between sentences. Footer still reports **Python 3.14.7** on the host: the Advanced-settings version remains to be set by the owner (UNVERIFIED as 3.12). |
| 2026-09-10/11 | c17a36c, 97eacab, da2b8a2 | CI green (memory gate now loads T5 from the release: peak 386 MB on the runner). For 15 minutes after the push the host kept serving the previous build; it then went to sleep and, woken at 22:58, booted from current `main`. Live check with the tab visible: Samoa item plays, the sign label changes exactly with its clip (NIGHT, SUNDAY, then S-A-M-O-A letter by letter, every clip readyState 4), Pause and Restart behave. The page shows no commit id, so the build is identified by Cloud's boot-from-main behaviour, not read from the page. Python still 3.14.7 on the host (owner setting). |
