#!/usr/bin/env node
/**
 * render_video.mjs — Zero-npm-dependency Three.js Deterministic Video Renderer (k12-lesson-studio v5.0)
 *
 * Drives assets/video_stage.html + assets/three.min.js + a subject scene JS deterministically frame-by-frame
 * via Chrome DevTools Protocol (WebGL + 2D HUD), synthesizes optional procedural WAV audio from scene audioCues,
 * encodes crisp offline H.264+AAC MP4 via ffmpeg, and optionally outputs a hero poster PNG + 4x4 16-frame contact sheet.
 */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import http from 'node:http';
import { spawn, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SKILL_ROOT = path.resolve(__dirname, '..');

function parseArgs(argv) {
  const opts = {
    scene: null,
    out: null,
    poster: null,
    posterSec: null,
    contactSheet: null,
    width: 0,
    height: 0,
    fps: 0,
    crf: 18,
  };
  for (let i = 2; i < argv.length; i++) {
    const k = argv[i];
    const v = argv[i + 1];
    if (k === '--scene') { opts.scene = path.resolve(v); i++; }
    else if (k === '--out') { opts.out = path.resolve(v); i++; }
    else if (k === '--poster') { opts.poster = path.resolve(v); i++; }
    else if (k === '--poster-sec') { opts.posterSec = Number(v); i++; }
    else if (k === '--contact-sheet') { opts.contactSheet = path.resolve(v); i++; }
    else if (k === '--width') { opts.width = Number(v); i++; }
    else if (k === '--height') { opts.height = Number(v); i++; }
    else if (k === '--fps') { opts.fps = Number(v); i++; }
    else if (k === '--crf') { opts.crf = Number(v); i++; }
  }
  if (!opts.scene || !opts.out) {
    console.error('Usage: node render_video.mjs --scene <scene.js> --out <out.mp4> [--poster <p.png>] [--poster-sec <sec>] [--contact-sheet <sheet.png>]');
    process.exit(2);
  }
  return opts;
}

function findBrowser() {
  const cands = [
    process.env.CHROME_PATH,
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/usr/bin/google-chrome',
    '/usr/bin/chromium',
  ].filter(Boolean);
  for (const p of cands) {
    if (fs.existsSync(p)) return p;
  }
  throw new Error('No Chrome/Edge binary found for WebGL video rendering.');
}

function findFfmpeg() {
  const probe = spawnSync('ffmpeg', ['-version'], { encoding: 'utf8' });
  if (probe.status === 0) return 'ffmpeg';
  throw new Error('ffmpeg not found in PATH.');
}

async function fetchJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let data = '';
      res.on('data', (c) => data += c);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); } catch (e) { reject(e); }
      });
    }).on('error', reject);
  });
}

async function waitForDevTools(port, timeoutMs = 15000) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeoutMs) {
    try {
      const list = await fetchJson(`http://127.0.0.1:${port}/json`);
      const page = list.find((t) => t.type === 'page' && t.webSocketDebuggerUrl);
      if (page) return page.webSocketDebuggerUrl;
    } catch (_) {}
    await new Promise((r) => setTimeout(r, 150));
  }
  throw new Error('Timed out waiting for Chrome DevTools endpoint.');
}

class CDPClient {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.id = 0;
    this.pending = new Map();
    this.ready = new Promise((resolve, reject) => {
      this.ws.addEventListener('open', resolve);
      this.ws.addEventListener('error', reject);
    });
    this.ws.addEventListener('message', (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        if (msg.error) reject(new Error(msg.error.message || JSON.stringify(msg.error)));
        else resolve(msg.result);
      }
    });
  }
  async send(method, params = {}) {
    await this.ready;
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
  async evalJson(expression) {
    const res = await this.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (res.exceptionDetails) {
      const desc = res.exceptionDetails.exception?.description || res.exceptionDetails.text;
      throw new Error('Page JS error: ' + desc);
    }
    return res.result?.value;
  }
  close() {
    try { this.ws.close(); } catch (_) {}
  }
}

