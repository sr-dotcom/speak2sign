"""The interpreter panel in a real browser: what the Python tests cannot see (playback, cancellation, fallbacks, rendering).

Playback is recorded by the browser itself: listeners on the panel's two video elements record, per play() the panel
issues, the label, the clip file and the time it started at, then how many seeks happened while it played and the
time it reached when it stopped (one record per play, whether it ended by pause or by reaching the end of the file).
A repeat, a skip, a late start, a clip cut short or a jump inside a clip is seen whatever its length.
"""
import time

import pytest

FIRST_ITEM_STATUS = "3 sentences"   # the first curated item (Samoa oil spill) has three sentences

# The panel that holds a caption starting with a given word (several panels can be mounted: news item + typed text);
# with no word, the first panel on the page.
PANEL = """(startsWith) => {
  const roots = [...document.querySelectorAll('*')].map(e => e.shadowRoot).filter(r => r && r.querySelector('.s2s'));
  if (!startsWith) return roots[0] || null;
  return roots.find(r => [...r.querySelectorAll('.s2s-captions span')].some(s => s.textContent.startsWith(startsWith))) || null;
}"""
RECORD = f"""([startsWith, key]) => {{
  const root = ({PANEL})(startsWith);
  window.__plays = window.__plays || {{}};
  window.__plays[key] = [];
  root.querySelectorAll('.s2s-video').forEach(v => {{
    v.addEventListener('play', () => {{
      v.__inst = {{gloss: root.querySelector('.s2s-gloss').textContent, src: v.src.split('/').pop(), start: v.currentTime, seeks: 0, end: null,
                  shown: !v.hidden}};   // the element that plays must be the one on screen
      window.__plays[key].push(v.__inst);
    }});
    v.addEventListener('seeking', () => {{ if (v.__inst) v.__inst.seeks += 1; }});
    const done = () => {{ if (v.__inst && v.__inst.end === null) {{ v.__inst.end = v.currentTime; v.__inst = null; }} }};
    // the stop position is captured the moment the panel calls pause(), before any later seek or reload on the same
    // element; the queued pause event and a natural ended close the record only if pause() did not already
    const pause = v.pause.bind(v);
    v.pause = () => {{ done(); pause(); }};
    v.addEventListener('pause', done); v.addEventListener('ended', done);
  }});
  root.querySelector('.s2s-audio').addEventListener('play', () => window.__plays[key].push({{gloss: null, src: 'narration'}}));   // narration starts too
}}"""
READ = f"""(startsWith) => {{
  const r = ({PANEL})(startsWith);
  const vis = [...r.querySelectorAll('.s2s-video')].find(v => !v.hidden);
  return {{status: r.querySelector('.s2s-status').textContent, button: r.querySelector('.s2s-play').textContent,
          gloss: r.querySelector('.s2s-gloss').textContent, note: r.querySelector('.s2s-note').textContent,
          card: r.querySelector('.s2s-textsign').hidden ? null : r.querySelector('.s2s-textsign').textContent,
          visible: vis ? {{src: vis.src.split('/').pop(), t: vis.currentTime, paused: vis.paused, ready: vis.readyState}} : null,
          playing: [...r.querySelectorAll('.s2s-video')].some(v => !v.paused),
          visiblePlaying: !!vis && !vis.paused,
          allPaused: [...r.querySelectorAll('.s2s-video')].every(v => v.paused) && r.querySelector('.s2s-audio').paused}};
}}"""


def wait_until(fn, timeout=15.0, every=0.1):
    end = time.time() + timeout
    while time.time() < end:
        v = fn()
        if v:
            return v
        time.sleep(every)
    raise AssertionError("condition not met in time")


def record(page, key, caption_start=None):
    page.evaluate(RECORD, [caption_start, key])


def plays(page, key):
    """Every play the panel issued since record(): dicts with gloss, src, start, seeks, end (None while still playing)."""
    return page.evaluate(f"() => window.__plays['{key}']")


def starts(page, key):
    """Clip starts only (narration records are kept apart)."""
    return [(x["gloss"], x["src"]) for x in plays(page, key) if x["src"] != "narration"]


def clip_plays(page, key):
    return [x for x in plays(page, key) if x["src"] != "narration"]


def read(page, caption_start=None):
    return page.evaluate(READ, caption_start)


