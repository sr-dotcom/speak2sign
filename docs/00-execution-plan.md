# Speak2Sign v2 — News Interpreter Panel: Execution Plan

**Date:** 2026-09-02 · **Status:** Proposed, awaiting developer approval
**Authors:** SME planning team (accessibility & Deaf studies, ML, full-stack, DevOps/cost, SDLC PM)
**Builds on:** `../../speak2sign/CLAUDE.md`, `docs/00-project-reflection.md`, ADR 0001–0003 and `docs/research/*` in the previous iteration. Every decision there is **kept** or **superseded** below, with a reason.

**What is being built.** A web page that does what the interpreter in the corner of a TV news bulletin does: a news item plays on the left, and a panel on the right shows the same content in American Sign Language (ASL), from recorded clips of Deaf signers, in time with the narration. Every sign carries a visible badge: validated, fingerspelled, or not available.

**Assumptions the developer must confirm** (marked ⚑ throughout):
- ⚑A1 Submission/viva date is **2026-10-30** (8 weeks from 2026-09-07). Adjust the phase table if not.
- ⚑A2 The module marks a **deep-learning component**; the English→gloss T5 model is that component (carried from the 2026-09-01 planning session, not from any document in the repo).
- ⚑A3 Sole developer, ~4 working days/week.
- ⚑A4 Target language is ASL.

---

## 1. Execution plan (read this first)

### 1.1 Critical path

```
Week 1: hello-world DEPLOYED + CI ──► clip source confirmed (CATS PD sample) ──► lexicon built
  └─► Weeks 2–3: text → gloss → timeline (rules first, T5 second) ──► DEPLOYED text + live weather
        └─► Weeks 4–5: interpreter panel synced to media + curated news items ──► DEPLOYED "it signs the news"
              └─► Week 6: upload mode (faster-whisper) + headline mode
                    └─► Week 7: evaluation + tests ──► Week 8: docs, demo recording, buffer
```

Earliest public deployment: **day 3** (a skeleton page on Streamlit Community Cloud). Everything else is built behind that URL, so something is always live.

### 1.2 Phase table

| Phase | Dates (⚑A1) | Effort (dev-days) | Documents written BEFORE code | Deliverables | Exit criteria | Top risk → mitigation |
|---|---|---|---|---|---|---|
| **0 Requirements & de-risk** | 09-07 → 09-13 | 4 | PRD (`docs/01-requirements/prd.md`); ADR 0004 (scope); this plan approved | Repo scaffold; hello-world app live on Community Cloud with a GitHub Actions gate; **four spikes** with written results in `docs/research/spikes.md`: (1) CATS archive.org sample of 30 clips: rights field, signer quality, letter/digit coverage; (2) Signbank per-entry download within its stated conditions; (3) `t5-small` → CTranslate2 int8 runs on CPU with only `ctranslate2` + `sentencepiece`; (4) `st.components.v2` page playing two `<video>` elements in sync after a click | URL live; CI green; spike results written | CATS quality unacceptable → Signbank primary with polite per-entry fetch (~200 entries) |
| **1 Design & lexicon** | 09-14 → 09-20 | 4 | TRD (`docs/02-design/system-design.md`); data model; `contracts/timeline.schema.json`; ADR 0005–0008 | Target vocabulary (~150–200 signs) ranked by ASL-LEX subjective frequency; lexicon index (keyword → concept → clip file, source, licence, badge); clips fetched, trimmed, normalised, committed under `static/clips/`; `attribution.json` generated | Every target sign has a clip or an explicit fingerspell / not-available row; coverage ≥ 85% on the demo scripts | Coverage < 85% → extend vocabulary (CATS has 24k entries, so this is cheap) or narrow the scripts |
| **2 Core pipeline** | 09-21 → 10-04 | 8 | Pipeline test plan; training protocol | `text → gloss (rules) → lexicon → timeline JSON`; T5-small fine-tuned on ASLG-PC12 on Kaggle, exported to CTranslate2 int8, wired behind a feature flag; live weather lane from the NWS API; unit tests | Deployed: type text or fetch the forecast, see the gloss ribbon with badges; T5-vs-rules comparison table exists | 2.7 GB RAM ceiling → `scripts/measure_rss.py` in CI; T5 int8 ≤ 100 MB resident |
| **3 Interpreter panel** | 10-05 → 10-11 | 5 | UI spec; revised resolution-cases table | Side-by-side layout: news media + captions left, ASL panel right; clips scheduled from the timeline; per-sign badge; overrun indicator; disclaimer and attribution at first exposure; 5–8 curated VOA newscast items with corrected transcripts and timings | Deployed: a VOA item plays and the panel signs it; demo script runs twice end-to-end without intervention | Sync drift → schedule from media `currentTime`, never wall clock; preload the next clip |
| **4 Inputs** | 10-12 → 10-18 | 4 | ADR for runtime ASR; upload constraints | Upload ≤ 60 s clip → faster-whisper `base.en` int8 → same pipeline; live headline mode from the Guardian Open Platform (key in Community Cloud secrets), GDELT titles as keyless fallback; fingerspelling-rate meter | Deployed full pipeline; peak RSS with whisper loaded < 1.8 GB | Whisper load time on 0.078 cores → lazy load, cache, cap length |
| **5 Evaluation & hardening** | 10-19 → 10-25 | 5 | Test strategy (`docs/04-testing/`) | pytest suite; evaluation report: BLEU/chrF on the ASLG-PC12 test split (T5 vs rules), lexical coverage and fingerspelling rate on the demo set, latency table; accessibility check (keyboard, captions, contrast) | CI runs tests + ruff + RSS budget; numbers in `docs/04-testing/evaluation.md` with a reproduction command | T5 worse than rules on real news → report it, ship rules as default, T5 as a toggle |
| **6 Hand-in** | 10-26 → 10-30 | 3 | Deployment doc; reflection | README; `docs/05-deployment/`; demo script; screen-recorded backup; tag `v1.0.0` | §9 checklist all true | App asleep at the viva → open the URL that morning; play the recording if needed |

