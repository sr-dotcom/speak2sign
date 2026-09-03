"""The honesty layer. The only place that decides what a badge means and what the app must say about itself."""

DISCLAIMER = (
    "Research demonstration. This panel retrieves recorded ASL clips for words it has validated "
    "signs for, fingerspells the rest, and says so on every sign. It does not represent ASL grammar "
    "(directional verbs, classifiers, facial grammar) and is not a substitute for a human interpreter."
)

SOURCES = {
    "cats": {"licence": "Public Domain", "text": "Sign clips: The ASL Dictionary, Center for Accessible Technology in Sign (Georgia Tech / Atlanta Area School for the Deaf), via archive.org",
             "url": "https://archive.org/search?query=creator%3A%28%22Center+for+Accessible+Technology+in+Sign%22%29"},
    "signbank": {"licence": "CC BY-NC-SA 4.0", "text": "Sign clips: Hochgesang, J. A., Crasborn, O., & Lillo-Martin, D. (2017-2026). ASL Signbank.",
                 "url": "https://aslsignbank.com"},
    "voa": {"licence": "Public Domain", "text": "News audio and transcript: Voice of America newscasts via the Internet Archive VOANewscasts collection",
            "url": "https://archive.org/details/VOANewscasts"},
    "nws": {"licence": "US government work", "text": "Forecast text: US National Weather Service API", "url": "https://api.weather.gov"},
    "guardian": {"licence": "Non-commercial developer terms", "text": "Headline text: Powered by the Guardian Open Platform", "url": "https://open-platform.theguardian.com"},
}
LANE_SOURCE = {"curated": "voa", "weather": "nws", "headline": "guardian"}

BADGE = {"sign": "validated", "number": "validated", "fingerspell": "fingerspelled", "name": "name", "none": "not_available"}


def badge(entry_kind):
    """Map a rule-pass entry kind to the badge shown on screen. Dropped words have no badge; they live in the caption."""
    if entry_kind not in BADGE:
        raise ValueError(f"no badge for entry kind {entry_kind!r}")
    return BADGE[entry_kind]


def note(entry, concept):
    if entry.kind == "fingerspell":
        return entry.why or "no established sign in this system"
    if entry.kind == "number":
        return "number, signed digit by digit"
    if entry.kind == "name":
        return entry.why or "name already fingerspelled once; shown as text"
    if entry.kind == "none":
        return entry.why or "no honest rendering available"
    if concept is not None and concept.note:
        return concept.note
    return None


def attributions(sources_used, lane):
    keys = list(dict.fromkeys(list(sources_used) + ([LANE_SOURCE[lane]] if lane in LANE_SOURCE else [])))
    return [{"source": k, **SOURCES[k]} for k in keys if k in SOURCES]
