"""The committed curated items: the primary demo lane, so nothing here may skip."""
import json
import wave
from pathlib import Path

from speak2sign import timeline
from speak2sign.ingest import demo_set

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_IDS = {i["id"] for i in json.loads((ROOT / "data" / "demo" / "excerpts.json").read_text(encoding="utf-8"))["items"]}
ITEMS = demo_set.items()


def test_every_excerpt_is_built_with_its_audio():
    assert {i["id"] for i in ITEMS} == EXPECTED_IDS and len(EXPECTED_IDS) == 6
    for it in ITEMS:
        with wave.open(str(ROOT / "static" / it["media"]), "rb") as w:
            assert w.getnchannels() == 1 and w.getframerate() == 16000
            assert abs(w.getnframes() / w.getframerate() - it["duration_s"]) < 0.05, it["id"]


def test_items_have_monotonic_timings_inside_the_audio_and_an_alignment_record():
    for it in ITEMS:
        onsets = [w["onset_s"] for w in it["words"]]
        assert onsets == sorted(onsets) and onsets[0] >= 0
        assert it["duration_s"] > onsets[-1]
        assert it["alignment"]["matched_words"] / it["alignment"]["total_words"] >= 0.6, it["id"]


def test_curated_transcripts_build_valid_audio_timelines(lexicon, check):
    for it in ITEMS:
        tl = timeline.build(demo_set.transcript(it), lexicon)
        check(tl)
        assert tl["media"]["kind"] == "audio" and (ROOT / "static" / tl["media"]["url"].removeprefix("app/static/")).exists()
        assert tl["item"]["lane"] == "curated" and tl["item"]["broadcast_date"] == it["broadcast_date"]
        assert [c["text"] for c in tl["captions"]] == [w["text"] for w in it["words"]]