Total **33 dev-days** in 8 weeks at 4 days/week (32 available). Cut order if behind: headline mode, then the T5 toggle. The app still signs the news without either.

### 1.3 Start-tomorrow checklist (Phase 0, in order)

1. Push the empty repo to a **public** GitHub repository (required for Community Cloud and free Actions minutes).
2. Create the folder tree in §5. Copy nothing from `legacy/`.
3. `app.py` with a title and the disclaimer block; `requirements.txt` = `streamlit==1.62.0`; `.github/workflows/ci.yml` running `ruff check` and `pytest`.
4. Deploy on Community Cloud; record the URL, date, and commit in `docs/05-deployment/deployment.md`.
5. Spike 1: query `https://archive.org/advancedsearch.php?q=creator:("Center for Accessible Technology in Sign")&fl[]=identifier,title,rights&output=json&rows=50`; download 30 clips; record rights field, resolution, signer consistency, whether A–Z and 0–9 exist.
6. Spike 2: on aslsignbank.com read `/about/conditions/`; download one compressed clip for a sign CATS lacks; record the URL pattern and the citation string.
7. Spike 3: in a Kaggle notebook run `ct2-transformers-converter --model google-t5/t5-small --output_dir t5_ct2 --quantization int8`; download; locally `pip install ctranslate2 sentencepiece` only; generate one line; record RSS and latency.
8. Spike 4: `st.components.v2.component` page with two `<video>` tags and a JS scheduler on `timeupdate`; confirm click-to-start satisfies autoplay policy in Chrome, Edge, Firefox, Safari.
9. Write the PRD from §2; open ADR 0004.

---

## 2. Scope definition (Step 1)

### 2.1 What "news" means here

| Candidate | Feasibility (1 dev, 8 weeks) | Free-tier fit | Viva demo quality | Vocabulary coverage | Verdict |
|---|---|---|---|---|---|
| **A. Live broadcast stream** | Low: no legal free live stream, live ASR on 0.078–2 cores, open vocabulary | Poor | High if it works, catastrophic if not | 50–70% → fingerspelling-heavy | **Rejected** |
| **B. Curated pre-recorded news items** (public-domain VOA newscast audio, corrected transcript, timings) | High | Excellent (a few MB in the repo) | High and deterministic | Controllable: items chosen so the lexicon covers them | **Chosen for the MVP demo** |
| **C. Live text feed**: NWS forecast API (public domain, JSON, no key) rendered as a weather segment with a browser-voice narrator (`speechSynthesis`, native, free) | High | Excellent | Good, and genuinely live | 85–95% (bounded weather lexicon) | **Chosen as the live lane** |
| **D. Live headline text** from the Guardian Open Platform (free developer key, non-commercial) with GDELT titles (keyless) as fallback | High | Excellent | Medium, text only | 50–70% | **Stretch (Phase 4)**, fingerspelling rate displayed |
| **E. User-uploaded clip ≤ 60 s** | Medium: needs server ASR | Fits with `base.en` int8 | Medium | Unbounded | **Phase 4**, shows generality honestly |

Why not "any news"? The previous iteration measured lexical coverage at roughly 50–70% of content tokens on open-domain English versus 85–95% in a bounded domain (old repo, `docs/research/asl-linguistics-findings.md`). A panel that fingerspells one word in three is a spelling bee, not an interpreter. The bulletin **format** is open; the **lexicon** is bounded, and the coverage number is shown on screen.

### 2.2 Minimum viable product

A public web page where a viewer picks a news item from a curated set, or the live weather segment, presses play, and sees the news media with captions on the left and an ASL panel on the right that plays recorded Deaf-signer clips in time with the narration. Each sign carries a badge: validated, fingerspelled, or not available. The page states its sources and licences and that it is not a substitute for a human interpreter. It costs nothing to run and is deployed from `main` by CI.

### 2.3 Stretch goals, in order

1. Upload-your-own clip (Phase 4).
2. Live headline mode (Guardian API) with a fingerspelling-rate meter (Phase 4).
3. T5 gloss model as a user toggle, with the comparison table in-app (Phases 2 and 5).
4. Directional-verb retargeting in pose space: **not this term**; future work.

### 2.4 Team dissent, recorded

