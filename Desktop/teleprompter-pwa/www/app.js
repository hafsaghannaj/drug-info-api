const scriptEl = document.getElementById('script');
const teletext = document.getElementById('teletext');
const viewport = document.getElementById('viewport');
const guideLine = document.getElementById('guideLine');

const startBtn = document.getElementById('start');
const pauseBtn = document.getElementById('pause');
const resetBtn = document.getElementById('reset');
const mirrorBtn = document.getElementById('mirror');
const guideBtn = document.getElementById('guide');
const fsBtn = document.getElementById('fullscreen');

const speedEl = document.getElementById('speed');
const fontEl = document.getElementById('font');
const lineEl = document.getElementById('line');
const speedVal = document.getElementById('speedVal');
const fontVal = document.getElementById('fontVal');
const lineVal = document.getElementById('lineVal');

const cueList = document.getElementById('cueList');
const prevCueBtn = document.getElementById('prevCue');
const nextCueBtn = document.getElementById('nextCue');
const nextPlayBtn = document.getElementById('nextPlay');
const autoplayBtn = document.getElementById('autoplay');

const timeStatus = document.getElementById('timeStatus');
const posStatus = document.getElementById('posStatus');

let running = false;
let last = null;
let accumulator = 0;
let mirrored = false;
let showGuide = true;
let state = 'Ready';

let words = [];
let cues = [];
let currentCueIndex = -1;
let currentWordIndex = 0;
let autoPlay = false;
let lastScriptValue = '';

function wordsPerMinute() {
  return Number(speedEl.value);
}

function secondsPerWord() {
  const wpm = Math.max(10, wordsPerMinute());
  return 60 / wpm;
}

function setState(next) {
  state = next;
  if (state !== 'Playing') {
    timeStatus.textContent = state;
  }
}

function setFont() {
  const size = Number(fontEl.value);
  teletext.style.fontSize = size + 'px';
  fontVal.textContent = size + 'px';
}

function setLineHeight() {
  const ratio = Number(lineEl.value) / 100;
  teletext.style.lineHeight = String(ratio);
  lineVal.textContent = ratio.toFixed(2);
}

function setSpeedLabel() {
  speedVal.textContent = wordsPerMinute() + ' wpm';
}

function updateAutoPlayButton() {
  autoplayBtn.textContent = autoPlay ? 'Auto-play: On' : 'Auto-play: Off';
  autoplayBtn.classList.toggle('on', autoPlay);
}

function toggleAutoPlay() {
  autoPlay = !autoPlay;
  updateAutoPlayButton();
}

function tokenizeLine(line) {
  const trimmed = line.trim();
  return trimmed ? trimmed.match(/\S+/g) || [] : [];
}

function parseCues(lines, lineStarts) {
  const found = [];
  lines.forEach((line, index) => {
    const trimmed = line.trim();
    if (!trimmed) return;
    let label = '';
    if (trimmed.startsWith('##')) {
      label = trimmed.replace(/^##+/, '').trim();
    } else {
      const match = trimmed.match(/^\[\[(.+?)\]\]$/);
      if (match) label = match[1].trim();
    }
    if (!label) return;
    found.push({ label, wordIndex: lineStarts[index] || 0 });
  });
  return found;
}

function updateCueButtons() {
  const hasCues = cues.length > 0;
  prevCueBtn.disabled = !hasCues || currentCueIndex <= 0;
  nextCueBtn.disabled = !hasCues || currentCueIndex >= cues.length - 1;
  nextPlayBtn.disabled = !hasCues || currentCueIndex >= cues.length - 1;
}

function renderCueList() {
  cueList.innerHTML = '';
  if (!cues.length) {
    const empty = document.createElement('div');
    empty.className = 'cue-empty';
    empty.textContent = 'No cues yet.';
    cueList.appendChild(empty);
    updateCueButtons();
    return;
  }

  const fragment = document.createDocumentFragment();
  cues.forEach((cue, idx) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'cue-btn' + (idx === currentCueIndex ? ' active' : '');
    btn.textContent = cue.label;
    btn.addEventListener('click', () => jumpToCue(idx));
    fragment.appendChild(btn);
  });
  cueList.appendChild(fragment);
  updateCueButtons();
}

