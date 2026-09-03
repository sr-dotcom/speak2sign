# ADR 0008 — Synchronisation: the bulletin is paced to the interpreter

**Date:** 2026-09-03 · **Status:** Accepted (developer decision, options 1 and 2 of the 2026-09-03 timing note)
**Supersedes:** the "media clock, catching-up indicator, ≤ 1.25×" policy in the execution plan §4 and system design §6
**Evidence:** [docs/research/timing-findings.md](../research/timing-findings.md)

## Context

With the real lexicon (258 clips) and the rule pass, signing time is 5.5–9.3× speech time on the six curated items, even after trimming clips to their active motion span. Dictionary citation clips carry ~2.8 s of motion per sign against ~0.4 s per spoken word, and letter clips cost ~1.8 s per letter against ~0.2 s for fluent fingerspelling. A "catching up" indicator designed for a few seconds of lag cannot honestly absorb a factor of four or more.

## Decision

1. **Interpreter-paced playback.** The news media plays one sentence, then pauses with a visible "waiting for the interpreter" state until the panel has finished every entry of that sentence, then resumes. Nothing is dropped, nothing is sped past legibility. The lag is a displayed, measured property of retrieval-based signing.
2. **Active spans and modest rates.** Each clip records `in_s`/`out_s` (motion span measured by frame differencing, `scripts/clip_durations.py`). The panel plays only that span, at **1.25×** for signs and **2.0×** for letters and digits. These rates are recorded in the timeline (`playback`) so the numbers on screen match what is played.
3. **Names once.** A capitalised word with no sign is fingerspelled the first time it appears in an item; later occurrences carry the badge **name** and are shown as text, not spelled. This mirrors interpreter practice (spell once, then refer) and cuts letter time by roughly a third.
4. **Estimates shown honestly.** `stats.signing_s` is the projected signing time at the recorded rates; the UI shows signing time next to speech time.

## Consequences

- The framing changes: the panel does not race the anchor; the bulletin waits. A 26 s item takes roughly two minutes. Demo items should stay under ~80 words.
- The timeline gains `sentences` (media-clock spans), `playback` (rates and mode), clip `in_s`/`out_s`, and the `name` badge; the contract schema and test change with it.
- The T5 comparison and coverage numbers are unaffected.
- The report gains a genuine finding: retrieval from validated clips is honest but slow, which is a quantified reason human interpreters remain necessary.

## Alternatives rejected

- **Free-running media** (the previous policy): the panel finishes ~90 s after the audio; looks broken and hides the cost.
- **Speed clips to match speech** (~3×): unreadable; violates the honesty rule.
- **Drop or compress signs**: a silent loss; requires a signer to do honestly.