- **Deaf-studies specialist:** a news panel is closer to the "live signing" the WFD/WASLI statement cautions against than a static kiosk was. Accepted on three conditions: disclaimer at first exposure, provenance per sign, and framing as a research demonstration of retrieval rather than a service. **Adopted.**
- **ML engineer:** T5 on ASLG-PC12 will score high on its own test split and poorly on real news, because the corpus glosses are rule-generated. Wants rules as default. **Adopted**; T5 ships behind a toggle with the honest comparison.
- **Deaf-studies specialist, again:** CATS clips are keyed by English word, which is the "tyranny of glossing" problem. **Partially adopted**: the lexicon keys on a concept id, the CATS title is one keyword among several, and ambiguous words (PRESENT, RUN, BACK) are resolved by a hand-written sense table for the target vocabulary.
- **Product strategist:** open headlines are the demo that lands. **Partially adopted**: curated newscast items are the MVP; headlines are Phase 4.

---

## 3. Resource inventory (Step 2)

Verification date is 2026-09-02 unless stated. "Prior" = verified 2026-08-30 in the previous iteration.

### 3.1 Sign language sources

| Resource | Contains | Licence (quoted from the fetched page) | Redistribute in a public app? | Bulk access | Verified |
|---|---|---|---|---|---|
| **CATS "The ASL Dictionary"** (Center for Accessible Technology in Sign, Georgia Tech / Atlanta Area School for the Deaf) on archive.org | **24,682 items**, one isolated-sign MP4 each (~1–2 MB) | Rights field: **"Public Domain"** on every sampled item (7 of 7) | **Yes**. Credit CATS / Harley Hamilton anyway | Yes: archive.org advancedsearch JSON + per-item download URLs | 2026-09-02 |
| **ASL Signbank** (aslsignbank.com; the Yale host redirects here) | 3,702 signs, 2,848 publicly browsable (count from the Hamburg LR mirror, UNVERIFIED on the site itself); ECV keyword index at `static/ecv/asl.ecv`, free | "This work is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License." Conditions page: users "may link directly to entries, download compressed versions, or request high-quality files from Julie Hochgesang"; "add a direct weblink when you share the video"; do not use draft (non-teal-background) videos. Citation string: "Julie A. Hochgesang, Onno Crasborn, and Diane Lillo-Martin. (2017-2026). ASL Signbank. https://aslsignbank.com." | **Yes**, non-commercial, attribution, share-alike, weblink per clip | **No API or bulk export**; per-entry download; HQ by request | 2026-09-02 |
| ASL-LEX 2.0 | 2,723 signs, phonology and subjective frequency, CSV | "The ASL-LEX database ... (excluding sign reference videos) are licensed under ... CC BY-NC 4.0"; videos "cannot be 'saved, displayed, or otherwise used'" | Metadata yes, video **no** | CSV | 2026-09-02 |
| WLASL | 2,000 glosses; JSON of third-party video URLs, many dead | C-UDA 1.0: "solely for Computational Use"; README: "academic and computational use only" | **No**: displaying clips to humans is not computational use, and the videos are third-party. *This corrects the previous iteration, which listed WLASL as a redistributable fallback.* | Script | 2026-09-02 |
| ASL Citizen (Microsoft) | ~84k videos | §1(c): "you may not distribute the data or your modifications to the data"; §2(e) forbids providing "the Materials as a stand-alone hosted solution" | **No** (training a model on it is permitted) | Zip | 2026-09-02 |
| Sem-Lex | 91,148 videos, 41 Deaf signers | Data terms inside a Google Form, not fetchable | UNVERIFIED → treat as no | Gated | 2026-09-02 |
| How2Sign | 80+ h continuous signing | CC BY-NC 4.0 | Yes, but sentence-level, no isolated-sign index | Drive | 2026-09-02 |
| Lifeprint / ASLU | Dictionary | "You do not have permission to use ASLU materials to make, apps of any kind" | **No** | — | 2026-09-02 |
| Handspeak, Signing Savvy, ASLLRP, Spreadthesign | Dictionaries | Forbid reproduction / embedding / redistribution (Spreadthesign wording UNVERIFIED: site unreachable) | **No** | — | 2026-09-02 |
| Wikimedia Commons ASL letters | 26 SVG line drawings (`Sign language A.svg` … `Z.svg`, wpclipart.com) | `A.svg` page: "Public Domain"; B–Z assumed same series, UNVERIFIED per file | Yes, labelled "static letter image" | Commons API | 2026-09-02 |

**Decision (ADR 0007):** CATS is the primary clip source (public domain, bulk, breadth); Signbank supplies letters, digits, and any sign CATS lacks or renders poorly, each with its weblink; ASL-LEX CSV supplies frequency ranking. Every clip row records source, licence, and URL.

### 3.2 Speech-to-text

| Option | Facts | Licence | Verdict |
|---|---|---|---|
| **faster-whisper** 1.2.1 `base.en` int8 | CTranslate2 backend; dependencies list **no torch**; `base` model 145 MB on disk, `tiny` 75.5 MB; `small` int8 measured at 1,477 MB RAM (published), `tiny`/`base` RAM **UNVERIFIED** (not published); word timestamps supported | MIT | **Chosen** for upload mode and for offline pre-transcription of the demo set |
| Browser Web Speech API | Microphone, or in Chrome 135+ only an audio track from a playing element; Chrome sends audio to a Google service; Firefox only behind a preference; caniuse 87.6% | Browser built-in | **Cut**: Chrome-only for the video case, and a news panel has no microphone use case |
| whisper.cpp WASM in the browser | MIT; `base-q5_1` 59.7 MB, `tiny-q5_1` 32.2 MB; ~2–3× realtime for short clips; needs WASM SIMD; COOP/COEP requirement UNVERIFIED | MIT | **Runner-up** if server RAM becomes binding |
| Vosk | `small-en-us-0.15` 40 MB, Apache-2.0, no torch; last PyPI release 2022-12 | Apache-2.0 | Rejected: no word-level quality advantage, stale package |
| Hugging Face Inference Providers | Free accounts get "$0.10/month" credits, "subject to change" | — | Rejected: not dependable for a live demo |