def sequence_of(tl, sentence=0):
    """The ordered (label, clip file) sequence a timeline prescribes for one sentence."""
    return [(e["gloss"], c["url"].rsplit("/", 1)[1]) for e in tl["entries"] if e["sentence"] == sentence for c in e["clips"]]


def spans_of(tl, sentence=0):
    """(label, clip file) -> (in_s, out_s): the active span each clip must play, start to end."""
    return {(e["gloss"], c["url"].rsplit("/", 1)[1]): (c["in_s"], c["out_s"]) for e in tl["entries"] if e["sentence"] == sentence for c in e["clips"]}


def first_item_timeline(lexicon):
    from speak2sign import timeline
    from speak2sign.ingest import demo_set

    return timeline.build(demo_set.transcript(demo_set.items()[0]), lexicon)


def typed_timeline(text, lexicon):
    from speak2sign import timeline
    from speak2sign.transcript import from_text

    return timeline.build(from_text(text, media_kind="tts"), lexicon)


def gloss_typed(page, text):
    page.get_by_role("tab", name="Type text").click()
    box = page.get_by_label("English text")
    box.fill(text)
    box.press("Control+Enter")
    page.get_by_role("button", name="Gloss it").click()


def test_page_mounts_the_first_item_ready_on_the_signers_first_frame(page, state, lexicon):
    assert "Ready" in state()["status"] and FIRST_ITEM_STATUS in state()["status"]
    assert page.locator(".s2s-chip").count() > 10   # the ribbon under the panel
    # the item card sits above the panel: coverage, fingerspelling, signing time, sentences, all read from the timeline
    tl = first_item_timeline(lexicon)
    card = page.locator('[data-testid="stMetric"]')
    assert card.count() >= 4 and card.first.bounding_box()["y"] < page.locator(".s2s-play").bounding_box()["y"]
    shown = {}
    for i in range(4):   # each metric: its label line, then its value line
        label, value = [line.strip() for line in card.nth(i).inner_text().split("\n") if line.strip()][:2]
        shown[label] = value
    s = tl["stats"]
    assert shown == {"Validated signs": f"{s['coverage']:.0%}", "Fingerspelled": f"{s['fingerspelling_rate']:.0%}",
                     "Signing time": f"~{s['signing_s']:.0f} s", "Sentences": str(len(tl["sentences"]))}
    (first_gloss, first_clip), = sequence_of(first_item_timeline(lexicon))[:1]
    in_s = spans_of(first_item_timeline(lexicon))[(first_gloss, first_clip)][0]
    # before Play the panel shows the first clip's first active frame, paused, with a hint; never a black box
    s = wait_until(lambda: state() if state()["visible"] and state()["visible"]["ready"] >= 2 else None)
    assert s["visible"]["src"] == first_clip and s["visible"]["paused"] and abs(s["visible"]["t"] - in_s) < 0.05
    first_entry = first_item_timeline(lexicon)["entries"][0]
    assert s["gloss"] == first_entry["gloss"] == first_gloss   # a shown signer carries its label ...
    assert page.locator(".s2s-badge").text_content() == {"validated": "validated", "fingerspelled": "fingerspelled"}[first_entry["badge"]]   # ... and its badge (text_content: the CSS uppercases it on screen)
    hint = page.locator(".s2s-hint")
    assert hint.is_visible() and "Play" in hint.inner_text()
    page.locator(".s2s-play").click()
    wait_until(lambda: not hint.is_visible())


