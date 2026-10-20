import React from 'react';
import {interpolate, useCurrentFrame, Easing} from 'remotion';
import {C, display} from '../theme';

// Mark: rounded square + a ledger tick that climbs into a heading arrow ("prepared, then piloted").
export const Mark: React.FC<{size: number; draw?: number}> = ({size, draw = 1}) => {
  const sq = 4 * 78;
  const path = 150;
  return (
    <svg width={size} height={size} viewBox="0 0 100 100">
      <defs>
        <linearGradient id="pp" x1="0" y1="1" x2="1" y2="0">
          <stop offset="0" stopColor={C.accent} />
          <stop offset="1" stopColor={C.accent2} />
        </linearGradient>
      </defs>
      <rect x="11" y="11" width="78" height="78" rx="22" fill="none" stroke="url(#pp)" strokeWidth="6" strokeDasharray={sq} strokeDashoffset={sq * (1 - Math.min(1, draw * 1.4))} strokeLinecap="round" />
      <path
        d="M30 54 L44 67 L71 36 M58 35 L71 35 L71 48"
        fill="none"
        stroke={C.text}
        strokeWidth="7"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={path}
        strokeDashoffset={path * (1 - Math.max(0, Math.min(1, (draw - 0.3) / 0.7)))}
      />
    </svg>
  );
};

export const Wordmark: React.FC<{size: number; progress?: number}> = ({size, progress = 1}) => {
  const letters = 'PayrollPilot'.split('');
  return (
    <div style={{fontFamily: display, fontSize: size, letterSpacing: '-0.035em', color: C.text, display: 'flex'}}>
      {letters.map((l, i) => {
        const p = Math.max(0, Math.min(1, progress * letters.length * 0.55 - i * 0.45));
        return (
          <span key={i} style={{fontWeight: i < 7 ? 500 : 750, opacity: p, transform: `translateY(${(1 - p) * size * 0.25}px)`, filter: `blur(${(1 - p) * 8}px)`, display: 'inline-block'}}>
            {l}
          </span>
        );
      })}
    </div>
  );
};

export const useEase = (from: number, to: number) => {
  const f = useCurrentFrame();
  return interpolate(f, [from, to], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.16, 1, 0.3, 1)});
};
