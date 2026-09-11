"""Offline checks of the build scripts' decision logic (no network, no media)."""
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


demo = load("build_demo_set")


def hyp(text, start=0.0):
    return [{"text": w, "start": round(start + i * 0.4, 2), "end": round(start + i * 0.4 + 0.3, 2)} for i, w in enumerate(text.split())]


NEWSCAST = "welcome to the news . rain hit samoa on sunday officials said the island is safe now . in other news the market rose"


def test_locate_finds_the_excerpt_inside_the_newscast():
    ref = "Rain hit Samoa on Sunday. Officials said the island is safe now.".split()
    a, b, hs, ts = demo.locate(ref, hyp(NEWSCAST))
    words = NEWSCAST.split()
    assert words[a] == "rain" and words[b - 1] == "now" and hs >= 0.9 and ts >= 0.9


def test_locate_refuses_when_either_end_is_not_in_the_audio():
    with pytest.raises(RuntimeError, match="start"):
        demo.locate("Completely different words about football scores tonight everyone".split(), hyp(NEWSCAST))
    with pytest.raises(RuntimeError, match="end"):
        demo.locate("Rain hit Samoa on Sunday. Nothing like this ending appears anywhere near".split(), hyp(NEWSCAST))


def test_locate_handles_an_excerpt_shorter_than_its_edge_window():
    ref = "Rain hit Samoa".split()   # shorter than EDGE: the end index must not run past the excerpt
    a, b, *_ = demo.locate(ref, hyp(NEWSCAST))
    assert b - a == len(ref) and NEWSCAST.split()[a:b] == ["rain", "hit", "samoa"]


def test_download_writes_whole_files_only(tmp_path, monkeypatch):
    class Resp:
        def __init__(self, data):
            self.data = data

        def read(self):
            if self.data is None:
                raise OSError("connection reset")
            return self.data

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    dest = tmp_path / "clip.mp3"
    monkeypatch.setattr(demo.urllib.request, "urlopen", lambda req, timeout: Resp(None))
    with pytest.raises(OSError):
        demo.download("https://example.invalid/x.mp3", dest)
    assert not dest.exists() and not list(tmp_path.glob("*.part"))
    monkeypatch.setattr(demo.urllib.request, "urlopen", lambda req, timeout: Resp(b"ID3 data"))
    assert demo.download("https://example.invalid/x.mp3", dest) == dest and dest.read_bytes() == b"ID3 data"
    assert not list(tmp_path.glob("*.part"))


def test_build_lexicon_runs_nothing_on_an_unknown_command():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_lexicon.py"), "--help"], capture_output=True, text=True)
    assert r.returncode == 2 and "usage" in r.stderr
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_lexicon.py"), "fetch", "extra"], capture_output=True, text=True)
    assert r.returncode == 2


