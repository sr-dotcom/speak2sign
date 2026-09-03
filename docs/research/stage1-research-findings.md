# Stage 1 — Research Evidence

Researched 2026-08-30. This file holds the evidence behind the three decisions
summarised in `docs/00-project-reflection.md`. Claims that could not be verified
from a fetched source are marked **UNVERIFIED**.

---

## Decision A — How the signing avatar is produced

### Sign-source datasets, by licence

| Source | Licence | Redistributable? | Scale |
|---|---|---|---|
| **ASL Signbank** | **CC BY-NC-SA 4.0** | **YES** (non-commercial, attribution, share-alike) | 4,526 entries |
| **Sem-Lex Benchmark** | CC BY-NC-SA 4.0 (data); Apache-2.0 (code) | YES, via Google Form terms | 91,148 videos / 3,149 signs / 41 Deaf participants |
| **Voxel51/WLASL** (HF) | C-UDA 1.0 — section 3.1 expressly permits redistribution | YES, ungated | 11,980 videos / 2,000 glosses / 5.5 GB |
| WLASL (original repo) | C-UDA 1.0 | Metadata + YouTube URLs only | 2,000 glosses |
| ASL-LEX 2.0 | CC BY-NC 4.0 | Yes (lexical metadata layer) | 2,700+ signs, 60+ features |
| How2Sign | CC BY-NC 4.0 | Yes, but continuous signing, ~290 GB | 80+ hours |
| **ASL Citizen** (Microsoft) | **BLOCKED** — "you may not distribute the data or your modifications" | **NO** | 83,399 videos |
| **ASLLVD** (Boston/Rutgers) | **BLOCKED** — "cannot be redistributed without permission" | **NO** | 3,300+ signs |
| **Signing Savvy** | **BLOCKED** — all rights reserved; ToS forbids redistribution | **NO** | — |
| Handspeak | Terms page 404 — **UNVERIFIED**, assume all rights reserved | Assume NO | — |
| MS-ASL | No licence text on download page — **UNVERIFIED**; metadata only | — | — |
| ASL-100-RGBD | **UNVERIFIED** | — | 100 signs, RGB-D |
| Lifeprint/ASLU | Some clips CC-BY; scope **UNVERIFIED** | Per-clip only | — |

