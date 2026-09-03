# ASL Linguistics, Vocabulary and Missing-Sign Research

**Researched:** 2026-08-30 · Three independent research streams
**Purpose:** answer three questions before finalising the design — how signs are structured
and segregated, where vocabulary legally comes from, and what happens when a sign is missing.

Claims that could not be verified from a fetched source are marked **UNVERIFIED**.

---

## ⚠️ 0. An unresolved licence conflict — resolve before building

Two researchers reached **opposite conclusions** about ASL Citizen (Microsoft Research,
83,399 videos, 2,731 signs):

| Stream | Claim | Basis |
|---|---|---|
| Sign-structure | "CC BY 4.0, redistributable" | Attributed to the arXiv paper |
| Vocabulary/licensing | **"you may not distribute the data or your modifications to the data"** | **Verbatim from the [MSR dataset licence page](https://www.microsoft.com/en-us/research/project/asl-citizen/dataset-license/)** |

**Treat the restrictive reading as authoritative until proven otherwise.** A verbatim quote
from the dataset's own licence page outranks a licence attributed to the paper — arXiv
preprints are frequently CC BY while the dataset they describe is not.

**ACTION REQUIRED:** open the MSR licence page and read it before any clip sourcing
decision. If redistribution is barred, ASL Citizen is unusable as a shipped asset source
regardless of how good the data is.

Similarly **UNVERIFIED:** Sem-Lex's data terms (gated behind a Google Form; the Apache-2.0
on the GitHub repo covers *code*, not data).

---

## 1. How an ASL sign decomposes — and why that does not let us build signs

### The parameters

Stokoe (1960) first showed signs are not holistic: they decompose into **tab** (location),
**dez** (handshape) and **sig** (movement). Orientation and non-manual markers were added
later — Stokoe's system explicitly has **no** facial expression, mouthing, eye gaze or body
posture. The modern teaching list is five parameters: **handshape, location, movement, palm
orientation, non-manual markers**.

Both ASL-LEX and ASL Signbank implement an abbreviated **Brentari Prosodic Model (1998)**.

### Measured inventory (counted directly from ASL-LEX 2.0 `signdata.csv`, 2,723 rows)

| Parameter | Distinct values |
|---|---|
| Handshape | **58** |
| Non-dominant handshape | 56 |
| Major location | 6 |
| **Minor location** | **37** |
| Selected fingers | 12 |
| Flexion | 7 |
| Path movement | 8 |
| Sign type (Battison + violations) | 6 |
| Contact, thumb position, spread, rotation, repetition… | binary each |

ASL's *contrastive* handshape inventory is usually estimated at **~40–50**; ASL-LEX's 58 is
a phonetic coding inventory, not a phoneme count.

### 🔴 The finding that kills parameter-based sign generation

Measured directly against the data, not quoted:

| Test | Result |
|---|---|
| Signs with a **unique full 17-feature vector** | **1,926 / 2,723 = 70.7%** |
| Signs unique on the **three textbook parameters** (handshape + major location + path) | **301 / 2,723 = 11%** |
| Largest single three-parameter collision cell | **57 different signs** |

A 2026 paper puts it concretely: conditioning on 8 ASL-LEX attributes, *book* and *walk*
are **identical across all 8**.

**Conclusion: the parameters are a contrastive index, not an articulatory specification.**
They are excellent for search, similarity and neighbourhood density. **You cannot animate
from them** — 29% of signs cannot even be *distinguished* by their full feature vector.

ASL-LEX also codes only the **citation form**, not regional or signer variants.

---

## 2. Sign identity: never key on an English word

### The ID-gloss convention

An **ID-gloss** (Johnston 1991) is "the common identifier for each lexical sign" — **a
label, not a translation.** This is the single most important data-modelling decision in
the project.

**One English word → many distinct signs** (live from ASL Signbank, 2026-08-30):

| English | Distinct ASL signs |
|---|---|
| "run" | `RUNasym`, `RUNsym`, `RUN-ARMS`, `RUNNY-NOSE` |
| "give" | `GIVEo`, `GIVEx`, `GIVE-ME`, `GIVE-UP`, `GIVE-TIP8`, `GIVE-TIP9` |
| "back" | `BACK`, `BACK-BODY`, `BACK-OF`, `BACK-TO`, `BACK-OF-MIND`, … |
| "apple" | `APPLEa`, `APPLEck`, `APPLEx` |