### 3.3 News input sources

| Source | What | Terms (quoted) | Verdict |
|---|---|---|---|
| **Voice of America** (voanews.com terms page) | Text, audio, video news | "All text, audio and video material produced exclusively by the Voice of America is in the public domain." "Credit for any use of VOA material should be given to voanews.com, Voice of America, or VOA." AFP/AP/Reuters material on the site "may not be copied, published or redistributed without the written permission of each agency." **The site has not updated since 2025-03-15** (shutdown and ongoing litigation); the "Worldwide in Five" feed has zero items. | **Chosen for licence only**: VOA-produced newscasts from the archive, never live |
| Internet Archive collection `VOANewscasts` | Daily VOA newscast MP3s (128 kbps) with PDF/DOCX transcripts; each item carries a Creative Commons Public Domain Mark | Items dated 2024-09 to 2024-11; historical | **Chosen** as the demo-set source (transcripts included). Items are labelled with their broadcast date on screen |
| **NWS API** (`api.weather.gov`) | Live forecast text, JSON, no key | US government work; public-domain status UNVERIFIED today (terms page not fetched) | **Chosen** for the live weather lane |
| **Guardian Open Platform** | Full article text via `show-fields=bodyText`; free developer key, no card | Non-commercial; Guardian staff on the API forum (2023, 2025): student and teaching use is fine if not commercialised; daily cap **UNVERIFIED** (500/day per a 2026 third party vs 5,000/day per staff in 2023); T&C page blocked today | **Chosen** for the Phase 4 headline lane |
| GDELT DOC 2.0 API | Titles, URLs, dates; no key | "unlimited and unrestricted use for any academic, commercial, or governmental use ... without fee", cite and link gdeltproject.org; ~1 request / 5 s / IP (search-only) | Keyless fallback for headline titles |
| NPR News Now, ABC News Update | Hourly 5-minute and 2.5-minute MP3 feeds, current today | NPR channel: "For Personal Use Only"; ABC: "All rights reserved" | **Rejected** for a public demo |
| BBC RSS, Reuters, AP, NewsAPI, Wikinews | Headlines only / no official feed / dev-only ("cannot be used in a staging or production environment") / Wikinews read-only since 2026-05-04 | BBC terms UNVERIFIED (blocked) | Not used |

### 3.4 NLP and modelling

| Resource | Facts | Licence | Verified |
|---|---|---|---|
| **ASLG-PC12** (`achrafothman/aslg_pc12` on Hugging Face) | 87,710 English→ASL-gloss pairs (Othman & Jemni 2012); glosses were rule-generated | CC BY-NC 4.0 | 2026-09-02 |
| **t5-small** (`google-t5/t5-small`) | 60.5 M parameters | Apache-2.0 | 2026-09-02 |
| **CTranslate2** 4.8.2 (2026-08-31) | Converts and runs T5 encoder-decoders; conversion needs torch, **inference does not**; int8 on x86-64 CPU supported | MIT | 2026-09-02 |
| **sentencepiece** 0.2.2 | T5 tokenizer, 1–2 MB wheel, no torch | Apache-2.0 | 2026-09-02 |
| Python stdlib: `difflib`, `xml.etree`, `json`, `re`, `urllib` | Phrase matching, ECV/JSON parsing, HTTP | PSF | — |
| `spoken-to-signed-translation` (sign-language-processing) | Rule-based reorder/drop text→gloss stage; pushed 2026-07-23; borrow the rule ideas, not the package (its lexicon is Swiss) | MIT | 2026-09-02 |
| spaCy `en_core_web_sm` 3.8.0 (12 MB, MIT), rapidfuzz 3.14.6 (MIT) | Available if the rule pass needs POS tags or faster fuzzy matching; not in the MVP | MIT | 2026-09-02 |

### 3.5 Training compute (offline only)

| Resource | Facts | Verified |
|---|---|---|
| **Kaggle notebooks** | ~30 GPU-hours/week (P100 or 2×T4), 12 h session cap, weekly reset, no card. Official quota page returned 404 today; figures from secondary sources | 2026-09-02 (secondary) |
| Google Colab free | GPU access "heavily restricted"; ≤ 12 h; limits "vary over time" and are unpublished | 2026-09-02 (official FAQ) |

Fine-tuning t5-small on 87k short pairs is a 1–2 GPU-hour job. Kaggle primary, Colab backup, overnight CPU as last resort.

### 3.6 Platform

