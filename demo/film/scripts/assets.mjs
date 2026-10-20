// Collects clips, mockups and voice lines into public/a and writes src/generated/demo.json
// (per-segment timing driven by voice length, clip durations, redacted text clips).
// Run from demo/film: node scripts/assets.mjs
import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const REPO = path.resolve(ROOT, '../..');
const PUB = path.join(ROOT, 'public');
const A = path.join(PUB, 'a');
const CLIPS = path.join(ROOT, 'clips');
fs.mkdirSync(path.join(A, 'clips'), {recursive: true});
fs.mkdirSync(path.join(ROOT, 'src', 'generated'), {recursive: true});

const probe = (f) => {
  try {
    const j = JSON.parse(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration:stream=width,height', '-of', 'json', f]).toString());
    const st = (j.streams || []).find((s) => s.width) || {};
    return {dur: parseFloat(j.format?.duration) || 0, w: st.width || 0, h: st.height || 0};
  } catch {
    return {dur: 0, w: 0, h: 0};
  }
};

// No phone numbers, real names, keys or env values on screen.
const redact = (t) =>
  t
    .replace(/\+?1?[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b/g, '•••-•••-••••')
    .replace(/\b(sk|pk|rk)[-_][A-Za-z0-9_-]{8,}/g, '[redacted]')
    .replace(/\b[A-Z][A-Z0-9_]*(KEY|SECRET|TOKEN|PASSWORD)\s*=\s*\S+/g, '$1=[redacted]')
    .replace(/Shanin\s+Drucquer|Shanin|Drucquer/gi, 'Owner')
    .replace(/sdrucquer/gi, 'owner')
    .replace(/any;-;\S+/g, 'any;-;•••');

// Mockups of the frozen new UI (design/*.html), rendered once.
const CHROME = '/opt/pw-browsers/chromium';
for (const name of ['home', 'ready', 'idle']) {
  const out = path.join(A, `mock-${name}.png`);
  if (!fs.existsSync(out) && fs.existsSync(CHROME)) {
    execFileSync(CHROME, ['--headless=new', '--no-sandbox', '--hide-scrollbars', '--force-device-scale-factor=2', '--window-size=1280,1500', '--virtual-time-budget=4000', `--screenshot=${out}`, `file://${REPO}/design/${name}.html`], {stdio: 'ignore'});
  }
}

const files = {};
for (const f of fs.readdirSync(A)) if (/\.(png|jpe?g)$/i.test(f)) files[f] = {kind: 'image', ...probe(path.join(A, f))};

const clips = {};
if (fs.existsSync(CLIPS)) {
  for (const f of fs.readdirSync(CLIPS).sort()) {
    const src = path.join(CLIPS, f);
    if (/\.txt$/i.test(f)) {
      clips[f] = {kind: 'text', text: redact(fs.readFileSync(src, 'utf8')).slice(0, 6000)};
    } else if (/\.(mp4|mov|m4v|webm|png|jpe?g)$/i.test(f)) {
      fs.copyFileSync(src, path.join(A, 'clips', f));
      clips[f] = {kind: /\.(png|jpe?g)$/i.test(f) ? 'image' : 'video', ...probe(src)};
    }
  }
}

// Voice: owner recording wins per line, else Kokoro placeholder.
const lines = fs
  .readFileSync(path.join(ROOT, 'narration.txt'), 'utf8')
  .split('\n')
  .filter((l) => l.trim() && !l.startsWith('#'))
  .map((l) => {
    const [id, , text] = l.split('|').map((p) => p.trim());
    return {id, text};
  });
const vo = {};
for (const {id} of lines) {
  for (const [dir, source] of [['owner', 'owner'], ['kokoro', 'kokoro']]) {
    const hit = ['m4a', 'wav', 'mp3'].map((e) => path.join(PUB, 'vo', dir, `${id}.${e}`)).find((p) => fs.existsSync(p));
    if (hit) {
      vo[id] = {file: path.relative(PUB, hit), dur: probe(hit).dur, source};
      break;
    }
  }
}

// Minimum seconds per segment; voice + pad stretches it. `needs` drops a segment when its clip is absent.
const PLAN = [
  {id: '01', min: 13}, {id: '02', min: 8}, {id: '03', min: 8}, {id: '04', min: 10},
  {id: '05', min: 9}, {id: '06', min: 9}, {id: '07', min: 8}, {id: '08', min: 8}, {id: '09', min: 5},
  {id: '10', min: 10}, {id: '11', min: 8}, {id: '12', min: 9}, {id: '13', min: 12},
  {id: '14', min: 6, needs: '13-band-dev-team.png'}, {id: '15', min: 17}, {id: '16', min: 11}, {id: '17', min: 10},
];
const LEAD = {'01': 0.4, '02': 1.6};
let t = 0;
const timeline = [];
for (const p of PLAN) {
  if (p.needs && !clips[p.needs]) continue;
  const lead = LEAD[p.id] ?? 0.5;
  const v = vo[p.id]?.dur ?? 0;
  const dur = Math.max(p.min, lead + v + 0.8);
  timeline.push({id: p.id, from: +t.toFixed(3), dur: +dur.toFixed(3), voAt: lead, text: lines.find((l) => l.id === p.id)?.text ?? ''});
  t += dur;
}
const out = {total: +t.toFixed(3), timeline, vo, files, clips, voSource: [...new Set(Object.values(vo).map((v) => v.source))].join('+') || 'none'};
fs.writeFileSync(path.join(ROOT, 'src', 'generated', 'demo.json'), JSON.stringify(out, null, 2));
const mmss = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
for (const s of timeline) console.log(`${s.id} ${mmss(s.from)}-${mmss(s.from + s.dur)} vo=${(vo[s.id]?.dur ?? 0).toFixed(1)}s ${vo[s.id]?.source ?? 'none'}`);
console.log(`total ${mmss(t)} (${t.toFixed(1)} s) · clips: ${Object.keys(clips).join(', ') || 'none'}`);