**One sign → many English words:**

| Sign | English translations |
|---|---|
| `PROMISE` | absolutely, commit, confirm, dedicate, guarantee, promise |
| `TRASH` | basket, bin, garbage, trash, waste, wastebasket |
| `BAG` | bag, handbag, luggage, purse, suitcase, bucket, container |

38 English words in ASL-LEX map to ≥2 distinct entries (*shave* → 4, *stupid* → 3).

**Desai et al. (2024), a Deaf-led review, name this "the tyranny of glossing"** and show
WLASL collapsing PRESENT-as-gift and PRESENT-as-time into a single gloss. That is exactly
what English-keyed lookup does.

### Signbank's naming scheme (SLAASh conventions)

- **Two tiers:** *Lemma ID-gloss* (abstract category) and *Annotation ID-gloss* (unique per
  citation form).
- Variants take lowercase suffixes: handshape (`APPLEx`, `BIGb`), orientation
  (`EXERCISEsup`), location (`fh`, `ch`, `ns`), movement (`wig`, `alt`, `rot`), handedness
  (`sym`/`asym`).
- Derivational morphology gets separate IDs (TEACH vs TEACHER); inflectional does not.
- Compounds get **one** lemma ID despite multiple morphemes.
- Proposed-but-unapproved glosses carry a `~` prefix.
- **Note:** the classroom `#BACK` convention is *not* what Signbank uses — zero glosses in
  the 4,526-entry inventory begin with `#`. Loan signs appear as ordinary glosses whose
  keyword list flags them (`BACK-TO` carries "fingerspelled, FS(back)").

---

## 3. Where vocabulary legally comes from

| Source | Size | Machine-readable list? | Licence | Ship the video? |
|---|---|---|---|---|
| **ASL Signbank ECV** | **4,526 entries** | **YES — free, no login: `aslsignbank.com/static/ecv/asl.ecv`** | CC BY-NC-SA 4.0 | **Yes**, with attribution + weblink |
| **ASL-LEX 2.0** | 2,723 signs, 191 columns | YES — CSV via [OSF](https://osf.io/zpha4/) | CC BY-NC 4.0 (**data only**) | **NO** — videos "may not be saved, displayed, or otherwise used" |
| **FSboard** (fingerspelling) | 3.2M chars, 147 Deaf signers, MediaPipe landmarks | YES — Kaggle | **CC BY 4.0** | **YES — fully permissive** |
| ASL-CDI 2.0 | **533 curated items** | Yes | — | Videos inherit ASL-LEX restriction |
| ASL Citizen | 83,399 videos | Behind MSR licence | **DISPUTED — see §0** | **Assume no** |
| Sem-Lex | 3,149 signs / 91,148 videos | Repo Apache-2.0 | Data ToU gated | UNVERIFIED |
| WLASL / MS-ASL | 2,000 / 1,000 glosses | Yes | C-UDA / MSR | **No** — YouTube URLs, third-party video |
| Wikimedia ASL letters | 26 SVG | Yes | **Public domain** | Yes |

### The two best finds

**1 · ASL Signbank ECV is our English→gloss index, already built.** It is ELAN External
Controlled Vocabulary XML (~1.1 MB, 4,526 entries), each carrying a numeric `CVE_ID`, the
ID-gloss, and **a `DESCRIPTION` field of English synonyms**. Free, no login, machine-readable,
CC BY-NC-SA. We adopt this schema rather than inventing one.

**2 · FSboard is the only fully permissive ASL resource in the entire review.** CC BY 4.0,
147 Deaf signers, and it ships MediaPipe landmarks — exactly what our pose renderer consumes.

**Join rate:** 2,003 of 2,723 ASL-LEX rows (**73%**) carry a `SignBankAnnotationID`, so the
two datasets join on the ID-gloss string.

### Traps

- **Wikimedia "ASL numbers" digits are labelled LSQ** (Quebec Sign Language), which diverges
  from ASL on 6–9. Do not ship them as ASL without checking each.
- **The Gallaudet TrueType font** has contradictory licence claims (personal-use-only per
  FontSpace vs "free" elsewhere). **Treat as unusable.**
- **Static letter images are not adequate fingerspelling.** Real fingerspelling is heavily
  co-articulated; final handshapes for some letters look similar but are distinct *during
  the transition*. Confusable clusters: **a/e/o** and **m/n/s/t**. Fluent readers read the
  envelope of movement, not frozen shapes.

### How many signs?

There is **no published ASL frequency list**, for a principled reason: ASL has no written
form, so frequency needs hand-transcribed video corpora, and existing ones "do not even
approach" spoken-corpus scale.

**The defensible substitute:** ASL-LEX carries **subjective frequency ratings** — deaf
signers rating how often each sign appears in everyday conversation, 1–7, with 25–35 ratings
per sign from 129 participants. The ASL-LEX authors' own position is that **absent large
corpora, subjective frequency may be preferable to corpus counts.** That makes sorting by
frequency Z-score a *citable* method rather than a guess.

**Recommended: 300–500 signs = ASL-CDI 2.0's 533 curated items** (already filtered for
outdated signs, homophones, dialect variants and non-1:1 glosses) **∩ ASL-LEX frequency
ranking**, plus domain terms, letters and digits.

