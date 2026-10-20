import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, Easing} from 'remotion';
import {Background} from '../components/Background';
import {CornerChip} from '../components/Chip';
import {ParticleMark} from '../components/ParticleMark';
import {C, display, inter, mono, s} from '../theme';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const ease = Easing.bezier(0.16, 1, 0.3, 1);

export const ColdOpen: React.FC = () => {
  const f = useCurrentFrame();
  const text = 'Friday, 4:52 PM.';
  const n = Math.floor(interpolate(f, [s(0.5), s(1.6)], [0, text.length], clamp));
  const blink = Math.floor(f / 15) % 2 === 0;
  const out = interpolate(f, [s(2.8), s(3.2)], [1, 0], clamp);
  return (
    <AbsoluteFill style={{background: '#000', alignItems: 'center', justifyContent: 'center', opacity: out}}>
      <div style={{fontFamily: mono, fontSize: 64, color: C.text, letterSpacing: '0.02em'}}>
        {text.slice(0, n)}
        <span style={{opacity: blink ? 1 : 0, color: C.accent}}>▍</span>
      </div>
      <div style={{position: 'absolute', bottom: 130, fontFamily: inter, fontSize: 26, color: C.muted, opacity: interpolate(f, [s(1.8), s(2.3)], [0, 1], clamp)}}>Payroll runs Monday.</div>
      <CornerChip kind="ILLUSTRATION" />
    </AbsoluteFill>
  );
};

const FRAGS: {t: string; x: number; y: number; size: number; color?: string; mono?: boolean}[] = [
  {t: '4 timesheets', x: -420, y: -250, size: 96},
  {t: '3 systems', x: 380, y: -150, size: 96},
  {t: '1 spreadsheet', x: -250, y: 40, size: 96},
  {t: 'a shift on the wrong job', x: 360, y: 210, size: 58, mono: true},
  {t: 'a receipt nobody can place', x: -360, y: 300, size: 52, mono: true},
  {t: 'who quoted job 2?', x: 420, y: -330, size: 54, mono: true},
  {t: 'overtime?', x: -560, y: -60, size: 48, mono: true},
  {t: 'paid twice?', x: 600, y: 40, size: 48, mono: true},
  {t: 'pay it anyway?', x: 0, y: -10, size: 120, color: C.blocked},
];

const Grid: React.FC<{o: number}> = ({o}) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{opacity: o, transform: `perspective(1200px) rotateX(58deg) translateY(${(f % 60) * 1.2}px) scale(2)`, transformOrigin: '50% 80%'}}>
      <svg width="100%" height="100%">
        <defs>
          <pattern id="cells" width="120" height="40" patternUnits="userSpaceOnUse">
            <path d="M120 0 L0 0 0 40" fill="none" stroke="rgba(139,147,165,0.18)" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#cells)" />
      </svg>
    </AbsoluteFill>
  );
};

// Local frame 0 = 3.2s. Fragments every ~1.25s, last one lands at ~10.5s local.
export const Montage: React.FC = () => {
  const f = useCurrentFrame();
  const step = s(1.2);
  const shake = (i: number) => (f > i * step ? Math.sin(f * 1.7 + i) * interpolate(f, [0, s(11)], [0, 3], clamp) : 0);
  const out = interpolate(f, [s(11.6), s(12)], [1, 0], clamp);
  return (
    <AbsoluteFill style={{opacity: out}}>
      <Background hue="warm" glow={interpolate(f, [0, s(10)], [0.3, 1], clamp)} />
      <Grid o={interpolate(f, [0, s(2)], [0, 0.55], clamp)} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
        {FRAGS.map((fr, i) => {
          const start = i * step;
          const local = f - start;
          if (local < 0) return null;
          const p = interpolate(local, [0, 10], [0, 1], {...clamp, easing: ease});
          const isLast = i === FRAGS.length - 1;
          const lastAt = (FRAGS.length - 1) * step;
          const dim = isLast ? 1 : interpolate(f, [start + step, start + step + 8], [1, 0.28], clamp) * interpolate(f, [lastAt, lastAt + 8], [1, 0.4], clamp);
          return (
            <div
              key={fr.t}
              style={{
                position: 'absolute',
                transform: `translate(${fr.x + shake(i)}px, ${fr.y}px) scale(${1.25 - 0.25 * p})`,
                opacity: p * dim,
                filter: `blur(${(1 - p) * 14}px)`,
                fontFamily: fr.mono ? mono : display,
                fontWeight: fr.mono ? 500 : 700,
                fontSize: fr.size,
                letterSpacing: fr.mono ? '0' : '-0.04em',
                color: fr.color ?? C.text,
                whiteSpace: 'nowrap',
              }}
            >
              {fr.t}
            </div>
          );
        })}
      </AbsoluteFill>
      <CornerChip kind="ILLUSTRATION" />
    </AbsoluteFill>
  );
};

