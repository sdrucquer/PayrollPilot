import React from 'react';
import {AbsoluteFill, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame, Easing} from 'remotion';
import {Background} from '../components/Background';
import {Chip} from '../components/Chip';
import {Pending, PhoneFrame, WindowFrame} from '../components/Frames';
import manifest from '../generated/manifest.json';
import {Beat, Segment} from '../beats';
import {C, display, inter, mono, s} from '../theme';

const footage = (manifest as {footage: Record<string, number>}).footage;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const Clip: React.FC<{file?: string; segDur: number; lines: string[]; label: string; compact?: boolean}> = ({file, segDur, lines, label, compact}) => {
  if (file && footage[file]) {
    const clipDur = footage[file];
    const rate = clipDur >= segDur ? 1 : Math.max(0.6, clipDur / segDur);
    return <OffthreadVideo src={staticFile(`footage/${file}`)} playbackRate={rate} muted style={{width: '100%', height: '100%', objectFit: 'contain', background: '#000'}} />;
  }
  return <Pending lines={lines} label={label} compact={compact} />;
};

const SegmentView: React.FC<{seg: Segment; dur: number}> = ({seg, dur}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [0, 14], [0, 1], {...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1)});
  const o = interpolate(f, [0, 8, dur - 6, dur], [0, 1, 1, 0], clamp);
  const planned = (seg.screen && !footage[seg.screen]) || (seg.phone && !footage[seg.phone]);
  const label = seg.chip.kind + (seg.chip.text ? ` · ${seg.chip.text}` : '');
  const segSec = dur / 30;
  return (
    <AbsoluteFill style={{opacity: o}}>
      <div style={{position: 'absolute', right: 120, top: 92}}>
        <Chip kind={planned ? 'PLANNED' : seg.chip.kind} text={planned ? label : seg.chip.text} />
      </div>
      {seg.layout === 'screen' && (
        <div style={{position: 'absolute', left: 260, top: 176, transform: `scale(${0.97 + 0.03 * p})`, transformOrigin: '50% 0%'}}>
          <WindowFrame width={1400} height={790} title={seg.route}>
            <Clip file={seg.screen} segDur={segSec} lines={seg.pending} label={label} />
          </WindowFrame>
        </div>
      )}
      {seg.layout === 'split' && (
        <>
          <div style={{position: 'absolute', left: 120, top: 196, transform: `translateX(${(1 - p) * -30}px)`}}>
            <WindowFrame width={1200} height={700} title={seg.route}>
              <Clip file={seg.screen} segDur={segSec} lines={seg.pending.slice(0, 2)} label={label} compact />
            </WindowFrame>
          </div>
          <div style={{position: 'absolute', left: 1400, top: 176, transform: `translateY(${(1 - p) * 60}px)`}}>
            <PhoneFrame height={780}>
              <Clip file={seg.phone} segDur={segSec} lines={seg.pending.slice(-1)} label="PHONE" compact />
            </PhoneFrame>
          </div>
        </>
      )}
    </AbsoluteFill>
  );
};

export const ProductBeat: React.FC<{beat: Beat; dur: number}> = ({beat, dur}) => {
  const f = useCurrentFrame();
  const head = interpolate(f, [4, 18], [0, 1], {...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1)});
  const out = interpolate(f, [dur - 8, dur], [1, 0], clamp);
  let at = 0;
  return (
    <AbsoluteFill style={{opacity: out}}>
      <Background glow={0.55} />
      <div style={{position: 'absolute', left: 120, top: 66, opacity: head, transform: `translateY(${(1 - head) * 10}px)`}}>
        <div style={{display: 'flex', alignItems: 'baseline', gap: 18}}>
          <span style={{fontFamily: mono, fontSize: 22, color: C.accent, letterSpacing: '0.08em'}}>{beat.n} / 07</span>
          <span style={{fontFamily: display, fontSize: 46, fontWeight: 700, color: C.text, letterSpacing: '-0.03em'}}>{beat.title}</span>
        </div>
        <div style={{fontFamily: inter, fontSize: 24, color: C.muted, marginTop: 4, marginLeft: 2}}>{beat.sub}</div>
      </div>
      {beat.segments.map((seg, i) => {
        const from = Math.round(at * dur);
        at += seg.share;
        const len = Math.round(at * dur) - from;
        return (
          <Sequence key={i} from={from} durationInFrames={len} layout="none">
            <SegmentView seg={seg} dur={len} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
