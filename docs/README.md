# docs/

The SDLC record, one folder per stage. Documents are written before the code they describe (working rule in `CLAUDE.md`). Files marked **generated** are produced by a script and carry a header saying so; edit the script, not the file.

| Folder / file | What it is |
|---|---|
| `00-execution-plan.md` | The plan: scope, verified resources, trade-offs, folder structure (§5 is kept true to the repo), SDLC process, cost model, pre-mortem, open items |
| `01-requirements/prd.md` | Requirements FR-01..17, NFR-01..07, success metrics, assumptions to confirm |
| `02-design/system-design.md` | The TRD: components, data model, flows, pacing policy, provenance rules, memory budget, deployment, failure handling |
| `02-design/diagrams/` | Three archify diagrams: `*.json` sources, `*.html` delivered viewers, `*.png` containment captures (evidence) |
| `03-implementation/dev-log.md` | One entry per working day: done, blocked, decided. A log; never rewritten |
| `04-testing/test-strategy.md` | Layers as built, requirement traceability, known gaps |
| `04-testing/accessibility.md` | WCAG 2.2 AA pass: axe result, contrast table, keyboard and screen-reader changes |
| `04-testing/evaluation.md` | **generated** by `scripts/evaluate_gloss.py`: rules vs T5 |
| `04-testing/coverage-rules.md` | **generated** by `scripts/coverage_report.py`: coverage per item |
| `05-deployment/deployment.md` | Deployment record, deploy steps, release procedure, runbook, deploy log |
| `adr/` | Architecture decision records; index below |
| `research/` | Dated evidence: 2026-08-30 findings carried from the previous iteration, 2026-09-02 verification reports, `spikes.md` (Phase 0 spikes), `timing-findings.md`, `clip-review-*.jpg` (contact sheets of every clip) |

## ADR index

| ADR | Decision | Status |
|---|---|---|
| [0001](adr/0001-hosting-and-runtime-architecture.md) | Self-hosted runtime architecture (previous iteration) | Superseded by 0002 |
| [0002](adr/0002-hosting-streamlit-community-cloud.md) | Streamlit Community Cloud hosting | Accepted; its R2 storage clause amended by 0007 |
| [0003](adr/0003-domain-scope-service-counter.md) | Service-counter scope (previous iteration) | Superseded by 0004 |
| [0004](adr/0004-scope-news-interpreter-panel.md) | News-bulletin interpreter panel with a bounded lexicon | Accepted |
| [0005](adr/0005-gloss-engine-rules-and-t5.md) | Rule pass by default, T5-small via CTranslate2 behind a toggle | Accepted; evaluated 2026-09-04, rules stay default |
| [0006](adr/0006-rendering-recorded-clips.md) | Recorded clip playback; no skeleton view, avatar or generated video | Accepted |
| [0007](adr/0007-clip-sources-and-storage.md) | CATS public-domain clips primary, Signbank secondary, clips in the repo | Accepted |
| [0008](adr/0008-synchronisation-interpreter-paced.md) | Bulletin paced to the interpreter; active spans at fixed rates; names once | Accepted |

Still to write for hand-in: `05-deployment/demo-script.md` and `06-reflection.md`.
