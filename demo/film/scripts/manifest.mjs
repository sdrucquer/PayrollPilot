// Scans public/ and writes src/generated/manifest.json (durations in seconds). Run before every render.
import {execFileSync} from 'node:child_process';
import {existsSync, readdirSync, readFileSync, writeFileSync} from 'node:fs';
const root = new URL('..', import.meta.url).pathname;
const dur = (p) => Number(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]).toString().trim());
const vo = {};
for (const f of readdirSync(root + 'public/vo')) if (f.endsWith('.mp3')) vo[f.replace('.mp3', '')] = +dur(root + 'public/vo/' + f).toFixed(2);
const footage = {};
for (const f of readdirSync(root + 'public/footage')) if (/\.(mov|mp4|webm)$/i.test(f)) footage[f] = +dur(root + 'public/footage/' + f).toFixed(2);
const music = existsSync(root + 'public/music/bed.wav') ? 'music/bed.wav' : null;
const voSource = existsSync(root + 'public/vo/source.txt') ? readFileSync(root + 'public/vo/source.txt', 'utf8').trim() : 'none';
writeFileSync(root + 'src/generated/manifest.json', JSON.stringify({vo, footage, music, voSource}, null, 1) + '\n');

// Timing check: each VO line must end before the next line starts.
const {lines} = JSON.parse(readFileSync(root + 'src/narration.json', 'utf8'));
let ok = true;
lines.forEach((l, i) => {
  const next = lines[i + 1]?.start ?? 175;
  const end = l.start + (vo[l.id] ?? 0);
  const slack = next - end;
  if (slack < 0.25) ok = false;
  console.log(`${l.id} start ${l.start.toFixed(1)} dur ${(vo[l.id] ?? 0).toFixed(1)} end ${end.toFixed(1)} next ${next.toFixed(1)} slack ${slack.toFixed(1)}${slack < 0.25 ? '  <-- OVERLAP' : ''}`);
});
console.log('footage:', Object.keys(footage).length ? footage : 'none', '| voice:', voSource, '| music:', music);
if (!ok) process.exitCode = 2;
