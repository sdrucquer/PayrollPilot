import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, Easing} from 'remotion';
import {Background} from '../components/Background';
import {CornerChip} from '../components/Chip';
import {ParticleMark} from '../components/ParticleMark';
import {C, display, inter, mono, s} from '../theme';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const ease = Easing.bezier(0.16, 1, 0.3, 1);

// ---------- Hook B-roll vignettes. All data here is fictional (no real business data). ----------
const Card: React.FC<{title: string; children: React.ReactNode; w?: number}> = ({title, children, w = 1180}) => (
  <div style={{width: w, borderRadius: 22, background: 'rgba(18,21,28,0.92)', border: `1px solid ${C.border}`, boxShadow: '0 50px 140px rgba(0,0,0,0.6)', overflow: 'hidden', fontFamily: inter}}>
    <div style={{padding: '18px 28px', borderBottom: `1px solid ${C.border}`, fontSize: 22, color: C.muted, display: 'flex', justifyContent: 'space-between'}}>
      <span>{title}</span>
      <span style={{fontFamily: mono, fontSize: 16, color: C.faint}}>fictional</span>
    </div>
    <div style={{padding: '10px 28px 22px'}}>{children}</div>
  </div>
);
const Row: React.FC<{cells: (string | {t: string; bad?: boolean; warn?: boolean})[]; head?: boolean}> = ({cells, head}) => (
  <div style={{display: 'grid', gridTemplateColumns: `repeat(${cells.length}, 1fr)`, padding: '14px 0', borderBottom: `1px solid ${C.border}`, fontSize: head ? 18 : 28, color: head ? C.faint : C.text, fontFamily: head ? inter : mono, letterSpacing: head ? '0.08em' : 0}}>
    {cells.map((c, i) => {
      const o = typeof c === 'string' ? {t: c} : c;
      return (
        <span key={i} style={{color: o.bad ? C.blocked : o.warn ? C.pending : undefined, textDecoration: o.bad ? 'underline wavy' : undefined}}>
          {o.t}
        </span>
      );
    })}
  </div>
);
const Timesheet = () => (
  <Card title="Timesheets · week 40">
    <Row head cells={['WORKER', 'DAY', 'IN – OUT', 'JOB']} />
    <Row cells={['Worker A', 'Mon', '7:58 – 16:12', 'Job 01']} />
    <Row cells={['Worker B', 'Tue', {t: '8:02 – ?', bad: true}, {t: 'timer running 31h', warn: true}]} />
    <Row cells={['Worker C', 'Wed', '2h14', {t: '— no job —', bad: true}]} />
    <Row cells={['Worker D', 'Thu', '7:30 – 17:10', {t: 'Job 02 ?', warn: true}]} />
  </Card>
);
const Bank = () => (
  <Card title="Bank feed · unreconciled">
    <Row head cells={['MERCHANT', 'AMOUNT', 'CATEGORY']} />
    <Row cells={['Hardware store', '−$84.12', {t: 'uncategorized', bad: true}]} />
    <Row cells={['Fuel', {t: '−$61.40 vs −$64.10', warn: true}, 'vehicles']} />
    <Row cells={['Dump fee', '−$182.50', {t: 'which job?', bad: true}]} />
    <Row cells={['Pavers + base', '−$600.00', {t: 'split ?', warn: true}]} />
  </Card>
);
const Bubble: React.FC<{who: string; t: string; d: number}> = ({who, t, d}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [d, d + 6], [0, 1], {...clamp, easing: ease});
  return (
    <div style={{opacity: p, transform: `translateY(${(1 - p) * 16}px)`, display: 'flex', gap: 18, alignItems: 'center', padding: '14px 18px', margin: '10px 0', borderRadius: 16, background: C.surface2, border: `1px solid ${C.border}`}}>
      <span style={{width: 46, height: 46, borderRadius: 99, background: C.chipBg, display: 'grid', placeItems: 'center', color: C.chipFg, fontSize: 18}}>{who[0]}</span>
      <span style={{fontSize: 26, color: C.text}}>
        <b style={{color: C.muted, fontWeight: 600}}>{who}</b> {t}
      </span>
    </div>
  );
};
const Messages = () => (
  <Card title="Messages · 14 unread" w={980}>
    <Bubble who="Ops lead" t="which job was tuesday’s?" d={0} />
    <Bubble who="Worker B" t="did u get my hours" d={5} />
    <Bubble who="Accountant" t="need the commission split by Fri" d={10} />
    <Bubble who="Worker C" t="forgot to clock out again 😬" d={15} />
  </Card>
);
const Sheet = () => (
  <Card title="payroll_FINAL_v7(2).xlsx">
    <Row head cells={['', 'HOURS', 'RATE', 'GROSS']} />
    <Row cells={['Worker A', '80.0', '—', {t: '#REF!', bad: true}]} />
    <Row cells={['Worker B', {t: '81.5 ?', warn: true}, '—', '—']} />
    <Row cells={['Commission', '', '', {t: '=SUM(?)', bad: true}]} />
    <Row cells={['Total', '', '', {t: '4,812.50 ≠ 4,790.00', bad: true}]} />
  </Card>
);

