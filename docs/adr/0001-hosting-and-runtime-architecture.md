# ADR 0001 — Hosting and runtime architecture

**Date:** 2026-08-30 · **Status:** ~~Proposed~~ **SUPERSEDED by
[ADR 0002](0002-hosting-streamlit-community-cloud.md)** — the developer directed that
their personal production server not be used for this project. Retained for the record;
its analysis of the protobuf conflict and the two-environment split still applies.

## Context

The student owns an Oracle Cloud instance that was not known when Decision C was
first made. As reported by the student:

- `oracle-arm-1`, `VM.Standard.A1.Flex`, **2 OCPU / 12 GB RAM, Ampere aarch64**
- Ubuntu 24.04 LTS, ~47 GB boot volume, US East (Ashburn)
- Docker + **Coolify v4.1.2**, **Traefik v3.6** owning 80/443
- **cloudflared** systemd service, tunnel with 4 edge connections
- Tailscale for admin; Coolify UI bound to the tailnet, never public
- OCI security list permits **TCP 22 only** — all public traffic arrives via the outbound tunnel
- Three apps already deployed on `gnsr.dev` subdomains, all arm64
- Deploys are currently **manual redeploys in Coolify**; no CI webhook

*(Not independently verified — no access to the host. Headroom figures still
outstanding: `free -h`, `df -h /`.)*

## Decision

**Deploy Speak2Sign to `oracle-arm-1` as the primary host**, on a `gnsr.dev`
subdomain routed through the existing Traefik + Cloudflare Tunnel path. Keep a
trimmed **Streamlit Community Cloud mirror as a hot standby** for the viva.

**Split the project into two environments** (see "Consequences").

## Rationale

| Factor | Oracle box | Streamlit Community Cloud |
|---|---|---|
| RAM | **12 GB** | 2.7 GB max |
| CPU | 2 OCPU | 0.078–2 cores |
| Sleeps | No | After 12 h |
| HTTPS | **Already working** | Automatic |
| Inbound ports | **None open** (tunnel only) | n/a |
| Cost | $0 | $0 |
| SDLC evidence | Docker, Traefik, tunnel, tailnet, CI webhook | "Connected a repo" |

Memory is the binding constraint. faster-whisper `small` int8 alone is **1,477 MB**;
add TensorFlow (~400–600 MB RSS) and Streamlit and the app sits at roughly
**2.4–2.7 GB** — exactly at Community Cloud's ceiling, where "this app has gone over
its resource limits" is a well-documented failure. 12 GB removes the constraint and
lets us keep a larger Whisper model.

The infrastructure story is also materially better for a process-assessed project,
and wiring the outstanding Coolify CI webhook converts existing tech debt into a
graded CI/CD deliverable.

## The two problems this had to solve

### 1. `tensorflow-cpu` has no aarch64 wheel — but `tensorflow` does

Verified on PyPI (2026-08-30): `tensorflow-cpu` 2.21.0 publishes x86_64 and Windows
wheels only; plain `tensorflow` 2.21.0 publishes
`manylinux_2_27_aarch64` at 281.9 MB. TensorFlow's own install page still claims ARM
routes via `tensorflow-cpu-aws`, but that package is stale (2.15.1, March 2024).

**This inverts the standard x86 advice** and reverses the guidance previously
recorded in `CLAUDE.md`, which has been corrected.

### 2. A protobuf conflict that breaks the stack on *every* architecture

| Package | protobuf constraint |
|---|---|
| `tensorflow==2.21.0` | `>=6.31.1,<8` |
| `mediapipe==0.10.21` | `>=4.25.3,<5` |

**Unsatisfiable.** The stack as originally described does not `pip install` on x86
either — this was latent and would have surfaced in week 2 regardless of hosting.

There is also a hard ARM gate: `mediapipe` 0.10.21 is the **last** version
containing the legacy `mp.solutions.holistic` API and has **no aarch64 wheel**;
`mediapipe` 1.0.1 (Aug 2026) is the **first** with an aarch64 wheel and **no longer
contains `mp.solutions`**. No single version satisfies both.