| Resource | Facts (quoted) | Verified |
|---|---|---|
| **Streamlit Community Cloud** | "CPU: 0.078 cores minimum, 2 cores maximum"; "Memory: 690MB minimum, 2.7GBs maximum"; "Storage: No minimum, 50GB maximum"; "All apps without traffic for 12 hours go to sleep"; "You are only allowed one private app at a time"; custom subdomain 6–63 chars on `*.streamlit.app`; no card; "These limits may change at any time without notice" (February 2024 figures) | 2026-09-02 |
| **Streamlit 1.62.0** (2026-08-19) | `st.components.v2.component(name, html=, css=, js=)` GA since 1.51.0: frameless, JS runs "with normal app-page DOM privileges"; `st.components.v1.html` deprecated since 1.56 | 2026-09-02 |
| **GitHub** public repo | Actions: "The use of standard GitHub-hosted runners is free: In public repositories". Pages: sites ≤ 1 GB, "soft bandwidth limit of 100 GB per month". Per-file push limit 100 MB (long-standing, not re-fetched) | 2026-09-02 |
| Cloudflare R2 | 10 GB-month free, egress free, **but** "Complete the checkout flow to add an R2 subscription" (payment method, community-confirmed only) and "Public access through r2.dev subdomains is rate-limited and should only be used for development purposes"; a proper public URL needs a domain zoned in the same account | 2026-09-02 |
| Hugging Face Spaces | "Gradio and Docker Spaces run on compute and require a paid plan to create"; only ZeroGPU Gradio Spaces (2 per account, >30 days old) are free | 2026-09-02 |
| Render free | 512 MB, 0.1 CPU, "spins down ... 15 minutes without receiving any inbound traffic" | 2026-09-02 |
| Fly.io | No free tier: trial "2 hours of machine runtime or 7 days of access" | 2026-09-02 |
| **UptimeRobot** free | "50 monitors", "5 min. monitoring interval", 1 status page, no card | 2026-09-02 |

### 3.7 Carried-forward unresolved items

| Item | Resolution | When |
|---|---|---|
| ASL Signbank bulk video access | Confirmed today: **no bulk endpoint**; per-entry compressed download is permitted by the conditions page. Now a secondary source, so ~20–50 entries at most | Spike 2, Phase 0 |
| ASL Citizen licence | Confirmed blocked for redistribution. Not used | Closed |
| WLASL as fallback | Confirmed **not** redistributable (C-UDA computational use). Removed | Closed |
| Web Speech API inside Streamlit components | Moot: microphone input is out of scope | Closed |
| Peak RSS on Community Cloud | `scripts/measure_rss.py` in CI on every push; budget 1.8 GB with whisper loaded | Phases 2, 4 |
| Keras intent model under TF 2.21 | Moot: TensorFlow and the 16-class classifier are retired; the DL component is T5 (ADR 0005) | Closed |
| Cloudflare R2 for clips | Superseded: needs a payment method and a zoned domain for a non-rate-limited URL. Clips live in the repo (ADR 0007) | Closed |

---

## 4. Technology selection with trade-offs (Step 3)

Existing ADRs: **0001** superseded (already), **0002 kept** (hosting) with its R2 clause superseded by 0007, **0003 superseded** by 0004. New: 0004 scope, 0005 gloss model, 0006 rendering, 0007 clip source and storage, 0008 synchronisation.

