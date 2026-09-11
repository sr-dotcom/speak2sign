# Design critique, 2026-09-11 (impeccable `critique`, run on the page after front-end changes 1–5)

**Method:** ⚠️ DEGRADED: dual-agent for the design review (Assessment A ran as an isolated sub-agent from four screenshots, desktop 1440 px and mobile 375 px, before and during playback), but the deterministic detector (Assessment B) did not run: the skill's launcher downloads a binary on first use, and downloaded binaries are not executed in this project's sessions. Overlays therefore unavailable. Target: the deployed page (`app.py` + `src/speak2sign/ui/panel.*`), mode Operate. Screenshots were taken from a local run of commit e5deb61.

## Design health score (Assessment A)

| # | Heuristic | Score | Key issue |
|---|---|---|---|
| 1 | Visibility of system status | 3 | "Sentence 1 of 3" and the gloss are right; no progress across a ~152 s run |
| 2 | Match system / real world | 2 | "Gloss engine", "rules / t5"; uppercase glosses (NIGHT for "late") unexplained |
| 3 | User control and freedom | 3 | Play/Pause/Restart only |
| 4 | Consistency and standards | 2 | Two button systems (Streamlit vs panel); lowercase sidebar labels |
| 5 | Error prevention | 3 | Changing speed mid-play reruns silently |
| 6 | Recognition rather than recall | 2 | Legend below the fold |
| 7 | Flexibility and efficiency | 2 | Shortcuts exist but are invisible |
| 8 | Aesthetic and minimalist design | 2 | ~180 words and four metrics before Play |
| 9 | Error recovery | 3 | "(clip unavailable)" fallback is honest |
| 10 | Help and documentation | 3 | Nothing explains why signing takes 5.6× the audio |
| **Total** | | **25/40** | mid band |

## Design-specificity verdict

Half-authored. The panel (dark stage, gloss and badge row, amber current word, waiting bar) is unmistakably this product; everything around it is stock Streamlit. Deterministic scan: not run (see Method).

## Priority issues and what was done with them

| Sev | Finding (Assessment A) | Decision | Reason |
|---|---|---|---|
| P0 | Mobile: captions and interpreter never on screen together; the panel sits below a 470 px caption card | **Applied** | The dual view is the product. Panel first on narrow screens and pinned at the top while the captions scroll under it (only while the panel's measured height leaves at least 35% of the viewport for captions, re-checked on resize and whenever the panel grows; a short landscape screen scrolls normally); the controls scroll away with the page; captions 17 px |
| P1 | 152 s of signing for 27 s of audio is never framed; the waiting bar reads as a fault | **Applied** | Status line states the projected time and that the narration waits; a thin progress bar advances per sign |
| P1 | The current-word highlight lands on dropped words with no link to the sign | **Applied in part** | The panel now shows the source word under the gloss ("late" → NIGHT). The highlight keeps following the narration, dropped words included: the narration is saying that word, and pretending otherwise would be the desync. A caption↔entry link needs a contract field and is left for later |
| P2 | Legend below the fold; Streamlit chrome shows "Deploy" | **Applied in part** | Toolbar set to minimal. The legend stays under the ribbon (the ribbon is what it explains) |
| P3 | Jargon in the sidebar: "Gloss engine: rules / t5" | **Applied** | "Translation: Rule-based / T5 model"; the engine keys are unchanged underneath |
| minor | The "Press Play" pill overlaps the signer's hands | **Applied** | Moved to the top-left corner |
| minor | The waiting bar covers the captions, the channel a Deaf viewer is reading | **Applied** | Moved into the panel side |
| minor | Struck words at 40% opacity are near-invisible | **Applied** | 55%, line-through kept |
| minor | Signer video small on desktop | **Applied** | Stage columns 1fr 1fr instead of 3fr 2fr |
| minor | "NIGHT VALIDATED" shown before play | **Rejected** | A shown signer must carry its label and badge (Codex finding on change 1; honesty rule) |
| minor | Sidebar "How it works" duplicates the disclaimer | **Rejected** | The disclaimer is the legal/ethical statement, the sidebar is the mechanism; different jobs |
| P3 | Skip-sentence and seek controls | **Not now** | A structure change to playback; would need its own design and tests |

## Persona red flags (Assessment A, kept for the record)

- First-time phone visitor: two screens of text before Play; tab bar clips; never sees signer and captions together (addressed by the P0 fix).
- Viva examiner on a laptop: the 4% remainder after 68% + 28% is not labelled on the card; "not available" is never demonstrated on this item.
- Deaf or hard-of-hearing viewer: small signer, faint struck words, waiting bar over the captions (all three addressed).

## Questions the critique raised, left open

1. If the disclaimer is non-negotiable, why is it the largest element on the page rather than the panel that proves it?
2. Should the interpreter be the hero element, with the news as the sidecar, given that the ASL channel is the research contribution?
3. Would a "Not signed: N words" line under the panel say more about honesty than the coverage metric does?