function setCues(nextCues) {
  const prevWord = cues[currentCueIndex]?.wordIndex;
  cues = nextCues;
  if (!cues.length) {
    currentCueIndex = -1;
  } else if (prevWord != null) {
    const matchIndex = cues.findIndex((cue) => cue.wordIndex === prevWord);
    currentCueIndex = matchIndex !== -1 ? matchIndex : 0;
  } else if (currentCueIndex < 0) {
    currentCueIndex = 0;
  }
  renderCueList();
}

function loadText({ keepPosition = false } = {}) {
  const raw = scriptEl.value;
  const fallback = 'Paste your script on the left to begin.';
  const baseText = raw.trim() || fallback;
  const lines = baseText.split(/\r?\n/);
  const nextWords = [];
  const lineStarts = [];

  lines.forEach((line) => {
    lineStarts.push(nextWords.length);
    nextWords.push(...tokenizeLine(line));
  });

  if (!nextWords.length) {
    nextWords.push(...tokenizeLine(fallback));
  }

  const prevProgress = words.length > 1 ? currentWordIndex / (words.length - 1) : 0;
  words = nextWords;
  currentWordIndex = keepPosition && words.length > 1 ? Math.round(prevProgress * (words.length - 1)) : 0;
  accumulator = 0;
  lastScriptValue = raw;

  setCues(parseCues(lines, lineStarts));
  render();
}

function ensureTextLoaded(keepPosition) {
  if (!words.length || scriptEl.value !== lastScriptValue) {
    loadText({ keepPosition });
  }
}

function formatTime(seconds) {
  if (!isFinite(seconds) || seconds <= 0) return '0:00';
  const total = Math.round(seconds);
  const mins = Math.floor(total / 60);
  const secs = total % 60;
  return `${mins}:${String(secs).padStart(2, '0')}`;
}

function updateStatus() {
  const total = words.length;
  const index = total ? Math.min(currentWordIndex + 1, total) : 0;
  const pct = total ? Math.round((index / total) * 100) : 0;
  posStatus.textContent = total ? `Word ${index}/${total} (${pct}%)` : '';

  if (state === 'Playing') {
    const remaining = total ? Math.max(0, (total - index) * secondsPerWord()) : 0;
    timeStatus.textContent = `Playing ${formatTime(remaining)}`;
  }
}

function syncActiveCue() {
  if (!cues.length) return;
  let activeIndex = 0;
  cues.forEach((cue, idx) => {
    if (cue.wordIndex <= currentWordIndex) activeIndex = idx;
  });
  if (activeIndex !== currentCueIndex) {
    currentCueIndex = activeIndex;
    renderCueList();
  } else {
    updateCueButtons();
  }
}

function render() {
  teletext.textContent = words[currentWordIndex] || '';
  teletext.style.transform = mirrored ? 'scaleX(-1)' : 'none';
  updateStatus();
  syncActiveCue();
}

function playFromCurrent() {
  if (!words.length) return;
  if (running) return;
  if (currentWordIndex >= words.length - 1) {
    currentWordIndex = 0;
  }
  accumulator = 0;
  running = true;
  setState('Playing');
  pauseBtn.disabled = false;
  startBtn.disabled = true;
  last = null;
  render();
  requestAnimationFrame(tick);
}

function tick(ts) {
  if (!running) return;
  if (last == null) last = ts;
  const dt = (ts - last) / 1000;
  last = ts;
  accumulator += dt;

  const step = secondsPerWord();
  while (accumulator >= step) {
    accumulator -= step;
    if (currentWordIndex < words.length - 1) {
      currentWordIndex += 1;
    } else {
      running = false;
      setState('Done');
      pauseBtn.disabled = true;
      startBtn.disabled = false;
      break;
    }
  }

  render();
  if (running) requestAnimationFrame(tick);
}

function start() {
  ensureTextLoaded(true);
  playFromCurrent();
}

function pause() {
  running = false;
  last = null;
  setState('Paused');
  pauseBtn.disabled = true;
  startBtn.disabled = false;
}

function resetScroll() {
  running = false;
  last = null;
  setState('Ready');
  pauseBtn.disabled = true;
  startBtn.disabled = false;
  loadText({ keepPosition: false });
}

function jumpToCue(index, options = {}) {
  if (!cues.length) return;
  const nextIndex = Math.max(0, Math.min(index, cues.length - 1));
  currentCueIndex = nextIndex;
  currentWordIndex = Math.min(cues[nextIndex].wordIndex, words.length - 1);
  if (!running && state === 'Done') setState('Paused');
  render();
  renderCueList();
  const shouldPlay = options.play || autoPlay;
  if (shouldPlay) playFromCurrent();
}