| Layer | Chosen | Rejected | Why chosen | Why rejected | What would reverse it |
|---|---|---|---|---|---|
| **Input capture** | Curated demo items in the repo; NWS live text; upload ≤ 60 s | Live stream; microphone (Web Speech); WebRTC | Deterministic demo; no keys; no TURN server | No free legal live stream; mic has no news use case; WebRTC needs TURN on Community Cloud | A free public-domain live stream with captions appears |
| **Transcription** | faster-whisper `base.en` int8 with word timestamps; demo set pre-transcribed offline and human-corrected | `small`; openai-whisper; cloud STT | Fits RAM; no torch; word timing drives sync | `small` int8 = 1.5 GB; openai-whisper needs torch; cloud STT costs or has dev-only terms | Measured RSS > 1.8 GB → whisper in the browser via transformers.js |
| **Text → gloss** | Rule-based pass (stdlib) as default; **T5-small fine-tuned on ASLG-PC12, served by CTranslate2 int8** behind a toggle (ADR 0005) | Keras 16-class intent classifier; LLM API; sentence-transformers | Rules are inspectable and honest; T5 is the assessable DL contribution and runs torch-free at ~60 MB | Intent classifier cannot generalise beyond 16 phrases; LLM APIs cost, rate-limit, and are not reproducible; sentence-transformers needs torch | T5 beats rules on the real demo set by a clear margin → make it default |
| **Gloss → sign identity** | Concept-keyed lexicon: CATS title + Signbank ECV keywords → concept id → clip; sense table for ambiguous words | Hand-typed dictionary; keying on English strings | Uses two validated indexes; badges per concept | The prototype's 26-word table is the documented defect; English-string keys collapse distinct signs | — |
| **Sign source** | **CATS ASL Dictionary (public domain, 24,682 clips)** primary; Signbank (CC BY-NC-SA) for letters, digits, gaps (ADR 0007) | WLASL; ASL Citizen; Lifeprint; Signing Savvy | No licence obligations; bulk; breadth covers news vocabulary; Signbank fills quality gaps with linguist-curated forms | Computational-use-only; no-distribution; explicit app bans | Spike 1 finds CATS signer quality unacceptable → Signbank primary with a ~200-entry polite fetch |
| **Sign rendering** | Recorded clip playback in HTML5 `<video>`, sequenced by a timeline JSON (ADR 0006) | MediaPipe skeleton view; CWASA/HamNoSys avatar; AI video generation | Real ASL from real signers; zero runtime dependencies; removes a whole build environment (MediaPipe) | Skeleton view added an environment and RAM for no evaluative gain; no ASL HamNoSys lexicon exists; no evidence generative video produces correct ASL (Apple CHI 2025, prior) | An examiner requests an avatar and a licence-clean pose set exists |
| **Synchronisation** | Clips scheduled at word onset from whisper timestamps; if signing runs longer than speech the panel **shows the overrun** ("catching up" indicator), never drops signs, playback ≤ 1.25× (ADR 0008) | Drop signs to absorb overrun; semantic compression | Honesty: a dropped sign is a silent loss | Compression is what a human interpreter does and requires a signer, not code | Deaf-reviewed compression rules become available |
| **UI framework** | Streamlit 1.62.0 + `st.components.v2` panel (ADR 0002 kept) | Static site on GitHub Pages with in-browser ONNX; FastAPI + React | One language; existing deploy path; the Python pipeline is the assessed artefact | Static-only turns the Python pipeline into a build step, harder to evidence and demo; two-tier stack doubles the surface for one developer | Community Cloud RAM or sleep proves unreliable in Phase 2 → static site is the runner-up |
| **Hosting** | Streamlit Community Cloud (ADR 0002 kept) | Render free; HF Spaces; Railway; Fly.io; the developer's Oracle box | Free, x86, 2.7 GB, auto-HTTPS, push-to-deploy; the only free host verified today that gives Python > 1 GB with no card | 512 MB and 15-min sleep; $9/mo gate; $16–30/mo; no free tier; excluded by developer direction | Published limits change (they say they can) → HF ZeroGPU Gradio Space is the free runner-up |
| **Asset storage** | **Clips and demo media committed in the app repo** under `static/`, served by Streamlit static file serving (`server.enableStaticServing`) (ADR 0007) | Cloudflare R2; Git LFS; HF Dataset repo | ~0.4 GB fits the 1 GB guidance; zero moving parts; Community Cloud reads local files | R2 needs a payment method and a zoned domain; LFS is unreliable on Community Cloud (prior) and not served by Pages; HF storage policy has shifted | Repo passes ~800 MB → second public repo served by GitHub Pages, referenced by URL |
| **Training compute** | Kaggle primary, Colab backup, CPU overnight last resort | Paid GPU rental | Free; sufficient for a 2-hour job | Not needed | — |
| **CI/CD** | GitHub Actions: ruff, pytest, RSS budget; Community Cloud auto-deploys `main` | Self-hosted runners | Free on public repos | — | — |
| **Testing** | pytest + pytest-cov; JSON-schema contract test on the timeline; `streamlit.testing.v1.AppTest` smoke | Selenium; manual only | Small and standard | — | — |
| **Monitoring** | UptimeRobot free + public status page | Sentry | Free; evidences operations | Community Cloud already shows logs | — |

**Paid components:** none are critical. The only paid item ever considered is a ~$7 one-off GPU rental if Kaggle and Colab both fail during the training week; the free fallback is overnight CPU training.

---

## 5. Project folder structure (Step 5)

