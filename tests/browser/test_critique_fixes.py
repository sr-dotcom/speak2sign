"""What the 2026-09-11 design critique changed (docs/research/design-critique-2026-09-11.md), checked in the browser."""
import time

import pytest

from test_panel import PANEL, first_item_timeline, wait_until


def test_narrow_screens_put_the_signer_first_and_keep_it_pinned(page):
    page.set_viewport_size({"width": 375, "height": 812})
    time.sleep(0.5)
    boxes = page.evaluate(f"""() => {{ const r = ({PANEL})(null); const b = (sel) => r.querySelector(sel).getBoundingClientRect();
      return {{panel: b('.s2s-panel').top, news: b('.s2s-news').top, captions: getComputedStyle(r.querySelector('.s2s-captions')).fontSize}}; }}""")
    assert boxes["panel"] < boxes["news"] and boxes["captions"] == "17px"
    # during playback the signer stays on screen while the captions scroll under it (the page's scroller is Streamlit's main section)
    page.locator(".s2s-play").click()
    wait_until(lambda: page.evaluate(f"() => !!({PANEL})(null).querySelector('.s2s-video:not([hidden])') && !({PANEL})(null).querySelector('.s2s-video:not([hidden])').paused"))
    # scroll the page so the caption card's top reaches the top of the viewport: the pinned signer must still be in view above it
    page.evaluate(f"""() => {{ const m = document.querySelector('section.stMain') || document.querySelector('[data-testid="stMain"]');
      const c = ({PANEL})(null).querySelector('.s2s-captions').getBoundingClientRect(); m.scrollBy(0, c.top); }}""")
    time.sleep(0.6)
    rect = page.evaluate(f"""() => {{ const r = ({PANEL})(null); const v = r.querySelector('.s2s-videos').getBoundingClientRect();
      const c = r.querySelector('.s2s-captions').getBoundingClientRect(); return {{video: [v.top, v.bottom], captions: [c.top, c.bottom], h: window.innerHeight}}; }}""")
    assert 0 <= rect["video"][0] and rect["video"][1] <= rect["h"], rect          # the signer is fully on screen after scrolling to the end
    # nothing sits on the pinned panel: the controls and the bar are above it or off screen (the captions scrolling under it is the point)
    overlap = page.evaluate(f"""() => {{ const r = ({PANEL})(null); const p = r.querySelector('.s2s-panel').getBoundingClientRect();
      return [...r.querySelectorAll('.s2s-controls, .s2s-progress')].map(el => el.getBoundingClientRect()).filter(b => b.bottom > p.top && b.top < p.bottom && b.height > 0).length; }}""")
    assert overlap == 0
    assert rect["captions"][0] < rect["h"] and rect["captions"][1] > rect["video"][1], rect   # and the caption card is on screen below it
    # the word being spoken is kept visible below the pinned panel as the narration advances (the panel scrolls it into view)
    def now_box():
        return page.evaluate(f"""() => {{ const r = ({PANEL})(null); const w = r.querySelector('.s2s-captions span.now'); const p = r.querySelector('.s2s-panel').getBoundingClientRect();
          return w ? {{text: w.textContent, top: w.getBoundingClientRect().top, bottom: w.getBoundingClientRect().bottom, panelBottom: p.bottom, h: window.innerHeight}} : null; }}""")
    first_now = (now_box() or {}).get("text")
    now = wait_until(lambda: now_box() if now_box() and now_box()["text"] != first_now else None, timeout=20)   # the next spoken word
    assert now["top"] >= now["panelBottom"] - 1 and now["bottom"] <= now["h"], now


