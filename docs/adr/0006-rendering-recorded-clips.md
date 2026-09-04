# ADR 0006 — Rendering: recorded clip playback; no skeleton view, no avatar, no generated video

**Date:** 2026-09-03 · **Status:** Accepted
**Retires:** the MediaPipe skeleton toggle and the pose build environment from the previous iteration

## Decision

Signs are shown by playing recorded clips of Deaf signers in an HTML5 `<video>`, sequenced by the timeline JSON. Nothing else renders a sign.

## Rationale

- Real ASL from real signers is the only output that needs no disclaimer beyond provenance.
- The skeleton view added a build environment (MediaPipe, protobuf conflict), RAM, and an evaluation burden for no gain in honesty or coverage.
- No ASL HamNoSys lexicon exists for CWASA/JASigning; generative video has no evidence of producing correct ASL (Apple CHI 2025); both would present unvalidated form as authoritative.

## Consequences

- One build environment fewer; runtime has no vision dependency; `opencv-python-headless` is a dev tool for contact sheets and motion spans only.
- Clips are dictionary citation forms and therefore slow; see ADR 0008 for the pacing consequence.
- Upgrade path stays open: a licence-clean pose dataset plus an examiner's request would justify a pose renderer as a separate ADR.