```
speak2sign/
├── README.md                     # what it is, live URL, how to run, attribution summary
├── CLAUDE.md                     # working rules: non-negotiables, stack, hard rules
├── LICENSE                       # code licence (MIT)
├── NOTICE.md                     # attributions: CATS/archive.org, ASL Signbank (CC BY-NC-SA), VOA, ASLG-PC12, T5
├── app.py                        # Streamlit entry point (thin: layout + calls into src/)
├── requirements.txt              # RUNTIME ONLY: streamlit, faster-whisper, ctranslate2, sentencepiece
├── requirements-dev.txt          # ruff, pytest, pytest-cov
├── requirements-train.txt        # torch, transformers, datasets, evaluate  (Kaggle only, never deployed)
├── runtime.txt                   # python-3.12
├── Dockerfile                    # reproducible local run; mirrors Community Cloud
├── .streamlit/config.toml        # server.enableStaticServing = true
├── .github/
│   ├── workflows/ci.yml          # ruff + pytest + RSS budget on every push and PR
│   └── pull_request_template.md  # definition-of-done checklist
├── src/speak2sign/
│   ├── __init__.py
│   ├── ingest/
│   │   ├── nws.py                #   live forecast text (api.weather.gov; stdlib urllib + json)
│   │   ├── headlines.py          #   Guardian Open Platform (key from st.secrets), GDELT fallback
│   │   └── demo_set.py           #   curated items: id, media path, transcript, timings
│   ├── asr.py                    # faster-whisper wrapper: lazy-loaded, ≤ 60 s guard, word timestamps
│   ├── gloss/
│   │   ├── rules.py              #   normalise, drop copulas/articles, fingerspell out-of-vocabulary
│   │   ├── t5.py                 #   CTranslate2 generation behind a flag
│   │   └── lexicon.py            #   concept index: keyword → concept → clip, source, licence, badge
│   ├── timeline.py               # word onsets + gloss sequence → timeline JSON (the contract)
│   ├── provenance.py             # badge rules: validated / fingerspelled / not available
│   └── ui/
│       ├── panel.html            #   news media + captions + ASL panel, plain HTML5 video
│       └── panel.js              #   scheduler driven by media.currentTime; overrun indicator
├── static/                       # served by Streamlit at /app/static/...
│   ├── clips/<concept_id>.mp4    #   ~150–200 sign clips, trimmed and normalised (≤ 2 MB each)
│   ├── letters/<A..Z, 0..9>.mp4  #   fingerspelling set
│   └── news/<item_id>.mp3        #   5–8 VOA newscast excerpts (public domain)
├── data/
│   ├── lexicon/
│   │   ├── concepts.json         #   concept id, keywords, sense notes, clip file, badge
│   │   ├── target_vocab.csv      #   ~150–200 signs, ASL-LEX frequency rank, status
│   │   ├── senses.json           #   hand-written disambiguation for ambiguous English words
│   │   └── attribution.json      #   per-clip source, item id or entry URL, licence
│   ├── demo/<item_id>.json       #   transcript + word timings for each curated item
│   └── phrases.json              #   fixed phrase → validated gloss sequence
├── models/t5_gloss_ct2/          # CTranslate2 int8 export (~60 MB), downloaded from a GitHub Release at build
├── scripts/
│   ├── build_lexicon.py          # CATS search + Signbank ECV → concepts.json
│   ├── fetch_clips.py            # target vocab → download (rate-limited, resumable) → trim → static/clips
│   ├── build_demo_set.py         # VOA MP3 → whisper → manual correction → data/demo
│   └── measure_rss.py            # peak RSS with models loaded; fails CI over budget
├── training/
│   ├── train_t5_gloss.ipynb      # Kaggle notebook (also exported as .py)
│   ├── export_ct2.py
│   └── results/                  # metrics JSON, sample outputs, run log
├── tests/
│   ├── test_rules.py
│   ├── test_lexicon.py
│   ├── test_timeline_contract.py
│   ├── test_provenance.py
│   └── test_smoke_app.py         # streamlit AppTest
├── contracts/timeline.schema.json # the one interface between Python and the panel JS
└── docs/
    ├── 00-execution-plan.md      # this file
    ├── 01-requirements/prd.md
    ├── 02-design/{system-design.md, data-model.md, resolution-cases.md, cost-model.md}
    ├── 03-implementation/{dev-log.md, coding-standards.md}
    ├── 04-testing/{test-strategy.md, evaluation.md}
    ├── 05-deployment/{deployment.md, runbook.md, demo-script.md}
    ├── 06-reflection.md
    ├── adr/0001..0008-*.md       # 0001–0003 copied verbatim from the old repo, status fields updated
    └── research/                 # prior findings copied; spikes.md and this session's verification added
```

**Not in the repository:** T5 weights before export (Kaggle output); the `legacy/` prototype (stays in the old folder, cited by path); the Guardian API key (Community Cloud secrets manager, Phase 4 only; the MVP needs no secret). The repo stays under ~0.5 GB; every committed media file stays under 100 MB.

---

## 6. SDLC process (Step 6)

**Model:** iterative-incremental with stage gates. Each phase writes its documents first, then code, then ships a deployed increment. The spec-kit workflow already installed in the old repo (`.specify/`) is copied over and provides the templates: constitution → specify → plan → tasks → implement.

