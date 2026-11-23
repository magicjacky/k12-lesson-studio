#!/usr/bin/env node
/**
 * audit_html.mjs — K12 Interactive Big-Screen HTML Automated Verifier (k12-lesson-studio v4.0)
 * Zero external dependencies (uses Node built-ins + local Chrome/Edge CDP).
 *
 * Usage:
 *   node audit_html.mjs <path/to/lab.html> [out_screenshots_dir]
 *
 * Checks:
 *   1. Zero external http(s):// runtime URLs (allows only w3.org SVG namespace).
 *   2. Inline <script> syntax validation via vm.Script.
 *   3. 1280x720 zero horizontal/vertical overflow across all modes.
 *   4. Interactive click tests: all film tabs, embedded <video> readiness, Mode 2 options,
 *      dynamic <dialog> open + top-right close (.xBtn) + footer [data-close], +1 scoring, award modal.
 *   5. Captures keyframe PNGs of every film (t=0.05, 0.50, 0.96) + Mode 2 + modals for visual inspection.
 */
import { spawn } from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';
import vm from 'vm';
import { pathToFileURL } from 'url';

const htmlArg = process.argv[2];
if (!htmlArg) {
  console.error('Usage: node audit_html.mjs <path/to/lab.html> [out_screenshots_dir]');
  process.exit(2);
}
const HTML_PATH = path.resolve(htmlArg);
const OUT_DIR = path.resolve(process.argv[3] || path.join(path.dirname(HTML_PATH), '.audit_shots'));
fs.mkdirSync(OUT_DIR, { recursive: true });

function findBrowser() {
  const candidates = [
    process.env.CHROME_PATH,
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/usr/bin/google-chrome',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
  ].filter(Boolean);
  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }
  throw new Error('No Chrome/Edge binary found; set CHROME_PATH env var.');
}

