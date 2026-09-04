# Phase 0 spikes

Results of the four de-risking spikes from `docs/00-execution-plan.md` §1.3. Each entry states what was run, what was observed, and what it changes.

## Spike 1 — CATS "ASL Dictionary" on archive.org — DONE 2026-09-03

**Run:** `python scripts/spike_cats_sample.py <out> 10` (advancedsearch API + metadata API + 10 downloads).

| Question | Result |
|---|---|
| Collection size | `numFound` = **24,682** items by "Center for Accessible Technology in Sign" |
| Rights field | **"Public Domain" on 50 of 50** sampled search hits and on all 10 downloaded item metadata records; `licenseurl` empty; uploader account consistent with CATS (Harley Hamilton) |
| Video format | Every item has an `.ia.mp4` derivative at **854×480, 30 fps, H.264**, 80 KB–1.1 MB, 1.3–12.3 s; and an original `.mp4` at 960×540 (2–6 MB) |
| Signer quality | Frames from 10 clips: studio lighting, plain blue backdrop, black or dark top, waist-up framing, three different adult signers across the sample. Consistent and clean. Whether signers are Deaf is **UNVERIFIED** (the collection's description only says "ASL vocabulary"); CATS is a Georgia Tech / Atlanta Area School for the Deaf unit. |
| Titles | Keyed by English word or phrase, sometimes several synonyms in one title (`curse,cuss,swear,salty`), sometimes with a sense hint (`dazzle, blind`, `police-verb`). Many multi-word idioms. |
| Weather / news words | Title probes found items for `rain` (drizzle, driving pour), `storm`, `president`, `government`, `police`, `weather` (front, brutal-weather). `election` only as `runoff-election` → check `vote`/`elect`. |
| Letters and digits | Title search for single letters and digits returns phrase hits, not letter entries. **Not found by this probe**; may exist under other titles. Treat as absent. |

**Changes:** CATS is confirmed as primary clip source (ADR 0007 stands). Use the `.ia.mp4` derivative directly (already ≤ 1.1 MB, 480p): no transcoding step. Fingerspelling letters and digits come from **Signbank** (spike 2). The lexicon builder must parse comma-separated synonyms and sense hints in titles.

## Spike 2 — ASL Signbank per-entry access — DONE 2026-09-03

**Run:** fetched `https://aslsignbank.com/static/ecv/asl.ecv` (1,148,885 bytes, **4,526 entries**, each with `CVE_ID`, ID-gloss, and a keyword description); fetched entry and video URLs with Python `urllib`.

| Question | Result |
|---|---|
| Entry URL pattern | `https://aslsignbank.com/dictionary/gloss/<CVE_ID>.html` (e.g. 1011 → "Sign for RAIN") |
| Video URL pattern | `/dictionary/protected_media/glossvideo/ASL/<first two letters of gloss>/<GLOSS>-<CVE_ID>.mp4` (e.g. `/ASL/RA/RAIN-1011.mp4`) |
| Download without login | **HTTP 200, video/mp4, 191,521 bytes** for RAIN-1011; 656×370, 24 fps, 2.8 s; teal background (not a draft) |
| Conditions page | "If you're using a video, please add a direct weblink when you share the video"; sharing by "right-clicking on the video and saving that to your computer (note that is a very compressed version ideal for websites)" is listed as permitted; "Please do not use any draft image or video in your disseminated work. Drafts are those that are not produced using the teal background."; no statement on automated access |
| Weather / news glosses present | RAIN, RAINFALL, STORM, HURRICANE, TORNADO8, WIND, CLOUDneut, SNOW (several variants), SUN (variants), COLD, COOL-WEATHER, WEATHER, CLIMATE, WINTER, SUMMER, PRESIDENT, VICE-PRESIDENT, GOVERNMENT, FEDERAL, SENATE, SENATOR, GOVERNOR, LEGISLATURE, VOTE, POLICE (three variants) |
| Letters and digits | ECV has `ONE` (CVE 519); letter glosses need a targeted look-up in Phase 1 (search the ECV for single-letter glosses and fingerspelled-loan entries) |

**Changes:** Signbank is a workable secondary source at ~20–60 entries with a polite, rate-limited fetch (1 request/s, `User-Agent` naming the project), each recorded with its entry weblink and the citation string. Do not bulk-scrape.

## Spike 3 — T5-small → CTranslate2 int8 on CPU without torch — DONE 2026-09-04

Measured 2026-09-03 while building the demo set: faster-whisper `base.en` int8 loads in 6.2 s at 191 MB RSS and peaks at **507 MB RSS** while transcribing a 300 s newscast (about 6 s per newscast on the developer's laptop). CTranslate2 4.8.2 ran without torch installed. `scripts/measure_rss.py` (lexicon + whisper + one 27 s transcription) peaks at **334 MB** on Windows; CI enforces 1800 MB. T5 half: trained on the developer's RTX 4080 (17 min, 3 epochs), exported with CTranslate2 int8 → **62.3 MB folder** (model.bin 61 MB, spiece.model, shared vocabulary); in the runtime venv with only `ctranslate2` + `sentencepiece` it loads in **0.15 s**, adds **86 MB RSS** (25 → 111 MB), and translates a sentence in **32–71 ms**. Published as GitHub Release `v0.5.0-t5`; the app fetches it when `T5_RELEASE_URL` is set. Evaluation: `docs/04-testing/evaluation.md`.

## Spike 4 — components v2 with two `<video>` elements, and static serving — LOCAL PART DONE 2026-09-03

**Run:** the interpreter panel (`src/speak2sign/ui/panel.*`) mounted through `st.components.v2.component` (Streamlit 1.62.0, `isolate_styles=True`), checked in the browser pane on Windows/Chromium.

| Question | Result |
|---|---|
| Two `<video>` elements inside the component | Yes: double-buffered, hidden one preloads the next clip, `currentTime`/`playbackRate`/`play()` all work; DOM check showed readyState 4, 854×480 frames advancing |
| Static clips via `server.enableStaticServing` | Yes: `/app/static/clips/*.mp4` served with **206 Partial Content** (range requests, so seeking to `in_s` is cheap) |
| Autoplay after one click | Yes: the Play button's gesture starts both the browser voice (speechSynthesis) and the muted video |
| Shadow DOM gotcha | Author `display:flex` beats the UA `[hidden]` rule inside the shadow root; the panel CSS now has `.s2s [hidden]{display:none!important}` |
| Component caching gotcha | `st.cache_resource` on the component means CSS/JS edits need a server restart, not a page reload |
| Interpreter pacing | Observed: sentence 1 narrated, then "Waiting for the interpreter…" until the panel finished, then sentence 2 |

**Remote part DONE 2026-09-04** at https://speak2sign.streamlit.app (Chromium): clips and news audio served with 206 from `/~/+/app/static/…` (relative URLs resolved through `document.baseURI` worked unchanged), curated item played with caption highlight and the waiting state, weather lane fetched live. The app is embedded in a same-origin iframe on the Community Cloud page, which matters only for automation. **Still not run:** Safari and Firefox.

Local part can run once the panel skeleton exists; the Community Cloud part needs the first deploy. Record: autoplay behaviour after one click in Chrome, Edge, Firefox, Safari; that `/app/static/clips/x.mp4` serves with `video/mp4`.

## Local environment — DONE 2026-09-03

`.venv` with `requirements-dev.txt`; `ruff check .` clean; `pytest` 1 passed (AppTest smoke: app loads, disclaimer present). Python 3.12.10 on Windows 11.