| Practice | How | Evidence for the assessor |
|---|---|---|
| Requirements | PRD in Phase 0 from §2; each requirement has an id (FR-nn), priority, acceptance criterion; changes via PR to `docs/01-requirements/` | PRD git history |
| Architecture decisions | One ADR per decision; status Proposed → Accepted → Superseded; never edited after acceptance | `docs/adr/` |
| Design | TRD, data model, and timeline contract before Phase 2 code; diagrams as Mermaid in Markdown | `docs/02-design/` |
| Branching | Trunk-based: `main` always deployable; short-lived `feat/<id>-<slug>`; PR to `main` even as a sole developer, with the self-review checklist | PR list |
| Commits | Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`) referencing the task id | git log |
| Definition of done | Code + test + docs + CI green + RSS budget met + verified at the live URL | PR template |
| Quality gate | Actions on every push: `ruff check`, `pytest`, `scripts/measure_rss.py`; red cannot merge | Actions history |
| Testing | Unit tests per module; schema contract test; AppTest smoke; model evaluation script | `docs/04-testing/` + CI |
| Deployment | Merge to `main` → Community Cloud redeploys; tag `vX.Y.Z` at each phase exit; deployment doc records URL, date, commit | Tags + `docs/05-deployment/` |
| Operations | UptimeRobot public status page; runbook for "app asleep", "model failed to load", "clip missing" | `runbook.md` |
| Dev log | One dated entry per working day: done, blocked, decided | `docs/03-implementation/dev-log.md` |
| Honesty rules | UNVERIFIED marked; skipped work stated; nothing described that is not deployed | Throughout |

Cadence: a weekly self-retro entry in the dev log (what slipped, what to cut), aligned to the phase table.

---

## 7. Cost model (Step 7)

| Component | Provider | Free-tier limit | Expected demo-scale usage | Headroom | Monthly cost |
|---|---|---|---|---|---|
| App hosting | Streamlit Community Cloud | 0.078–2 cores, 690 MB–2.7 GB RAM, 50 GB disk, sleeps after 12 h idle | 1 app, ≤ 1.8 GB peak | ~0.9 GB | $0 |
| Clip and media storage | GitHub repo (public) | 1 GB guidance, 100 MB per file | ~200 clips × ≤ 2 MB + 8 items × ~2 MB ≈ 0.4 GB | ~60% | $0 |
| Source control + CI | GitHub Actions | Free on public repos | ~50 runs/week × ~3 min | Ample | $0 |
| Model artefact | GitHub Releases | 2 GB per file | one ~60 MB file | Ample | $0 |
| Training | Kaggle | ~30 GPU-h/week | ~2 GPU-h total | Ample | $0 |
| Speech-to-text | faster-whisper, self-hosted | — | ≤ 60 s clips | — | $0 |
| News data | VOA archive (public domain), NWS API (no key), Guardian developer key (free, Phase 4) | Guardian: 500–5,000 calls/day (UNVERIFIED which) | a few requests/hour | Ample | $0 |
| Monitoring | UptimeRobot | 50 monitors, 5-min interval | 1 monitor | Ample | $0 |
| Domain and TLS | `*.streamlit.app` | — | — | — | $0 |
| **Total** | | | | | **$0.00** |

Contingency: ~$7 one-off GPU rental only if Kaggle and Colab both fail in the training week; free fallback is overnight CPU training.

---

## 8. Pre-mortem (Step 8)

It is 2026-10-30 and the demo failed at the viva. The five most likely causes:

| # | Cause | Early warning sign | Countermeasure built in |
|---|---|---|---|
| 1 | **Clips never arrived**: CATS quality was poor and Signbank per-entry fetching ate the schedule | Spike 1 has no written result by day 5 | CATS sampled on day 3; Signbank is secondary and capped at ~50 entries; fetch script is rate-limited and resumable |
| 2 | **The panel looked like a spelling bee**: fingerspelling above 20% | Coverage under 85% on the demo scripts at end of Phase 1 | Bounded lexicon; items chosen for coverage; live lane is weather; CATS has 24k entries so extending vocabulary is cheap; rate displayed, not hidden |
| 3 | **Out of memory on Community Cloud** with whisper and T5 loaded together | `measure_rss.py` over 1.8 GB in CI | Lazy load; `base.en` int8 only; T5 int8; demo path pre-transcribed so whisper is never loaded for the demo |
| 4 | **Sync drift**: signs fell behind and the panel looked broken | Overrun indicator on for most of an item in Phase 3 | Schedule from media `currentTime`; preload; overrun shown as design; playback ≤ 1.25× |
| 5 | **Docs written after the code**, process mark suffered | A PR with a code diff and no docs diff | Definition of done requires docs; PR template; weekly retro entry |

---

## 9. End-state checklist

- [ ] Public URL works during the viva; screen recording exists as backup
- [ ] Every technology choice has an ADR with alternatives and a reversal condition
- [ ] Every external resource in §3 is verified or marked UNVERIFIED with an owner and date
- [ ] Total monthly cost is $0 and the cost model quotes the limits
- [ ] Folder tree matches §5; SDLC practices in §6 are evidenced in git
- [ ] Every sign on screen carries a badge; disclaimer and attribution shown at first exposure
- [ ] Evaluation report with a reproduction command exists

---

## 10. UNVERIFIED items and decisions for the developer

**UNVERIFIED (owner: developer unless stated):**
1. CATS collection: only 7 items sampled for the Public Domain rights field; signer identity and consistency unknown; letter and digit coverage unknown. Spike 1.
2. ASL Signbank public video count (2,848 from a mirror) and per-entry download URL pattern. Spike 2.
3. Guardian Open Platform daily cap (500 vs 5,000) and current T&C wording; NPR terms text (page timed out). Phase 4.
4. NWS API terms page (public-domain status assumed as US government work). Phase 0, five minutes.
4a. faster-whisper `tiny`/`base` int8 resident RAM (only `small` is published). Spike 3 can measure it in the same session.
4b. Whether any VOA English audio feed resumes in 2026; irrelevant to the MVP, which uses the archive.
5. Kaggle weekly GPU quota (official page 404 today; ~30 h/week from secondary sources). Check the account's Quotas panel before Phase 2.
6. Peak RSS with faster-whisper `base.en` int8 + T5 int8 on Community Cloud. Phase 2.
7. `st.components.v2.component` hosting two `<video>` elements with JS scheduling after a click. Spike 4.
8. Streamlit static file serving works on Community Cloud for MP4 (`server.enableStaticServing`). Spike 4.
9. Wikimedia letter SVGs B–Z licence per file (A confirmed Public Domain). Only if Signbank/CATS lack letters.
10. Sem-Lex data terms (inside a Google Form). Not needed unless CATS and Signbank both fail.

**Decisions the developer must confirm (⚑):**
- ⚑A1 Deadline 2026-10-30 · ⚑A2 T5 gloss model is the marked DL component · ⚑A3 4 dev-days/week · ⚑A4 ASL
- ⚑D1 Scope per §2: curated VOA items + live NWS weather lane as MVP; headlines and upload in Phase 4
- ⚑D2 CATS public-domain dictionary as primary clip source, Signbank secondary (ADR 0007)
- ⚑D3 MediaPipe skeleton view and the Keras intent classifier are retired (ADR 0005, 0006)
- ⚑D4 Microphone input is out of scope
- ⚑D5 Clips committed in the repo, not on R2 (ADR 0007)