def test_a_panel_that_would_swallow_the_screen_is_not_pinned(page):
    page.set_viewport_size({"width": 800, "height": 600})
    time.sleep(0.5)
    is_pinned = lambda: page.evaluate(f"() => getComputedStyle(({PANEL})(null).querySelector('.s2s-panel')).position === 'sticky'")   # noqa: E731
    assert is_pinned()   # normal content: the panel takes well under 65% of a 600 px screen
    # grow the panel (a wrapped note plus the waiting notice): it must let go of the pin so the captions keep their room
    page.evaluate(f"""() => {{ const r = ({PANEL})(null); r.querySelector('.s2s-note').textContent = 'a long note '.repeat(60); r.querySelector('.s2s-wait').hidden = false; }}""")
    time.sleep(0.5)
    tall = page.evaluate(f"() => {{ const r = ({PANEL})(null); return r.querySelector('.s2s-panel').offsetHeight > window.innerHeight * 0.65; }}")
    assert tall and not is_pinned()


LONG_TEXT = " ".join(["The of and to in on at by for with the of and to."] * 24)   # function words only: narration alone paces it


def start_long_typed(page, width=375, height=600):
    """A typed item whose captions run far past the fold on a phone, scrolled into place, ready to play."""
    from test_panel import gloss_typed
    page.set_viewport_size({"width": width, "height": height})
    gloss_typed(page, LONG_TEXT)
    wait_until(lambda: page.evaluate(PANEL, "The") is not None, timeout=20)
    panel = f"({PANEL})('The')"
    page.evaluate(f"() => {panel}.querySelector('.s2s').scrollIntoView({{block: 'start'}})")
    return panel


def scroll_of(page):
    return page.evaluate("() => document.querySelector('section.stMain').scrollTop")


def gesture_wheel(page, panel):
    page.mouse.wheel(0, -120)


def gesture_scrollbar(page, panel):   # a scrollbar drag: mousedown on the scroller itself, then movement
    page.evaluate("() => { const m = document.querySelector('section.stMain'); m.dispatchEvent(new MouseEvent('mousedown', {bubbles: true})); m.scrollTop = Math.max(0, m.scrollTop - 150); }")


def gesture_space(page, panel):   # the page's own scroll key, with the focus outside the panel
    page.evaluate("() => document.activeElement && document.activeElement.blur()")
    page.keyboard.press("Shift+Space")


@pytest.mark.parametrize("gesture", [gesture_wheel, gesture_scrollbar, gesture_space], ids=["wheel", "scrollbar", "space"])
def test_a_manual_scroll_up_stops_the_caption_follow(page, gesture):
    panel = start_long_typed(page)
    page.evaluate(f"() => {panel}.querySelector('.s2s-play').click()")
    wait_until(lambda: scroll_of(page) > 0)
    start = scroll_of(page)
    wait_until(lambda: scroll_of(page) > start + 100, timeout=75)   # the follow is on: the page has moved down with the narration
    gesture(page, panel)                                              # one upward gesture, right after an automatic scroll
    time.sleep(0.4)                                                   # let the gesture's own scroll land
    page.evaluate(f"() => {panel}.querySelector('.s2s-controls').scrollIntoView({{block: 'start'}})")
    pos = scroll_of(page)
    words_before = page.evaluate(f"() => [...{panel}.querySelectorAll('.s2s-captions span')].findIndex(s => s.classList.contains('now'))")
    time.sleep(3.0)   # several narrated words go by
    assert abs(scroll_of(page) - pos) < 12, (scroll_of(page), pos)   # ... and none pulled the page away (Streamlit's own layout jitter is ~5 px)
    assert page.evaluate(f"() => [...{panel}.querySelectorAll('.s2s-captions span')].findIndex(s => s.classList.contains('now'))") > words_before   # narration went on
    top = page.evaluate(f"() => {panel}.querySelector('.s2s-play').getBoundingClientRect().top")
    assert -1 <= top <= 600, top
    page.evaluate(f"() => {panel}.querySelector('.s2s-play').click()")
    wait_until(lambda: page.evaluate(f"() => {panel}.querySelector('.s2s-play').textContent") == "Replay sentence")


