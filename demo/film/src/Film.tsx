import React from 'react';
import {AbsoluteFill, Audio, interpolate, Sequence, staticFile} from 'remotion';
import {Captions} from './components/Captions';
import narration from './narration.json';
import manifest from './generated/manifest.json';
import status from './status.json';
import {SECTIONS} from './beats';
import {HowItWorks} from './scenes/HowItWorks';
import {Hook, Reveal} from './scenes/Opening';
import {SectionView} from './scenes/ProductBeat';
import {Close} from './scenes/Closing';
import {T, TOTAL} from './timeline';
import {C, mono, s} from './theme';

const m = manifest as {vo: Record<string, number>; footage: Record<string, number>; music: string | null; voSource: string};
const span = (k: keyof typeof T) => ({from: s(T[k][0]), durationInFrames: s(T[k][1]) - s(T[k][0])});

const Watermark: React.FC = () => {
  const missing = SECTIONS.flatMap((x) => x.segments.flatMap((g) => [g.screen, g.phone])).filter((f) => f && !m.footage[f]);
  const parts = [] as string[];
  if (status.draft) parts.push('DRAFT RENDER');
  if (m.voSource !== 'elevenlabs' && m.voSource !== 'owner') parts.push(m.voSource === 'say' ? 'placeholder voice' : 'no voice');
  if (missing.length) parts.push(`${new Set(missing).size} clips pending`);
  if (!parts.length) return null;
  return <div style={{position: 'absolute', right: 28, top: 22, fontFamily: mono, fontSize: 16, color: C.pending, opacity: 0.8, letterSpacing: '0.08em'}}>{parts.join(' · ')}</div>;
};

export const Film: React.FC = () => {
  const musicVol = (f: number) =>
    interpolate(f, [0, s(1), s(12.8), s(13.2), s(15.2), s(17), s(25), s(27), s(144), s(146), s(TOTAL)], [0.35, 0.55, 0.8, 0.9, 0.95, 0.8, 0.6, 0.3, 0.3, 0.7, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{backgroundColor: C.bg}}>
      <Sequence {...span('hook')}><Hook /></Sequence>
      <Sequence {...span('reveal')}><Reveal /></Sequence>
      {SECTIONS.map((x) => (
        <Sequence key={x.key} {...span(x.key)}>
          <SectionView section={x} start={T[x.key][0]} dur={span(x.key).durationInFrames} />
        </Sequence>
      ))}
      <Sequence {...span('how')}><HowItWorks /></Sequence>
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