---

## 4. What a clip library can and cannot represent

### ✅ Representable

| Category | Notes |
|---|---|
| Frozen / citation-form lexical signs | The bulk of a beginner vocabulary |
| Lexicalized fingerspelling (loan signs) | **38 flagged in ASL-LEX.** Play as whole units — spelling them letter-by-letter is wrong |
| Initialized signs | **363 flagged (13.3%).** Play attested ones; never *generate* initialized forms |
| Compounds | **225 flagged.** Whole units only — MOTHER+FATHER ≠ PARENTS, compounds phonologically reduce |
| Fingerspelling | 26 letters + 10 digits; a known-crude approximation |
| **Numeral incorporation** | **The one productive process a clip library can economically fake** — "Rule of 9", ~9 numerals × ~8 time bases ≈ **72 clips** covers it |

### ❌ Not representable — state this plainly, don't hide it

| Category | Why |
|---|---|
| **Directional / agreement verbs** (GIVE, ASK, TELL, SHOW, HELP, PAY) | Path direction encodes subject and object. The literature: "there may be an infinite number of possible locations." An analog parameter cannot be enumerated as clips |
| **Spatial loci / referent tracking** | Discourse-level, unbounded |
| **Classifiers / depicting verbs** | Productive by definition — not listable |
| **Phrase-scoped non-manual markers** | Brow raise = question, headshake = negation. They **scope over phrases, not signs**, so they cannot be baked into per-sign clips. Absent from ASL-LEX entirely (not among its 191 columns) |
| **Coarticulation and prosody** | Concatenated citation forms look robotic and at sentence length are often unintelligible to fluent signers |
| **Role shift, aspect, ASL syntax** | English word order ≠ ASL |

**The ASL Citizen authors say this themselves**, and it is the single best sentence to quote
in the report: the dataset holds "isolated signs like those in dictionaries," only "a subset
of sign languages," and they **warn researchers against assuming that "tokenizing a video
into a sequence of signs" suffices for translation, noting this approach has generated
community objections.**

### The one place parametric composition *is* reachable

In **pose space**, the start and end wrist positions of a directional verb are just numbers.
Retargeting path endpoints for a hand-curated handful of verbs (GIVE, ASK, TELL, SHOW, HELP,
PAY) is achievable in weeks and is a genuine, narrow, honest contribution. Everything else in
the renderer is playback.

---

## 5. Can a machine generate a sign it has never seen?

**No. Not for a student, and not for anyone, right now.**

wSignGen's own paper: current sign-language-production methods **"only perform close-set
generation and cannot handle words that were not previously seen."**

Two mechanisms get confused, and the distinction matters enormously:

| Mechanism | What it really is | Example |
|---|---|---|
| **Semantic re-routing** | Maps a new *English word* onto a motion already learned. A lexicon lookup with a fuzzy key | wSignGen: CLIP puts *desk* near *table*, so "desk" plays TABLE's motion. If the real sign differs, the output is **confidently wrong** |
| **Phonological composition** | Genuinely renders unseen notation — but only if every *glyph* was seen | Ham2Pose. **But writing HamNoSys for a missing sign requires someone who already knows the sign.** It relocates the problem to a Deaf signer rather than solving it |

**Quality of the state of the art:** Ham2Pose reports **rank-1 accuracy 0.08, rank-10 0.35**,
produces coarse 2D skeletons, and states "predicted hand shapes or movements are not always
entirely correct." The SignWriting animation repo is **archived read-only** (2026-08-17).