def test_the_panel_plays_the_whole_first_sentence_in_the_prescribed_order(page, lexicon):
    tl = first_item_timeline(lexicon)
    expected, next_sentence = sequence_of(tl), sequence_of(tl, 1)
    allowed = {}
    for gloss, clip in expected:
        allowed.setdefault(gloss, set()).add(clip)
    record(page, "item")
    page.locator(".s2s-play").click()
    bad = []
    end = time.time() + 90
    while time.time() < end:
        s = read(page)
        if "Sentence 2" in s["status"] or "Done" in s["status"]:
            break
        if s["playing"] and (not s["visiblePlaying"] or s["gloss"] == "—"):
            bad.append(("a clip is playing but it is not the one on screen", s["gloss"], s["visible"]))   # signing is on screen, never hidden
        if s["visible"] and s["gloss"] != "—":
            # every sample: the visible clip is one of this label's own clips, and its frame is decoded
            if s["visible"]["src"] not in allowed.get(s["gloss"], ()) or s["visible"]["ready"] < 2:
                bad.append((s["gloss"], s["visible"]["src"], s["visible"]["ready"]))
        time.sleep(0.04)
    else:
        raise AssertionError(f"sentence 1 never finished; last state {read(page)}")
    assert not bad, bad
    # every clip start of the sentence, in order, and nothing else: no reordered, repeated, skipped or stalled clip
    # (the loop may catch the first start of sentence 2 before it sees the status change; nothing beyond that)
    played = starts(page, "item")
    assert played[: len(expected)] == expected and played[len(expected):] in ([], next_sentence[:1]), played
    # and every clip played exactly its active span: started at in_s (the panel seeks there before play(), so 0.05 s),
    # no seek while playing, stopped at or past out_s - 0.03 (the panel's stop test) and not more than one timeupdate
    # interval beyond it (250 ms of wall clock at the 2.0x letter rate is 0.5 s of media; 0.6 s is the bound)
    spans = spans_of(tl)
    wrong = []
    for (g, c), rec in zip(expected, clip_plays(page, "item")):
        in_s, out_s = spans[(g, c)]
        if rec["end"] is None or not rec["shown"] or abs(rec["start"] - in_s) > 0.05 or rec["seeks"] != 0 or not (out_s - 0.05 <= rec["end"] <= out_s + 0.6):
            wrong.append((g, c, rec, spans[(g, c)]))
    assert not wrong, wrong
    assert any(len(allowed[g]) > 1 for g in allowed)   # a fingerspelled word was played letter by letter


def test_pause_stops_everything_and_replay_starts_the_sentence_over(page, state, lexicon):
    first = sequence_of(first_item_timeline(lexicon))[0]
    page.locator(".s2s-play").click()
    wait_until(lambda: state()["gloss"] not in ("—", first[0]), timeout=20)   # well into the sentence, past its first sign
    page.locator(".s2s-play").click()   # pause
    s = wait_until(lambda: state() if state()["allPaused"] else None)
    assert s["button"] == "Replay sentence" and s["status"].startswith("Paused at sentence 1")
    record(page, "after-pause")   # any play() from here on, clip or narration, is a late callback that Pause failed to cancel
    time.sleep(2.5)
    assert state()["allPaused"] and plays(page, "after-pause") == []
    page.locator(".s2s-play").click()   # replay the sentence
    s = wait_until(lambda: state() if state()["button"] == "Pause" and starts(page, "after-pause") else None)
    assert "Sentence 1" in s["status"]
    assert starts(page, "after-pause")[0] == first   # the sentence starts over with its first prescribed clip, not mid-sentence
    audio_t = page.evaluate(f"() => ({PANEL})(null).querySelector('.s2s-audio').currentTime")
    assert audio_t < 3.0   # narration reset to the sentence onset


def test_restart_goes_back_to_the_first_sign(page, state, lexicon):
    first = sequence_of(first_item_timeline(lexicon))[0]
    page.locator(".s2s-play").click()
    wait_until(lambda: state()["gloss"] not in ("—", first[0]), timeout=20)   # playback has moved past the first sign
    moved_to = state()["gloss"]
    record(page, "restart")
    page.locator(".s2s-restart").click()
    s = wait_until(lambda: state() if starts(page, "restart")[:1] == [first] and state()["button"] == "Pause" else None)
    assert "Sentence 1 of" in s["status"] and moved_to != first[0]
    audio_t = page.evaluate("() => { const r = [...document.querySelectorAll('*')].map(e => e.shadowRoot).find(r => r && r.querySelector('.s2s')); return r.querySelector('.s2s-audio').currentTime; }")
    assert audio_t < 3.0


def test_a_clip_that_fails_to_load_shows_the_word_as_text_and_playback_continues(page, state, lexicon):
    first, second = sequence_of(first_item_timeline(lexicon))[:2]
    page.route(f"**/clips/{first[1]}", lambda route: route.abort())   # the first sign of the item
    page.reload()
    page.locator(".s2s-play").wait_for(timeout=30000)
    record(page, "failed")
    page.locator(".s2s-play").click()
    s = wait_until(lambda: state() if state()["card"] and "clip unavailable" in state()["card"] else None, timeout=20)
    assert s["gloss"] == first[0] and "could not be played" in s["note"]
    wait_until(lambda: second in starts(page, "failed"), timeout=20)   # playback went on with the next sign's own clip
    assert first not in starts(page, "failed")


