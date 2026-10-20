import React, {useMemo} from 'react';
import {interpolate, useCurrentFrame, Easing} from 'remotion';
import {C} from '../theme';

// The PayrollPilot mark rendered as fine particles (Wonderlust register): points sampled along the
// rounded square and the tick-arrow, assembling from a loose cloud; a few drift off the right edge.
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const hex = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
const mix = (a: string, b: string, t: number) => {
  const A = hex(a), B = hex(b);
  return `rgb(${A.map((v, i) => Math.round(lerp(v, B[i], t))).join(',')})`;
};

const samplePath = (): [number, number][] => {
  const pts: [number, number][] = [];
  // rounded square 11..89, r=22
  const seg = (x0: number, y0: number, x1: number, y1: number, n: number) => {
    for (let i = 0; i < n; i++) pts.push([lerp(x0, x1, i / n), lerp(y0, y1, i / n)]);
  };
  const arc = (cx: number, cy: number, a0: number, a1: number, n: number) => {
    for (let i = 0; i < n; i++) {
      const a = lerp(a0, a1, i / n);
      pts.push([cx + 22 * Math.cos(a), cy + 22 * Math.sin(a)]);
    }
  };
  const P = Math.PI;
  seg(33, 11, 67, 11, 34); arc(67, 33, -P / 2, 0, 24);
  seg(89, 33, 89, 67, 34); arc(67, 67, 0, P / 2, 24);
  seg(67, 89, 33, 89, 34); arc(33, 67, P / 2, P, 24);
  seg(11, 67, 11, 33, 34); arc(33, 33, P, 1.5 * P, 24);
  seg(30, 54, 44, 67, 22); seg(44, 67, 71, 36, 40); seg(58, 35, 71, 35, 16); seg(71, 35, 71, 48, 16);
  return pts;
};

export const ParticleMark: React.FC<{size: number; start: number; dur: number}> = ({size, start, dur}) => {
  const f = useCurrentFrame();
  const parts = useMemo(() => {
    let seed = 11;
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    const base = samplePath();
    const out: {x: number; y: number; sx: number; sy: number; r: number; d: number; drift: boolean; o: number}[] = [];
    for (const [x, y] of base) {
      for (let k = 0; k < 3; k++) {
        const ang = rnd() * Math.PI * 2, rad = 30 + rnd() * 90;
        out.push({
          x: x + (rnd() - 0.5) * 2.2,
          y: y + (rnd() - 0.5) * 2.2,
          sx: 50 + Math.cos(ang) * rad,
          sy: 50 + Math.sin(ang) * rad,
          r: 0.5 + rnd() * 0.7,
          d: rnd() * 0.35,
          drift: x > 70 && rnd() < 0.25,
          o: 0.55 + rnd() * 0.45,
        });
      }
    }
    return out;
  }, []);
  const t = (f - start) / dur;
  return (
    <svg width={size} height={size} viewBox="-10 -10 120 120" style={{overflow: 'visible'}}>
      {parts.map((p, i) => {
        const k = interpolate(t, [p.d, p.d + 0.55], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.16, 1, 0.3, 1)});
        let x = lerp(p.sx, p.x, k), y = lerp(p.sy, p.y, k);
        let o = p.o * k;
        if (p.drift) {
          const dk = Math.max(0, t - 0.75 - p.d * 0.5);
          x += dk * 60;
          y -= dk * 8;
          o *= Math.max(0, 1 - dk * 2.2);
        }
        return <circle key={i} cx={x} cy={y} r={p.r} fill={mix(C.steel, C.sand, Math.min(1, Math.max(0, (p.x - 5) / 90)))} opacity={o} />;
      })}
    </svg>
  );
};
