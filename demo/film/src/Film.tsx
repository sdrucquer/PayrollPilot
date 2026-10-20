import React from 'react';
import {AbsoluteFill, Audio, interpolate, Sequence, staticFile} from 'remotion';
import {Captions} from './components/Captions';
import narration from './narration.json';
import manifest from './generated/manifest.json';
import status from './status.json';
import {BEATS} from './beats';
import {HowItWorks} from './scenes/HowItWorks';
import {ColdOpen, LogoReveal, Montage, Turn} from './scenes/Opening';
import {ProductBeat} from './scenes/ProductBeat';
import {Close, StatusCard} from './scenes/Closing';
import {T, TOTAL} from './timeline';
import {C, mono, s} from './theme';

const m = manifest as {vo: Record<string, number>; footage: Record<string, number>; music: string | null; voSource: string};
const span = (k: keyof typeof T) => ({from: s(T[k][0]), durationInFrames: s(T[k][1]) - s(T[k][0])});

const Watermark: React.FC = () => {
  const missing = BEATS.flatMap((b) => b.segments.flatMap((x) => [x.screen, x.phone])).filter((f) => f && !m.footage[f]);
  const parts = [] as string[];
  if (status.draft) parts.push('DRAFT RENDER');
  if (m.voSource !== 'elevenlabs') parts.push(m.voSource === 'say' ? 'placeholder voice' : 'no voice');
  if (missing.length) parts.push(`${new Set(missing).size} clips pending`);
  if (!parts.length) return null;
  return <div style={{position: 'absolute', right: 28, top: 22, fontFamily: mono, fontSize: 16, color: C.pending, opacity: 0.8, letterSpacing: '0.08em'}}>{parts.join(' · ')}</div>;
};

export const Film: React.FC = () => {
  const musicVol = (f: number) =>
    interpolate(f, [0, s(3), s(23.6), s(24), s(32), s(34), s(160), s(168.5), s(TOTAL)], [0.0, 0.5, 0.75, 0.9, 0.85, 0.32, 0.32, 0.7, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{backgroundColor: C.bg}}>
      <Sequence {...span('coldOpen')}><ColdOpen /></Sequence>
      <Sequence {...span('montage')}><Montage /></Sequence>
      <Sequence {...span('turn')}><Turn /></Sequence>
      <Sequence {...span('logo')}><LogoReveal /></Sequence>
      <Sequence {...span('how')}><HowItWorks /></Sequence>
      {BEATS.map((b) => (
        <Sequence key={b.key} {...span(b.key)}>
          <ProductBeat beat={b} dur={span(b.key).durationInFrames} />
        </Sequence>
      ))}
      <Sequence {...span('status')}><StatusCard dur={span('status').durationInFrames} /></Sequence>
      <Sequence {...span('close')}><Close /></Sequence>
      <Captions />
      <Watermark />
      {m.music ? <Audio src={staticFile(m.music)} volume={musicVol} /> : null}
      {narration.lines.map((l) =>
        m.vo[l.id] ? (
          <Sequence key={l.id} from={s(l.start)} durationInFrames={Math.ceil((m.vo[l.id] + 0.3) * 30)} layout="none">
            <Audio src={staticFile(`vo/${l.id}.mp3`)} volume={1} />
          </Sequence>
        ) : null,
      )}
    </AbsoluteFill>
  );
};