def test_space_inside_the_panel_starts_playback_and_keeps_following(page):
    panel = start_long_typed(page)
    page.evaluate(f"() => {panel}.querySelector('.s2s').focus()")
    page.keyboard.press("Space")   # the panel's own shortcut, seen by the window listener as an event on the component host
    wait_until(lambda: page.evaluate(f"() => {panel}.querySelector('.s2s-play').textContent") == "Pause")
    start = scroll_of(page)
    wait_until(lambda: scroll_of(page) > start + 100, timeout=75)   # following survived the Space that started it


def test_remounting_the_panel_releases_its_resize_hooks(page):
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    # count resize listeners and ResizeObservers added and released from here on (the first panel's hooks predate the count)
    page.evaluate("""() => {
      window.__hooks = {added: 0, removed: 0, observed: 0, disconnected: 0};
      const add = window.addEventListener.bind(window), rem = window.removeEventListener.bind(window);
      // only the panel's own hooks count: its resize listener is the named function updatePin, its observer watches .s2s-panel
      window.addEventListener = (t, fn, ...a) => { if (t === 'resize' && fn && fn.name === 'updatePin') window.__hooks.added += 1; return add(t, fn, ...a); };
      window.removeEventListener = (t, fn, ...a) => { if (t === 'resize' && fn && fn.name === 'updatePin') window.__hooks.removed += 1; return rem(t, fn, ...a); };
      const obs = ResizeObserver.prototype.observe, dis = ResizeObserver.prototype.disconnect;
      ResizeObserver.prototype.observe = function (el, ...a) { if (el.classList && el.classList.contains('s2s-panel')) { this.__s2s = true; window.__hooks.observed += 1; } return obs.call(this, el, ...a); };
      ResizeObserver.prototype.disconnect = function (...a) { if (this.__s2s) window.__hooks.disconnected += 1; return dis.apply(this, a); };
    }""")
    for _ in range(3):   # each item change tears the panel down and mounts a new one
        page.get_by_role("combobox").first.click()
        page.get_by_role("option").nth(1).click()
        page.locator(".s2s-play").wait_for(timeout=30000)
        page.get_by_role("combobox").first.click()
        page.get_by_role("option").nth(0).click()
        page.locator(".s2s-play").wait_for(timeout=30000)
    page.set_viewport_size({"width": 375, "height": 812})   # the resize hook of the live panel still runs; the dead ones are gone
    time.sleep(0.5)
    assert page.locator(".s2s").count() == 1 and errors == [], errors
    hooks = page.evaluate("() => window.__hooks")
    # Six panels mounted after the count started; six teardowns ran (the five of those panels that were replaced, plus the
    # original panel's, whose listener removal is counted but whose observer predates the count). One live set remains.
    assert hooks == {"added": 6, "removed": 6, "observed": 6, "disconnected": 5}, hooks
    assert page.evaluate(f"() => getComputedStyle(({PANEL})(null).querySelector('.s2s-panel')).position") == "sticky"


def test_short_landscape_screens_do_not_pin_the_panel(page):
    page.set_viewport_size({"width": 740, "height": 360})   # a small phone held sideways: narrow enough to stack, too short to pin
    time.sleep(0.5)
    layout = page.evaluate(f"""() => {{ const r = ({PANEL})(null); const b = (sel) => r.querySelector(sel).getBoundingClientRect();
      return {{position: getComputedStyle(r.querySelector('.s2s-panel')).position, panelH: b('.s2s-panel').height, h: window.innerHeight, first: b('.s2s-panel').top < b('.s2s-news').top}}; }}""")
    assert layout["position"] != "sticky" and layout["first"], layout   # pinning a panel taller than the screen would hide the captions for good


def playback_estimate(tl):
    """What the panel says the item takes: per sentence the longer of narration and signing, summed (the same rule as panel.js)."""
    total = 0.0
    for s in tl["sentences"]:
        signing = sum(sum((c["out_s"] - c["in_s"]) / c["rate"] for c in e["clips"]) if e["clips"] else tl["playback"]["text_hold_s"]
                      for e in tl["entries"] if e["sentence"] == s["index"])
        total += max(s["t_end"] - s["t_start"], signing)
    return f"{max(1, round(total))} s" if total < 60 else f"{round(total / 30) / 2:g} min"


