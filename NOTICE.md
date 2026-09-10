# Third-party content and attributions

The MIT licence in `LICENSE` covers the code in this repository only. Media and data
under `static/` and `data/` come from the sources below and keep their own terms.
`data/lexicon/attribution.json` is the per-clip record; `tests/test_lexicon.py` checks that
every clip in `data/lexicon/concepts.json` has a licence and an attribution URL.

## Shipped in this repository and shown in the app

| Content | Source | Terms | Attribution text shown in the app |
|---|---|---|---|
| Sign clips (168 under `static/clips/`) | "The ASL Dictionary", Center for Accessible Technology in Sign (Georgia Tech / Atlanta Area School for the Deaf), via archive.org | Public Domain (per item rights field) | The ASL Dictionary, CATS, archive.org |
| Sign clips (letters, digits and gaps: 36 under `static/letters/`, 54 under `static/clips/`) | ASL Signbank | CC BY-NC-SA 4.0; direct weblink per clip; no draft videos | Hochgesang, J. A., Crasborn, O., & Lillo-Martin, D. (2017-2026). ASL Signbank. https://aslsignbank.com |
| News audio and transcripts (6 excerpts under `static/news/`, timings under `data/demo/`) | Voice of America newscasts via the Internet Archive `VOANewscasts` collection | Public Domain (VOA-produced content); credit VOA | Voice of America |
| Forecast text (live lane, and one recorded sample in `tests/fixtures/`) | US National Weather Service API | US government work | National Weather Service |

## Used to build the T5 engine (not shipped; attributed in the app when the T5 engine is selected)

| Content | Source | Terms | Attribution text shown in the app |
|---|---|---|---|
| Training data | ASLG-PC12 (Othman & Jemni, 2012) | CC BY-NC 4.0 | T5 training data: ASLG-PC12 |
| Base model | google-t5/t5-small | Apache-2.0 | Gloss engine: google-t5/t5-small fine-tuned on ASLG-PC12 |

## Considered and not used

The Guardian Open Platform (headline lane, optional in the plan) was never built. Wikimedia Commons letter images
were a fallback in the plan and are not in the repository. Neither appears in the app or in any timeline.

This project is non-commercial.
