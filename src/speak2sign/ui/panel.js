// Speak2Sign interpreter panel. Reads a timeline (contracts/timeline.schema.json); decides nothing about signs.
// Interpreter-paced (ADR 0008): the news plays one sentence, then waits until the panel has signed it.
// Every asynchronous step checks state.token: Pause, Restart and unmount bump it, and anything started
// under an older token stops touching the screen.
export default function (component) {
  const { parentElement, data } = component;
  const tl = data;
  const root = parentElement.querySelector(".s2s");
  const $ = (sel) => root.querySelector(sel);
  const playBtn = $(".s2s-play"), restartBtn = $(".s2s-restart"), status = $(".s2s-status");
  const audio = $(".s2s-audio"), caps = $(".s2s-captions"), wait = $(".s2s-wait");
  const vids = Array.from(root.querySelectorAll(".s2s-video")), textSign = $(".s2s-textsign");
  const glossEl = $(".s2s-gloss"), badgeEl = $(".s2s-badge"), noteEl = $(".s2s-note"), wordEl = $(".s2s-word"), bar = $(".s2s-progress-bar");

  const BADGE_TEXT = { validated: "validated", fingerspelled: "fingerspelled", name: "name, shown as text", not_available: "not available" };
  const TEXT_SIGN_MS = tl.playback.text_hold_s * 1000;
  const CLIP_LOAD_TIMEOUT_MS = 8000;
  const CLIP_STALL_MS = 4000;   // playing but no timeupdate for this long: the clip is stuck, treat it as failed
  const sentences = tl.sentences.length ? tl.sentences : [{ index: 0, t_start: 0, t_end: tl.media.duration_s || 0 }];
  const entriesBySentence = sentences.map((s) => tl.entries.filter((e) => e.sentence === s.index));
  const captionsBySentence = sentences.map((s) => tl.captions.filter((c) => c.sentence === s.index));

  // captions: one span per source word, in spoken order
  const capSpans = [];
  captionsBySentence.forEach((words, si) => {
    words.forEach((c, wi) => {
      const span = document.createElement("span");
      span.textContent = c.text;
      if (c.dropped) span.classList.add("dropped");
      if (c.partly) {   // the unsigned parts of the word, struck through after it: 30% percent
        span.classList.add("partly");
        const s = document.createElement("s");
        s.textContent = " " + c.missing.join(" ");
        span.appendChild(s);
      }
      caps.appendChild(span);
      caps.appendChild(document.createTextNode(" "));
      capSpans.push({ span, si, wi });
    });
  });

  const state = { playing: false, sentence: 0, stopped: true, token: 0, speaking: false };
  let cur = 0;              // which video element is showing
  let cancelClip = null;    // cleanup for the clip in flight
  let cancelNarration = null;

  const live = (token) => token === state.token;
  const setStatus = (t) => { status.textContent = t; };
  const showSign = (e) => {
    glossEl.textContent = e ? e.gloss : "—";
    badgeEl.textContent = e ? BADGE_TEXT[e.badge] : "";
    badgeEl.className = "s2s-badge" + (e ? " " + e.badge : "");
    noteEl.textContent = e && e.note ? e.note : "";
    // the source word under the gloss, so NIGHT for "late" reads as a lookup, not a mistake (word and gloss are required strings in the contract)
    wordEl.textContent = e && e.word.toUpperCase() !== e.gloss.replace(/[a-z]+$/, "") ? `for \u201c${e.word}\u201d` : "";
  };
  const progress = (done) => { bar.style.width = `${Math.round(100 * done / Math.max(1, tl.entries.length))}%`; };
  // Pin the panel over the captions on narrow screens only while it leaves at least 35% of the viewport for caption lines;
  // measured, not assumed, because the panel grows with a wrapped note; the waiting notice alone must not flip the pin.
  const panelEl = $(".s2s-panel"), narrow = window.matchMedia("(max-width:800px)");
  const updatePin = () => panelEl.classList.toggle("pinned", narrow.matches && panelEl.offsetHeight <= window.innerHeight * 0.65);
  updatePin();
  window.addEventListener("resize", updatePin);
  const pinObserver = "ResizeObserver" in window ? new ResizeObserver(updatePin) : null;
  if (pinObserver) pinObserver.observe(panelEl);
  // While the panel is pinned, the spoken word is kept in the visible caption area (below the panel, above the fold).
  // A viewer who scrolls by hand opts out until the next Play, Replay or Restart, so reaching the controls is never
  // fought. Intent is read from the gestures themselves (wheel, touch, a mousedown on the scroller's own scrollbar, the
  // scrolling keys outside the panel), never from scroll positions: Streamlit's own layout shifts move the page too.
  const scroller = (root.getRootNode().host || root).closest("section.stMain") || document.documentElement;
  const follow = { on: true };
  const optOut = () => { follow.on = false; };
  const optOutBar = (e) => { if (e.target === scroller) follow.on = false; };   // a mousedown on the scroller itself is its scrollbar
  const optOutKeys = (e) => {
    // a window listener sees events from inside the component retargeted to its host, so membership is read from the composed path
    const inPanel = e.composedPath().includes(root), field = /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) || e.target.isContentEditable;
    if (["ArrowUp", "ArrowDown", "PageUp", "PageDown", "Home", "End"].includes(e.key) || (e.key === " " && !inPanel && !field)) follow.on = false;
  };
  window.addEventListener("wheel", optOut, { passive: true });
  window.addEventListener("touchmove", optOut, { passive: true });
  scroller.addEventListener("mousedown", optOutBar);
  window.addEventListener("keydown", optOutKeys);
  const highlight = (si, wi) => {
    capSpans.forEach((x) => {
      x.span.classList.toggle("now", x.si === si && x.wi === wi);
      x.span.classList.toggle("said", x.si < si || (x.si === si && x.wi < wi));
      if (follow.on && panelEl.classList.contains("pinned") && x.si === si && x.wi === wi) {
        const w = x.span.getBoundingClientRect(), p = panelEl.getBoundingClientRect();
        if (w.top < p.bottom || w.bottom > window.innerHeight) {
          x.span.style.scrollMarginTop = `${panelEl.offsetHeight + 8}px`;
          x.span.style.scrollMarginBottom = "24px";
          x.span.scrollIntoView({ block: "nearest" });
        }
      }
    });
  };
  const sleep = (ms, token) => new Promise((r) => setTimeout(() => r(live(token)), ms));

  // ---- one clip: load on the hidden buffer, seek to in_s, wait for the frame, swap, play to out_s ----
  // Resolves "played", "failed" (could not load, decode or play) or "cancelled". Every callback is guarded by a
  // done flag and the run token, so a late event from a cancelled clip cannot touch a newer run.
  function playClip(clip, token, onShown) {
    return new Promise((resolve) => {
      const v = vids[1 - cur];
      let timer = null, done = false;
      const cleanup = () => {
        clearTimeout(timer);
        v.removeEventListener("timeupdate", onTime); v.removeEventListener("ended", onEnd);
        v.removeEventListener("loadedmetadata", onLoaded); v.removeEventListener("seeked", onSeeked); v.removeEventListener("error", onError);
        if (cancelClip === cancel) cancelClip = null;   // only this clip's own handle, never a newer clip's
      };
      const finish = (result) => { if (done) return; done = true; cleanup(); resolve(result); };
      const cancel = () => { v.pause(); finish("cancelled"); };
      const onTime = () => {
        if (!live(token)) return finish("cancelled");
        clearTimeout(timer); timer = setTimeout(onError, CLIP_STALL_MS);   // progress watchdog
        if (v.currentTime >= clip.out_s - 0.03) { v.pause(); finish("played"); }
      };
      // a clip that ends before its out-point is truncated media: a sign that did not complete counts as failed, not played
      // out_s never exceeds the recorded duration (lexicon.load checks it), so an honest "ended" lands within one frame of
      // out_s or after it; 50 ms covers a frame at the slowest rate plus the 3-decimal rounding of the recorded times
      const onEnd = () => finish(!live(token) ? "cancelled" : v.currentTime >= clip.out_s - 0.05 ? "played" : "failed");
      const onError = () => finish(live(token) ? "failed" : "cancelled");
      const onSeeked = () => {   // the target frame is decoded: now the buffer may be shown under this entry's label
        if (done) return;          // a late seek after a timeout or a cancel must not touch the screen
        if (!live(token)) return finish("cancelled");
        clearTimeout(timer); timer = setTimeout(onError, CLIP_STALL_MS);   // the load/seek deadline is met; from here the watchdog is progress
        vids[cur].hidden = true; v.hidden = false; cur = 1 - cur;
        onShown();
        v.addEventListener("timeupdate", onTime); v.addEventListener("ended", onEnd);
        v.play().catch(onError);
      };
      const onLoaded = () => {
        if (done) return;
        if (!live(token)) return finish("cancelled");
        clearTimeout(timer);
        timer = setTimeout(onError, CLIP_LOAD_TIMEOUT_MS);
        v.playbackRate = clip.rate || 1;
        v.addEventListener("seeked", onSeeked, { once: true });
        v.currentTime = clip.in_s || 0;   // fires seeked even when already there (a seek to the same time still seeks)
      };
      cancelClip = cancel;
      v.addEventListener("error", onError);
      timer = setTimeout(onError, CLIP_LOAD_TIMEOUT_MS);
      const src = new URL(clip.url, document.baseURI).href;
      if (v.src === src && v.readyState >= 1) { onLoaded(); return; }
      v.addEventListener("loadedmetadata", onLoaded);
      if (v.src !== src) { v.src = src; v.load(); }
    });
  }

  // A word shown as text instead of a clip: a name, an unavailable word, or an entry whose clip failed.
  async function holdText(e, token, text, note) {
    showSign(e);
    if (note) noteEl.textContent = note;
    vids.forEach((v) => { v.pause(); v.hidden = true; });
    textSign.textContent = text;
    textSign.hidden = false;
    const ok = await sleep(TEXT_SIGN_MS, token);
    if (ok) textSign.hidden = true;   // a stale timer must not hide a newer run's text
    return ok;
  }

  async function playEntry(e, token) {
    if (!live(token)) return false;
    if (e.clips.length === 0) return holdText(e, token, e.badge === "name" ? e.word : e.word + "\n(no sign)");
    let shown = false;
    for (const clip of e.clips) {
      // the label changes only once this entry's first clip is on screen, never over the previous sign's last frame
      const r = await playClip(clip, token, () => { if (!shown) { showSign(e); shown = true; } });
      if (r === "cancelled") return false;
      // one clip of the entry failed: the rest must not play under this word's label (a number missing a digit is a different number)
      if (r === "failed") return holdText(e, token, e.word + "\n(clip unavailable)", "a clip for this word could not be played; shown as text instead");
    }
    return true;
  }

  // ---- narration for one sentence: recorded audio, browser voice, or a silent timer ----
  // Resolves true when the sentence was narrated, false when cancelled or the browser refused to play.
  function narrate(si, token) {
    const s = sentences[si];
    const words = captionsBySentence[si];
    return new Promise((resolve) => {
      if (tl.media.kind === "audio" && tl.media.url) {
        const onTime = () => {
          const t = audio.currentTime;
          let wi = -1;
          words.forEach((c, i) => { if (c.t <= t) wi = i; });
          if (wi >= 0) highlight(si, wi);
          if (t >= s.t_end - 0.05) { audio.pause(); finish(live(token)); }
        };
        const onEnd = () => finish(live(token));
        let done = false;
        const cleanup = () => { audio.removeEventListener("timeupdate", onTime); audio.removeEventListener("ended", onEnd); if (cancelNarration === cancel) cancelNarration = null; };
        const finish = (ok) => { if (done) return; done = true; cleanup(); resolve(ok); };
        const cancel = () => { audio.pause(); finish(false); };
        cancelNarration = cancel;
        audio.addEventListener("timeupdate", onTime);
        audio.addEventListener("ended", onEnd);
        audio.currentTime = s.t_start;
        audio.play().catch(() => finish(false));
        return;
      }
      const text = words.map((c) => c.text).join(" ");
      if (tl.media.kind === "tts" && "speechSynthesis" in window && words.length) {
        const u = new SpeechSynthesisUtterance(text);
        const starts = []; let pos = 0;
        words.forEach((c) => { starts.push(pos); pos += c.text.length + 1; });
        let done = false;
        const finish = (ok) => { if (done) return; done = true; state.speaking = false; if (cancelNarration === cancel) cancelNarration = null; resolve(ok); };
        const cancel = () => { window.speechSynthesis.cancel(); finish(false); };
        cancelNarration = cancel;
        u.onboundary = (ev) => { if (!live(token)) return; let wi = 0; starts.forEach((st, i) => { if (ev.charIndex >= st) wi = i; }); highlight(si, wi); };
        u.onend = () => finish(live(token));
        u.onerror = () => finish(live(token));
        window.speechSynthesis.cancel();   // the user pressed Play here: this narration wins over any other panel's
        state.speaking = true;
        window.speechSynthesis.speak(u);
        return;
      }
      // captions only: reveal words on the estimated clock
      let i = 0;
      const step = () => {
        if (!live(token)) return resolve(false);
        if (i >= words.length) return resolve(true);
        highlight(si, i);
        const dt = i + 1 < words.length ? (words[i + 1].t - words[i].t) : (s.t_end - words[i].t);
        i += 1; setTimeout(step, Math.max(150, dt * 1000));
      };
      step();
    });
  }

  async function run(fromSentence) {
    const token = ++state.token;
    state.stopped = false; state.playing = true; playBtn.textContent = "Pause";
    follow.on = true;   // Play, Replay and Restart opt back in to caption following
    hint.hidden = true;
    progress(sentences.slice(0, fromSentence).reduce((n, s2) => n + entriesBySentence[s2.index].length, 0));   // the bar shows what this run has done: nothing yet of the sentence being (re)played
    for (let si = fromSentence; si < sentences.length; si++) {
      if (!live(token)) return;
      state.sentence = si;
      setStatus(`Sentence ${si + 1} of ${sentences.length}`);
      wait.hidden = true;
      const narration = narrate(si, token);
      let signed = true;
      const before = sentences.slice(0, si).reduce((n, s2) => n + entriesBySentence[s2.index].length, 0);
      const signing = (async () => { let k = 0; for (const e of entriesBySentence[si]) { if (!(await playEntry(e, token))) { signed = false; break; } if (live(token)) progress(before + ++k); } })();
      const narrated = await narration;
      if (!live(token)) return;
      if (!narrated) { halt("Playback was blocked by the browser. Press Play to try again.", "Play"); return; }
      let waiting = true;
      signing.then(() => { waiting = false; });
      await Promise.race([signing, sleep(50, token)]);
      if (!live(token)) return;
      if (waiting) { wait.hidden = false; setStatus(`Sentence ${si + 1} of ${sentences.length} · waiting for the interpreter`); }
      await signing;
      if (!live(token)) return;
      wait.hidden = true;
      if (!signed) return;
    }
    progress(tl.entries.length);
    highlight(-1, -1); capSpans.forEach((x) => x.span.classList.add("said"));
    showSign(null); state.playing = false; state.stopped = true; playBtn.textContent = "Play again";
    setStatus(`Done · speech ${Math.round(tl.stats.speech_s)} s, signing about ${Math.round(tl.stats.signing_s)} s`);
  }

  // Stop everything now. label is what the Play button offers next.
  function halt(message, label = "Play") {
    state.token += 1; state.playing = false;
    if (cancelClip) cancelClip();
    if (cancelNarration) cancelNarration();
    audio.pause(); vids.forEach((v) => v.pause());
    if (state.speaking && "speechSynthesis" in window) { window.speechSynthesis.cancel(); state.speaking = false; }
    textSign.hidden = true; wait.hidden = true;
    setStatus(message);
    playBtn.textContent = label;
  }

  function stop() {
    // resuming replays the current sentence from its start (narration and signing together)
    halt(`Paused at sentence ${state.sentence + 1} of ${sentences.length}`, "Replay sentence");
  }

  if (tl.media.kind === "audio" && tl.media.url) audio.src = new URL(tl.media.url, document.baseURI).href;
  const hint = $(".s2s-hint");
  if (tl.entries.length && tl.entries[0].clips.length) {
    // Preload the first clip and show its first active frame, paused, as the poster: the panel opens on the signer,
    // not on a black box. The first playClip finds this element already loaded and seeks from here.
    const first = tl.entries[0].clips[0], v = vids[1];
    v.src = new URL(first.url, document.baseURI).href;
    v.addEventListener("loadedmetadata", () => {
      v.addEventListener("seeked", () => {
        if (state.stopped && !state.playing) { vids[0].hidden = true; v.hidden = false; showSign(tl.entries[0]); }   // a shown signer always carries its label and badge
      }, { once: true });
      v.currentTime = first.in_s || 0;
    }, { once: true });
  } else {
    hint.hidden = true;   // nothing to preview when the first entry is text
  }
  playBtn.addEventListener("click", () => { if (state.playing) stop(); else run(state.stopped ? 0 : state.sentence); });
  restartBtn.addEventListener("click", () => { stop(); state.stopped = true; run(0); });
  // Keyboard: Space plays/pauses and R restarts while the focus is anywhere in the panel (the buttons carry aria-keyshortcuts).
  // Space on a focused button is left to the button itself, so it is not handled twice.
  root.addEventListener("keydown", (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey) return;   // Ctrl+R and friends stay the browser's
    const space = e.key === " " && e.target.tagName !== "BUTTON";
    if (space) e.preventDefault();   // a held Space must not scroll the page either, so this comes before the repeat check
    if (e.repeat) return;            // a held key acts once
    if (space) playBtn.click();
    else if (e.key === "r" || e.key === "R") { e.preventDefault(); restartBtn.click(); }
  });
  // Projected playback: per sentence the narration and the signing overlap and the longer one sets the pace (the media
  // waits for the signer, and the signer waits for the next sentence), so the total is the sum of the per-sentence maxima.
  const clipTime = (e) => (e.clips.length ? e.clips.reduce((t, c) => t + (c.out_s - c.in_s) / c.rate, 0) : tl.playback.text_hold_s);
  const total = sentences.reduce((t, s2) => t + Math.max(s2.t_end - s2.t_start, entriesBySentence[s2.index].reduce((u, e) => u + clipTime(e), 0)), 0);
  // seconds under a minute, half minutes above; never "0" for something that plays
  const about = total < 60 ? `${Math.max(1, Math.round(total))} s` : `${Math.round(total / 30) / 2} min`;
  setStatus(`Ready · ${sentences.length} sentence${sentences.length === 1 ? "" : "s"}, ${tl.entries.length} signs · about ${about} to play: the narration waits for the signer`);

  return () => {   // teardown on rerun or unmount: stop playback and release the resize hooks so nothing outlives the panel
    halt("Stopped", "Play");
    window.removeEventListener("resize", updatePin);
    window.removeEventListener("wheel", optOut); window.removeEventListener("touchmove", optOut);
    scroller.removeEventListener("mousedown", optOutBar); window.removeEventListener("keydown", optOutKeys);
    if (pinObserver) pinObserver.disconnect();
  };
}