def test_fetch_keeps_the_published_clip_until_its_replacement_is_complete(tmp_path, monkeypatch):
    import json

    lexicon_mod = load("build_lexicon")
    static, lex_dir = tmp_path / "static", tmp_path / "lexicon"
    (static / "clips").mkdir(parents=True)
    lex_dir.mkdir()
    monkeypatch.setattr(lexicon_mod, "ROOT", tmp_path)
    monkeypatch.setattr(lexicon_mod, "STATIC", static)
    monkeypatch.setattr(lexicon_mod, "CANDIDATES", lex_dir / "candidates.json")
    monkeypatch.setattr(lexicon_mod, "CONCEPTS", lex_dir / "concepts.json")
    monkeypatch.setattr(lexicon_mod, "ATTRIBUTION", lex_dir / "attribution.json")
    monkeypatch.setattr(lexicon_mod, "signbank_video_url", lambda s: "https://example.invalid/new.mp4")
    (tmp_path / "data" / "lexicon").mkdir(parents=True)   # fetch_failures.json goes under ROOT/data/lexicon
    old_clip = {"file": "clips/rain.mp4", "source": "signbank", "source_id": "old", "gloss": "RAIN", "attribution_url": "https://x/old",
                "licence": "CC BY-NC-SA 4.0", "citation": "c", "duration_s": 2.0, "in_s": 0.1, "out_s": 1.9}
    published = [{"concept_id": "rain", "gloss": "RAIN", "keywords": ["rain"], "clip": old_clip, "status": "attested"}]
    (lex_dir / "concepts.json").write_text(json.dumps(published), encoding="utf-8")
    (static / "clips" / "rain.mp4").write_bytes(b"OLD FOOTAGE")
    new = {"source": "signbank", "score": 3, "id": "new", "gloss": "RAINb", "attribution_url": "https://x/new", "video_url": "u", "licence": "CC BY-NC-SA 4.0", "citation": "c"}
    (lex_dir / "candidates.json").write_text(json.dumps({"rain": {"concept_id": "rain", "source_block": "weather", "keywords": ["rain"], "cats": None,
                                                                   "signbank": new, "chosen": "signbank", "note": "reviewed override"}}), encoding="utf-8")

    def failing_get(url, binary=False, tries=3):
        raise ConnectionError("dropped")

    monkeypatch.setattr(lexicon_mod, "get", failing_get)
    assert lexicon_mod.fetch() == 1   # the replacement failed: the old footage and the old record stay published
    assert (static / "clips" / "rain.mp4").read_bytes() == b"OLD FOOTAGE" and not list(static.rglob("*.part"))
    assert json.loads((lex_dir / "concepts.json").read_text(encoding="utf-8")) == published

    monkeypatch.setattr(lexicon_mod, "get", lambda url, binary=False, tries=3: b"NEW FOOTAGE")
    assert lexicon_mod.fetch() == 0
    assert (static / "clips" / "rain.mp4").read_bytes() == b"NEW FOOTAGE"
    rec = json.loads((lex_dir / "concepts.json").read_text(encoding="utf-8"))[0]
    assert rec["clip"]["source_id"] == "new" and rec["status"] == "review" and "badge" not in rec   # new footage: back to review
    assert "duration_s" not in rec["clip"]   # measurements belong to the old footage and are not carried over
    assert not list(static.rglob("*.part"))


def test_fetch_recovers_when_a_run_stopped_between_manifest_and_footage(tmp_path, monkeypatch):
    import json

    lexicon_mod = load("build_lexicon")
    static, lex_dir = tmp_path / "static", tmp_path / "lexicon"
    (static / "clips").mkdir(parents=True)
    lex_dir.mkdir()
    (tmp_path / "data" / "lexicon").mkdir(parents=True)
    for name, value in {"ROOT": tmp_path, "STATIC": static, "CANDIDATES": lex_dir / "candidates.json", "CONCEPTS": lex_dir / "concepts.json",
                        "ATTRIBUTION": lex_dir / "attribution.json"}.items():
        monkeypatch.setattr(lexicon_mod, name, value)
    monkeypatch.setattr(lexicon_mod, "signbank_video_url", lambda s: "u")
    new = {"source": "signbank", "score": 3, "id": "new", "gloss": "RAIN", "attribution_url": "https://x/new", "video_url": "u", "licence": "CC BY-NC-SA 4.0", "citation": "c"}
    (lex_dir / "candidates.json").write_text(json.dumps({"rain": {"concept_id": "rain", "source_block": "weather", "keywords": ["rain"], "cats": None,
                                                                   "signbank": new, "chosen": "signbank", "note": None}}), encoding="utf-8")
    # the state a crash leaves: manifest already names 'new', old footage still on disk, the staged file and its marker present
    clip = {"file": "clips/rain.mp4", "source": "signbank", "source_id": "new", "gloss": "RAIN", "attribution_url": "https://x/new", "licence": "CC BY-NC-SA 4.0", "citation": "c"}
    (lex_dir / "concepts.json").write_text(json.dumps([{"concept_id": "rain", "gloss": "RAIN", "keywords": ["rain"], "clip": clip, "status": "review"}]), encoding="utf-8")
    (static / "clips" / "rain.mp4").write_bytes(b"OLD FOOTAGE")
    (static / "clips" / "rain.mp4.part").write_bytes(b"HALF")
    (static / "clips" / "rain.mp4.pending").write_text("x")
    monkeypatch.setattr(lexicon_mod, "get", lambda url, binary=False, tries=3: b"NEW FOOTAGE")
    assert lexicon_mod.fetch() == 0
    assert (static / "clips" / "rain.mp4").read_bytes() == b"NEW FOOTAGE"   # not trusted, fetched again
    assert not list(static.rglob("*.part")) and not list(static.rglob("*.pending"))
