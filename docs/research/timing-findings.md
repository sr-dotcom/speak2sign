# Timing findings: signing time vs speech time (2026-09-03)

Measured with the real lexicon (258 clips) and the rule pass on the six curated items, onsets estimated at 2.6 words/s.

| Item | Speech s | Sign clips, full | Letter clips, full | Sign clips, active | Letter clips, active | Active / speech |
|---|---|---|---|---|---|---|
| samoa-oil-spill | 27.3 | 109.7 | 204.5 | 79.5 | 174.1 | 9.3× |
| sichuan-landslide | 20.0 | 91.0 | 120.7 | 72.0 | 103.7 | 8.8× |
| astronauts-return | 29.6 | 120.5 | 166.6 | 95.0 | 144.1 | 8.1× |
| california-fire-warning | 26.2 | 121.9 | 56.6 | 97.8 | 47.1 | 5.5× |
| pope-infection | 22.7 | 119.4 | 119.3 | 98.0 | 104.7 | 8.9× |
| canada-new-pm | 41.9 | 200.3 | 208.1 | 156.7 | 179.3 | 8.0× |

"Active" = the span of visible motion, measured by frame-difference energy above 12% of the clip's peak (`data/lexicon/active_spans.json`). Clips are 78% active overall; CATS clips average 3.59 s (2.77 s active), Signbank 2.32 s (1.83 s active), letters and digits 2.15 s (1.78 s active).

## What this means

1. Dictionary citation clips are slow by nature: about 2.8 s of motion per sign against about 0.4 s per spoken word. Conversational ASL runs near one sign per second; these clips are demonstration speed.
2. Fingerspelling from letter clips costs about 1.8 s per letter; a fluent signer spells at roughly 0.2 s per letter. A six-letter name takes 11 s.
3. Trimming to the active span and modest speed-ups do not close the gap. Even at 1.25× for signs and 2× for letters, signing takes three to four times as long as speech.

Conclusion: a panel that plays validated clips cannot keep up with a news anchor. The honest design is a bulletin paced to the interpreter, not an interpreter racing the bulletin. See ADR 0008 (to be revised) and the options put to the developer on 2026-09-03.
