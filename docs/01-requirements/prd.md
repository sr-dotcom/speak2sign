# Speak2Sign v2 — Product Requirements

**Date:** 2026-09-02 · **Status:** Proposed, awaiting developer approval
**Reads with:** [Execution plan](../00-execution-plan.md) · [ADR 0004](../adr/0004-scope-news-interpreter-panel.md) · [System design](../02-design/system-design.md)

## 1. Problem

A Deaf viewer watching a news bulletin without an interpreter gets captions at best. Broadcasters add a human interpreter in a corner panel; most bulletins have none. This project demonstrates, honestly and at zero cost, what a retrieval-based panel can and cannot do: it signs the words it has validated clips for, spells the ones it does not, and says so on screen.

It is a university capstone. Both the deployed artefact and the documented process are assessed. It is not a service and does not replace a human interpreter.

## 2. Users

| User | Need |
|---|---|
| Deaf or hard-of-hearing viewer (demo audience) | See the news item signed beside the media, know which signs are validated |
| Examiner | See a deployed, working app; verify the process evidence; understand the limits |
| Developer | Build and evidence it in 8 weeks alone, at $0 |

## 3. Goals and non-goals

**Goals**
- G1 A public URL that plays a curated news item with a synchronised ASL panel.
- G2 A live lane (weather) that signs current text.
- G3 Every sign labelled by provenance; coverage and fingerspelling rate visible.
- G4 A deep-learning English→gloss model evaluated against the rule baseline.
- G5 Zero monthly cost; every dependency free-tier and licence-clean.

**Non-goals**
- Real-time broadcast interpretation; microphone input.
- ASL grammar beyond lexical retrieval (directional verbs, classifiers, non-manual markers).
- Serving as an accessibility product.

## 4. Functional requirements

Priority: P0 = MVP, P1 = Phase 4, P2 = stretch. Each has an acceptance test.

| ID | Requirement | Pri | Acceptance |
|---|---|---|---|
| FR-01 | The viewer can choose one of at least 5 curated news items and press Play | P0 | Item list renders; Play starts media and panel from one click |
| FR-02 | The news media plays with captions synchronised to the transcript | P0 | Caption text changes within 300 ms of the word onset |
| FR-03 | The panel plays a recorded sign clip for every entry at its onset on the media clock | P0 | Contract test: entries sorted by onset; manual check on the demo script |
| FR-04 | Every entry shows a badge: validated, fingerspelled, or not available | P0 | Badge visible with text label and icon, not colour alone |
| FR-05 | Fingerspelled entries play letter clips in order | P0 | "Ohio" plays O-H-I-O |
| FR-06 | If signing runs longer than speech, the panel shows a catching-up indicator with the lag; no entry is skipped; playback ≤ 1.25× | P0 | Test timeline with dense entries shows the indicator; entry count played equals entry count in timeline |
| FR-07 | A disclaimer and attribution block appear above the panel before the first Play | P0 | Present on load; lists sources and licences |
| FR-08 | The weather lane fetches the current NWS forecast for a fixed location, narrates it with browser speech synthesis, and signs it | P0 | Forecast timestamp shown; fallback message if the API is unreachable |
| FR-09 | Typed text is glossed and signed with the same badges | P0 | Any sentence produces a timeline that validates against the schema |
| FR-10 | Coverage and fingerspelling rate for the current item are shown | P0 | Numbers match `stats` in the timeline |
| FR-11 | Function words dropped by the rule pass are shown struck through in the caption | P0 | "The rain is heavy" shows "the" and "is" struck through |
| FR-12 | A gloss-engine toggle switches between rules and the T5 model, showing which is active | P1 | Toggle changes `stats.gloss_engine`; T5 unavailable → toggle disabled with a note |
| FR-13 | The viewer can upload an audio or video clip ≤ 60 s, review the transcript, and sign it | P1 | Longer files rejected with the limit stated; transcript editable |
| FR-14 | A headline lane fetches current Guardian article text and signs it | P1 | Absent key hides the lane |
| FR-15 | Keyboard operation with visible focus for all controls | P0 | Tab through item list, Play, lanes, toggle |
| FR-16 | The app states it does not replace a human interpreter and lists what it cannot represent | P0 | Text present in the disclaimer |
| FR-17 | Uploaded audio is never stored beyond the session or sent to a third party | P1 | Code review; no outbound call in upload path |

## 5. Non-functional requirements

| ID | Requirement | Measure |
|---|---|---|
| NFR-01 | Cost | $0/month; cost model in the execution plan |
| NFR-02 | Memory | Peak RSS ≤ 1.8 GB with all models loaded; enforced in CI |
| NFR-03 | Demo latency | Timeline build ≤ 1 s (rules) / ≤ 4 s (T5) for a 60 s item on Community Cloud |
| NFR-04 | Availability for the viva | URL opened the morning of; screen recording as backup |
| NFR-05 | Licences | Every clip and dataset has a recorded licence permitting redistribution or non-commercial use; attribution rendered |
| NFR-06 | Reproducibility | Pinned dependencies; training notebook and export script in the repo; evaluation has a reproduction command |
| NFR-07 | Honesty | No claim in the UI or docs that is not deployed or measured |

## 6. Success metrics

| Metric | Target | Where measured |
|---|---|---|
| Lexical coverage on curated items | ≥ 85% | `stats.coverage` |
| Fingerspelling rate on curated items | ≤ 15% | `stats.fingerspelling_rate` |
| Demo script completion | 2 runs without intervention | Phase 3 exit |
| Peak RSS | ≤ 1.8 GB | CI |
| T5 vs rules | Reported, whichever wins | `docs/04-testing/evaluation.md` |

## 7. Assumptions to confirm (⚑)

A1 deadline 2026-10-30 · A2 T5 is the marked DL component · A3 ~4 dev-days/week · A4 ASL · D1–D5 as listed in the execution plan §10.