function nextCue() {
  if (!cues.length) return;
  const nextIndex = currentCueIndex < 0 ? 0 : Math.min(currentCueIndex + 1, cues.length - 1);
  jumpToCue(nextIndex);
}

function prevCue() {
  if (!cues.length) return;
  const prevIndex = currentCueIndex <= 0 ? 0 : currentCueIndex - 1;
  jumpToCue(prevIndex);
}

function nextCueAndPlay() {
  if (!cues.length) return;
  const nextIndex = currentCueIndex < 0 ? 0 : Math.min(currentCueIndex + 1, cues.length - 1);
  jumpToCue(nextIndex, { play: true });
}

function toggleMirror() {
  mirrored = !mirrored;
  mirrorBtn.textContent = mirrored ? 'Mirror: On' : 'Mirror: Off';
  mirrorBtn.classList.toggle('on', mirrored);
  render();
}

function toggleGuide() {
  showGuide = !showGuide;
  guideLine.style.display = showGuide ? 'block' : 'none';
  guideBtn.textContent = showGuide ? 'Guide: On' : 'Guide: Off';
  guideBtn.classList.toggle('on', showGuide);
}

async function toggleFullscreen() {
  try {
    if (!document.fullscreenElement) {
      await document.documentElement.requestFullscreen();
    } else {
      await document.exitFullscreen();
    }
  } catch (err) {
    // Ignore fullscreen errors.
  }
}

startBtn.addEventListener('click', start);
pauseBtn.addEventListener('click', pause);
resetBtn.addEventListener('click', resetScroll);
mirrorBtn.addEventListener('click', toggleMirror);
guideBtn.addEventListener('click', toggleGuide);
fsBtn.addEventListener('click', toggleFullscreen);
prevCueBtn.addEventListener('click', prevCue);
nextCueBtn.addEventListener('click', nextCue);
nextPlayBtn.addEventListener('click', nextCueAndPlay);
autoplayBtn.addEventListener('click', toggleAutoPlay);

speedEl.addEventListener('input', () => {
  setSpeedLabel();
  updateStatus();
});

fontEl.addEventListener('input', () => {
  setFont();
  render();
});

lineEl.addEventListener('input', () => {
  setLineHeight();
  render();
});

scriptEl.addEventListener('input', () => {
  loadText({ keepPosition: false });
});

viewport.addEventListener('click', () => {
  if (running) pause();
  else start();
});

document.addEventListener('keydown', (e) => {
  const tag = e.target.tagName ? e.target.tagName.toLowerCase() : '';
  const isTyping = tag === 'textarea' || (tag === 'input' && e.target.type !== 'range');
  if (isTyping && e.key !== 'Escape') return;

  if (e.key === ' ') {
    e.preventDefault();
    running ? pause() : start();
  }
  if (e.key === 'ArrowUp') {
    speedEl.value = Math.min(240, Number(speedEl.value) + 10);
    setSpeedLabel();
    updateStatus();
  }
  if (e.key === 'ArrowDown') {
    speedEl.value = Math.max(10, Number(speedEl.value) - 10);
    setSpeedLabel();
    updateStatus();
  }
  if (e.key === '+' || e.key === '=') {
    fontEl.value = Math.min(88, Number(fontEl.value) + 2);
    setFont();
    render();
  }
  if (e.key === '-') {
    fontEl.value = Math.max(24, Number(fontEl.value) - 2);
    setFont();
    render();
  }
  if (e.key === '[') {
    lineEl.value = Math.max(120, Number(lineEl.value) - 5);
    setLineHeight();
    render();
  }
  if (e.key === ']') {
    lineEl.value = Math.min(190, Number(lineEl.value) + 5);
    setLineHeight();
    render();
  }
  if (e.key.toLowerCase() === 'n' && e.shiftKey) {
    nextCueAndPlay();
  } else if (e.key.toLowerCase() === 'n') {
    nextCue();
  }
  if (e.key.toLowerCase() === 'p') prevCue();
  if (e.key.toLowerCase() === 'a') toggleAutoPlay();
  if (e.key.toLowerCase() === 'r') resetScroll();
});

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js').catch(() => {});
  });
}

setSpeedLabel();
setFont();
setLineHeight();
updateAutoPlayButton();
loadText({ keepPosition: false });