**No public large-scale ASL lexicon in HamNoSys exists** (DGS, PJM, GSL, LSF, LSE and KSL do —
ASL does not). The one notation→avatar path with a working renderer (HamNoSys → SiGML →
JASigning) is **deprecated by its own maintainers** and is not open source.

**Resourcing check:** the EU SignON project had **€5.6M**, a multi-country consortium and
three years, and reached TRL6 — a prototype, in a *low-stakes hospitality* domain.

**The failure mode that decides the design:** fingerspelling announces itself. **A
confidently wrong generated sign does not.**

Notably, the strongest 2024–2025 systems (SOKE / Signs as Tokens) are moving *toward*
retrieval from a sign dictionary, reporting +20–24% from adding it. We are not behind the
field by doing retrieval — **we are at it.**

---

## 6. What the Deaf community and regulators actually say

### WFD + WASLI, Statement on Use of Signing Avatars (2018)

> "The difference in linguistic quality between humans and avatars is why WFD and WASLI
> **cautions against the use of signing avatars as a replacement for human signers.**"

Their reason #1 is precisely our architecture:

> "Direct word-for-sign translations often do not exist. Achieving equivalence relies on
> more than just lexical word-sign matches."

The single carve-out, with its conditions intact:

> avatars "might be used for **pre-recorded static** customer information… **as long as deaf
> people have been involved in advising on the appropriateness of the signed sentences, and
> that there is no interaction or 'live' signing required.**"

**A real-time English→ASL app is interactive and live. It sits outside that carve-out.**

They also state: **"It is not advisable to pick only one sign for one word… The WFD and
WASLI therefore does not support any formal standardization activities related to any sign
language."** A UI showing one canonical sign per word is therefore taking a contested
position — where we hold variants, we should show them.

### Desai, De Meulder, Hochgesang, Kocab & Lu (2024) — Deaf-led, 101 papers reviewed

- 64 of 101 papers frame themselves as fixing deaf–hearing communication barriers; the
  authors argue this "portrays deaf people as deficient and in need of technological
  interventions."
- "The tyranny of glossing" — glosses "cannot represent all linguistic phenomena in signing."
- Risk named: users "compelled to adjust their sign language use to accommodate the
  limitations of AI technologies… **a form of linguistic subordination to technology.**"

### EUD, *Sign Language in the Era of AI* (July 2025)

- **Principle 5:** users must be told they are dealing with AI-generated content **"and from
  what resources the content is generated"** — provenance, not just an "AI" badge.
- **Principle 2:** AI "must not be imposed as a substitute for human professional
  interpretation, particularly in high-stakes settings such as education, justice, health,
  political life, and employment."
- **Principle 7:** training data must come from Deaf native signers, **not** from interpreted
  events or news broadcasts. *(This would rule out PHOENIX14T as a source.)*

### EU AI Act Article 50 — in force since 2 August 2026

AI-generated video must be marked machine-readable and detectable; disclosure must be "clear
and distinguishable," at first exposure, understandable "without need for any specific
technical tools."

**Design consequence: a single global "AI-generated" banner does not discharge this.**
Provenance must be **per-sign**, because within one sentence some signs are validated
recordings and others are fallbacks.

### Who may coin a new sign

Consistently documented Deaf-community norm, backed by Deaf-led organisational policy: new
signs come from within the Deaf community. Signing Savvy's advisory board: a hearing person
inventing signs "constitutes disrespect toward ASL and the Deaf community"; their guidance is
"when in doubt, finger spell the word." The parallel norm for **name signs** — which must be
given by a Deaf person and ratified by the community — is the clearest illustration.

**State this accurately:** it is a strong, near-unanimously-backed community norm reinforced
by Deaf-led policy. It is **not** a law, and no source frames it as one. Do not overstate it;
do not soften it either.

---

## 7. The missing-sign decision ladder

Descending preference. **Every rung below rung 0 must be visibly labelled in the UI.**