Sources: [ASL Signbank copyright](https://aslsignbank.com/about/copyright/) ·
[Sem-Lex](https://www.sign-lang.uni-hamburg.de/lrec/data/semlexbenchmark.html) ·
[Voxel51/WLASL](https://huggingface.co/datasets/Voxel51/WLASL) ·
[C-UDA 1.0](https://github.com/microsoft/Computational-Use-of-Data-Agreement/blob/master/C-UDA-1.0.md) ·
[ASL Citizen licence](https://www.microsoft.com/en-us/research/project/asl-citizen/dataset-license/) ·
[ASLLVD](https://www.bu.edu/asllrp/av/dai-asllvd.html) ·
[Signing Savvy ToS](https://www.signingsavvy.com/termsofservice) ·
[ASL-LEX](https://asl-lex.org/) · [How2Sign](https://how2sign.github.io/)

### Rendering approaches evaluated

**SiGML / HamNoSys / CWASA (UEA)** — actively maintained (CWASA 2026 is current),
licence permits public use, embeds in-browser via WebGL. **Rejected: there is no
ASL lexicon.** UEA's demo lexicons are BSL, DGS, GSL and LSF only. Every ASL sign
would be HamNoSys notation the student invented, with no linguist to validate it —
which looks authoritative while being guesswork. Secondary problem: UEA's
documented includes are served over `http://`, causing mixed-content blocking on
any HTTPS deployment. This is the overall runner-up.
[CWASA conditions of use](https://vh.cmp.uea.ac.uk/index.php/CWASA_Conditions_of_Use) ·
[JASigning demos](https://vh.cmp.uea.ac.uk/index.php/JASigning_Demos)

**Pose-driven skeleton rendering** — `pose-format` and the `pose-viewer` web
component are **MIT**. MediaPipe `HolisticLandmarker` yields 543 landmarks
(33 pose + 468 face + 21×2 hands). Cannot stand alone as a source:
`spoken-to-signed-translation` is MIT but covers Swiss SL only, **not ASL**. It is
an excellent *renderer* that still needs a clip source.
[pose-format](https://github.com/sign-language-processing/pose) ·
[pose-viewer](https://www.npmjs.com/package/pose-viewer) ·
[MediaPipe HolisticLandmarker](https://ai.google.dev/edge/api/mediapipe/python/mp/tasks/vision/HolisticLandmarker)

**AI text-to-video generation — REJECTED.** No verified evidence that any current
general text-to-video model produces correct ASL. Apple's CHI 2025 work (Best Paper
Honourable Mention) finds current systems "fail to meet user needs due to poor
translation of grammatical structures, the absence of facial cues and body language,
and insufficient visual and motion fidelity" — and notably that work does *not* use
a general T2V model; it uses GPT-4o for gloss plus explicit pose synthesis. A
nearly-right sign is a confidently wrong sign, which is worse than showing nothing.
Having evaluated and rejected this on evidence is a viva point in our favour.
[Apple CHI 2025](https://machinelearning.apple.com/research/ai-sign-language-generation)

**Hand-authored 2D (CSS/SVG/Lottie/Rive)** — fully owned and works everywhere, but
16–30 signs drawn by a non-signer produces a cartoon, reads as a toy in a live demo,
and has zero upgrade path. Fallback only.

**Adaptable existing projects** — searched Hugging Face Spaces and GitHub. HF Spaces
matching "sign language" are almost entirely *recognition*, not production or avatar
work. `aws-samples/genai-asl-avatar-generator` is MIT-0 but requires paid AWS **and**
sources its signs from ASLLVD, which forbids redistribution — doubly disqualified.
`DFKI-SignLanguage/MMS-Player` is GPL-3.0 (viral), requires Blender 4.2 LTS, is
German SL, and its own authors state it "DOES NOT represent whatsoever an
application ready for production."

### The upgrade path is real

wSignGen (EMNLP 2024 Findings) has **released code and pre-trained diffusion
weights**, uses **SMPL-X**, is licensed CC BY-NC 4.0, and **requires a CUDA GPU**.
SignAvatars (ECCV 2024) provides 8.34M SMPL-X annotations across 70k videos.
Their input representation is keypoints and meshes — exactly what MediaPipe
extraction produces. So the architecture document's Phase 2 becomes an *extension*
of our data pipeline rather than a rewrite.
[wSignGen code](https://github.com/dongludeeplearning/wsigngen) ·
[SignAvatars](https://signavatars.github.io/)

---

## Decision B — Application stack

### Current versions (PyPI, 2026-08-30)

streamlit **1.62.0** · gradio **6.26.0** · tensorflow **2.21.0** ·
torch **2.13.0** · scikit-learn **1.9.0** · faster-whisper **1.2.1**

Python 3.12.10 is supported by all of these. Note: Streamlit Community Cloud
defaults to Python 3.12, but multiple 2025–2026 community reports say `runtime.txt`
is sometimes ignored and 3.13 forced — pin defensively and test.

### Wheel sizes (manylinux x86_64, cp312) — the decisive numbers

| Package | Wheel |
|---|---|
| `tensorflow` (default Linux, bundles CUDA) | **572.6 MB** |
| **`tensorflow-cpu`** | **274.0 MB** |
| `torch` 2.13.0 | **526.6 MB** |
| `faster-whisper` | **1.1 MB** (CTranslate2, no torch) |
| `scikit-learn` | 9.1 MB |

Unpacked on-disk sizes: **UNVERIFIED**.

**Conclusion: ship exactly one heavy framework.** TensorFlow plus torch plus a
loaded Whisper model will breach the 2.7 GB Community Cloud RAM ceiling.

### Streamlit's iframe limitation has been removed

This invalidates the standard objection to Streamlit for custom visuals:

- `st.components.v2.component()` (added **1.51.0**, 2025-10-31): *"Components do not
  run in iframes. They execute with normal app-page DOM privileges"* and *"No npm
  build process is required."* JS returns data to Python via `setTriggerValue()`.
- `st.html(..., unsafe_allow_javascript=True)` — DOMPurify-sanitised, *"not iframed."*
- `st.iframe` (added **1.56.0**, 2026-03-31) accepts a URL, a local `Path`, or raw HTML.
- `st.components.v1.html` and `.iframe` were **deprecated in 1.56.0** — the legacy
  prototype's intended injection pattern is already outdated.

This matters concretely because **the Web Speech API is unreliable inside an iframe**
(documented Chrome and Edge failures even with `allow="microphone *"` and
`Permissions-Policy: microphone=*`). Components v2 runs same-origin, which is what
makes free live-microphone input viable at all.
[st.components.v2.component](https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v2.component) ·
[st.iframe](https://docs.streamlit.io/develop/api-reference/text/st.iframe) ·
[st.html](https://docs.streamlit.io/develop/api-reference/utilities/st.html)

### ASR options

| Option | Dependencies | Benchmark (i7-12700K) |
|---|---|---|
| `openai-whisper` | torch + system ffmpeg | small fp32 CPU: **6m58s, 2335 MB RAM** |
| **`faster-whisper`** | CTranslate2 + PyAV — **no torch, no system ffmpeg** | small int8 CPU: **1m42s, 1477 MB RAM** (~4× faster) |
| `transformers` pipeline | torch + transformers | heaviest |
| Web Speech API | none server-side | instant, browser-side, free |

Benchmarks are on an i7-12700K; Community Cloud gives 0.078–2 cores, so only
`tiny`/`base` int8 are realistic there. [faster-whisper](https://github.com/SYSTRAN/faster-whisper)

Browser Web Speech API support: Chrome partial from v25, Safari partial from 14.1,
**Edge listed as unsupported**, Firefox unsupported (disabled by default). ~87.55%
global usage, spec status UNOFF, MDN marks it "not Baseline." Audio is sent to a
server-side recognition engine, so it does **not** work offline.
[caniuse](https://caniuse.com/speech-recognition) ·
[MDN SpeechRecognition](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition)

`streamlit-webrtc` requires **a TURN server specifically on Community Cloud** (Twilio
or self-hosted) — real friction and a live-demo failure mode. **Skip it**; use the
built-in `st.audio_input`, which returns 16 kHz WAV described in the docs as the
default "for speech recognition."

The legacy prototype's `recognize_google()` call is an undocumented free Google
endpoint. It is the single most likely thing to fail during a live demo, and it
silently uploads user audio to a third party. Replace it.

### Should the Keras model be replaced?

**No — keep it.** The model file is 98 KB; TensorFlow is the cost, not the model.
It is the academic artefact and the viva defence for "we built a neural network."
A scikit-learn TF-IDF baseline (9.1 MB) is worth training *as a comparison table*
to demonstrate rigour, and as a lazy fallback if the TF import fails on the host.
sentence-transformers was rejected outright: it requires torch, making it *heavier*
than TensorFlow, not lighter.

---

## Decision C — Deployment target

### The finding that overturns the obvious answer

**Hugging Face Spaces is no longer free for this use case.**

> "Static Spaces are free for everyone. Gradio and Docker Spaces run on compute and
> require a paid plan to create: PRO for personal accounts... Free personal accounts
> in good standing can still host up to 2 Gradio Spaces running on ZeroGPU."
> — [spaces-overview](https://huggingface.co/docs/hub/spaces-overview)

And the Streamlit SDK is gone: **"[2025-04-30] Deprecate Streamlit SDK — Streamlit is
no longer provided as a default built-in SDK option. Streamlit applications are now
created using the Docker template."**
([changelog](https://huggingface.co/docs/hub/en/spaces-changelog)) — and Docker Spaces
are paid. So Streamlit on HF now costs **PRO, $9/month**.

The only free HF path is a **ZeroGPU Gradio Space**: maximum 2, requires verified
email and an account older than 30 days, 5 minutes/day GPU quota, *"exclusively
compatible with the Gradio SDK"*, and PyTorch-oriented. **TensorFlow on ZeroGPU is
UNVERIFIED** and is not a documented configuration. Spaces persistent storage has
also been withdrawn.
[ZeroGPU](https://huggingface.co/docs/hub/spaces-zerogpu) ·
[pricing](https://huggingface.co/pricing)

Two researchers reached this conclusion independently from separate sources.

### Verified free-tier comparison

| Platform | RAM | CPU | Sleeps after | Cold start | Free? |
|---|---|---|---|---|---|
| **Streamlit Community Cloud** | **690 MB – 2.7 GB** | 0.078–2 cores | **12 h** | wake-page click | **Yes** |
| HF Spaces CPU Basic | 16 GB | 2 vCPU | 48 h | container boot | **No — PRO $9/mo** |
| HF ZeroGPU | dynamic | dynamic | 48 h | container boot | Yes (2 max, Gradio only) |
| **Render free** | **512 MB** | **0.1 CPU** | **15 min** | **~1 min** | Yes |
| Railway Free | 0.5 GB | 1 vCPU | pauses at $1 credit | — | Credit only |
| Railway Hobby | 48 GB | 48 vCPU | never | — | $5/mo |
| Fly.io | 256 MB | shared-cpu-1x | — | — | **No free tier for new users** |
| GitHub Pages | static only | — | never | none | Yes |

[SCC limits](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app) ·
[HF spaces-gpus](https://huggingface.co/docs/hub/spaces-gpus) ·
[Render compute plans](https://render.com/docs/compute-plans) ·
[Railway pricing](https://docs.railway.com/reference/pricing/plans) ·
[Vercel limits](https://vercel.com/docs/limits)

Streamlit's published limits carry the note that they date from **February 2024** and
*"may change at any time without notice."* This is a real risk, recorded in the
reflection report.

### Why Render is disqualified

512 MB RAM cannot hold TensorFlow — importing the framework alone will approach or
exceed that before the model loads. Separately, *"Render spins down a Free web service
that goes 15 minutes without receiving any inbound traffic"* and *"This process takes
about one minute."* Fifteen minutes is **shorter than a viva Q&A session**: an
assessor could open the link mid-answer and get a blank minute.

### Where the sign clips should live

**Not in the application repo.** GitHub recommends repositories stay under 1 GB and
hard-blocks files over 100 MiB. **Streamlit Community Cloud combined with Git LFS is
documented as unreliable** — multiple community reports of LFS pointer files being
served instead of real content (`OSError: file signature not found`).

Recommended: a **public Hugging Face Dataset repo** (free, CloudFront-served,
best-effort storage), referenced by URL. Second choice: **GitHub Releases assets +
jsDelivr CDN**, which keeps binaries out of git history entirely. This separation
also gives a clean architectural story for the viva: application tier, asset tier, CDN.