def test_status_frames_the_wait_and_the_bar_advances_per_sign(page, state, lexicon):
    tl = first_item_timeline(lexicon)
    assert f"about {playback_estimate(tl)} to play: the narration waits for the signer" in state()["status"]
    assert tl["stats"]["signing_s"] > tl["stats"]["speech_s"]   # a signing-dominant item: the estimate is the signing, not the audio

    def width():
        return page.evaluate(f"() => ({PANEL})(null).querySelector('.s2s-progress-bar').style.width")

    assert width() in ("", "0%")
    page.locator(".s2s-play").click()
    wait_until(lambda: width() not in ("", "0%"), timeout=20)
    # the waiting notice lives on the panel side, off the captions, and never over the signer's face or hands
    assert page.locator(".s2s-panel .s2s-wait").count() == 1
    wait_until(lambda: not page.evaluate(f"() => ({PANEL})(null).querySelector('.s2s-wait').hidden"), timeout=90)
    geometry = page.evaluate(f"""() => {{ const r = ({PANEL})(null); const w = r.querySelector('.s2s-wait').getBoundingClientRect();
      const v = r.querySelector('.s2s-videos').getBoundingClientRect(); return {{w: [w.top, w.bottom], v: [v.top, v.bottom]}}; }}""")
    assert geometry["w"][0] >= geometry["v"][1] - 1, geometry   # the notice sits below the video box, not on it


def test_a_short_item_says_seconds_not_zero_minutes(page, lexicon):
    from test_panel import gloss_typed, typed_timeline
    text = "Rain today."
    gloss_typed(page, text)
    wait_until(lambda: page.evaluate(PANEL, "Rain") is not None, timeout=20)
    status = page.evaluate(f"() => ({PANEL})('Rain').querySelector('.s2s-status').textContent")
    assert f"about {playback_estimate(typed_timeline(text, lexicon))} to play" in status, status


def test_a_narration_dominant_item_is_estimated_by_its_narration(page, lexicon):
    from test_panel import typed_timeline
    panel = start_long_typed(page)   # function words: little to sign, so the narration sets the duration
    tl = typed_timeline(LONG_TEXT, lexicon)
    assert tl["stats"]["signing_s"] < tl["stats"]["speech_s"] and tl["stats"]["speech_s"] > 60   # a few of these words do have signs; the narration still dominates
    status = page.evaluate(f"() => {panel}.querySelector('.s2s-status').textContent")
    assert f"about {playback_estimate(tl)} to play" in status and "min" in status, status


def test_play_again_after_the_end_starts_the_bar_over(page, state):
    page.locator(".s2s-play").click()
    s = wait_until(lambda: state() if "Done" in state()["status"] else None, timeout=240)
    assert s["button"] == "Play again"

    def width():
        return page.evaluate(f"() => ({PANEL})(null).querySelector('.s2s-progress-bar').style.width")

    assert width() == "100%"
    page.locator(".s2s-play").click()
    wait_until(lambda: width() not in ("100%",), timeout=10)   # the bar starts over with the new run, not after its first sign
    assert int(width().rstrip("%")) < 20


def test_replaying_a_later_sentence_starts_its_bar_at_the_sentence_boundary(page, lexicon):
    from test_panel import gloss_typed, read, typed_timeline
    text = "Rain today. Snow tomorrow morning."
    tl = typed_timeline(text, lexicon)
    n_first = sum(1 for e in tl["entries"] if e["sentence"] == 0)
    gloss_typed(page, text)
    wait_until(lambda: page.evaluate(PANEL, "Rain") is not None, timeout=20)
    panel = f"({PANEL})('Rain')"
    page.evaluate(f"() => {panel}.querySelector('.s2s-play').click()")
    wait_until(lambda: "Sentence 2" in read(page, "Rain")["status"] and read(page, "Rain")["visible"] and not read(page, "Rain")["visible"]["paused"], timeout=60)
    page.evaluate(f"() => {panel}.querySelector('.s2s-play').click()")   # pause somewhere inside sentence 2
    wait_until(lambda: read(page, "Rain")["button"] == "Replay sentence")
    page.evaluate(f"() => {panel}.querySelector('.s2s-play').click()")   # replay sentence 2 from its start
    time.sleep(0.2)
    width = page.evaluate(f"() => {panel}.querySelector('.s2s-progress-bar').style.width")
    assert width == f"{round(100 * n_first / len(tl['entries']))}%", (width, n_first, len(tl["entries"]))   # exactly sentence 1's share, no more