| Rung | Action | Legitimate without Deaf review? |
|---|---|---|
| **0** | **Validated clip**, keyed to a *concept* not an English string | ✅ |
| **1** | Validated clip for a Deaf-reviewed **synonym or superordinate**, mapped via ASL-semantic sense IDs — never English string similarity | ✅ with guardrails. Label "closest available sign" |
| **2** | **Pre-authored, Deaf-reviewed expansion** — a stored gloss sequence written by a Deaf signer. Expensive per term, and the *best* answer | ✅ if pre-authored |
| **3** | **Lexicalized fingerspelling** (loan sign) — playback only from a recorded set | ✅ |
| **4** | **Fingerspelling** — recorded handshapes. The honest floor | ✅ Label "fingerspelled — no established sign in this system" |
| **5** | **Refuse.** "No ASL rendering available for this term" — a first-class output, not an error | ✅ |
| ═══ | **THE LINE — an automated system without Deaf review stops here** | ═══ |
| 6 | Neural pose generation of a sign not in the validated set | ❌ |
| 7 | Rule-based initialization | ❌ |
| 8 | Machine-invented compounds or ungrounded classifiers | ❌ |
| 9 | Any coined sign | ❌ **Never** |

**The principle:** rungs 0–5 are retrieval or refusal, and all are honest about being so.
Rungs 6–9 **fabricate form** — the category Deaf-led sources object to, and the category a
user cannot detect.

**One caution on fingerspelling volume.** ASL STEM Wiki (37 certified interpreters, 316
hours) measured fingerspelling at **18.6% of all words**, versus 3.3–8.7% in casual
discourse, and says plainly: "the overreliance on fingerspelling is unlikely to help deaf
students acquire a conceptual understanding of the term." High fingerspelling rate is an
**index of failure, not of skill.** Measure and report ours.

---

## 8. Recommended data model

```
Sign
  sign_id          -- ASL Signbank CVE_ID (stable numeric surrogate key)
  id_gloss         -- Signbank Annotation ID-gloss, e.g. "RUNasym"   ← PRIMARY IDENTITY
  lemma_id_gloss   -- e.g. "RUN"
  asllex_entry_id  -- join key, ~73% coverage
  variant_tag      -- "asym", "x", "sup", "fh" … per SLAASh
  status           -- attested | proposed(~) | deprecated

SignKeyword        -- many-to-many. NEVER key on English
  sign_id, keyword, rank, agreement   -- ASL-LEX DominantTranslationAgreement

SignMorpheme       -- 1..6 rows per sign
  handshape, non_dominant_handshape, selected_fingers, flexion,
  major_location, minor_location, contact, sign_type,
  path_movement, repeated_movement, ulnar_rotation

SignLexical
  lexical_class, is_initialized, is_fingerspelled_loan, is_compound,
  n_morphemes, sign_frequency_z, iconicity_z, neighborhood_density

SignMedia
  media_type (video|pose), uri, licence, source, signer_id,
  attribution_required, consent_recorded, onset_ms, offset_ms

SignBehaviour      -- ← THE HONESTY LAYER. Drives the UI and the fallback ladder
  inflection_class -- plain | directional | spatial | classifier | numeral_incorporating
  requires_nmm     -- none | question | negation | topic
  renderable       -- exact | approximate | not_representable
  caveat_text      -- shown to the user whenever renderable != exact
```

Plus a phrase-level layer the sign table cannot carry:
`Utterance{ nmm_span(type, start, end), locus_assignments[], role_shift_spans[] }`.
Even if we only *display* these as an annotation ribbon rather than rendering them, **having
the slot is what makes the project linguistically honest.**

**Ingest order:** (1) `asl.ecv` → 4,526 gloss + keyword records, free; (2) ASL-LEX
`signdata.csv` → phonology and ratings, join on ID-gloss, ~2,000 covered; (3) clip video from
a licence-verified source; (4) MediaPipe → pose, offline.

---

## 9. Verdict

**Parameter-based composition of new signs: not feasible.** The features cannot even
distinguish 29% of existing signs; no public ASL HamNoSys lexicon exists; the one working
notation→avatar renderer is deprecated; the best research result is rank-1 0.08.

**Generation of unseen signs: not feasible for anyone**, per the field's own papers.

**What is feasible, and defensible:** an **ID-gloss-keyed retrieval system** over a
licence-clean validated clip set, with rule-based reordering, a visible fallback ladder, a
first-class refusal state, per-sign provenance labelling, and a limitations section citing
§4 and §6.

**The intellectual contribution is not a generator. It is the coverage-and-disclosure
architecture** — precisely what the WFD/WASLI, EUD and Desai et al. critiques identify as
missing. Framed as *honest degradation under lexical gaps*, this is a defensible master's
project. Framed as *generating missing signs*, it overclaims — and overclaiming is itself
named as a harm in the literature.

Optional narrow novelty within reach: **pose-space endpoint retargeting for ~6 directional
verbs.**
