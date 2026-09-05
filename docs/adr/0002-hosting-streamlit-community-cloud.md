# ADR 0002 — Host on Streamlit Community Cloud

**Date:** 2026-08-30 · **Status:** Accepted
**Supersedes:** [ADR 0001](0001-hosting-and-runtime-architecture.md) (Oracle Cloud ARM host)

## Context

ADR 0001 selected the developer's personal Oracle Cloud ARM server. **The developer has
directed that this server not be used for this project.** It runs live production
workloads (`bowtie-api`, `bowtie-frontend`, `policy-assistant`) and a student project
should not share that blast radius in either direction.

This is a constraint, not a technical finding. It is accepted without further debate.

With Oracle removed, the remaining candidates are:

| Option | Verdict |
|---|---|
| **Streamlit Community Cloud** | Free, x86, 2.7 GB RAM, automatic HTTPS, push-to-deploy |
| Railway Hobby | **$16–30/month** — see [cost-model.md](../02-design/cost-model.md) |
| Hugging Face Spaces | $9/month PRO; free tier is Gradio + ZeroGPU only |
| Render free | 512 MB — cannot hold TensorFlow |
| Azure for Students | $100 ≈ 4 months of a 4 GiB VM, built from scratch |
| Fly.io | No free tier for new users |

## Decision

**Deploy to Streamlit Community Cloud.** Free, x86, automatic HTTPS, GitHub-native
push-to-deploy.

## Consequences

### Good — the ARM problem disappears entirely

Streamlit Community Cloud runs **Debian 11 on x86_64**. Every ARM concern from ADR 0001
is void:

- **Revert to `tensorflow-cpu`.** On x86 it is **274 MB** versus 572 MB for plain
  `tensorflow`, which bundles CUDA. *(Note: this flag has now flipped twice —
  `tensorflow-cpu` on x86, plain `tensorflow` on ARM. It is easy to get wrong.)*
- MediaPipe, CTranslate2 and OpenCV all have standard x86 wheels.
- No QEMU cross-builds, no native-ARM CI runners needed.

Automatic HTTPS also means the **browser microphone works** — that requirement is met
without any certificate work.

### Bad — the 2.7 GB memory ceiling returns, and it is binding

Community Cloud caps at **690 MB – 2.7 GB RAM and 0.078–2 CPU cores**. Measured
footprints put us uncomfortably close:

| Component | RAM |
|---|---|
| faster-whisper `small` int8 | **1,477 MB** |
| TensorFlow resident | ~400–600 MB |
| Streamlit + app | ~200–300 MB |
| **Total with `small`** | **~2.4–2.7 GB — at the ceiling** |

Mandatory mitigations:

1. **Use faster-whisper `base` or `tiny` int8. Never `small`.**
2. **Lazy-load the ASR model**, and release it when idle.
3. **Cap uploaded audio length** (target ≤ 30 s).
4. **Measure peak RSS in Phase 2**, before building anything on top of it.
5. Keep a documented fallback: disable server-side ASR and rely on the browser Web
   Speech API if memory becomes the binding failure.

The published limits also carry Streamlit's own caveat that they date from **February
2024** and "may change at any time without notice."

### The two-environment split is retained — for a different reason

ADR 0001 split MediaPipe (offline) from the runtime to dodge the aarch64 gate. On x86
that gate is gone, and `tensorflow==2.19` + `mediapipe==0.10.21` would in fact resolve
together.

**We keep the split anyway, on memory grounds.** MediaPipe at runtime would consume
headroom we do not have inside 2.7 GB, and pose extraction is inherently a build-time
batch job, not a per-request cost. The protobuf conflict between current TensorFlow
(`protobuf>=6.31.1`) and legacy MediaPipe (`protobuf<5`) is also architecture-independent
and remains a live hazard if anyone recombines them.

So: **the deployed app still never imports MediaPipe.** Keypoints ship as committed data.

### Other consequences

- **Sleeps after 12 hours without traffic**, showing a wake interstitial. Mitigation:
  open the app the morning of the viva; record a screen-capture backup.
- **Git LFS on Community Cloud is documented as unreliable** (LFS pointer files served
  instead of content). Clips must live on **Cloudflare R2**, not in the repo. *(Amended 2026-09-03 by [ADR 0007](0007-clip-sources-and-storage.md): R2 needs a payment method, so clips are committed under `static/` and served by Streamlit static serving; the hosting decision stands.)*
- **Pin the Python version defensively** — `runtime.txt` is reported to be ignored
  intermittently, with 3.13 forced.
- **The DevOps story is thinner** than self-hosting. Compensate deliberately: a GitHub
  Actions gate (ruff + pytest) in front of deploys, a Dockerfile for reproducible local
  runs, a documented deployment architecture, and UptimeRobot with a public status page.
  This is weaker evidence than Traefik + tunnel + tailnet would have been, and the
  reflection report should say so plainly rather than overclaim.
- **No upgrade path.** Community Cloud has no paid tier and no GPU. If Phase 5 ever needs
  one, that is a migration, not an upgrade — most likely to Hugging Face Spaces PRO.

### Cost

**$0/month**, unchanged. See [cost-model.md](../02-design/cost-model.md).

## Alternatives rejected

- **Oracle Cloud ARM box** — excluded by developer direction. Not a technical rejection.
- **Railway** — $16–30/month for less memory; the only route to $5 risks a 502 on the
  first request after sleep.
- **Hugging Face Spaces** — $9/month for Streamlit-via-Docker since the SDK deprecation.
- **Render free** — 512 MB cannot hold TensorFlow; 15-minute spin-down.
- **Azure for Students** — $100 buys ~4 months on a 4 GiB VM, but requires building the
  host, TLS and deploy pipeline from scratch, and DigitalOcean's July 2026 withdrawal
  proved Pack credits can be revoked mid-project. **Retained as a documented failover
  only** — claimed, but nothing built on it.
