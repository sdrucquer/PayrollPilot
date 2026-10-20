import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, Easing} from 'remotion';
import {Background} from '../components/Background';
import {CornerChip} from '../components/Chip';
import {C, display, inter, mono, s} from '../theme';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const ease = Easing.bezier(0.16, 1, 0.3, 1);

const AGENTS = [
  {name: 'Audit', verb: 'finds issues', tools: ['read_snapshot', 'run_checks', 'request_handoff'], at: 2.0},
  {name: 'Resolution', verb: 'asks people', tools: ['draft_batch', 'parse_reply', 'memory_write'], at: 2.6},
  {name: 'Payroll Prep', verb: 'assembles the result', tools: ['compute_readiness', 'build_workbook', 'memory_recall'], at: 3.2},
];
const CW = 440;
const GAP = 120;
const X0 = (1920 - (CW * 3 + GAP * 2)) / 2;
const CY = 300;
const CH = 270;

// Local 0 = 100s; VO e1 starts at local 0.8s. Scene is 11s.
export const HowItWorks: React.FC = () => {
  const f = useCurrentFrame();
  const head = interpolate(f, [s(0.2), s(1.2)], [0, 1], {...clamp, easing: ease});
  const bar = interpolate(f, [s(4.4), s(5.2)], [0, 1], {...clamp, easing: ease});
  const arrows = interpolate(f, [s(5.8), s(6.6)], [0, 1], {...clamp, easing: ease});
  const mem = interpolate(f, [s(6.8), s(7.6)], [0, 1], {...clamp, easing: ease});
  const morph = interpolate(f, [s(10.0), s(10.9)], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const others = 1 - morph;
  const barY = interpolate(morph, [0, 1], [CY + CH + 110, 0]);
  const barX = interpolate(morph, [0, 1], [X0, 0]);
  const barW = interpolate(morph, [0, 1], [CW * 3 + GAP * 2, 1920]);
  const barH = interpolate(morph, [0, 1], [96, 72]);
  const barR = interpolate(morph, [0, 1], [20, 0]);
  return (
    <AbsoluteFill>
      <Background glow={others} />
      <div style={{position: 'absolute', top: 120, width: '100%', textAlign: 'center', opacity: head * others, fontFamily: display, fontWeight: 700, fontSize: 64, letterSpacing: '-0.035em', color: C.text}}>
        Three agents. <span style={{color: C.muted}}>One rulebook.</span> You decide.
      </div>
      {AGENTS.map((a, i) => {
        const appear = interpolate(f, [s(0.9 + i * 0.25), s(1.9 + i * 0.25)], [0, 1], {...clamp, easing: ease});
        const lit = interpolate(f, [s(a.at), s(a.at + 0.3), s(a.at + 1.0), s(a.at + 1.5)], [0, 1, 1, 0.35], clamp);
        const x = X0 + i * (CW + GAP);
        return (
          <div
            key={a.name}
            style={{
              position: 'absolute',
              left: x,
              top: CY + (1 - appear) * 40,
              width: CW,
              height: CH,
              opacity: appear * others,
              borderRadius: 28,
              background: 'linear-gradient(180deg,#F3F8FF,#FFFFFF 38%)',
              border: `1px solid ${lit > 0.5 ? C.accent : C.border}`,
              boxShadow: '0 1px 2px rgba(0,0,0,.03), 0 20px 48px -28px rgba(20,20,40,.22)',
              padding: 34,
              fontFamily: inter,
            }}
          >
            <div style={{fontFamily: mono, fontSize: 18, color: C.faint, letterSpacing: '0.1em'}}>AGENT 0{i + 1}</div>
            <div style={{fontFamily: display, fontSize: 50, fontWeight: 700, color: C.text, letterSpacing: '-0.03em', marginTop: 6}}>{a.name}</div>
            <div style={{fontSize: 26, color: C.muted, marginTop: 2}}>{a.verb}</div>
            <div style={{display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 22}}>
              {a.tools.map((t) => (
                <span key={t} style={{fontFamily: mono, fontSize: 16, color: C.accent2, padding: '5px 10px', borderRadius: 8, background: 'rgba(10,122,255,0.10)', border: '1px solid rgba(10,122,255,0.25)'}}>
                  {t}
                </span>
              ))}
            </div>
          </div>
        );
      })}
      {[0, 1].map((i) => {
        const x = X0 + CW + i * (CW + GAP);
        return (
          <div key={i} style={{position: 'absolute', left: x + 8, top: CY + CH / 2 - 40, width: GAP - 16, opacity: arrows * others, textAlign: 'center'}}>
            <div style={{fontFamily: mono, fontSize: 14, color: C.ready, letterSpacing: '0.06em', marginBottom: 8}}>BAND</div>
            <svg width={GAP - 16} height="24" viewBox="0 0 104 24">
              <path d={`M4 12 H${4 + 90 * arrows}`} stroke={C.ready} strokeWidth="3" strokeLinecap="round" />
              <path d="M88 4 L98 12 L88 20" fill="none" stroke={C.ready} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" opacity={arrows > 0.9 ? 1 : 0} />
            </svg>
            <div style={{fontFamily: inter, fontSize: 14, color: C.muted, marginTop: 8}}>handoff</div>
          </div>
        );
      })}
      <div
        style={{
          position: 'absolute',
          left: barX,
          top: barY,
          width: barW,
          height: barH,
          borderRadius: barR,
          opacity: bar,
          background: morph > 0 ? C.surface : 'rgba(10,122,255,0.10)',
          border: `1px solid ${morph > 0.5 ? C.border : 'rgba(10,122,255,0.45)'}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: morph > 0.5 ? 'flex-start' : 'center',
          padding: '0 36px',
          gap: 22,
          fontFamily: inter,
          fontSize: 28,
          color: C.text,
        }}
      >
        <span style={{fontFamily: mono, fontSize: 18, color: C.accent, letterSpacing: '0.1em'}}>COORDINATOR</span>
        <span style={{fontWeight: 600}}>Plain code owns state, permissions and every approval</span>
        <span style={{color: C.muted, fontSize: 22}}>· agents only propose</span>
      </div>
      <div
        style={{
          position: 'absolute',
          left: X0 + CW + GAP + CW / 2,
          width: CW + GAP,
          top: CY + CH + 250,
          opacity: mem * others,
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <div style={{display: 'flex', alignItems: 'center', gap: 14, padding: '14px 26px', borderRadius: 999, border: '1px solid rgba(10,122,255,0.5)', background: 'rgba(10,122,255,0.10)', fontFamily: inter, fontSize: 24, color: C.text}}>
          <svg width="26" height="26" viewBox="0 0 26 26">
            <ellipse cx="13" cy="6" rx="10" ry="4" fill="none" stroke={C.accent2} strokeWidth="2" />
            <path d="M3 6 V20 C3 22.2 7.5 24 13 24 C18.5 24 23 22.2 23 20 V6" fill="none" stroke={C.accent2} strokeWidth="2" />
          </svg>
          <b>Cognee</b> memory <span style={{color: C.muted}}>· Resolution writes, Payroll Prep recalls</span>
        </div>
      </div>
      <div style={{opacity: others}}>
        <CornerChip kind="ILLUSTRATION" text="architecture" />
      </div>
    </AbsoluteFill>
  );
};
