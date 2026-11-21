// Air Harp - advanced web version
// MediaPipe Hands (JS) + Web Audio API + Canvas + live waveform visualizer.

const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const vizCanvas = document.getElementById('vizCanvas');
const vizCtx = vizCanvas.getContext('2d');

const fpsEl = document.getElementById('fps');
const nstrEl = document.getElementById('nstr');
const noteEl = document.getElementById('note');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const startBtn = document.getElementById('startBtn');
const startOverlay = document.getElementById('startOverlay');
const clearBtn = document.getElementById('clearBtn');
const stopBtn = document.getElementById('stopBtn');
const noteLegend = document.getElementById('noteLegend');
const stringList = document.getElementById('stringList');
const statActive = document.getElementById('statActive');
const statPlucks = document.getElementById('statPlucks');
const howModal = document.getElementById('howModal');
const aboutModal = document.getElementById('aboutModal');

const NOTE_NAMES = ["C4", "D4", "E4", "G4", "A4", "C5", "D5", "E5"];
const NOTE_FREQS = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25, 587.33, 659.25];
const STRING_COLORS = [
  [255, 90, 110], [255, 170, 70], [255, 230, 90], [120, 255, 140],
  [80, 255, 220], [90, 180, 255], [180, 120, 255], [255, 120, 220],
];

NOTE_NAMES.forEach((n, i) => {
  const c = STRING_COLORS[i % STRING_COLORS.length];
  const pill = document.createElement('div');
  pill.className = 'note-pill';
  pill.innerHTML = `${n}<span class="freq">${NOTE_FREQS[i].toFixed(1)} Hz</span>`;
  pill.style.background = `linear-gradient(135deg, rgb(${c[0]},${c[1]},${c[2]}), rgba(${c[0]},${c[1]},${c[2]},0.7))`;
  pill.style.boxShadow = `0 4px 18px rgba(${c[0]},${c[1]},${c[2]},0.4)`;
  pill.style.cursor = 'pointer';
  pill.title = `Play ${n}`;
  pill.addEventListener('click', () => {
    ensureAudio();
    if (audioCtx.state === 'suspended') audioCtx.resume();
    playNote(NOTE_FREQS[i]);
    lastNote = n;
    noteEl.textContent = lastNote;
    pill.animate([{ transform: 'scale(1.15)' }, { transform: 'scale(1)' }], { duration: 200 });
  });
  noteLegend.appendChild(pill);
});

let audioCtx = null;
let analyser = null;
let masterGain = null;
function ensureAudio() {
  if (audioCtx) return;
  audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  masterGain = audioCtx.createGain();
  masterGain.gain.value = 0.8;
  analyser = audioCtx.createAnalyser();
  analyser.fftSize = 256;
  masterGain.connect(analyser);
  analyser.connect(audioCtx.destination);
}
function playNote(freq) {
  ensureAudio();
  const now = audioCtx.currentTime;
  const dur = 0.8;
  const gain = audioCtx.createGain();
  gain.gain.setValueAtTime(0.0001, now);
  gain.gain.exponentialRampToValueAtTime(0.9, now + 0.01);
  gain.gain.exponentialRampToValueAtTime(0.0001, now + dur);
  gain.connect(masterGain);

  const o1 = audioCtx.createOscillator();
  o1.type = 'sine'; o1.frequency.value = freq;
  o1.connect(gain); o1.start(now); o1.stop(now + dur);

  const o2 = audioCtx.createOscillator();
  o2.type = 'sine'; o2.frequency.value = freq * 2;
  const g2 = audioCtx.createGain(); g2.gain.value = 0.5;
  o2.connect(g2); g2.connect(gain);
  o2.start(now); o2.stop(now + dur);
}

function dist(a, b) { return Math.hypot(a.x - b.x, a.y - b.y); }
function signedDist(px, py, x1, y1, x2, y2) {
  const dx = x2 - x1, dy = y2 - y1;
  const len = Math.hypot(dx, dy) || 1;
  return (dx * (py - y1) - dy * (px - x1)) / len;
}

