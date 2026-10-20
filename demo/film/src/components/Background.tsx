import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {C} from '../theme';

// Calm frozen canvas; no dark vignette, neon glow, or grain.
export const Background: React.FC<{glow?: number; hue?: 'accent' | 'warm' | 'none'}> = () => (
  <AbsoluteFill style={{background: 'linear-gradient(180deg,#F5F5F8,#EEEEF3)'}} />
);

export const FadeInOut: React.FC<{dur: number; inF?: number; outF?: number; children: React.ReactNode}> = ({dur, inF = 12, outF = 12, children}) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [0, inF, dur - outF, dur], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{opacity: o}}>{children}</AbsoluteFill>;
};
