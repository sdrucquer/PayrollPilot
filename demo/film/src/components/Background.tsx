import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {C} from '../theme';

export const Background: React.FC<{glow?: number; hue?: 'accent' | 'warm' | 'none'}> = ({glow = 1, hue = 'accent'}) => {
  const f = useCurrentFrame();
  const x = 50 + Math.sin(f / 140) * 12;
  const y = 40 + Math.cos(f / 170) * 10;
  const col = hue === 'warm' ? 'rgba(255,92,108,0.16)' : hue === 'none' ? 'rgba(0,0,0,0)' : 'rgba(79,124,255,0.18)';
  const col2 = hue === 'warm' ? 'rgba(245,185,66,0.07)' : 'rgba(127,160,255,0.08)';
  return (
    <AbsoluteFill style={{backgroundColor: C.bg}}>
      <AbsoluteFill
        style={{
          opacity: glow,
          background: `radial-gradient(60% 55% at ${x}% ${y}%, ${col} 0%, rgba(0,0,0,0) 70%), radial-gradient(40% 40% at ${100 - x}% ${100 - y}%, ${col2} 0%, rgba(0,0,0,0) 70%)`,
        }}
      />
      <Grain />
      <AbsoluteFill style={{background: 'radial-gradient(120% 90% at 50% 50%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%)'}} />
    </AbsoluteFill>
  );
};

const Grain: React.FC = () => {
  const f = useCurrentFrame();
  const seed = Math.floor(f / 2) % 8;
  return (
    <AbsoluteFill style={{opacity: 0.07, mixBlendMode: 'overlay'}}>
      <svg width="100%" height="100%">
        <filter id={`g${seed}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={seed} stitchTiles="stitch" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#g${seed})`} />
      </svg>
    </AbsoluteFill>
  );
};

export const FadeInOut: React.FC<{dur: number; inF?: number; outF?: number; children: React.ReactNode}> = ({dur, inF = 12, outF = 12, children}) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [0, inF, dur - outF, dur], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{opacity: o}}>{children}</AbsoluteFill>;
};
