// Generates public/vo/NN.mp3 for every narration line.
// ElevenLabs when ELEVENLABS_API_KEY is set (env or demo/film/.env, never committed); otherwise macOS `say` (placeholder, labeled in the film).
import {execFileSync} from 'node:child_process';
import {existsSync, readFileSync, writeFileSync, mkdirSync} from 'node:fs';

const root = new URL('..', import.meta.url).pathname;
if (existsSync(root + '.env')) {
  for (const l of readFileSync(root + '.env', 'utf8').split('\n')) {
    const m = l.match(/^\s*([A-Z_]+)\s*=\s*(.*)\s*$/);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2];
  }
}
const key = process.env.ELEVENLABS_API_KEY;
const voice = process.env.ELEVENLABS_VOICE_ID || 'JBFqnCBsd6RMkjVDRZzb';
const only = process.argv.slice(2);
const {lines} = JSON.parse(readFileSync(root + 'src/narration.json', 'utf8'));
mkdirSync(root + 'public/vo', {recursive: true});

for (const l of lines) {
  if (only.length && !only.includes(l.id)) continue;
  const out = `${root}public/vo/${l.id}.mp3`;
  if (key) {
    const r = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voice}?output_format=mp3_44100_128`, {
      method: 'POST',
      headers: {'xi-api-key': key, 'content-type': 'application/json', accept: 'audio/mpeg'},
      body: JSON.stringify({text: l.text, model_id: process.env.ELEVENLABS_MODEL || 'eleven_multilingual_v2', voice_settings: {stability: 0.5, similarity_boost: 0.8, style: 0.25, use_speaker_boost: true}}),
    });
    if (!r.ok) throw new Error(`ElevenLabs ${l.id}: ${r.status} ${await r.text()}`);
    writeFileSync(out, Buffer.from(await r.arrayBuffer()));
  } else {
    const aiff = `${root}public/vo/${l.id}.aiff`;
    execFileSync('say', ['-v', process.env.SAY_VOICE || 'Samantha', '-r', process.env.SAY_RATE || '178', '-o', aiff, l.text]);
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', aiff, '-ar', '44100', '-ac', '2', '-b:a', '160k', out]);
  }
  console.log(l.id, key ? 'elevenlabs' : 'say');
}
writeFileSync(root + 'public/vo/source.txt', key ? 'elevenlabs' : 'say');
