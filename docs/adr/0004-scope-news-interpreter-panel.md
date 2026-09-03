# ADR 0004 — Scope: a news-bulletin interpreter panel with a bounded lexicon

**Date:** 2026-09-02 · **Status:** Proposed (⚑D1 in the execution plan)
**Supersedes:** [ADR 0003](0003-domain-scope-service-counter.md) (service counter)
**Reads with:** [Execution plan §2](../00-execution-plan.md) · [System design](../02-design/system-design.md)

## Context

The developer re-scoped the project on 2026-09-02 to "the interpreter beside the news anchor": a news item plays and an ASL panel signs it in time. The previous scope (service counter, ADR 0003) and the interim weather-panel scope (2026-09-01, never committed) are replaced.

Open-domain news is a vocabulary problem. The previous iteration's research puts lexical coverage at roughly 50–70% of content tokens on open English at 300–500 signs versus 85–95% in a bounded domain. A panel that fingerspells one word in three is not an interpreter.

Verified today: Voice of America content is public domain but the site has not updated since 2025-03-15; the Internet Archive holds VOA newscasts with transcripts under a Public Domain Mark; the NWS API gives live forecast text with no key; the Guardian Open Platform gives full article text under non-commercial terms with a free key. See `docs/research/verification-2026-09-02-stt-news-nlp.md`.

## Decision

The **format** is a news bulletin: media left, captions, ASL panel right, per-sign badges. The **lexicon** is bounded to ~150–200 signs chosen for the demo content.

Input lanes, in delivery order:

1. **Curated items** (MVP): 5–8 VOA newscast excerpts from the archive, hand-corrected transcripts and timings, chosen so the lexicon covers them. Broadcast date shown on screen.
2. **Live weather** (MVP): NWS forecast text narrated by the browser's speech synthesis. Bounded vocabulary, genuinely live, no key.
3. **Typed text** (from Phase 2, because the pipeline is tested through it).
4. **Upload ≤ 60 s** (Phase 4): server transcription with faster-whisper.
5. **Live headlines** (Phase 4): Guardian API text, GDELT titles as keyless fallback, with the fingerspelling rate displayed.

Out of scope: live broadcast streams, microphone input, open-vocabulary claims.

## Rationale

- Curated items make the viva demo deterministic and let the lexicon be sized to the content.
- The weather lane gives a live, bounded, free data source so "live" is true without an open vocabulary.
- Displaying coverage and fingerspelling rate turns the coverage limit into an honest, measurable property instead of a hidden failure.
- No lane depends on a licence review of a commercial news publisher.

## Consequences

- Vocabulary target ~150–200 concepts plus letters and digits, ranked by ASL-LEX subjective frequency, drawn from the CATS public-domain dictionary (ADR 0007).
- Coverage ≥ 85% on the curated scripts is a Phase 1 exit criterion.
- Demo items are 2024 news. This is stated on screen; freshness is not a goal of the MVP.
- The WFD/WASLI caution on live signing applies more strongly to a news panel than to a kiosk. Conditions adopted: disclaimer at first exposure, provenance per sign, and framing as a research demonstration of retrieval.

## Alternatives rejected

- **Live broadcast stream**: no legal free stream; live ASR on 0.078–2 cores; open vocabulary.
- **Open headlines as the MVP**: coverage 50–70%; demo quality depends on the day's news. Kept as Phase 4 with the rate displayed.
- **Weather only** (the 2026-09-01 scope): defensible but narrower than the developer's stated concept. The weather lane survives inside this scope.