class HarpString {
  constructor(p1, p2, color, noteIdx) {
    this.p1 = p1; this.p2 = p2;
    this.color = color; this.noteIdx = noteIdx;
    this.length = Math.hypot(p2.x - p1.x, p2.y - p1.y);
    this.lastPluck = 0; this.vibStart = 0; this.vibAmp = 0; this.vibDur = 0.6;
  }
  pluck(now) {
    if (now - this.lastPluck >= 0.25) {
      this.lastPluck = now; this.vibStart = now; this.vibAmp = 15;
      playNote(NOTE_FREQS[this.noteIdx]);
      return NOTE_NAMES[this.noteIdx];
    }
    return null;
  }
  ampNow(now) {
    const e = now - this.vibStart;
    if (e >= this.vibDur || this.vibAmp === 0) return 0;
    return this.vibAmp * (1 - e / this.vibDur);
  }
}

let strings = [];
let liveP1 = null, liveP2 = null, drawingActive = false;
const smoothedTips = {};
const prevDists = {};
const ALPHA = 0.5;
let lastNote = "—";
let pluckCount = 0;

function drawGlowLine(p1, p2, color, thick = 12, core = 2) {
  const [r, g, b] = color;
  ctx.save();
  ctx.lineCap = 'round';
  ctx.shadowColor = `rgb(${r},${g},${b})`;
  ctx.shadowBlur = 28;
  ctx.strokeStyle = `rgba(${r},${g},${b},0.9)`;
  ctx.lineWidth = thick;
  ctx.beginPath(); ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.stroke();
  ctx.shadowBlur = 0;
  ctx.strokeStyle = '#ffffff'; ctx.lineWidth = core;
  ctx.beginPath(); ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.stroke();
  ctx.restore();
}

function drawVibratingString(s, now) {
  const amp = s.ampNow(now);
  if (amp <= 0) { drawGlowLine(s.p1, s.p2, s.color); return; }
  const phase = (now - s.vibStart) * 20;
  const { p1, p2 } = s;
  const dx = p2.x - p1.x, dy = p2.y - p1.y;
  const len = Math.hypot(dx, dy) || 1;
  const nx = -dy / len, ny = dx / len;
  const pts = [];
  for (let i = 0; i < 30; i++) {
    const t = i / 29;
    const bx = p1.x + dx * t, by = p1.y + dy * t;
    const off = amp * Math.sin(2 * Math.PI * 3 * t + phase) * Math.sin(Math.PI * t);
    pts.push({ x: bx + nx * off, y: by + ny * off });
  }
  const [r, g, b] = s.color;
  ctx.save();
  ctx.lineCap = 'round';
  ctx.shadowColor = `rgb(${r},${g},${b})`; ctx.shadowBlur = 28;
  ctx.strokeStyle = `rgba(${r},${g},${b},0.9)`; ctx.lineWidth = 12;
  ctx.beginPath(); ctx.moveTo(pts[0].x, pts[0].y);
  for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
  ctx.stroke();
  ctx.shadowBlur = 0; ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(pts[0].x, pts[0].y);
  for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
  ctx.stroke();
  ctx.restore();
}

const HAND_CONNECTIONS = [
  [0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],
  [5,9],[9,10],[10,11],[11,12],[9,13],[13,14],[14,15],[15,16],
  [13,17],[17,18],[18,19],[19,20],[0,17],
];
function drawSkeleton(lms) {
  ctx.save();
  ctx.lineCap = 'round'; ctx.lineWidth = 3;
  ctx.strokeStyle = 'rgba(80,255,120,0.85)';
  ctx.shadowColor = 'rgba(80,255,120,0.6)'; ctx.shadowBlur = 8;
  for (const [a, b] of HAND_CONNECTIONS) {
    ctx.beginPath(); ctx.moveTo(lms[a].x, lms[a].y); ctx.lineTo(lms[b].x, lms[b].y); ctx.stroke();
  }
  ctx.shadowBlur = 0;
  ctx.fillStyle = 'rgba(255,80,80,0.95)';
  for (const p of lms) { ctx.beginPath(); ctx.arc(p.x, p.y, 4, 0, Math.PI*2); ctx.fill(); }
  ctx.restore();
}

