"""The one input shape every lane produces: words with onset seconds on the media clock."""
from dataclasses import dataclass

WORDS_PER_SECOND = 2.6   # estimate for lanes with no recorded audio (typed text, forecast narrated by the browser)


@dataclass(frozen=True)
class Word:
    text: str
    onset_s: float
    end_s: float | None = None


@dataclass(frozen=True)
class TimedTranscript:
    item_id: str
    lane: str                 # curated | weather | headline | upload | typed
    words: tuple
    media_kind: str = "none"  # audio | video | tts | none
    media_url: str | None = None
    duration_s: float | None = None
    title: str = ""
    source: str = ""
    broadcast_date: str | None = None

    @property
    def text(self):
        return " ".join(w.text for w in self.words)


def from_text(text, item_id="typed", lane="typed", media_kind="none", wps=WORDS_PER_SECOND, **meta):
    """Estimate onsets at a steady rate. Used when nothing recorded the timing."""
    words = tuple(Word(w, round(i / wps, 3), round((i + 1) / wps, 3)) for i, w in enumerate(text.split()))
    dur = round(len(words) / wps, 3) if words else 0.0
    return TimedTranscript(item_id, lane, words, media_kind, duration_s=dur, **meta)
