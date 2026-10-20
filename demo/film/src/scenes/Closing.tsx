import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, Easing} from 'remotion';
import {Chip, CornerChip, Prov} from '../components/Chip';
import {ParticleMark} from '../components/ParticleMark';
import status from '../status.json';
import {C, display, inter, mono, s} from '../theme';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const ease = Easing.bezier(0.16, 1, 0.3, 1);
type Row = {name: string; label: string; status: 'shown' | 'not_shown' | 'pending'; row: string};

// Local 0 = 145 s, 7 s long. States the boundary from docs/PRODUCT-STATEMENT.md "It cannot".
export const Close: React.FC = () => {
  const f = useCurrentFrame();
  const a = interpolate(f, [s(0.3), s(1.2)], [0, 1], {...clamp, easing: ease});
  const b = interpolate(f, [s(1.6), s(2.4)], [0, 1], {...clamp, easing: ease});
  const c = interpolate(f, [s(2.6), s(3.4)], [0, 1], {...clamp, easing: ease});
  const out = interpolate(f, [s(6.4), s(7)], [1, 0], clamp);
  const rows = status.rows as Row[];
  return (
    <AbsoluteFill style={{opacity: out, background: 'linear-gradient(180deg,#F5F5F8,#EEEEF3)'}}>
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 26}}>
          <ParticleMark size={120} start={0} dur={s(2)} />
          <div style={{fontFamily: display, fontSize: 84, letterSpacing: '-0.03em', color: C.text}}>
            <span style={{fontWeight: 500}}>Payroll</span>
            <span style={{fontWeight: 700}}>Pilot</span>
          </div>
        </div>
        <div style={{marginTop: 34, fontFamily: display, fontWeight: 600, fontSize: 46, letterSpacing: '-0.025em', color: C.text, opacity: a}}>
          From missing information to payroll-ready. <span style={{color: C.accent}}>With you in control.</span>
        </div>
        <div style={{marginTop: 16, fontFamily: inter, fontSize: 28, color: C.muted, opacity: b}}>You approve every message and correction. PayrollPilot never submits payroll.</div>
        <div style={{marginTop: 46, display: 'flex', gap: 12, flexWrap: 'wrap', justifyContent: 'center', maxWidth: 1500, opacity: c}}>
          {rows.map((r) => {
            const kind: Prov = r.status === 'not_shown' ? 'NOT SHOWN' : r.status === 'pending' ? 'PLANNED' : (r.label as Prov);
            return <Chip key={r.name} kind={kind} text={r.name} size={18} />;
          })}
        </div>
        <div style={{marginTop: 34, fontFamily: mono, fontSize: 22, color: C.muted, opacity: c}}>github.com/sdrucquer/PayrollPilot · AI Startup Challenge, SF · Oct 20, 2026</div>
      </AbsoluteFill>
      <CornerChip kind="ILLUSTRATION" />
    </AbsoluteFill>
  );
};