type Shot = {from: number; to: number; V: React.FC; slam?: string; zoom?: boolean};
const SHOTS: Shot[] = [
  {from: 0, to: 1.9, V: Timesheet},
  {from: 1.9, to: 3.6, V: Bank},
  {from: 3.6, to: 5.0, V: Messages},
  {from: 5.0, to: 6.4, V: Sheet},
  {from: 6.4, to: 8.6, V: Timesheet, slam: 'Missing hours.', zoom: true},
  {from: 8.6, to: 11.0, V: Bank, slam: 'Unassigned expenses.', zoom: true},
  {from: 11.0, to: 15.0, V: Sheet, slam: 'Numbers that don’t add up.', zoom: true},
];

export const Hook: React.FC = () => {
  const f = useCurrentFrame();
  const sec = f / 30;
  const shot = SHOTS.find((x) => sec >= x.from && sec < x.to) ?? SHOTS[SHOTS.length - 1];
  const local = f - s(shot.from);
  const len = s(shot.to) - s(shot.from);
  const freeze = interpolate(sec, [13.0, 13.4], [0, 1], clamp); // the "freeze" before the reveal
  const lf = freeze > 0 ? Math.min(local, s(13.0) - s(shot.from)) : local;
  const p = interpolate(lf, [0, 8], [0, 1], {...clamp, easing: ease});
  const drift = interpolate(lf, [0, len], [0, 1]);
  const scale = 1.3 * ((shot.zoom ? 1.12 : 1.04) - 0.06 * p + 0.04 * drift);
  const out = interpolate(sec, [14.4, 15], [1, 0], clamp);
  const V = shot.V;
  return (
    <AbsoluteFill style={{background: '#000', opacity: out}}>
      <AbsoluteFill style={{filter: `saturate(${1 - 0.9 * freeze}) brightness(${1 - 0.45 * freeze})`}}>
        <Background hue="warm" glow={0.7 * (1 - freeze)} />
        <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
          <div style={{transform: `scale(${scale}) translateX(${(shot.zoom ? -40 : 30) * drift}px) rotate(${shot.zoom ? -1.2 : 0.6}deg)`, filter: `blur(${(1 - p) * 10}px)`, opacity: shot.slam ? 0.42 : 1}}>
            <V />
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
      {shot.slam ? (
        <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
          <div style={{fontFamily: display, fontWeight: 800, fontSize: 128, letterSpacing: '-0.045em', color: C.text, transform: `scale(${1.15 - 0.15 * p})`, opacity: p, textShadow: '0 20px 80px rgba(0,0,0,0.8)'}}>{shot.slam}</div>
        </AbsoluteFill>
      ) : null}
      <AbsoluteFill style={{background: '#fff', opacity: interpolate(sec, [13.0, 13.08, 13.4], [0, 0.18, 0], clamp)}} />
      <CornerChip kind="ILLUSTRATION" text="fictional data" />
    </AbsoluteFill>
  );
};

// ---------- Reveal: particle mark on black, one quiet word (docs/DESIGN-DIRECTION.md). Local 0 = 15 s, 10 s long. ----------
export const Reveal: React.FC = () => {
  const f = useCurrentFrame();
  const word = interpolate(f, [s(3.4), s(4.4)], [0, 1], {...clamp, easing: ease});
  const tag = interpolate(f, [s(4.4), s(5.4)], [0, 1], {...clamp, easing: ease});
  const scale = interpolate(f, [0, s(10)], [1.06, 1], clamp);
  const glow = interpolate(f, [s(2), s(4)], [0, 1], clamp);
  const out = interpolate(f, [s(9.4), s(10)], [1, 0], clamp);
  return (
    <AbsoluteFill style={{opacity: out, background: '#000'}}>
      <AbsoluteFill style={{opacity: glow * 0.9, background: 'radial-gradient(30% 34% at 50% 42%, rgba(127,166,217,0.16), rgba(226,201,160,0.05) 55%, rgba(0,0,0,0) 75%)'}} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', transform: `scale(${scale})`}}>
        <div style={{marginTop: -60}}>
          <ParticleMark size={330} start={s(0.2)} dur={s(4.6)} />
        </div>
        <div style={{marginTop: 34, fontFamily: display, fontSize: 80, letterSpacing: '-0.03em', color: C.text, opacity: word, filter: `blur(${(1 - word) * 6}px)`}}>
          <span style={{fontWeight: 500}}>Payroll</span>
          <span style={{fontWeight: 700}}>Pilot</span>
        </div>
        <div style={{marginTop: 18, fontFamily: inter, fontSize: 30, color: C.muted, opacity: tag}}>Your AI-powered payroll operations team.</div>
      </AbsoluteFill>
      <CornerChip kind="ILLUSTRATION" />
    </AbsoluteFill>
  );
};
