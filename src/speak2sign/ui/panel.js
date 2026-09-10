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
  const glossEl = $(".s2s-gloss"), badgeEl = $(".s2s-badge"), noteEl = $(".s2s-note");

  const BADGE_TEXT = { validated: "validated", fingerspelled: "fingerspelled", name: "name, shown as text", not_available: "not available" };
  const TEXT_SIGN_MS = tl.playback.text_hold_s * 1000;
  const CLIP_LOAD_TIMEOUT_MS = 8000;
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
  };
  const highlight = (si, wi) => {
    capSpans.forEach((x) => {
      x.span.classList.toggle("now", x.si === si && x.wi === wi);
      x.span.classList.toggle("said", x.si < si || (x.si === si && x.wi < wi));
    });
  };
  const sleep = (ms, token) => new Promise((r) => setTimeout(() => r(live(token)), ms));

  // ---- one clip: load on the hidden buffer, seek to in_s, swap, play to out_s ----
  // Resolves true when the clip played (or could not load and was skipped with a visible note), false when cancelled.
  function playClip(clip, token, onShown) {
    return new Promise((resolve) => {
      const v = vids[1 - cur];
      let timer = null;
      const cleanup = () => {
        clearTimeout(timer);
        v.removeEventListener("timeupdate", onTime); v.removeEventListener("ended", onEnd);
        v.removeEventListener("loadedmetadata", start); v.removeEventListener("error", onError);
        cancelClip = null;
      };
      const finish = (ok) => { cleanup(); resolve(ok); };
      cancelClip = () => { v.pause(); finish(false); };
      const onTime = () => { if (v.currentTime >= clip.out_s - 0.03) { v.pause(); finish(live(token)); } };
      const onEnd = () => finish(live(token));
      const onError = () => { noteEl.textContent = "clip could not be loaded; skipped"; finish(live(token)); };
      const start = () => {
        if (!live(token)) return finish(false);
        clearTimeout(timer);
        v.currentTime = clip.in_s || 0;
        v.playbackRate = clip.rate || 1;
        vids[cur].hidden = true; v.hidden = false; cur = 1 - cur;
        onShown();
        v.addEventListener("timeupdate", onTime); v.addEventListener("ended", onEnd);
        v.play().catch(onError);
      };
      v.addEventListener("error", onError);
      timer = setTimeout(onError, CLIP_LOAD_TIMEOUT_MS);
      const src = new URL(clip.url, document.baseURI).href;
      if (v.src === src && v.readyState >= 1) { start(); return; }
      v.addEventListener("loadedmetadata", start);
      if (v.src !== src) { v.src = src; v.load(); }
    });
  }

  async function playEntry(e, token) {
    if (!live(token)) return false;
    if (e.clips.length === 0) {
      showSign(e);
      textSign.textContent = e.badge === "name" ? e.word : e.word + "\n(no sign)";
      textSign.hidden = false;
      const ok = await sleep(TEXT_SIGN_MS, token);
      textSign.hidden = true;
      return ok;
    }
    let shown = false;
    for (const clip of e.clips) {
      // the label changes only once this entry's first clip is on screen, never over the previous sign's last frame
      if (!(await playClip(clip, token, () => { if (!shown) { showSign(e); shown = true; } }))) return false;
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
        const cleanup = () => { audio.removeEventListener("timeupdate", onTime); audio.removeEventListener("ended", onEnd); cancelNarration = null; };
        const finish = (ok) => { cleanup(); resolve(ok); };
        cancelNarration = () => { audio.pause(); finish(false); };
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
        const finish = (ok) => { state.speaking = false; cancelNarration = null; resolve(ok); };
        cancelNarration = () => { window.speechSynthesis.cancel(); finish(false); };
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
    for (let si = fromSentence; si < sentences.length; si++) {
      if (!live(token)) return;
      state.sentence = si;
      setStatus(`Sentence ${si + 1} of ${sentences.length}`);
      wait.hidden = true;
      const narration = narrate(si, token);
      let signed = true;
      const signing = (async () => { for (const e of entriesBySentence[si]) { if (!(await playEntry(e, token))) { signed = false; break; } } })();
      const narrated = await narration;
      if (!live(token)) return;
      if (!narrated) { halt("Playback was blocked by the browser. Press Play to try again."); return; }
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
    highlight(-1, -1); capSpans.forEach((x) => x.span.classList.add("said"));
    showSign(null); state.playing = false; state.stopped = true; playBtn.textContent = "Play again";
    setStatus(`Done · speech ${Math.round(tl.stats.speech_s)} s, signing about ${Math.round(tl.stats.signing_s)} s`);
  }

  function halt(message) {
    state.token += 1; state.playing = false;
    if (cancelClip) cancelClip();
    if (cancelNarration) cancelNarration();
    audio.pause(); vids.forEach((v) => v.pause());
    if (state.speaking && "speechSynthesis" in window) { window.speechSynthesis.cancel(); state.speaking = false; }
    textSign.hidden = true; wait.hidden = true;
    setStatus(message);
  }

  function stop() {
    halt(`Paused at sentence ${state.sentence + 1} of ${sentences.length}`);
    playBtn.textContent = "Replay sentence";   // resuming replays the current sentence from its start (narration and signing together)
  }

  if (tl.media.kind === "audio" && tl.media.url) audio.src = new URL(tl.media.url, document.baseURI).href;
  if (tl.entries.length && tl.entries[0].clips.length) {
    vids[1].src = new URL(tl.entries[0].clips[0].url, document.baseURI).href; // preload the first clip
  }
  playBtn.addEventListener("click", () => { if (state.playing) stop(); else run(state.stopped ? 0 : state.sentence); });
  restartBtn.addEventListener("click", () => { stop(); state.stopped = true; run(0); });
  setStatus(`Ready · ${sentences.length} sentence${sentences.length === 1 ? "" : "s"}, ${tl.entries.length} signs`);

  return () => halt("Stopped");
}
