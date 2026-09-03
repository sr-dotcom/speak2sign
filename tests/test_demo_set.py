import pytest

from speak2sign import timeline
from speak2sign.gloss import lexicon as lex
from speak2sign.ingest import demo_set

ITEMS = demo_set.items()
needs_items = pytest.mark.skipif(not ITEMS, reason="curated items not built (scripts/build_demo_set.py)")


@needs_items
def test_items_have_audio_monotonic_timings_and_alignment_record():
    for it in ITEMS:
        onsets = [w["onset_s"] for w in it["words"]]
        assert onsets == sorted(onsets) and onsets[0] >= 0
        assert it["duration_s"] > onsets[-1]
        assert it["alignment"]["matched_words"] / it["alignment"]["total_words"] >= 0.6, it["id"]


@needs_items
def test_curated_transcript_builds_a_valid_audio_timeline():
    L = lex.load()
    for it in ITEMS:
        tl = timeline.build(demo_set.transcript(it), L)
        assert tl["media"]["kind"] == "audio" and tl["media"]["url"].startswith("app/static/news/")
        assert tl["item"]["lane"] == "curated" and tl["item"]["broadcast_date"] == it["broadcast_date"]
        assert tl["sentences"][-1]["t_end"] <= it["duration_s"] + 1e-6