def test_following_keeps_the_spoken_word_visible_through_captions_longer_than_the_screen(page):
    from test_panel import gloss_typed
    page.set_viewport_size({"width": 375, "height": 600})   # short enough that the captions run past the fold, tall enough to pin the panel
    # function words only: nothing to sign, so the narration alone paces the walk and the captions run far past the fold
    text = " ".join(["The of and to in on at by for with the of and to."] * 24)
    gloss_typed(page, text)
    wait_until(lambda: page.evaluate(PANEL, "The") is not None, timeout=20)
    panel = f"({PANEL})('The')"
    page.evaluate(f"() => {panel}.querySelector('.s2s').scrollIntoView({{block: 'start'}})")
    page.evaluate(f"() => {panel}.querySelector('.s2s-play').click()")
    scroll0 = page.evaluate("() => document.querySelector('section.stMain').scrollTop")
    lost, seen, scrolled, end, off, off_i = [], set(), 0, time.time() + 75, 0, None
    while time.time() < end:   # captions-only narration in headless Chromium (no speechSynthesis): the highlight walks the words
        now = page.evaluate(f"""() => {{ const r = {panel}; const w = r.querySelector('.s2s-captions span.now'); if (!w) return null;
          const b = w.getBoundingClientRect(), p = r.querySelector('.s2s-panel').getBoundingClientRect();
          return {{i: [...r.querySelectorAll('.s2s-captions span')].indexOf(w), top: b.top, bottom: b.bottom, panelBottom: p.bottom, h: window.innerHeight,
                  pinned: r.querySelector('.s2s-panel').classList.contains('pinned'), scroll: document.querySelector('section.stMain').scrollTop}}; }}""")
        if now:
            seen.add(now["i"])
            scrolled = max(scrolled, now["scroll"] - scroll0)
            hidden = now["pinned"] and (now["top"] < now["panelBottom"] - 1 or now["bottom"] > now["h"] + 1)
            off = (off + 1 if hidden and off_i == now["i"] else 1) if hidden else 0   # consecutive samples this word has been off screen
            off_i = now["i"]
            if off >= 4:   # 0.6 s off screen: the follow did not act (one or two samples is the follow catching up under load)
                lost.append(now)
        if scrolled > 150 and len(seen) > 24:
            break
        time.sleep(0.15)
    assert len(seen) > 24 and scrolled > 150, (len(seen), scrolled)   # the narration walked past the first screen and the page followed
    assert not lost, lost[:3]                                          # the spoken word was never under the panel or below the fold


def test_the_source_word_is_shown_when_it_differs_from_the_gloss(page, lexicon):
    tl = first_item_timeline(lexicon)
    page.locator(".s2s-play").click()
    seen = {}
    end = time.time() + 12
    while time.time() < end:
        gloss, word = page.evaluate(f"() => {{ const r = ({PANEL})(null); return [r.querySelector('.s2s-gloss').textContent, r.querySelector('.s2s-word').textContent]; }}")   # one read, no race
        if gloss != "—":
            seen[gloss] = word
        time.sleep(0.1)
    assert len(seen) >= 3
    for gloss, shown in seen.items():
        entry = next(e for e in tl["entries"] if e["gloss"] == gloss)
        differs = entry["word"].upper() != gloss.rstrip("abcdefghijklmnopqrstuvwxyz")
        assert shown == (f"for “{entry['word']}”" if differs else ""), (gloss, shown, entry["word"])