const raw = fs.readFileSync(HTML_PATH, 'utf8');
const allUrls = raw.match(/https?:\/\/[^\s'"<>)]+/g) || [];
const externalUrls = allUrls.filter(u => !/^https?:\/\/www\.w3\.org\//.test(u));

// Syntax check all inline <script> blocks
const scriptRe = /<script\b[^>]*>([\s\S]*?)<\/script>/gi;
let scriptCount = 0;
let syntaxError = null;
let m;
while ((m = scriptRe.exec(raw)) !== null) {
  const code = m[1];
  if (!code.trim()) continue;
  scriptCount++;
  try {
    new vm.Script(code, { filename: `${path.basename(HTML_PATH)}#script${scriptCount}` });
  } catch (e) {
    syntaxError = String(e);
    break;
  }
}

const BROWSER = findBrowser();
const PORT = 9400 + Math.floor(Math.random() * 400);
const USER_DIR = path.join(os.tmpdir(), 'k12-audit-' + process.pid + '-' + Date.now());
const sleep = ms => new Promise(r => setTimeout(r, ms));

const proc = spawn(BROWSER, [
  '--headless=new',
  '--remote-debugging-port=' + PORT,
  '--user-data-dir=' + USER_DIR,
  '--window-size=1280,720',
  '--hide-scrollbars',
  '--no-first-run',
  '--disable-gpu',
  pathToFileURL(HTML_PATH).href,
]);

(async () => {
  const report = {
    file: HTML_PATH,
    size_bytes: fs.statSync(HTML_PATH).size,
    external_urls: externalUrls,
    inline_scripts: scriptCount,
    syntax_error: syntaxError,
    dims: {},
    films_checked: [],
    video_checks: [],
    modal_checks: {},
    errors: [],
    screenshots_dir: OUT_DIR,
    screenshots: [],
    passed: false,
  };

  if (syntaxError) {
    console.log(JSON.stringify(report, null, 2));
    proc.kill();
    process.exit(1);
  }

  let page = null;
  for (let i = 0; i < 45; i++) {
    try {
      const list = await (await fetch('http://127.0.0.1:' + PORT + '/json')).json();
      page = list.find(t => t.type === 'page' && t.url.startsWith('file:'));
      if (page) break;
    } catch (_) {}
    await sleep(250);
  }
  if (!page) throw new Error('Headless browser CDP endpoint did not become ready');

  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let seq = 0;
  const pending = new Map();
  const send = (method, params) =>
    new Promise((res, rej) => {
      const id = ++seq;
      pending.set(id, { res, rej });
      ws.send(JSON.stringify({ id, method, params: params || {} }));
    });

  ws.onmessage = ev => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      const p = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? p.rej(new Error(JSON.stringify(msg.error))) : p.res(msg.result);
    } else if (msg.method === 'Runtime.exceptionThrown') {
      report.errors.push('EXC: ' + (msg.params.exceptionDetails.text || 'Runtime exception'));
    } else if (msg.method === 'Log.entryAdded' && msg.params.entry.level === 'error') {
      report.errors.push('LOG: ' + msg.params.entry.text);
    } else if (msg.method === 'Runtime.consoleAPICalled' && msg.params.type === 'error') {
      report.errors.push('CONSOLE: ' + JSON.stringify(msg.params.args));
    }
  };
  await new Promise(r => (ws.onopen = r));
  await send('Runtime.enable');
  await send('Log.enable');
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 720, deviceScaleFactor: 1, mobile: false });
  await sleep(750);

  const ev = async expr => {
    const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));
    return r.result.value;
  };
  const shot = async name => {
    const r = await send('Page.captureScreenshot', { format: 'png' });
    const fp = path.join(OUT_DIR, name + '.png');
    fs.writeFileSync(fp, Buffer.from(r.data, 'base64'));
    report.screenshots.push(name + '.png');
  };

  report.dims.mode1 = await ev('({sw:document.documentElement.scrollWidth,sh:document.documentElement.scrollHeight})');

  // Inspect all film pills & capture key states
  const filmCount = await ev('document.querySelectorAll(".filmPill").length');
  const hasSeek = await ev('typeof switchFilm === "function" && typeof seek === "function"');
  for (let i = 0; i < filmCount; i++) {
    const label = await ev(`document.querySelectorAll(".filmPill")[${i}].textContent.trim()`);
    const isVid = await ev(`typeof FILMS !== "undefined" && !!(FILMS[${i}] && FILMS[${i}].isVideo)`);
    if (hasSeek) {
      await ev(`switchFilm(${i}, false)`);
      await sleep(300);
      if (isVid) {
        const vidInfo = await ev(`(()=>{
          const v = document.querySelector("video");
          return v ? {rs:v.readyState,dur:Number((v.duration||0).toFixed(2)),vw:v.videoWidth,vh:v.videoHeight} : null;
        })()`);
        report.video_checks.push({ film: i, label, ...vidInfo });
        await ev(`(()=>{const v=document.querySelector("video"); if(v && v.duration) v.currentTime = v.duration*0.52;})()`);
        await sleep(350);
        await shot(`film${i + 1}_video`);
      } else {
        for (const [tag, p] of [['start', 0.05], ['mid', 0.50], ['end', 0.96]]) {
          await ev(`seek(${p})`);
          await sleep(240);
          await shot(`film${i + 1}_${tag}`);
        }
        // Extra check: if film 2 has density chips (e.g. 32), capture assembled 32-slice too
        const has32 = await ev('!!document.querySelector(".chip[data-d=\\"32\\"]")');
        if (has32) {
          await ev('document.querySelector(".chip[data-d=\\"32\\"]").click(); seek(0.96);');
          await sleep(240);
          await shot(`film${i + 1}_end_32`);
        }
        // Extra check: if film 3 has short counterexample & video jump button, test both!
        const hasShort = await ev('!!document.querySelector(".scn[data-s=\\"short\\"]")');
        if (hasShort) {
          await ev('document.querySelector(".scn[data-s=\\"short\\"]").click(); seek(0.95);');
          await sleep(280);
          await shot(`film${i + 1}_short`);
          await ev('document.querySelector(".scn[data-s=\\"equal\\"]").click(); seek(0.25);');
          await sleep(260);
          await shot(`film${i + 1}_pour`);
        }
      }
    } else {
      await ev(`document.querySelectorAll(".filmPill")[${i}].click()`);
      await sleep(400);
      await shot(`film${i + 1}`);
    }
    report.films_checked.push({ index: i, label, isVideo: isVid });
  }

  // Verify Mode 2 PK Arena & all modal open/close buttons
  const hasSeg2 = await ev('!!document.querySelector("#seg2, [data-mode=\\"pk\\"]")');
  if (hasSeg2) {
    await ev('document.querySelector("#seg2, [data-mode=\\"pk\\"]").click()');
    await sleep(300);
    report.dims.mode2 = await ev('({sw:document.documentElement.scrollWidth,sh:document.documentElement.scrollHeight})');

    const hasOpt = await ev('!!document.querySelector(".qOpt")');
    if (hasOpt) await ev('document.querySelector(".qOpt").click()');
    await sleep(150);

    const hasExp = await ev('!!document.querySelector("#qExp")');
    if (hasExp) {
      await ev('document.querySelector("#qExp").click()');
      await sleep(220);
      const open1 = await ev('!!document.querySelector("#expDlg[open]")');
      await shot('modal_exp');
      await ev('document.querySelector("#expDlg .xBtn").click()');
      await sleep(200);
      const closedX = await ev('!document.querySelector("#expDlg[open]")');

      await ev('document.querySelector("#qExp").click()');
      await sleep(220);
      await ev('document.querySelector("#expDlg .dlgFoot [data-close]").click()');
      await sleep(200);
      const closedFoot = await ev('!document.querySelector("#expDlg[open]")');
      report.modal_checks.exp = { open1, closedX, closedFoot };
    }

    const hasPlus = await ev('!!document.querySelector(".plusPad")');
    if (hasPlus) {
      await ev('document.querySelectorAll(".plusPad")[0].click(); document.querySelectorAll(".plusPad")[3].click();');
      await sleep(950);
    }
    await shot('mode2_pk');

    const hasAward = await ev('!!document.querySelector("#qAward")');
    if (hasAward) {
      await ev('document.querySelector("#qAward").click()');
      await sleep(320);
      const awOpen = await ev('!!document.querySelector("#awardDlg[open]")');
      await shot('modal_award');
      await ev('document.querySelector("#awardDlg [data-close]").click()');
      await sleep(200);
      const awClosed = await ev('!document.querySelector("#awardDlg[open]")');
      report.modal_checks.award = { awOpen, awClosed };
    }
  }

  const dimsOk = Object.values(report.dims).every(d => d.sw <= 1280 && d.sh <= 720);
  const videosOk = report.video_checks.every(v => v.rs >= 3 && v.vw > 0 && v.dur > 0);
  const modalsOk =
    (!report.modal_checks.exp || (report.modal_checks.exp.open1 && report.modal_checks.exp.closedX && report.modal_checks.exp.closedFoot)) &&
    (!report.modal_checks.award || (report.modal_checks.award.awOpen && report.modal_checks.award.awClosed));

  // Build a single 4x4 labeled contact sheet inside browser canvas (zero extra deps, 1-shot ViewImage audit!)
  try {
    const tiles = report.screenshots.slice(0, 16).map(name => ({
      name,
      dataUrl: 'data:image/png;base64,' + fs.readFileSync(path.join(OUT_DIR, name)).toString('base64'),
    }));
    const sheetB64 = await ev(`(async () => {
      const tiles = ${JSON.stringify(tiles)};
      const cols = 4, rows = Math.ceil(tiles.length / cols), tw = 480, th = 270;
      const cv = document.createElement('canvas');
      cv.width = cols * tw; cv.height = rows * th;
      const g = cv.getContext('2d');
      g.fillStyle = '#071118'; g.fillRect(0, 0, cv.width, cv.height);
      for (let i = 0; i < tiles.length; i++) {
        const img = new Image();
        await new Promise((res, rej) => { img.onload = res; img.onerror = rej; img.src = tiles[i].dataUrl; });
        const r = Math.floor(i / cols), c = i % cols;
        g.drawImage(img, c * tw, r * th, tw, th);
        g.fillStyle = 'rgba(6,14,20,0.82)'; g.fillRect(c * tw + 6, r * th + 6, 170, 22);
        g.fillStyle = '#F7E2B8'; g.font = 'bold 13px Consolas, monospace';
        g.fillText(tiles[i].name, c * tw + 12, r * th + 22);
      }
      return cv.toDataURL('image/png').split(',')[1];
    })()`);
    const sheetPath = path.join(OUT_DIR, 'audit_contact_sheet.png');
    fs.writeFileSync(sheetPath, Buffer.from(sheetB64, 'base64'));
    report.contact_sheet = sheetPath;
  } catch (e) {
    report.contact_sheet_error = String(e);
  }

  report.passed =
    externalUrls.length === 0 &&
    !syntaxError &&
    dimsOk &&
    videosOk &&
    modalsOk &&
    report.errors.length === 0;

  console.log(JSON.stringify(report, null, 2));
  ws.close();
  proc.kill();
  try { fs.rmSync(USER_DIR, { recursive: true, force: true }); } catch (_) {}
  process.exit(report.passed ? 0 : 1);
})().catch(err => {
  console.error('AUDIT_FAIL:', err);
  proc.kill();
  try { fs.rmSync(USER_DIR, { recursive: true, force: true }); } catch (_) {}
  process.exit(1);
});