/** Synthesize crisp procedural WAV (44.1 kHz, 16-bit mono) from scene audioCues. */
function synthesizeWav(durationSec, cues, wavPath) {
  const sr = 44100;
  const totalSamples = Math.ceil((durationSec + 0.25) * sr);
  const buf = new Float32Array(totalSamples);

  // Deterministic PRNG for clean repeatable sand/water noise
  let seed = 135792468;
  const rand = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return (seed / 4294967296) * 2 - 1;
  };

  for (const cue of cues || []) {
    if (cue.type === 'pour' || cue.type === 'water') {
      const i0 = Math.max(0, Math.floor((cue.start || 0) * sr));
      const i1 = Math.min(totalSamples, Math.floor((cue.end || 0) * sr));
      const len = Math.max(1, i1 - i0);
      const gain = cue.gain ?? (cue.type === 'pour' ? 0.19 : 0.16);
      const pitch = cue.pitch ?? 1.0;
      let lp1 = 0, lp2 = 0, hp = 0, prevIn = 0;
      const alphaLP = cue.type === 'pour' ? Math.min(0.45, 0.24 * pitch) : 0.14;
      const alphaHP = cue.type === 'pour' ? 0.86 : 0.92;
      for (let i = i0; i < i1; i++) {
        const u = (i - i0) / len;
        const env = Math.min(1, u / 0.08) * Math.min(1, (1 - u) / 0.12);
        const n = rand();
        // Bandpass granular sand shimmer
        hp = alphaHP * (hp + n - prevIn);
        prevIn = n;
        lp1 += alphaLP * (hp - lp1);
        lp2 += (alphaLP * 0.7) * (lp1 - lp2);
        const grain = cue.type === 'pour'
          ? (0.72 + 0.28 * Math.sin(2 * Math.PI * (26 * pitch) * (i / sr)) + (Math.abs(n) > 0.92 ? 0.45 * n : 0))
          : (0.7 + 0.3 * Math.sin(2 * Math.PI * 14 * (i / sr)));
        buf[i] += lp2 * env * gain * grain;
      }
    } else if (cue.type === 'chime') {
      const i0 = Math.max(0, Math.floor((cue.at || 0) * sr));
      const dur = cue.duration ?? 0.95;
      const i1 = Math.min(totalSamples, i0 + Math.floor(dur * sr));
      const freq = cue.freq ?? 523.25;
      const gain = cue.gain ?? 0.24;
      for (let i = i0; i < i1; i++) {
        const dt = (i - i0) / sr;
        const env = Math.min(1, dt / 0.008) * Math.exp(-dt * 4.2);
        const sig =
          0.65 * Math.sin(2 * Math.PI * freq * dt) +
          0.25 * Math.sin(2 * Math.PI * freq * 2.0 * dt) * Math.exp(-dt * 3.0) +
          0.10 * Math.sin(2 * Math.PI * freq * 3.01 * dt) * Math.exp(-dt * 6.0);
        buf[i] += sig * env * gain;
      }
    } else if (cue.type === 'whoosh') {
      const i0 = Math.max(0, Math.floor((cue.at || 0) * sr));
      const dur = cue.duration ?? 0.45;
      const i1 = Math.min(totalSamples, i0 + Math.floor(dur * sr));
      const gain = cue.gain ?? 0.14;
      let lp = 0;
      for (let i = i0; i < i1; i++) {
        const u = (i - i0) / Math.max(1, i1 - i0);
        const env = Math.sin(Math.PI * u);
        const alpha = 0.04 + 0.16 * env;
        lp += alpha * (rand() - lp);
        buf[i] += lp * env * gain;
      }
    } else if (cue.type === 'fanfare') {
      const baseAt = cue.at || 0;
      const freqs = cue.freqs || [523.25, 659.25, 783.99, 1046.5];
      for (let k = 0; k < freqs.length; k++) {
        const i0 = Math.max(0, Math.floor((baseAt + k * 0.085) * sr));
        const i1 = Math.min(totalSamples, i0 + Math.floor(1.35 * sr));
        for (let i = i0; i < i1; i++) {
          const dt = (i - i0) / sr;
          const env = Math.min(1, dt / 0.01) * Math.exp(-dt * 2.8);
          const sig = 0.72 * Math.sin(2 * Math.PI * freqs[k] * dt) + 0.22 * Math.sin(2 * Math.PI * freqs[k] * 2 * dt);
          buf[i] += sig * env * 0.14;
        }
      }
    }
  }

  // Write 16-bit PCM WAV
  const dataBytes = totalSamples * 2;
  const wav = Buffer.alloc(44 + dataBytes);
  wav.write('RIFF', 0);
  wav.writeUInt32LE(36 + dataBytes, 4);
  wav.write('WAVE', 8);
  wav.write('fmt ', 12);
  wav.writeUInt32LE(16, 16);
  wav.writeUInt16LE(1, 20);
  wav.writeUInt16LE(1, 22);
  wav.writeUInt32LE(sr, 24);
  wav.writeUInt32LE(sr * 2, 28);
  wav.writeUInt16LE(2, 32);
  wav.writeUInt16LE(16, 34);
  wav.write('data', 36);
  wav.writeUInt32LE(dataBytes, 40);
  for (let i = 0; i < totalSamples; i++) {
    const s = Math.max(-0.98, Math.min(0.98, buf[i]));
    wav.writeInt16LE(Math.round(s * 32767), 44 + i * 2);
  }
  fs.writeFileSync(wavPath, wav);
}

