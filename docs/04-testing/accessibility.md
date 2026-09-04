# Accessibility pass (WCAG 2.2 AA, 2026-09-04)

Scope: the deployed page and the interpreter panel. An accessibility project must at least meet the basics for its own interface; this records what was checked, how, and what changed.

## 1. Automated check: axe-core 4.10.2

Run in Chromium against the local app with the News tab mounted (panel inside its shadow DOM, which axe traverses), tags `wcag2a wcag2aa wcag21a wcag21aa wcag22aa`.

| Result | Count |
|---|---|
| Violations | **0** |
| Passes | 28 rules |
| Incomplete (needs a human) | 1: `video-caption` |

`video-caption`: the sign clips carry no caption track because they are silent recordings of a sign; the "caption" for each clip is the gloss, badge and note rendered under the video and announced through a live region. Recorded as a deliberate decision, not a gap.

## 2. Contrast (computed from the stylesheet, WCAG formula)

| Element | Ratio | AA (4.5:1) |
|---|---|---|
| Ribbon chip, validated | 5.33 | pass |
| Ribbon chip, fingerspelled | 5.23 | pass |
| Ribbon chip, name | 7.65 | pass |
| Ribbon chip, not available | 7.02 | pass |
| Panel badge, validated | 6.55 | pass |
| Panel badge, fingerspelled | 6.80 | pass |
| Panel badge, name | 6.32 | pass |
| Panel badge, not available | 5.41 | pass |
| Panel text on panel background | 15.17 | pass |
| Current caption word (dark on amber) | 8.52 | pass |
| Waiting bar text | 4.80 | pass |
| Play button | 6.27 | pass |
| Text-sign card | 14.07 | pass |

Badges never rely on colour alone: each carries its text label, and the current caption word is bold and underlined as well as highlighted.

## 3. Keyboard and screen reader

| Check | Result | Change made |
|---|---|---|
| Play, Restart reachable by Tab, activate with Enter/Space | Yes (native buttons) | — |
| Visible focus | `:focus-visible` outline, 2 px, 4.5:1 on the panel background | — |
| Video elements as tab stops | Were two empty stops | `tabindex="-1"`; they have no controls |
| Status changes announced ("Sentence 2 of 3", "waiting for the interpreter", "Done …") | Not before | `role="status" aria-live="polite"` on the status line and the waiting bar |
| Current sign announced (gloss, badge, note) | Not before | `aria-live="polite" aria-atomic` on the sign line |
| Panel and sections named | Not before | `role="region"` with labels; videos labelled "Recorded ASL sign clip, silent; the sign is named below" |
| Ribbon chips readable in order | Visible text is gloss + badge label, read in document order; the note is a `title` only | Tried `role`/`aria-label` on the chips: **Streamlit strips `role` and `aria-*` from both `st.markdown` and `st.html`** (verified in the DOM), so the panel's live regions carry the note instead |
| Streamlit widgets (tabs, radio, text areas, uploader, selectbox) | Native Streamlit accessibility; labels present (collapsed labels keep their accessible name) | — |
| Reduced motion | No animation is used; explicit `prefers-reduced-motion` rule added anyway | added |
| Page language and title | `lang="en"`, title "Speak2Sign" | — |

## 4. Content-level accessibility (the project's own subject)

- Disclaimer at first exposure states what the panel cannot represent and that it is not a substitute for a human interpreter (FR-16).
- Every sign carries provenance; nothing is presented as ASL that was not retrieved from a validated clip.
- Function words dropped by the gloss pass are shown struck through, so the loss is visible, not silent.
- The bulletin is paced to the interpreter (ADR 0008): a Deaf viewer is never shown a panel racing ahead or lagging a minute behind.

## 5. Not done / limits

- Manual screen-reader session (NVDA) not performed; live regions are implemented per spec but unheard by a human so far. **UNVERIFIED** until someone runs NVDA through one item.
- Safari and Firefox: the panel's autoplay-after-click and speech synthesis paths are untested there.
- The Streamlit host chrome (Fork button, app menu) is outside our control.

Reproduce the automated check: open the app, load axe-core 4.10.2 from cdnjs in the console, `axe.run(document, {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}})`.
