import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, Easing} from 'remotion';
import {Background} from '../components/Background';
import {Chip, CornerChip, Prov} from '../components/Chip';
import {ParticleMark} from '../components/ParticleMark';
import {Wordmark} from '../components/Logo';
import status from '../status.json';
import {C, display, inter, mono, s} from '../theme';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const ease = Easing.bezier(0.16, 1, 0.3, 1);

type Row = {name: string; label: string; status: 'shown' | 'not_shown' | 'pending'; row: string};

export const StatusCard: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const out = interpolate(f, [dur - 10, dur], [1, 0], clamp);
  const rows = status.rows as Row[];
  return (
    <AbsoluteFill style={{opacity: out}}>
      <Background glow={0.6} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
        <div style={{width: 1240}}>
          <div style={{fontFamily: display, fontSize: 60, fontWeight: 700, letterSpacing: '-0.035em', color: C.text, marginBottom: 30, opacity: interpolate(f, [0, 12], [0, 1], clamp)}}>What you just saw</div>
          {rows.map((r, i) => {
            const p = interpolate(f, [8 + i * 6, 22 + i * 6], [0, 1], {...clamp, easing: ease});
            const kind: Prov = r.status === 'not_shown' ? 'NOT SHOWN' : r.status === 'pending' ? 'PLANNED' : (r.label as Prov);
            return (
              <div
                key={r.name}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '20px 4px',
                  borderTop: `1px solid ${C.border}`,
                  opacity: p,
                  transform: `translateX(${(1 - p) * 24}px)`,
                }}
              >
                <span style={{fontFamily: inter, fontSize: 34, color: C.text, fontWeight: 500}}>{r.name}</span>
                <span style={{display: 'flex', alignItems: 'center', gap: 16}}>
                  {r.status === 'pending' && <span style={{fontFamily: mono, fontSize: 18, color: C.pending}}>PENDING VERIFICATION</span>}
                  <Chip kind={kind} size={22} />
                </span>
              </div>
            );
          })}
          {status.bandUsage ? (
            <div style={{fontFamily: mono, fontSize: 20, color: C.muted, marginTop: 18}}>{String(status.bandUsage)}</div>
          ) : null}
        </div>
      </AbsoluteFill>
      <CornerChip kind="ILLUSTRATION" text="summary of labels used above" />
    </AbsoluteFill>
  );
};

export const Close: React.FC = () => {
  const f = useCurrentFrame();
  const word = interpolate(f, [s(0.5), s(1.8)], [0, 1], clamp);
  const meta = interpolate(f, [s(1.8), s(2.6)], [0, 1], {...clamp, easing: ease});
  const out = interpolate(f, [s(5.8), s(6.5)], [1, 0], clamp);
  return (
    <AbsoluteFill style={{opacity: out}}>
      <AbsoluteFill style={{background: '#000'}} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 28}}>
          <ParticleMark size={150} start={0} dur={s(2.4)} />
          <Wordmark size={110} progress={word} />
        </div>
        <div style={{marginTop: 30, fontFamily: inter, fontSize: 36, color: C.muted, opacity: meta}}>Payroll, prepared.</div>
        <div style={{marginTop: 70, fontFamily: mono, fontSize: 26, color: C.text, opacity: meta}}>github.com/sdrucquer/PayrollPilot</div>
        <div style={{marginTop: 14, fontFamily: inter, fontSize: 22, color: C.faint, opacity: meta}}>Built in one day · AI Startup Challenge · San Francisco · October 20, 2026</div>
      </AbsoluteFill>
      <CornerChip kind="ILLUSTRATION" />
    </AbsoluteFill>
  );
};
