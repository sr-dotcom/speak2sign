# CLAUDE.md — Speak2Sign v2

Guidance for Claude Code in this repository. Read `docs/00-execution-plan.md` first.

## What this is

A news bulletin plays on the left; an ASL interpreter panel on the right signs it from
recorded Deaf-signer clips, in time with the narration, with a provenance badge on every
sign. University capstone: the deployed app and the documented SDLC are both assessed.
Sole developer, ~8 weeks, $0 budget. Target ASL.

## Non-negotiables

1. Ends publicly deployed on Streamlit Community Cloud at a URL that works during the viva.
2. Documentation precedes code for every SDLC stage (`docs/01..05`, `docs/adr/`).
3. Never present a sign the system did not retrieve from a validated clip. Every entry
   carries a badge: validated, fingerspelled, not available. Overrun is shown, never
   absorbed by dropping signs.
4. Never claim a step is done that was not performed. Mark unverified claims `UNVERIFIED`.
5. Do not commit unless the developer asks.

## Stack (ADR 0002, 0004–0008)

| Layer | Choice |
|---|---|
| UI | Streamlit 1.62.0; panel in `st.components.v2` with plain HTML5 video + JS |
| Gloss | stdlib rules by default; T5-small fine-tuned on ASLG-PC12, served by CTranslate2 int8 behind a toggle |
| Clips | CATS "ASL Dictionary" on archive.org (public domain) primary; ASL Signbank (CC BY-NC-SA, weblink per clip) secondary; committed under `static/` |
| ASR | faster-whisper `base.en` int8, upload lane only, lazy-loaded, ≤ 60 s |
| News | Curated VOA newscasts from the Internet Archive (public domain); NWS API for live weather; Guardian API in Phase 4 |
| Host | Streamlit Community Cloud, public GitHub repo, Actions CI |

## Hard rules

- Runtime dependencies are exactly `requirements.txt`. No torch, TensorFlow, MediaPipe, spaCy at runtime.
- `requirements-train.txt` is for Kaggle only.
- Peak RSS with all models loaded ≤ 1.8 GB; `scripts/measure_rss.py` enforces it in CI.
- Every committed media file < 100 MB; repo total under ~0.5 GB.
- The timeline JSON (`contracts/timeline.schema.json`) is the only interface between Python and the panel. Change the schema and the contract test together.
- Key the lexicon on concept ids, never on an English string alone.
- Signbank clips carry their entry weblink; never use Signbank draft (non-teal) videos.
- Uploaded audio is never stored past the session or sent to a third party.
- Pin every dependency with `==`.

## Layout

See `docs/00-execution-plan.md` §5. Source in `src/speak2sign/`, app entry `app.py`,
static media in `static/`, lexicon data in `data/lexicon/`, tests in `tests/`.

## Work policy (set by the developer, 2026-09-03)

Every implementation, however small, follows three rules:

1. **Ponytail review before "done".** After writing code, run the `ponytail:ponytail-review` pass on the change (reinvented stdlib, unneeded dependency, speculative abstraction, dead flexibility). Apply the findings or state why not. A change is not finished until this review has happened.
2. **Say why.** Each change comes with a short rationale: the problem it solves and why this shape was chosen over the obvious alternatives. In a PR this goes in the description; in a session it goes in the message that delivers the change; durable decisions go in an ADR.
3. **Name the trade-off.** Every rationale states what was given up and what would reverse the choice. "No trade-off" is not an acceptable answer; if none is visible, the alternative was not considered.
4. **Involve the developer before structure changes.** Before adding a module, a data file, an interface, a dependency, or a new way of doing something, explain what it is, why it is needed, how it connects to the existing components, and the options considered. Wait for the developer's go-ahead. Small edits inside an agreed structure do not need this; new structure always does. The developer is learning the system through these explanations, so they are written for understanding, not just approval.

Format for delivering a change:

```
What: <one line>
Why: <problem, and why this shape>
Trade-off: <what is given up; what would reverse it>
Ponytail review: <findings applied / findings rejected and why / none>
```

## Working conventions

- Conventional Commits; short-lived `feat/<id>-<slug>` branches; PR template checklist is the definition of done.
- One dev-log entry per working day in `docs/03-implementation/dev-log.md`.
- Cite files as `path:line` in docs.
- The previous iteration lives in `../speak2sign/` (read-only reference; its `legacy/` prototype is never imported).
