import React from 'react';
import {C, inter} from '../theme';

export type Prov = 'REAL' | 'SYNTHETIC' | 'SEEDED ISSUE' | 'TEST REPLY' | 'PLAYBACK' | 'ILLUSTRATION' | 'CACHED' | 'PLANNED' | 'NOT PREPARED' | 'NOT SHOWN' | 'DESIGN MOCKUP';

const color: Record<Prov, string> = {
  REAL: C.ready,
  SYNTHETIC: C.accent2,
  'SEEDED ISSUE': C.seeded,
  'TEST REPLY': C.pending,
  PLAYBACK: C.pending,
  ILLUSTRATION: '#9AA3B5',
  CACHED: '#7FD1E6',
  PLANNED: '#6B7385',
  'NOT PREPARED': C.blocked,
  'NOT SHOWN': '#6B7385',
  'DESIGN MOCKUP': '#9AA3B5',
};

export const Chip: React.FC<{kind: Prov; text?: string; size?: number}> = ({kind, text, size = 20}) => (
  <div
    style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: size * 0.5,
      padding: `${size * 0.35}px ${size * 0.75}px`,
      borderRadius: 999,
      background: 'rgba(42,48,64,0.85)',
      border: `1px solid ${C.border}`,
      backdropFilter: 'blur(8px)',
      fontFamily: inter,
      fontSize: size,
      fontWeight: 600,
      letterSpacing: '0.04em',
      color: C.text,
      whiteSpace: 'nowrap',
    }}
  >
    <span style={{width: size * 0.5, height: size * 0.5, borderRadius: 99, background: color[kind], boxShadow: `0 0 ${size * 0.6}px ${color[kind]}`}} />
    <span style={{color: color[kind]}}>{kind}</span>
    {text ? <span style={{color: C.muted, fontWeight: 500, letterSpacing: '0.01em'}}>· {text}</span> : null}
  </div>
);

export const CornerChip: React.FC<{kind: Prov; text?: string}> = ({kind, text}) => (
  <div style={{position: 'absolute', left: 48, bottom: 44}}>
    <Chip kind={kind} text={text} />
  </div>
);