const hands = new Hands({ locateFile: (f) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${f}` });
hands.setOptions({ maxNumHands: 2, minDetectionConfidence: 0.7, minTrackingConfidence: 0.6 });
hands.onResults(onResults);

let camera = null;
let running = false;
let prevTime = performance.now();
let fps = 0;

function setStatus(on, text) {
  statusDot.className = 'dot ' + (on ? 'on' : 'off');
  statusText.textContent = text;
}

function renderStringList() {
  if (strings.length === 0) {
    stringList.innerHTML = '<div class="empty-state">No strings yet — pinch both hands to draw one</div>';
  } else {
    stringList.innerHTML = '';
    strings.forEach((s) => {
      const row = document.createElement('div');
      row.className = 'string-row';
      const [r, g, b] = s.color;
      row.innerHTML = `
        <span class="swatch" style="background:rgb(${r},${g},${b});color:rgb(${r},${g},${b})"></span>
        <span class="sname">${NOTE_NAMES[s.noteIdx]}</span>
        <span class="slen">${Math.round(s.length)} px</span>`;
      stringList.appendChild(row);
    });
  }
  statActive.textContent = strings.length;
  statPlucks.textContent = pluckCount;
}

function onResults(res) {
  if (!running) return;
  const now = performance.now() / 1000;
  const dt = (performance.now() - prevTime) / 1000;
  prevTime = performance.now();
  if (dt > 0) fps = 0.9 * fps + 0.1 * (1 / dt);

  if (canvas.width !== res.image.width || canvas.height !== res.image.height) {
    canvas.width = res.image.width; canvas.height = res.image.height;
  }
  ctx.save();
  ctx.translate(canvas.width, 0); ctx.scale(-1, 1);
  ctx.drawImage(res.image, 0, 0, canvas.width, canvas.height);
  ctx.restore();

  const W = canvas.width, H = canvas.height;
  const lmsToPx = (lm) => ({ x: (W - lm.x * W), y: lm.y * H });

  const pinchPoints = [];
  const tipPoints = [];
  let handCount = 0;

  if (res.multiHandLandmarks) {
    for (let h = 0; h < res.multiHandLandmarks.length; h++) {
      handCount++;
      const raw = res.multiHandLandmarks[h];
      const lms = raw.map(lmsToPx);
      drawSkeleton(lms);
      const thumb = lms[4], index = lms[8];

      let sx, sy;
      if (h in smoothedTips) {
        sx = ALPHA * index.x + (1 - ALPHA) * smoothedTips[h].x;
        sy = ALPHA * index.y + (1 - ALPHA) * smoothedTips[h].y;
      } else { sx = index.x; sy = index.y; }
      smoothedTips[h] = { x: sx, y: sy };
      tipPoints.push({ x: sx, y: sy });

      if (dist(thumb, index) < 40) {
        pinchPoints.push({ x: (thumb.x + index.x)/2, y: (thumb.y + index.y)/2 });
      }
      ctx.fillStyle = 'rgba(255,80,80,1)';
      ctx.beginPath(); ctx.arc(thumb.x, thumb.y, 6, 0, Math.PI*2); ctx.fill();
      ctx.beginPath(); ctx.arc(index.x, index.y, 6, 0, Math.PI*2); ctx.fill();
    }
  }

  if (pinchPoints.length >= 2) {
    liveP1 = pinchPoints[0]; liveP2 = pinchPoints[1]; drawingActive = true;
    drawGlowLine(liveP1, liveP2, [0, 255, 255]);
  } else {
    if (drawingActive && liveP1 && liveP2) {
      const len = Math.hypot(liveP2.x - liveP1.x, liveP2.y - liveP1.y);
      if (len >= 80) {
        const color = STRING_COLORS[strings.length % STRING_COLORS.length];
        strings.push(new HarpString(liveP1, liveP2, color, 0));
        if (strings.length > 8) strings.shift();
        const order = strings.map((_, i) => i).sort((a, b) => strings[b].length - strings[a].length);
        order.forEach((si, slot) => {
          let notePos = Math.floor(slot * NOTE_NAMES.length / strings.length);
          if (notePos >= NOTE_NAMES.length) notePos = NOTE_NAMES.length - 1;
          strings[si].noteIdx = notePos;
          strings[si].color = STRING_COLORS[slot % STRING_COLORS.length];
        });
        renderStringList();
      }
    }
    drawingActive = false; liveP1 = null; liveP2 = null;
  }

  for (const s of strings) drawVibratingString(s, now);

  for (let h = 0; h < tipPoints.length; h++) {
    const tip = tipPoints[h];
    if (!(h in prevDists)) prevDists[h] = {};
    for (let sid = 0; sid < strings.length; sid++) {
      const s = strings[sid];
      const sd = signedDist(tip.x, tip.y, s.p1.x, s.p1.y, s.p2.x, s.p2.y);
      const prev = prevDists[h][sid];
      if (prev !== undefined) {
        const crossed = (prev * sd < 0) || (Math.abs(sd) < 12);
        const wasFar = Math.abs(prev) > 20;
        if (crossed && wasFar) {
          const n = s.pluck(now);
          if (n) { lastNote = n; pluckCount++; statPlucks.textContent = pluckCount; }
        }
      }
      prevDists[h][sid] = sd;
    }
  }
  for (const h of Object.keys(prevDists)) { if (Number(h) >= handCount) delete prevDists[h]; }

  fpsEl.textContent = fps.toFixed(1);
  nstrEl.textContent = strings.length;
  noteEl.textContent = lastNote;
}

function drawVisualizer() {
  const w = vizCanvas.width = vizCanvas.clientWidth;
  const h = vizCanvas.height = vizCanvas.clientHeight;
  vizCtx.clearRect(0, 0, w, h);

  if (!analyser) {
    vizCtx.strokeStyle = 'rgba(110,168,255,0.3)';
    vizCtx.lineWidth = 2;
    vizCtx.beginPath();
    for (let x = 0; x < w; x++) {
      const y = h/2 + Math.sin(x*0.03 + performance.now()*0.002) * 6;
      x === 0 ? vizCtx.moveTo(x, y) : vizCtx.lineTo(x, y);
    }
    vizCtx.stroke();
  } else {
    const data = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteTimeDomainData(data);
    const grad = vizCtx.createLinearGradient(0, 0, w, 0);
    grad.addColorStop(0, '#6ea8ff'); grad.addColorStop(0.5, '#b388ff'); grad.addColorStop(1, '#ff6ec7');
    vizCtx.strokeStyle = grad; vizCtx.lineWidth = 2.5;
    vizCtx.shadowColor = '#b388ff'; vizCtx.shadowBlur = 10;
    vizCtx.beginPath();
    const slice = w / data.length;
    for (let i = 0; i < data.length; i++) {
      const v = data[i] / 128.0;
      const y = (v * h) / 2;
      i === 0 ? vizCtx.moveTo(i*slice, y) : vizCtx.lineTo(i*slice, y);
    }
    vizCtx.stroke();
    vizCtx.shadowBlur = 0;
  }
  requestAnimationFrame(drawVisualizer);
}
drawVisualizer();

async function start() {
  ensureAudio();
  if (audioCtx.state === 'suspended') await audioCtx.resume();
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 }, audio: false });
    video.srcObject = stream;
    await video.play();
    startOverlay.classList.add('hidden');
    setStatus(true, 'Live');
    running = true;
    prevTime = performance.now();
    camera = new Camera(video, {
      onFrame: async () => { if (running) await hands.send({ image: video }); },
      width: 1280, height: 720,
    });
    camera.start();
  } catch (err) {
    console.error(err);
    setStatus(false, 'Camera denied');
    alert('Could not access camera. Please allow camera permission and retry.\n\n' + err.message);
  }
}

function stop() {
  running = false;
  if (camera) { try { camera.stop(); } catch (e) {} }
  if (video.srcObject) { video.srcObject.getTracks().forEach(t => t.stop()); video.srcObject = null; }
  setStatus(false, 'Stopped');
  startOverlay.classList.remove('hidden');
}

startBtn.addEventListener('click', start);
clearBtn.addEventListener('click', () => { strings = []; lastNote = '—'; renderStringList(); });
stopBtn.addEventListener('click', stop);

window.addEventListener('keydown', (e) => {
  if (e.key === 'c' || e.key === 'C') { strings = []; lastNote = '—'; renderStringList(); }
  else if (e.key === 'q' || e.key === 'Q' || e.key === 'Escape') { stop(); }
});

// Clickable keymap buttons.
document.getElementById('keyC').addEventListener('click', () => { strings = []; lastNote = '—'; renderStringList(); });
document.getElementById('keyQ').addEventListener('click', stop);
document.getElementById('keyEsc').addEventListener('click', stop);

document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const tab = btn.dataset.tab;
    if (tab === 'how') howModal.classList.add('open');
    else if (tab === 'about') aboutModal.classList.add('open');
  });
});
document.querySelectorAll('[data-close]').forEach(b => b.addEventListener('click', () => {
  document.querySelectorAll('.modal').forEach(m => m.classList.remove('open'));
  document.querySelector('.nav-btn[data-tab="play"]').click();
}));
document.querySelectorAll('.modal').forEach(m => m.addEventListener('click', (e) => {
  if (e.target === m) { m.classList.remove('open'); document.querySelector('.nav-btn[data-tab="play"]').click(); }
}));

setStatus(false, 'Ready');
renderStringList();