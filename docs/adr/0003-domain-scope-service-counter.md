# ADR 0003 — Scope the domain to the service counter

**Date:** 2026-08-30 · **Status:** ~~Proposed~~ **SUPERSEDED by [ADR 0004](0004-scope-news-interpreter-panel.md)** on 2026-09-02. Retained for the record; the coverage arithmetic and the resolution ladder still apply.
**Reads with:** [resolution-cases.md](../02-design/resolution-cases.md) · [asl-linguistics-findings.md](../research/asl-linguistics-findings.md)

## Context

Research established that vocabulary coverage collapses on open-domain English: roughly
**50–70%** of content tokens at 300–500 signs, versus **85–95%** in a scoped domain. The
field's most-used benchmark (RWTH-PHOENIX-Weather) is itself domain-scoped, and treats the
narrow focus as a feature rather than a limitation.

The developer asked for a recommendation between classroom, café, and general.

## Decision

**Scope to the service counter** — café, reception desk, ticket window, pharmacy pickup.
Short, transactional, face-to-face exchanges.

## Rationale

**1. The existing model is already a service-interaction model.** Its 16 trained labels are
`hello, goodbye, good_morning, good_night, how_are_you, im_fine, please, thank_you, sorry,
excuse_me, yes, no, help, water, bathroom, dont_understand`. Every one is counter/service
vocabulary; none is classroom-subject-specific. The domain fits the asset we already have,
so no retraining is needed to change domain fit.

**2. Utterance length is the binding technical constraint.** Concatenated citation-form signs
remain intelligible over short utterances and degrade badly over long ones. Service-counter
turns are naturally short ("one large coffee, please"). Classroom explanation is naturally
long and continuous — exactly where a clip library fails. This is an engineering fit, not a
preference.

**3. It is the closest thing to the one permitted use case.** The WFD/WASLI carve-out for
signing avatars names *"hotels or train stations where instructions might be given about
where to check in or queue up"* — pre-recorded, static, non-interactive, Deaf-advised. A
service counter is that setting. **EUD Principle 2 explicitly names education** among
high-stakes settings where AI must not be imposed as a substitute for professional
interpretation, which makes classroom the weaker choice on ethics as well as on engineering.

**4. It exercises the resolution ladder without contrivance.** Prices and quantities produce
**digit signs** (C4); "name for the order?" produces **fingerspelling** (C5) exactly as a
real signer would; politeness formulas hit the **validated phrases** (B1); an unknown product
name produces a visible **refusal** (C6). Every implemented rung appears naturally in a
two-minute demo.

## Consequences

- **Vocabulary target: ~80–120 signs** — the service-counter terms themselves (drinks,
  sizes, payment, wait, receipt, order, card, cash, greetings, politeness), ranked by
  ASL-LEX frequency, plus 26 letters and 10 digits.
  *(Revised down from 300–500 by the audit. That figure came from ASL-CDI, a **general**
  core vocabulary. A counter interaction needs 40–60 signs; sourcing 500 clips would have
  consumed the schedule, 80 takes a week.)*
- **Expected coverage:** 85–95% lexical for in-domain utterances; fingerspelling reserved
  mainly for names, which is where a fluent signer would use it too.
- ~~Numeral incorporation~~ — **cut by the audit, and this was over-argued here.**
  Numeral incorporation is a *time-sign* process (THREE-WEEK, TWO-MONTH). A counter needs
  quantities and prices, which are plain digits: **10 clips, not 72.**
- **Demo script writes itself:** greeting → order with a number → name for the order →
  an out-of-vocabulary word that triggers a visible refusal.
- **Scope notice unchanged.** Still not an interpreter; still not for medical, legal,
  educational, emergency or employment use. Choosing a low-stakes domain does not remove
  the disclosure duty.

## Alternatives rejected

- **Classroom / education.** Attractive and relatable, and ASL-CDI vocabulary overlaps well.
  Rejected because EUD Principle 2 names education as high-stakes, and because classroom
  discourse is long-form and open-subject — the two properties a clip library handles worst.
- **General English.** Coverage falls to ~50–70%, fingerspelling rate rises toward the level
  ASL STEM Wiki identifies as a problem rather than a solution, and there is no bounded
  vocabulary to defend in a viva.
- **Medical triage.** Best-defined terminology of the three, but carries a genuine safety
  argument against a demo-grade system, and a supervisor may reasonably object. WFD/WASLI
  name health information among their areas of "particular concern."

## Related

Supplementary clip sources are **not** on the critical path. ASL Signbank (CC BY-NC-SA 4.0,
redistribution permitted with attribution) plus FSboard (CC BY 4.0) cover the need.
**ASL Citizen is deprioritised** — its licence permits research use but the disputed clause
bars redistribution, which is precisely our use case. Revisit only if Signbank coverage
proves thin for the target vocabulary.
