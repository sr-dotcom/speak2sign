# ADR 0007 — Clip sources and storage: CATS public-domain dictionary primary, ASL Signbank secondary, clips in the repo

**Date:** 2026-09-03 · **Status:** Accepted
**Supersedes:** the Cloudflare R2 clause of ADR 0002 and the WLASL fallback in the previous iteration's research

## Context

Verified 2026-09-02/03 (`docs/research/verification-2026-09-02-sign-sources.md`, `spikes.md`): the CATS "ASL Dictionary" on archive.org has 24,682 isolated-sign clips marked Public Domain with a bulk API; ASL Signbank (CC BY-NC-SA 4.0) permits per-entry compressed download with a weblink per clip and has no bulk endpoint; WLASL is computational-use only; ASL Citizen forbids distribution; Cloudflare R2 needs a payment method and its free public URLs are rate-limited.

## Decision

- **CATS primary** (168 concepts): matched by item title, scored, and every automatic pick reviewed; 40 wrong-sense or illustrated picks overridden in `data/lexicon/overrides.json` with reasons.
- **Signbank secondary** (90 concepts incl. all letters and digits): citation forms, fetched one per second with an identifying User-Agent, each recording its entry weblink and the required citation.
- **Concept-keyed lexicon** (`concepts.json`): English keywords are an index, never the identity; ambiguous words go through `senses.json`.
- **Every clip eyeballed once** (contact sheets) before status `attested`; only attested clips are served.
- **Clips committed under `static/`** (74 MB) and served by Streamlit static file serving. No object store, no LFS.

## Consequences

- Zero licence obligations on most clips; share-alike and attribution on the Signbank subset, rendered in the app and `NOTICE.md`.
- Repo stays under ~0.5 GB; each media file under 100 MB. If it passes ~800 MB, move clips to a second public repo on GitHub Pages.
- Two concepts had no clean clip in either source (`los-angeles`, `evening`) and were dropped or folded; two are approximations with an on-screen note (`evacuate` → ESCAPE, `coast` → BEACH).
