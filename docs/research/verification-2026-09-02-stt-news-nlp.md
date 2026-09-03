# Free-resource verification — speech-to-text, news sources, NLP, front-end (verified 2026-09-02)

Produced by the speech/NLP research pass for `docs/00-execution-plan.md`. "Search-only" = the official page was blocked or timed out; facts come from search snippets of the official page and are flagged.

## A. Speech-to-text

| # | Resource | URL | Key facts | Licence | Status |
|---|---|---|---|---|---|
| A1 | faster-whisper | pypi.org/pypi/faster-whisper/json; github.com/SYSTRAN/faster-whisper | v1.2.1 (2025-10-31), Python ≥ 3.9. Deps: ctranslate2, huggingface-hub, tokenizers, onnxruntime, av, tqdm, transformers — **no torch**. CT2 model sizes (HF Systran/*): tiny 75.5 MB, base 145 MB, small 484 MB. README RAM: small int8 CPU beam5 = 1,477 MB. tiny/base int8 RAM not published. CTranslate2 4.8.2 on PyPI, MIT. | MIT | Verified; tiny/base RAM UNVERIFIED |
| A2 | whisper.cpp WASM | github.com/ggml-org/whisper.cpp; ggml.ai/whisper.cpp/ | MIT. README mem table: tiny 75 MiB disk / ~273 MB RAM, base 142 / ~388, small 466 / ~852. Quantised: tiny-q5_1 32.2 MB, base-q5_1 59.7 MB, small-q5_1 190 MB. Browser demo: ~2–3× realtime for tiny/base, max 120 s audio in the example, greedy only, needs WASM SIMD. | MIT | Verified; COOP/COEP UNVERIFIED |
| A3 | Web Speech API | MDN SpeechRecognition (+ start); browser-compat-data; caniuse; developer.chrome.com/blog/new-in-chrome-139 | Chrome 33+ (webkit prefix), Edge mirrors Chrome, Safari 14.1+, Firefox 142 behind a pref — effectively no Firefox. caniuse 87.6%. MDN: "On some browsers, like Chrome … audio is sent to a web service". Chrome 139 added `processLocally`. **`start(audioTrack)` — Chrome 135+ only**: a playing `<video>` can be transcribed via `captureStream()` in Chrome ≥ 135; Safari/Firefox mic-only. | Browser built-in | Mostly verified; HTTPS strictness and continuous timeout UNVERIFIED |
| A4 | Vosk | alphacephei.com/vosk/models; pypi vosk 0.3.45 (2022-12-22) | Offline, CPU. `vosk-model-small-en-us-0.15` 40 MB, `en-us-0.22-lgraph` 128 MB, `en-us-0.22` 1.8 GB. No torch. | Apache-2.0 | Verified; RAM UNVERIFIED |
| A5 | HF Inference Providers | huggingface.co/docs/inference-providers/pricing | Free accounts: **$0.10/month** credits ("subject to change"). | service | Verified — not reliable for a live demo |

## B. News sources

| # | Source | URL | Key facts | Terms | Status |
|---|---|---|---|---|---|
| B1 | BBC RSS | bbc.co.uk/news/10628494; feeds.bbci.co.uk; bbc.co.uk/usingthebbc/terms-of-use | All BBC hosts blocked from the research environment. | UNVERIFIED | UNVERIFIED |
| B2 | NPR | feeds.npr.org/500005/podcast.xml (News Now); feeds.npr.org/1001/rss.xml; npr.org terms; npr.github.io/content-distribution-service | **NPR News Now**: hourly, first item "09-02-2026 1PM EDT", MP3 enclosure (280 s). Channel copyright "For Personal Use Only". Story API retired; CDS API "exclusively for Members of the NPR Network". Terms page timed out 3×; snippets: podcasts "only for personal, noncommercial use… may link to podcasts from your site". | Personal/non-commercial; linking OK, redistribution not | Feeds verified; terms search-only |
| B3 | Reuters / AP | search only | Reuters ended official RSS June 2020; AP offers no official RSS. | No free licensed feed | Search-only |
| B4 | Guardian Open Platform | open-platform.theguardian.com/access/ (blocked); groups.google.com/g/guardian-api-talk; freeapi.watch/the-guardian/ | Free developer key, no card. Guardian staff (2023-01-31): "5000 calls per day and a maximum of 12 per second", later "recently revised"; freeapi.watch (2026) says 500/day. Staff 2023 and 2025-02-05: "No problem" for student/teaching use if not commercialised. Full text via `show-fields=body`/`bodyText`. | Non-commercial; attribution/link | Limits UNVERIFIED |
| B5 | NewsAPI.org / GDELT | newsapi.org/pricing; gdeltproject.org/about.html; blog.gdeltproject.org/gdelt-doc-2-0-api-debuts | NewsAPI Developer: 100 req/day, 24 h delay, **"cannot be used in a staging or production environment"**. GDELT DOC 2.0: no key, title/URL/date/image; "unlimited and unrestricted use for any academic, commercial, or governmental use… without fee", cite + link; throttle 1 req/5 s/IP (search-only). | NewsAPI dev-only; GDELT free with attribution | Verified (GDELT rate limit search-only) |
| B6 | VOA | voanews.com/p/5338.html; /terms-use-and-privacy-notice; /rssfeeds; /podcast/?zoneId=7982 | Terms: "All text, audio and video material produced exclusively by the Voice of America is in the public domain"; credit "voanews.com, Voice of America, or VOA". AFP/AP/Reuters material "shall not be published, broadcast… or redistributed". **Homepage and RSS newest items are 2025-03-15** — site frozen since the March 2025 shutdown; litigation ongoing. "Worldwide in Five" feed has zero items. | Public domain (VOA-produced) with attribution | Terms verified; content not updating |
| B7 | Wikinews | en.wikinews.org/wiki/Wikinews:Copyright | **Closed**: read-only from 2026-05-04. Archive via MediaWiki API. CC BY 4.0 (from 2024-12-16), CC BY 2.5 earlier. Text only. | CC BY | Verified — archive only |
| B8 | Hourly audio briefs | feeds.megaphone.fm/ESP9792844572 (ABC News Update); NPR News Now | ABC: 150 s MP3, "Copyright 2026, ABC Audio. All rights reserved." NPR: personal use only. | No permissive live audio brief found | Feeds verified |

## C. Text-to-gloss / NLP

| # | Resource | URL | Key facts | Licence | Status |
|---|---|---|---|---|---|
| C1 | spaCy en_core_web_sm | github.com/explosion/spacy-models/releases/tag/en_core_web_sm-3.8.0 | v3.8.0 (2024-09-30), 12 MB, CPU-optimised | MIT | Verified |
| C2 | Rule-based EN→ASL gloss repos | api.github.com | `sign-language-processing/spoken-to-signed-translation` — 98★, pushed **2026-07-23**, MIT, rule-based reorder/drop text→gloss. `sign-language-translator/sign-language-translator` — 372★, 2024-09, Apache-2.0 (Pakistan SL). `rt3115/English-To-ASL-Gloss` — 2020, MIT. `monkeyhippies/lang2sign` — 2023, MIT. | MIT / Apache-2.0 | Verified |
| C3 | Gloss datasets | huggingface.co/datasets/achrafothman/aslg_pc12; achrafothman.net/site/asl-smt/; huggingface.co/datasets/ncslgr/ncslgr | ASLG-PC12: 87,710 pairs, 12.8 MB, **CC BY-NC 4.0** (HF tag and author site agree; a Kaggle mirror claims CC0 — ignore). Synthetic, parliamentary text. NCSLGR on HF: < 1K rows, tagged MIT (loader); original BU corpus terms not found. | CC BY-NC 4.0 | Verified; NCSLGR terms UNVERIFIED |
| C4 | difflib / rapidfuzz | pypi.org/project/rapidfuzz | difflib stdlib. rapidfuzz 3.14.6, MIT, wheels 1.7–3.2 MB. | MIT | Verified |

## D. Front-end compositing

| # | Question | URL | Answer | Status |
|---|---|---|---|---|
| D1 | Two `<video>` elements in sync, no library | MDN Autoplay guide; MDN `<video>` | Yes. Autoplay succeeds only if muted, or after a user gesture, or allowlisted; `play()` rejects with `NotAllowedError`. Pattern: one Play button → `Promise.all([news.play(), sign.play()])`; sign clips as a queue switching `src` on `ended`, or N hidden preloaded `<video>` elements swapped; `preload="auto"` on the next clip; drive sync from `news.currentTime` on `timeupdate` (~4 Hz) or `requestAnimationFrame`. | Verified |
| D2 | Streamlit / Gradio | docs.streamlit.io custom-components, st.components.v2.component, release notes; gradio.app/docs/gradio/html | `components.v1.html` deprecated since 1.56. **Components v2** (`st.components.v2.component(name, html=, css=, js=)`): GA in 1.51.0 (2025-10-29), frameless, JS runs "with normal app-page DOM privileges". Streamlit 1.62.0 (2026-08-19). Gradio `gr.HTML(js_on_load=…)` also works. | Verified |

## UNVERIFIED

- BBC RSS terms (all BBC hosts blocked).
- Guardian developer-key daily cap: 500/day vs 5,000/day.
- NPR Terms of Use text (timed out); whether Personal-Use bars a public demo embedding the MP3.
- faster-whisper tiny/base int8 RAM; Vosk RAM.
- whisper.wasm COOP/COEP requirement.
- Web Speech: strict HTTPS requirement, continuous-mode cap, Edge's engine.
- VOA: whether any English audio/video feed resumes in 2026.
- NCSLGR original corpus (BU) terms.
- Reuters/AP: only search evidence that no official free RSS exists.
- Streamlit v2 minimum version: 1.51.0 GA vs a 2026 note mentioning 1.57.0 (likely a style-isolation change).
