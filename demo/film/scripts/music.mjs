// Synthesizes public/music/bed.wav (175 s, 44.1 kHz stereo): drone build, montage ticks, riser,
// logo hit, a soft pulsing pad under the product section, and a resolve. Original, no samples, no licensing.
import {writeFileSync, mkdirSync} from 'node:fs';
const root = new URL('..', import.meta.url).pathname;
const SR = 44100, DUR = 175, N = SR * DUR;
const L = new Float32Array(N), R = new Float32Array(N);
const TAU = Math.PI * 2;
const hz = (n) => 440 * Math.pow(2, (n - 69) / 12); // midi -> Hz
const env = (t, a, d) => (t < 0 ? 0 : t < a ? t / a : Math.exp(-(t - a) / d));
const ramp = (t, t0, t1) => Math.max(0, Math.min(1, (t - t0) / (t1 - t0)));
const add = (i, v, pan = 0) => { L[i] += v * (1 - pan) ; R[i] += v * (1 + pan); };

// 1) Drone 3 -> 23.7 s (A1/A2/E3 with slow beating), cut to silence for a breath before the hit.
for (let i = SR * 3; i < SR * 23.7; i++) {
  const t = i / SR;
  const a = 0.16 * Math.pow(ramp(t, 3, 23), 1.6) * (1 - ramp(t, 23.55, 23.7));
  const v = Math.sin(TAU * 55 * t) * 0.9 + Math.sin(TAU * 110.4 * t) * 0.6 + Math.sin(TAU * 164.6 * t) * 0.35 + Math.sin(TAU * 220.7 * t) * 0.15 * ramp(t, 12, 22);
  add(i, a * v * (0.85 + 0.15 * Math.sin(TAU * 0.25 * t)), 0.1 * Math.sin(TAU * 0.07 * t));
}
// 2) Montage ticks: one per fragment (every 1.2 s from 3.2 s), short filtered click.
for (let k = 0; k < 9; k++) {
  const t0 = 3.2 + k * 1.2, i0 = Math.floor(t0 * SR);
  for (let j = 0; j < SR * 0.12; j++) {
    const t = j / SR;
    add(i0 + j, 0.22 * Math.exp(-t / 0.012) * Math.sin(TAU * (1800 - 9000 * t) * t) + 0.25 * Math.exp(-t / 0.05) * Math.sin(TAU * 70 * t), (k % 2 ? 0.25 : -0.25));
  }
}
// 3) Riser 15.5 -> 23.7 s: noise through a rising one-pole lowpass.
let lp = 0, seed = 7;
const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647) * 2 - 1;
for (let i = Math.floor(SR * 15.5); i < SR * 23.7; i++) {
  const t = i / SR, p = ramp(t, 15.5, 23.6);
  const c = 0.002 + 0.12 * p * p;
  lp += c * (rnd() - lp);
  add(i, lp * 0.5 * p * p * (1 - ramp(t, 23.6, 23.7)));
}
// 4) Logo hit at 24.3 s: A add9 chord, soft attack, long decay, plus sub thump.
const hitNotes = [45, 57, 61, 64, 68, 71, 76];
for (let i = Math.floor(SR * 24.3); i < SR * 34; i++) {
  const t = i / SR - 24.3;
  let v = 0;
  hitNotes.forEach((n, k) => { v += Math.sin(TAU * hz(n) * t + k) * (k === 0 ? 0.5 : 0.22) * env(t, 0.04 + k * 0.02, 3.2 + k * 0.4); });
  v += Math.sin(TAU * 48 * t * (1 - 0.2 * t)) * 0.7 * env(t, 0.005, 0.35);
  add(i, v * 0.3);
}
// Whooshes at scene changes (band-limited noise swell).
for (const tw of [31.6, 50.0, 160.0, 168.0]) {
  let z = 0;
  for (let j = 0; j < SR * 0.9; j++) {
    const t = j / SR, i = Math.floor((tw + t) * SR);
    z += 0.06 * (rnd() - z);
    add(i, z * 0.9 * Math.sin(Math.PI * (t / 0.9)) ** 2, Math.sin(TAU * t / 1.8) * 0.6);
  }
}
// 5) Product bed 32 -> 168 s: pad on Amaj7 F#m7 Dmaj9 E6, 8 s per chord, plus a soft 8th-note pluck at 96 bpm.
const prog = [[45, 57, 61, 64, 68], [42, 54, 57, 61, 64], [38, 50, 54, 57, 64], [40, 52, 56, 59, 61]];
const BPM = 96, eighth = 60 / BPM / 2;
for (let i = SR * 32; i < SR * 168.5; i++) {
  const t = i / SR, tl = t - 32;
  const ci = Math.floor(tl / 8) % 4, ct = tl % 8;
  const xf = Math.min(1, ct / 1.2);
  const fadeIn = ramp(t, 32, 36) * (1 - ramp(t, 167.5, 168.5));
  let v = 0;
  for (const [w, idx] of [[xf, ci], [1 - xf, (ci + 3) % 4]]) {
    if (w <= 0) continue;
    prog[idx].forEach((n, k) => { v += w * Math.sin(TAU * hz(n) * t + k * 1.3) * (k === 0 ? 0.32 : 0.12) * (0.8 + 0.2 * Math.sin(TAU * 0.2 * t + k)); });
  }
  // pluck arpeggio
  const step = Math.floor(tl / eighth), st = tl - step * eighth;
  const notes = prog[ci];
  const pn = notes[1 + (step % 4)] + 12;
  const pl = Math.sin(TAU * hz(pn) * st) * Math.exp(-st / 0.18) * 0.08 * (step % 8 === 0 ? 1.4 : 1);
  add(i, (v * 0.38 + pl) * fadeIn, (step % 2 ? 0.3 : -0.3) * (pl !== 0 ? 0.5 : 0));
}
// 6) Resolve 168.5 -> 175 s.
for (let i = Math.floor(SR * 168.5); i < N; i++) {
  const t = i / SR - 168.5;
  let v = 0;
  [45, 57, 64, 69, 73, 76].forEach((n, k) => { v += Math.sin(TAU * hz(n) * t + k) * (k === 0 ? 0.4 : 0.16) * env(t, 0.6, 2.6); });
  add(i, v * 0.32 * (1 - ramp(i / SR, 174, 175)));
}
// Simple stereo reverb: 4 feedback combs per channel.
const reverb = (x, delays) => {
  const y = new Float32Array(x.length);
  for (const d of delays) {
    const buf = new Float32Array(d); let p = 0;
    for (let i = 0; i < x.length; i++) { const o = buf[p]; buf[p] = x[i] + o * 0.78; y[i] += o * 0.18; p = (p + 1) % d; }
  }
  for (let i = 0; i < x.length; i++) y[i] = x[i] * 0.8 + y[i];
  return y;
};
const RL = reverb(L, [1557, 1617, 1491, 1422]), RR = reverb(R, [1277, 1356, 1188, 1116]);
let peak = 0;
for (let i = 0; i < N; i++) peak = Math.max(peak, Math.abs(RL[i]), Math.abs(RR[i]));
const g = 0.89 / peak;
const buf = Buffer.alloc(44 + N * 4);
buf.write('RIFF', 0); buf.writeUInt32LE(36 + N * 4, 4); buf.write('WAVE', 8); buf.write('fmt ', 12);
buf.writeUInt32LE(16, 16); buf.writeUInt16LE(1, 20); buf.writeUInt16LE(2, 22); buf.writeUInt32LE(SR, 24);
buf.writeUInt32LE(SR * 4, 28); buf.writeUInt16LE(4, 32); buf.writeUInt16LE(16, 34); buf.write('data', 36); buf.writeUInt32LE(N * 4, 40);
for (let i = 0; i < N; i++) {
  buf.writeInt16LE(Math.round(Math.tanh(RL[i] * g) * 32767), 44 + i * 4);
  buf.writeInt16LE(Math.round(Math.tanh(RR[i] * g) * 32767), 46 + i * 4);
}
mkdirSync(root + 'public/music', {recursive: true});
writeFileSync(root + 'public/music/bed.wav', buf);
console.log('bed.wav written, peak normalized from', peak.toFixed(2));