def test_a_failed_digit_inside_a_number_takes_the_whole_number_to_text(page, lexicon):
    text = "About 975 people."
    seq = sequence_of(typed_timeline(text, lexicon))
    number = [(g, c) for g, c in seq if g == "975"]
    after = seq[seq.index(number[-1]) + 1]   # the entry after the number, as the timeline names it (PEOPLEdis or whatever the lexicon says)
    assert [c for _, c in number] == ["digit-9.mp4", "digit-7.mp4", "digit-5.mp4"]
    page.route("**/letters/digit-7.mp4", lambda route: route.abort())   # the middle digit
    gloss_typed(page, text)
    wait_until(lambda: page.evaluate(PANEL, "About") is not None, timeout=20)
    record(page, "digit", "About")
    page.evaluate(f"() => ({PANEL})('About').querySelector('.s2s-play').click()")
    card = wait_until(lambda: read(page, "About") if (read(page, "About")["card"] or "").find("clip unavailable") >= 0 else None, timeout=25)
    assert card["gloss"] == "975" and "could not be played" in card["note"]
    wait_until(lambda: after in starts(page, "digit"), timeout=20)   # the sentence went on to the next word's own clip
    wait_until(lambda: "Done" in read(page, "About")["status"], timeout=30)   # ... and to the end of the item
    time.sleep(1.0)   # a bounded window after completion for any stale callback
    played = starts(page, "digit")
    assert ("975", "digit-9.mp4") in played, played
    assert not any(c in ("digit-7.mp4", "digit-5.mp4") for _, c in played), played   # neither the failed 7 nor the 5 ever started, under any label


def test_typed_lane_marks_partly_and_dropped_words_visibly(page):
    gloss_typed(page, "Don't panic. A 30% chance of rain at 2pm.")
    wait_until(lambda: page.locator(".s2s-captions span.partly").count() > 0, timeout=20)
    rendered = page.evaluate(f"""() => {{
      const r = ({PANEL})("Don't");
      const deco = (el) => getComputedStyle(el).textDecorationLine;
      return [...r.querySelectorAll('.s2s-captions span')].map(s => ({{
        text: s.firstChild.textContent.trim(), cls: s.className, deco: deco(s),
        missing: s.querySelector('s') ? {{text: s.querySelector('s').textContent.trim(), deco: deco(s.querySelector('s'))}} : null}}));
    }}""")
    by_text = {c["text"]: c for c in rendered}
    assert by_text["Don't"]["cls"] == "partly" and by_text["Don't"]["missing"]["text"] == "do"
    assert "line-through" in by_text["Don't"]["missing"]["deco"]        # the unsigned part is visibly struck
    assert by_text["A"]["cls"] == "dropped" and "line-through" in by_text["A"]["deco"]   # a dropped word is visibly struck
    assert "line-through" not in by_text["panic."]["deco"]
    chips = page.locator(".s2s-chip").all_inner_texts()
    assert any(c.startswith("2-P-M") for c in chips) and any(c.startswith("PERCENT") for c in chips)


@pytest.mark.parametrize("width", [375, 1440])
def test_layout_fits_the_viewport_with_the_controls_reachable(page, width):
    page.set_viewport_size({"width": width, "height": 900})
    time.sleep(0.5)
    assert page.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth + 1")   # the page itself
    overflow = page.evaluate(f"""() => {{
      const r = ({PANEL})(null);
      const boxes = ['.s2s', '.s2s-stage', '.s2s-news', '.s2s-panel', '.s2s-captions', '.s2s-videos', '.s2s-controls'];
      const over = boxes.filter(sel => {{ const el = r.querySelector(sel); return el.scrollWidth > el.clientWidth + 1; }});
      const off = ['.s2s-play', '.s2s-restart', '.s2s-videos'].filter(sel => {{ const b = r.querySelector(sel).getBoundingClientRect(); return b.left < 0 || b.right > window.innerWidth + 1 || b.width === 0; }});
      return {{over, off}};
    }}""")
    assert overflow == {"over": [], "off": []}, overflow   # nothing inside the panel is clipped and the controls sit inside the viewport