// Local 0 = 15.2s. Collapse to a rule, then the question, word by word.
export const Turn: React.FC = () => {
  const f = useCurrentFrame();
  const line = interpolate(f, [0, s(1)], [0, 1], {...clamp, easing: ease});
  const q1 = 'What if payroll came to you already checked,';
  const q2 = 'with the questions already asked,';
  const q3 = 'and nothing paid until you said so?';
  const words = [...q1.split(' '), '|', ...q2.split(' '), '|', ...q3.split(' ')];
  let wi = 0;
  const startW = s(0.6);
  const per = s(7.4) / words.length;
  const rows: React.ReactNode[][] = [[]];
  words.forEach((w) => {
    if (w === '|') {
      rows.push([]);
      return;
    }
    const t0 = startW + wi * per;
    const p = interpolate(f, [t0, t0 + 8], [0, 1], {...clamp, easing: ease});
    rows[rows.length - 1].push(
      <span key={wi} style={{display: 'inline-block', opacity: p, transform: `translateY(${(1 - p) * 18}px)`, marginRight: '0.28em', color: w.startsWith('nothing') || w === 'paid' ? C.text : undefined}}>
        {w}
      </span>,
    );
    wi++;
  });
  const out = interpolate(f, [s(8.4), s(8.8)], [1, 0], clamp);
  return (
    <AbsoluteFill style={{opacity: out}}>
      <Background glow={0.5} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
        <div style={{fontFamily: display, fontWeight: 600, fontSize: 64, letterSpacing: '-0.03em', color: '#C9D1E0', textAlign: 'center', lineHeight: 1.18}}>
          {rows.map((r, i) => (
            <div key={i}>{r}</div>
          ))}
        </div>
        <div style={{position: 'absolute', top: '74%', height: 2, width: 1100 * line, background: `linear-gradient(90deg, rgba(139,156,255,0), ${C.accent}, rgba(183,156,255,0))`}} />
      </AbsoluteFill>
      <CornerChip kind="ILLUSTRATION" />
    </AbsoluteFill>
  );
};

// Local 0 = 24s. 8s long. Title card: particle mark on black, one quiet word below (docs/DESIGN-DIRECTION.md).
export const LogoReveal: React.FC = () => {
  const f = useCurrentFrame();
  const word = interpolate(f, [s(2.6), s(3.8)], [0, 1], {...clamp, easing: ease});
  const tag = interpolate(f, [s(3.8), s(4.8)], [0, 1], {...clamp, easing: ease});
  const scale = interpolate(f, [0, s(8)], [1.06, 1], clamp);
  const glow = interpolate(f, [s(1.5), s(3.5)], [0, 1], clamp);
  const out = interpolate(f, [s(7.4), s(8)], [1, 0], clamp);
  return (
    <AbsoluteFill style={{opacity: out, background: '#000'}}>
      <AbsoluteFill style={{opacity: glow * 0.9, background: `radial-gradient(30% 34% at 50% 42%, rgba(127,166,217,0.16), rgba(226,201,160,0.05) 55%, rgba(0,0,0,0) 75%)`}} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', transform: `scale(${scale})`}}>
        <div style={{marginTop: -60}}>
          <ParticleMark size={330} start={s(0.1)} dur={s(4.2)} />
        </div>
        <div style={{marginTop: 34, fontFamily: display, fontSize: 76, fontWeight: 500, letterSpacing: '-0.025em', color: C.text, opacity: word, filter: `blur(${(1 - word) * 6}px)`}}>
          PayrollPilot
        </div>
        <div style={{marginTop: 18, fontFamily: inter, fontSize: 30, fontWeight: 400, color: C.muted, opacity: tag, letterSpacing: '0.01em'}}>
          Payroll, prepared. Never guessed.
        </div>
      </AbsoluteFill>
      <CornerChip kind="ILLUSTRATION" />
    </AbsoluteFill>
  );
};
