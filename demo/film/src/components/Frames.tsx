import React from 'react';
import {C, inter, mono} from '../theme';

export const WindowFrame: React.FC<{width: number; height: number; title?: string; children: React.ReactNode}> = ({width, height, title, children}) => (
  <div
    style={{
      width,
      height,
      borderRadius: 28,
      overflow: 'hidden',
      background: C.uiCanvas,
      border: `1px solid ${C.border}`,
      boxShadow: '0 1px 2px rgba(0,0,0,.03), 0 20px 48px -28px rgba(20,20,40,.22)',
      display: 'flex',
      flexDirection: 'column',
    }}
  >
    <div style={{height: 40, flexShrink: 0, display: 'flex', alignItems: 'center', gap: 8, padding: '0 16px', borderBottom: `1px solid ${C.uiLine}`, background: '#E9E9EF'}}>
      {['#FF5F57', '#FEBC2E', '#28C840'].map((c) => (
        <span key={c} style={{width: 12, height: 12, borderRadius: 99, background: c, opacity: 0.85}} />
      ))}
      <span style={{marginLeft: 16, fontFamily: mono, fontSize: 15, color: C.uiMuted}}>{title}</span>
    </div>
    <div style={{flex: 1, position: 'relative'}}>{children}</div>
  </div>
);

export const PhoneFrame: React.FC<{height: number; children: React.ReactNode}> = ({height, children}) => {
  const width = height * 0.49;
  return (
    <div
      style={{
        width,
        height,
        borderRadius: height * 0.075,
        padding: height * 0.018,
        background: 'linear-gradient(160deg,#FFFFFF,#D1D1D6)',
        boxShadow: '0 20px 48px -28px rgba(20,20,40,.22)',
      }}
    >
      <div style={{width: '100%', height: '100%', borderRadius: height * 0.06, overflow: 'hidden', background: C.uiCanvas, position: 'relative'}}>{children}</div>
    </div>
  );
};

export const Pending: React.FC<{lines: string[]; label: string; compact?: boolean}> = ({lines, label, compact}) => (
  <div
    style={{
      position: 'absolute',
      inset: compact ? 14 : 28,
      borderRadius: 12,
      border: '2px dashed #C7C7CC',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      padding: compact ? 22 : 56,
      gap: compact ? 10 : 16,
      fontFamily: inter,
      background: 'repeating-linear-gradient(135deg, rgba(0,0,0,0.025) 0 14px, rgba(0,0,0,0) 14px 28px)',
    }}
  >
    <div style={{fontFamily: mono, fontSize: compact ? 16 : 22, letterSpacing: '0.12em', color: '#D97A00'}}>FOOTAGE PENDING · {label}</div>
    {lines.map((l) => (
      <div key={l} style={{fontSize: compact ? 20 : 30, color: C.uiMuted, lineHeight: 1.3}}>
        — {l}
      </div>
    ))}
  </div>
);
