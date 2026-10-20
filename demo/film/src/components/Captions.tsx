import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import narration from '../narration.json';
import manifest from '../generated/manifest.json';
import {C, FPS, inter} from '../theme';

type Line = {id: string; start: number; caption: boolean; text: string};
const vo = (manifest as {vo: Record<string, number>}).vo;

// Split a line into phrases of ~9 words, timed by word share of the measured clip length.
const phrases = (l: Line) => {
  const dur = vo[l.id] ?? l.text.split(' ').length / 2.6;
  const words = l.text.split(' ');
  const chunks: string[][] = [];
  let cur: string[] = [];
  for (const w of words) {
    cur.push(w);
    const end = /[.,;:?!]$/.test(w);
    if ((cur.length >= 9 && end) || cur.length >= 12) {
      chunks.push(cur);
      cur = [];
    }
  }
  if (cur.length) chunks.push(cur);
  let t = l.start;
  return chunks.map((c) => {
    const d = (c.length / words.length) * dur;
    const p = {text: c.join(' '), from: t, to: t + d};
    t += d;
    return p;
  });
};

const all = (narration.lines as Line[]).filter((l) => l.caption).flatMap(phrases);

export const Captions: React.FC = () => {
  const f = useCurrentFrame();
  const sec = f / FPS;
  const p = all.find((x) => sec >= x.from && sec < x.to + 0.15);
  if (!p) return null;
  const o = interpolate(sec, [p.from, p.from + 0.12, p.to, p.to + 0.15], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 40, display: 'flex', justifyContent: 'center', opacity: o, pointerEvents: 'none'}}>
      <div
        style={{
          maxWidth: 1180,
          padding: '10px 22px',
          borderRadius: 12,
          background: 'rgba(255,255,255,.96)',
          fontFamily: inter,
          fontSize: 30,
          fontWeight: 500,
          color: C.text,
          textAlign: 'center',
          lineHeight: 1.3,
        }}
      >
        {p.text}
      </div>
    </div>
  );
};
