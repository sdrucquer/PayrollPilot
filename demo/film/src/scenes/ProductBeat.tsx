import React from 'react';
import {AbsoluteFill, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame, Easing} from 'remotion';
import {Background} from '../components/Background';
import {Chip} from '../components/Chip';
import {Pending, PhoneFrame, WindowFrame} from '../components/Frames';
import manifest from '../generated/manifest.json';
import {Section, Segment} from '../beats';
import {C, display, inter, mono, s} from '../theme';

const footage = (manifest as {footage: Record<string, number>}).footage;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const Clip: React.FC<{file?: string; segDur: number; lines: string[]; label: string; compact?: boolean}> = ({file, segDur, lines, label, compact}) => {
  // Missing recordings stay pending; screenshots and design mockups are not footage.
  if (file && footage[file]) {
    const clipDur = footage[file];
    const rate = clipDur >= segDur ? 1 : Math.max(0.6, clipDur / segDur);
    return <OffthreadVideo src={staticFile(`footage/${file}`)} playbackRate={rate} muted style={{width: '100%', height: '100%', objectFit: 'contain', background: C.uiCanvas}} />;
  }
  return <Pending lines={lines} label={label} compact={compact} />;
};

const SegmentView: React.FC<{seg: Segment; dur: number; kicker: string}> = ({seg, dur, kicker}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [0, 14], [0, 1], {...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1)});
  const o = interpolate(f, [0, 8, dur - 6, dur], [0, 1, 1, 0], clamp);
  const missing = (seg.screen && !footage[seg.screen]) || (seg.phone && !footage[seg.phone]);
  const planned = missing;
  const chip = seg.chip;
  const label = seg.chip.kind + (seg.chip.text ? ` · ${seg.chip.text}` : '');
  const segSec = dur / 30;
  return (
    <AbsoluteFill style={{opacity: o}}>
      <div style={{position: 'absolute', left: 120, top: 62, transform: `translateY(${(1 - p) * 10}px)`}}>
        <div style={{fontFamily: mono, fontSize: 20, color: C.stageAccent, letterSpacing: '0.14em'}}>{kicker}</div>
        <div style={{fontFamily: display, fontSize: 46, fontWeight: 700, color: C.text, letterSpacing: '-0.03em', marginTop: 4}}>{seg.title}</div>
      </div>
      <div style={{position: 'absolute', right: 120, top: 92}}>
        <Chip kind={planned ? 'PLANNED' : chip.kind} text={planned ? label : chip.text} />
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
              <Clip file={seg.screen} segDur={segSec} lines={seg.pending.slice(0, -1)} label={label} compact />
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

// One section (magic / engine / result). Local frame 0 = the section's start.
export const SectionView: React.FC<{section: Section; start: number; dur: number}> = ({section, start, dur}) => {
  const f = useCurrentFrame();
  const out = interpolate(f, [dur - 8, dur], [1, 0], clamp);
  const inO = interpolate(f, [0, 10], [0, 1], clamp);
  return (
    <AbsoluteFill style={{opacity: Math.min(out, inO)}}>
      <Background glow={0.55} />
      {section.segments.map((seg, i) => {
        const from = s(seg.from - start);
        const len = s(seg.to - start) - from;
        return (
          <Sequence key={i} from={from} durationInFrames={len} layout="none">
            <SegmentView seg={seg} dur={len} kicker={section.kicker} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
