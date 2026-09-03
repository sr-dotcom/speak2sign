// Speak2Sign interpreter panel. Reads a timeline (contracts/timeline.schema.json); decides nothing about signs.
// Interpreter-paced (ADR 0008): the news plays one sentence, then waits until the panel has signed it.
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
  const TEXT_SIGN_MS = 900;
  const sentences = tl.sentences || [{ index: 0, t_start: 0, t_end: tl.media.duration_s || 0 }];
  const entriesBySentence = sentences.map((s) => tl.entries.filter((e) => (e.sentence ?? 0) === s.index));
  const captionsBySentence = sentences.map((s, i) => tl.captions.filter((c) => c.t >= s.t_start && (i === sentences.length - 1 || c.t < sentences[i + 1].t_start)));

  // captions: one span per word, in spoken order
  const capSpans = [];
  captionsBySentence.forEach((words, si) => {
    words.forEach((c, wi) => {
      const span = document.createElement("span");
      span.textContent = c.text;
      if (c.dropped) span.classList.add("dropped");
      caps.appendChild(span);
      caps.appendChild(document.createTextNode(" "));
      capSpans.push({ span, si, wi, c });
    });
  });

  let state = { playing: false, sentence: 0, stopped: true, token: 0 };
  let cur = 0; // which video element is showing

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

  const sleep = (ms, token) => new Promise((r) => setTimeout(() => r(token === state.token), ms));

  // ---- one clip: play [in_s, out_s] at rate on the hidden buffer, then swap ----
  function playClip(clip, token) {
    return new Promise((resolve) => {
      const v = vids[1 - cur];
      const done = () => { v.removeEventListener("timeupdate", onTime); v.removeEventListener("ended", onEnd); resolve(token === state.token); };
      const onTime = () => { if (v.currentTime >= clip.out_s - 0.03) { v.pause(); done(); } };
      const onEnd = () => done();
      const start = () => {
        v.currentTime = clip.in_s || 0;
        v.playbackRate = clip.rate || 1;
        vids[cur].hidden = true; v.hidden = false; cur = 1 - cur;
        v.addEventListener("timeupdate", onTime); v.addEventListener("ended", onEnd);
        v.play().catch(() => done());
      };
      const src = new URL(clip.url, document.baseURI).href;
      if (v.src !== src) { v.src = src; v.addEventListener("loadedmetadata", start, { once: true }); v.load(); } else { start(); }
    });
  }

  async function playEntry(e, token) {
    if (token !== state.token) return false;
    showSign(e);
    if (!e.clips || e.clips.length === 0) {
      textSign.textContent = e.badge === "name" ? e.word : e.word + "\n(no sign)";
      textSign.hidden = false;
      const ok = await sleep(TEXT_SIGN_MS, token);
      textSign.hidden = true;
      return ok;
    }
    for (const clip of e.clips) {
      if (!(await playClip(clip, token))) return false;
    }
    return true;
  }

  // ---- narration for one sentence: recorded audio, browser voice, or a silent timer ----
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
          if (t >= s.t_end - 0.05) { audio.pause(); audio.removeEventListener("timeupdate", onTime); resolve(token === state.token); }
        };
        audio.addEventListener("timeupdate", onTime);
        audio.addEventListener("ended", () => { audio.removeEventListener("timeupdate", onTime); resolve(token === state.token); }, { once: true });
        audio.currentTime = s.t_start;
        audio.play().catch(() => resolve(false));
        return;
      }
      const text = words.map((c) => c.text).join(" ");
      if (tl.media.kind === "tts" && "speechSynthesis" in window && words.length) {
        const u = new SpeechSynthesisUtterance(text);
        const starts = []; let pos = 0;
        words.forEach((c) => { starts.push(pos); pos += c.text.length + 1; });
        u.onboundary = (ev) => { let wi = 0; starts.forEach((st, i) => { if (ev.charIndex >= st) wi = i; }); highlight(si, wi); };
        u.onend = () => resolve(token === state.token);
        u.onerror = () => resolve(token === state.token);
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(u);
        return;
      }
      // captions only: reveal words on the estimated clock
      let i = 0;
      const step = () => {
        if (token !== state.token) return resolve(false);
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
      if (token !== state.token) return;
      state.sentence = si;
      setStatus(`Sentence ${si + 1} of ${sentences.length}`);
      wait.hidden = true;
      const narration = narrate(si, token);
      let signed = true;
      const signing = (async () => { for (const e of entriesBySentence[si]) { if (!(await playEntry(e, token))) { signed = false; break; } } })();
      const narrated = await narration;
      if (!narrated) return;
      let waiting = true;
      signing.then(() => { waiting = false; });
      await Promise.race([signing, sleep(50, token)]);
      if (waiting) { wait.hidden = false; setStatus(`Sentence ${si + 1} of ${sentences.length} · waiting for the interpreter`); }
      await signing;
      wait.hidden = true;
      if (!signed) return;
    }
    highlight(-1, -1); capSpans.forEach((x) => x.span.classList.add("said"));
    showSign(null); state.playing = false; state.stopped = true; playBtn.textContent = "Play again";
    setStatus(`Done · speech ${Math.round(tl.stats.speech_s)} s, signing about ${Math.round(tl.stats.signing_s)} s`);
  }

  function stop() {
    state.token += 1; state.playing = false;
    audio.pause(); vids.forEach((v) => v.pause()); if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    wait.hidden = true; playBtn.textContent = "Resume";
    setStatus(`Paused at sentence ${state.sentence + 1} of ${sentences.length}`);
  }

  if (tl.media.kind === "audio" && tl.media.url) audio.src = new URL(tl.media.url, document.baseURI).href;
  if (tl.entries.length && tl.entries[0].clips && tl.entries[0].clips.length) {
    vids[1].src = new URL(tl.entries[0].clips[0].url, document.baseURI).href; // preload the first clip
  }
  playBtn.addEventListener("click", () => { if (state.playing) stop(); else run(state.stopped ? 0 : state.sentence); });
  restartBtn.addEventListener("click", () => { stop(); state.stopped = true; run(0); });
  setStatus(`Ready · ${sentences.length} sentence${sentences.length === 1 ? "" : "s"}, ${tl.entries.length} signs`);

  return () => { state.token += 1; audio.pause(); vids.forEach((v) => v.pause()); if ("speechSynthesis" in window) window.speechSynthesis.cancel(); };
}