## Consequences

**The two-environment split resolves both problems at once.**

| Environment | Platform | Packages | When it runs |
|---|---|---|---|
| **Preprocessing** | Local Windows x86 | mediapipe, opencv, numpy | **Once**, offline, to extract `.pose` keypoints from the sign clips |
| **Runtime** | ARM server + CI | streamlit, tensorflow, faster-whisper | The deployed app |

Because the deployed app **never imports MediaPipe**, the protobuf conflict cannot
occur and the aarch64 gate does not apply. Keypoints ship as committed data.

This is better architecture on its own merits — pose extraction is inherently a
build-time batch job, not a per-request runtime cost — and it is a defensible design
decision to present in the viva rather than a workaround.

### Additional consequences

- Use `compute_type="int8"` for CTranslate2; int16 is Intel-MKL-only and silently
  falls back on ARM.
- Streamlit behind Traefik needs `server.headless=true`, `server.address=127.0.0.1`,
  and `browser.serverAddress`/`serverPort` set to the **public** hostname and 443 —
  otherwise the browser tries to open a WebSocket to `localhost:8501` and the app hangs.
- Serve at the **root path**, not a sub-path. `server.baseUrlPath` has a long
  unresolved history of serving assets from `/static` and rendering a blank page.
- Traefik must allow a request body large enough for audio upload; Streamlit's
  `server.maxUploadSize` defaults to 200 MB and a proxy limit below it returns 413
  with nothing in the app log.
- The WebSocket path is `/_stcore/stream`. Older configs naming `/stream` are stale.
- Cloudflare supports WebSockets on all plans including Free.

## Risks accepted

- **Oracle halved the Always Free Ampere allocation** from 4 OCPU/24 GB to
  2 OCPU/12 GB around 15 June 2026, without announcement — the docs were silently
  edited. The current box matches the new allocation. Over-limit A1 instances are
  "disabled and then deleted after 30 days."
- **Idle reclamation:** Oracle may reclaim Always Free instances where, over a 7-day
  window, 95th-percentile CPU **and** network **and** memory are all under 20%.
  All three must hold simultaneously; the co-hosted apps make this unlikely, but it
  is not zero.
- **No SLA and no support eligibility** on Always Free. The student is the entire
  operations team.
- **Do not terminate the instance.** Always Free status is fixed at creation and
  non-transferable, and "out of host capacity" for Ampere remains widely reported.

**Mitigation:** the Streamlit Community Cloud standby, plus a recorded screen-capture
of a working demo.

## Alternatives rejected

- **Railway** — priced properly, this is **$16–30/month**, not $5. Railway bills
  $10/GB/month on *resident* memory regardless of traffic, and the $5 Hobby credit buys
  only ~0.49 GB-months. The one route to a genuine $5 bill (Serverless scale-to-zero)
  returns a possible **502 on the first request after sleep** — disqualifying for a live
  viva. Also x86-only, not in the Student Pack, and no student pricing exists. Full
  arithmetic in [cost-model.md](../02-design/cost-model.md). **Retained as a costed
  contingency** if ARM proves blocking: ~2 hours to migrate, $16–30/mo, and set a hard
  usage limit immediately.
- **GitHub Student Pack hosting** — the Pack's hosting tier collapsed when
  **DigitalOcean withdrew on 2026-07-31 and expired all credits on 2026-08-01**. What
  remains is a $100 Azure credit (~4 months of a 4 GiB VM) and a Heroku credit too small
  to run the app. Azure is **claimed as a documented failover only**; nothing is built
  on it, precisely because DigitalOcean demonstrated that Pack credits can be revoked
  mid-project.
- **Hugging Face Spaces** — Gradio/Docker Spaces now require PRO at $9/month; the
  Streamlit SDK was deprecated 2025-04-30.
- **Render free** — 512 MB RAM cannot hold TensorFlow; 15-minute spin-down with a
  ~1 minute cold start is shorter than a viva Q&A.
- **Streamlit Community Cloud as primary** — demoted to standby on memory headroom.