async function main() {
  const tStart = Date.now();
  const opts = parseArgs(process.argv);
  const browserPath = findBrowser();
  const ffmpegBin = findFfmpeg();

  const stageHtmlPath = path.join(SKILL_ROOT, 'assets', 'video_stage.html');
  const threeJsPath = path.join(SKILL_ROOT, 'assets', 'three.min.js');
  if (!fs.existsSync(stageHtmlPath) || !fs.existsSync(threeJsPath)) {
    throw new Error('Missing Skill assets: video_stage.html or three.min.js');
  }
  if (!fs.existsSync(opts.scene)) {
    throw new Error('Scene script not found: ' + opts.scene);
  }

  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'k12vid_'));
  const userDataDir = path.join(tmpDir, 'profile');
  fs.mkdirSync(userDataDir, { recursive: true });
  fs.copyFileSync(threeJsPath, path.join(tmpDir, 'three.min.js'));
  const sceneCode = fs.readFileSync(opts.scene, 'utf8');
  const stageTpl = fs.readFileSync(stageHtmlPath, 'utf8');
  const composedHtml = stageTpl.replace('<!-- SCENE_SCRIPT_SLOT -->', `<script>\n${sceneCode}\n</script>`);
  const stageFile = path.join(tmpDir, 'stage.html');
  fs.writeFileSync(stageFile, composedHtml, 'utf8');

  const port = 9300 + Math.floor(Math.random() * 500);
  const chromeArgs = [
    '--headless=new',
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${userDataDir}`,
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-background-networking',
    '--enable-webgl',
    '--ignore-gpu-blocklist',
    '--use-gl=angle',
    '--use-angle=swiftshader-webgl',
    '--enable-unsafe-swiftshader',
    '--hide-scrollbars',
    '--mute-audio',
    '--window-size=1280,720',
    'about:blank',
  ];
  const chrome = spawn(browserPath, chromeArgs, { stdio: ['ignore', 'ignore', 'pipe'] });
  let chromeStderr = '';
  chrome.stderr.on('data', (d) => { chromeStderr += d.toString(); });

  let cdp = null;
  try {
    const wsUrl = await waitForDevTools(port, 15000);
    cdp = new CDPClient(wsUrl);
    await cdp.send('Page.enable');
    await cdp.send('Runtime.enable');

    const fileUrl = 'file:///' + stageFile.replace(/\\/g, '/');
    await cdp.send('Page.navigate', { url: fileUrl });
    // Wait until __initVideoStage is defined
    for (let i = 0; i < 60; i++) {
      const ready = await cdp.evalJson('typeof window.__initVideoStage === "function" && typeof window.THREE === "object"');
      if (ready) break;
      await new Promise((r) => setTimeout(r, 100));
    }

    const meta = await cdp.evalJson(`window.__initVideoStage(${opts.width || 0}, ${opts.height || 0}, ${opts.fps || 0})`);
    await cdp.send('Emulation.setDeviceMetricsOverride', {
      width: meta.width,
      height: meta.height,
      deviceScaleFactor: 1,
      mobile: false,
    });

    // Synthesize procedural WAV if audioCues provided
    const hasAudio = Array.isArray(meta.audioCues) && meta.audioCues.length > 0;
    const wavPath = path.join(tmpDir, 'audio.wav');
    if (hasAudio) {
      synthesizeWav(meta.duration, meta.audioCues, wavPath);
    }

    fs.mkdirSync(path.dirname(opts.out), { recursive: true });
    const ffArgs = [
      '-y',
      '-f', 'image2pipe',
      '-vcodec', 'mjpeg',
      '-framerate', String(meta.fps),
      '-i', 'pipe:0',
    ];
    if (hasAudio) {
      ffArgs.push('-i', wavPath, '-c:a', 'aac', '-b:a', '128k', '-shortest');
    }
    ffArgs.push(
      '-c:v', 'libx264',
      '-profile:v', 'main',
      '-pix_fmt', 'yuv420p',
      '-crf', String(opts.crf),
      '-preset', 'medium',
      '-movflags', '+faststart',
      opts.out
    );

    const ff = spawn(ffmpegBin, ffArgs, { stdio: ['pipe', 'ignore', 'pipe'] });
    let ffErr = '';
    ff.stderr.on('data', (d) => { ffErr += d.toString(); });
    const ffDone = new Promise((resolve, reject) => {
      ff.on('close', (code) => code === 0 ? resolve() : reject(new Error(`ffmpeg exited ${code}: ${ffErr.slice(-400)}`)));
    });

    const posterFrameIdx = opts.poster
      ? Math.min(meta.totalFrames - 1, Math.max(0, Math.round((opts.posterSec ?? meta.duration * 0.66) * meta.fps)))
      : -1;

    for (let f = 0; f < meta.totalFrames; f++) {
      await cdp.evalJson(`window.__renderVideoFrame(${f})`);
      const shot = await cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: 94 });
      const jpegBuf = Buffer.from(shot.data, 'base64');
      if (!ff.stdin.write(jpegBuf)) {
        await new Promise((r) => ff.stdin.once('drain', r));
      }
      if (f === posterFrameIdx) {
        const pngShot = await cdp.send('Page.captureScreenshot', { format: 'png' });
        fs.mkdirSync(path.dirname(opts.poster), { recursive: true });
        fs.writeFileSync(opts.poster, Buffer.from(pngShot.data, 'base64'));
      }
    }
    ff.stdin.end();
    await ffDone;

    // Optional 4x4 16-frame visual inspection contact sheet
    if (opts.contactSheet) {
      fs.mkdirSync(path.dirname(opts.contactSheet), { recursive: true });
      const step = Math.max(1, Math.floor(meta.totalFrames / 16));
      const vf = `select='not(mod(n\\,${step}))',scale=360:202,tile=4x4:padding=4:color=0x0b1a20`;
      const cs = spawnSync(ffmpegBin, ['-y', '-i', opts.out, '-vf', vf, '-frames:v', '1', opts.contactSheet], { encoding: 'utf8' });
      if (cs.status !== 0) {
        console.error('Contact sheet warning:', cs.stderr.slice(-300));
      }
    }

    const outBytes = fs.statSync(opts.out).size;
    console.log(JSON.stringify({
      passed: true,
      out: opts.out,
      bytes: outBytes,
      width: meta.width,
      height: meta.height,
      fps: meta.fps,
      duration_sec: meta.duration,
      frames: meta.totalFrames,
      has_audio: hasAudio,
      poster: opts.poster || null,
      contact_sheet: opts.contactSheet || null,
      elapsed_sec: Number(((Date.now() - tStart) / 1000).toFixed(2)),
    }, null, 2));
  } finally {
    if (cdp) cdp.close();
    try { chrome.kill(); } catch (_) {}
    await new Promise((r) => setTimeout(r, 250));
    try { fs.rmSync(tmpDir, { recursive: true, force: true }); } catch (_) {}
  }
}

main().catch((err) => {
  console.error('RENDER_VIDEO_ERROR:', err.message);
  process.exit(1);
});