def test_keyboard_space_and_r_control_the_panel(page, lexicon):
    first = sequence_of(first_item_timeline(lexicon))[0]
    page.locator(".s2s").focus()   # the panel region itself, not a button
    page.keyboard.press("Space")
    s = wait_until(lambda: read(page) if read(page)["button"] == "Pause" and read(page)["visiblePlaying"] else None)
    assert "Sentence 1" in s["status"]
    page.keyboard.press("Space")
    s = wait_until(lambda: read(page) if read(page)["allPaused"] else None)
    assert s["button"] == "Replay sentence"
    record(page, "key-restart")
    page.keyboard.press("r")
    s = wait_until(lambda: read(page) if starts(page, "key-restart")[:1] == [first] and read(page)["button"] == "Pause" else None)
    assert "Sentence 1 of" in s["status"]
    # a held key acts once (autorepeat keydowns are ignored) and modified keys are left to the browser
    before, plays_before = read(page)["button"], len(plays(page, "key-restart"))
    repeats_prevented = page.evaluate(f"() => {{ const r = ({PANEL})(null).querySelector('.s2s'); const out = []; for (let i = 0; i < 5; i++) {{ const e = new KeyboardEvent('keydown', {{key: ' ', repeat: true, bubbles: true, cancelable: true}}); r.dispatchEvent(e); out.push(e.defaultPrevented); }} return out; }}")
    assert repeats_prevented == [True] * 5   # a held Space does not scroll the page ...
    page.keyboard.press("Control+r")
    page.keyboard.press("Alt+r")
    time.sleep(0.3)
    s = read(page)
    assert s["button"] == before and "Sentence 1 of" in s["status"]                       # no toggle from the held key
    assert [p["src"] for p in plays(page, "key-restart")[plays_before:]] in ([], ["narration"]) or all(
        p["gloss"] != first[0] for p in plays(page, "key-restart")[plays_before:])            # no second restart from Ctrl+R / Alt+R
    assert not page.evaluate(f"() => {{ const r = ({PANEL})(null).querySelector('.s2s'); const e = new KeyboardEvent('keydown', {{key: 'r', ctrlKey: true, bubbles: true, cancelable: true}}); r.dispatchEvent(e); return e.defaultPrevented; }}")
    # a focused button keeps its native Space: once on Play toggles once, once on Restart restarts once
    page.locator(".s2s-play").focus()
    page.keyboard.press("Space")
    s = wait_until(lambda: read(page) if read(page)["allPaused"] else None)
    assert s["button"] == "Replay sentence"
    record(page, "button-restart")
    page.locator(".s2s-restart").focus()
    page.keyboard.press("Space")
    wait_until(lambda: starts(page, "button-restart")[:1] == [first])
    time.sleep(1.0)
    assert [g for g, _ in starts(page, "button-restart")].count(first[0]) == 1   # not restarted twice
    assert page.locator(".s2s-play").get_attribute("aria-keyshortcuts") == "Space"
    assert page.locator(".s2s-restart").get_attribute("aria-keyshortcuts") == "R"
    legend = page.get_by_text("Badges: validated")
    assert legend.count() >= 1


def test_sign_speed_control_changes_the_rate_the_clips_play_at(page, lexicon):
    page.get_by_text("1.5×", exact=True).click()   # Streamlit's radio input is hidden; its label takes the click
    page.wait_for_timeout(1500)                       # the rerun replaces the panel
    page.locator(".s2s-play").wait_for(timeout=30000)
    record(page, "rate")
    page.locator(".s2s-play").click()
    s = wait_until(lambda: read(page) if read(page)["visiblePlaying"] else None)
    rate = page.evaluate(f"() => [...({PANEL})(null).querySelectorAll('.s2s-video')].find(v => !v.hidden).playbackRate")
    assert rate == 1.5 and "Sentence 1" in s["status"]
    signing = [line for line in page.locator('[data-testid="stMetric"]').nth(2).inner_text().split("\n") if line.strip()][1]
    tl = first_item_timeline(lexicon)
    from speak2sign import timeline
    from speak2sign.ingest import demo_set
    fast = timeline.build(demo_set.transcript(demo_set.items()[0]), lexicon, sign_rate=1.5)
    assert signing == f"~{fast['stats']['signing_s']:.0f} s" and fast["stats"]["signing_s"] < tl["stats"]["signing_s"]
