import React from 'react';
import {AbsoluteFill, Audio, interpolate, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {Caption, D, K} from './ui';
import {Audit, BoardCost, Close, DevTeam, Hook, Loop, Memory, Pull, Recap, Reveal, Room} from './scenes';

const FPS = 30;
const fr = (s: number) => Math.round(s * FPS);
const SCENES: Record<string, React.FC<{dur: number; voAt: number; voDur: number}>> = {
  '01': Hook, '02': Reveal, '03': Pull, '04': Audit, '12': Room, '13': BoardCost, '14': DevTeam, '15': Memory, '16': Recap, '17': Close,
};
const LOOP_IDS = ['05', '06', '07', '08', '09', '10', '11'];

// Short cross-dissolve + lift at each scene start.
const Enter: React.FC<{children: React.ReactNode; dur: number}> = ({children, dur}) => {
  const f = useCurrentFrame();
  const a = interpolate(f, [0, 10], [0, 1], {extrapolateRight: 'clamp'});
  const b = interpolate(f, [fr(dur) - 6, fr(dur)], [1, 0.0], {extrapolateLeft: 'clamp'});
  return <AbsoluteFill style={{opacity: Math.min(a, b < 1 ? Math.max(b, 0.001) : 1), transform: `scale(${0.985 + 0.015 * a})`}}>{children}</AbsoluteFill>;
};

export const Demo: React.FC = () => {
  const loop = D.timeline.filter((s) => LOOP_IDS.includes(s.id));
  const loopFrom = loop[0]?.from ?? 0;
  const loopDur = loop.reduce((a, s) => a + s.dur, 0);
  return (
    <AbsoluteFill style={{background: K.bg0}}>
      {D.timeline.map((s) => {
        const C = SCENES[s.id];
        if (!C) return null;
        const voDur = D.vo[s.id]?.dur ?? 0;
        return (
          <Sequence key={s.id} from={fr(s.from)} durationInFrames={fr(s.dur)} name={`${s.id}`}>
            {s.id === '01' || s.id === '02' ? <C dur={s.dur} voAt={s.voAt} voDur={voDur} /> : <Enter dur={s.dur}><C dur={s.dur} voAt={s.voAt} voDur={voDur} /></Enter>}
          </Sequence>
        );
      })}
      {loop.length ? (
        <Sequence from={fr(loopFrom)} durationInFrames={fr(loopDur)} name="loop">
          <Enter dur={loopDur}><Loop start={loopFrom} /></Enter>
        </Sequence>
      ) : null}
      {D.timeline.map((s) => (
        <Sequence key={`c${s.id}`} from={fr(s.from)} durationInFrames={fr(s.dur)} layout="none">
          <Caption text={s.text} voAt={s.voAt} voDur={D.vo[s.id]?.dur ?? 0} dur={s.dur} />
        </Sequence>
      ))}
      {D.timeline.map((s) =>
        D.vo[s.id] ? (
          <Sequence key={`v${s.id}`} from={fr(s.from + s.voAt)} durationInFrames={fr(D.vo[s.id].dur + 0.4)} layout="none">
            <Audio src={staticFile(D.vo[s.id].file)} />
          </Sequence>
        ) : null,
      )}
    </AbsoluteFill>
  );
};
