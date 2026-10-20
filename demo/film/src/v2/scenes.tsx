import React from 'react';
import {AbsoluteFill, Img, interpolate, random, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Background, Card, ci, D, fontFamily, has, Headline, K, Label, Media, mono, Pill, useSpring, Window} from './ui';

type P = {dur: number; voAt: number; voDur: number};
const FPS = 30;

/* ---------- 01 HOOK: the flood ---------- */
const FRAGS: ((i: number) => React.ReactNode)[] = [
  () => <FragRow a="Worker A · Fri" b="8h 05m" tag="— no job" tagC={K.red} />,
  () => <Bubble text="did you log Friday?" />,
  () => <FragTile big="14" small="unread" c={K.red} />,
  () => <FragCell v="#REF!" />,
  () => <FragReceipt />,
  () => <FragRow a="Timer still running" b="11h 42m" tag="open" tagC={K.orange} />,
  () => <Bubble text="where's the receipt??" />,
  () => <FragSum />,
  () => <FragRow a="Disposal run" b="Job 03" tag="no parent job" tagC={K.orange} />,
  () => <Bubble text="which job was that on?" />,
  () => <FragTile big="?" small="who approved" c={K.orange} />,
  () => <FragRow a="Worker C · Tue" b="—" tag="missing hours" tagC={K.red} />,
];
const FragBox: React.FC<{children: React.ReactNode; w?: number}> = ({children, w}) => (
  <div style={{background: '#fff', borderRadius: 18, boxShadow: K.shadowBig, padding: '14px 18px', fontFamily, color: K.text, width: w}}>{children}</div>
);
const FragRow: React.FC<{a: string; b: string; tag: string; tagC: string}> = ({a, b, tag, tagC}) => (
  <FragBox w={360}>
    <div style={{display: 'flex', justifyContent: 'space-between', fontSize: 20, fontWeight: 600}}><span>{a}</span><span style={{color: K.muted}}>{b}</span></div>
    <div style={{marginTop: 8}}><Pill color={tagC} bg={tagC === K.red ? K.redTint : K.orangeTint} size={15}>{tag}</Pill></div>
  </FragBox>
);
const Bubble: React.FC<{text: string}> = ({text}) => (
  <div style={{background: '#E9E9EB', color: K.text, borderRadius: '22px 22px 22px 6px', padding: '12px 18px', fontFamily, fontSize: 22, boxShadow: K.shadow}}>{text}</div>
);
const FragTile: React.FC<{big: string; small: string; c: string}> = ({big, small, c}) => (
  <FragBox w={170}>
    <div style={{fontSize: 46, fontWeight: 800, color: c, letterSpacing: '-0.03em'}}>{big}</div>
    <div style={{fontSize: 16, color: K.muted}}>{small}</div>
  </FragBox>
);
const FragCell: React.FC<{v: string}> = ({v}) => (
  <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 90px)', background: '#fff', borderRadius: 10, overflow: 'hidden', boxShadow: K.shadowBig, fontFamily: mono, fontSize: 18}}>
    {['1,240', '—', '880', '312', v, '—'].map((c, i) => (
      <div key={i} style={{padding: '10px 8px', borderRight: `1px solid ${K.line}`, borderBottom: `1px solid ${K.line}`, color: c === v ? K.red : K.text2, fontWeight: c === v ? 700 : 400, background: c === v ? K.redTint : '#fff'}}>{c}</div>
    ))}
  </div>
);
const FragReceipt: React.FC = () => (
  <FragBox w={220}>
    <div style={{fontSize: 15, color: K.muted, letterSpacing: '0.08em'}}>RECEIPT</div>
    <div style={{fontSize: 30, fontWeight: 700, margin: '4px 0'}}>$86.40</div>
    <Pill color={K.orangeText} bg={K.orangeTint} size={14}>uncategorized</Pill>
  </FragBox>
);
const FragSum: React.FC = () => (
  <FragBox w={250}>
    <div style={{fontFamily: mono, fontSize: 22}}>$4,812.00</div>
    <div style={{fontFamily: mono, fontSize: 22, color: K.red}}>≠ $4,640.00</div>
  </FragBox>
);

export const Hook: React.FC<P> = ({dur, voAt, voDur}) => {
  const f = useCurrentFrame();
  const total = dur * FPS;
  const rushAt = total - 26;
  const N = 46;
  // Phrase cues from word position in the VO line.
  const words = 19;
  const cue = (wi: number) => (voAt + (wi / words) * voDur) * FPS;
  const phrases = [
    {t: cue(0), text: 'Running payroll shouldn’t mean chasing down your whole team.', size: 58},
    {t: cue(9), text: 'Missing hours.', size: 132},
    {t: cue(11), text: 'Unassigned expenses.', size: 132},
    {t: cue(13), text: 'Numbers that don’t add up.', size: 132},
  ];
  const cur = phrases.reduce((a, p, i) => (f >= p.t ? i : a), 0);
  const rush = Math.max(0, f - rushAt);
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Background tint={1.2} />
      <AbsoluteFill style={{perspective: 1100, perspectiveOrigin: '50% 50%'}}>
        {Array.from({length: N}).map((_, i) => {
          const born = (i / N) * (rushAt * 0.85);
          if (f < born) return null;
          const age = f - born;
          const ang = random(`a${i}`) * Math.PI * 2;
          const rad = 260 + random(`r${i}`) * 720;
          const x = Math.cos(ang) * rad * 1.35;
          const y = Math.sin(ang) * rad * 0.75;
          const z = -2600 + age * (9 + random(`s${i}`) * 7) + rush * rush * 3.2;
          const op = ci(age, 0, 14) * ci(z, 700, 1000, 1, 0);
          const rot = (random(`t${i}`) - 0.5) * 22 + Math.sin((f + i * 20) / 40) * 3;
          return (
            <div key={i} style={{position: 'absolute', left: '50%', top: '50%', transform: `translate(-50%,-50%) translate3d(${x}px, ${y}px, ${z}px) rotate(${rot}deg)`, opacity: op}}>
              {FRAGS[i % FRAGS.length](i)}
            </div>
          );
        })}
      </AbsoluteFill>
      {/* center phrase */}
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', pointerEvents: 'none'}}>
        {phrases.map((p, i) => {
          if (i !== cur || f < p.t) return null;
          const a = f - p.t;
          const s = i === 0 ? 1 : interpolate(a, [0, 7, 12], [1.5, 0.97, 1], {extrapolateRight: 'clamp'});
          const op = ci(a, 0, 5) * ci(rush, 0, 8, 1, 0);
          return (
            <div key={i} style={{fontFamily, fontSize: p.size, fontWeight: 800, letterSpacing: '-0.045em', color: K.text, textAlign: 'center', maxWidth: 1500, lineHeight: 1.05, transform: `scale(${s})`, opacity: op, textShadow: '0 0 40px #F5F5F8, 0 0 80px #F5F5F8, 0 0 120px #F5F5F8'}}>
              {p.text}
            </div>
          );
        })}
      </AbsoluteFill>
      {/* rush into a blue point */}
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
        <div style={{width: 30, height: 30, borderRadius: 30, background: K.brand, transform: `scale(${ci(rush, 8, 26, 0, 1.4)})`, boxShadow: `0 0 ${ci(rush, 8, 26, 0, 120)}px ${K.brand}`}} />
      </AbsoluteFill>
      <Label kinds={['illustration']} note="fictional data" />
    </AbsoluteFill>
  );
};

/* ---------- 02 REVEAL ---------- */
export const Reveal: React.FC<P> = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const zoom = ci(f, 0, 38, 3.2, 1);
  const open = ci(f, 14, 46, 74, 0);
  const streak = ci(f, 0, 16, -40, 140);
  const tag = useSpring(48);
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', overflow: 'hidden'}}>
      <Background tint={0.8} />
      <div style={{position: 'absolute', left: `${streak}%`, top: '50%', width: 900, height: 6, background: `linear-gradient(90deg, transparent, ${K.brand}, transparent)`, transform: 'translateY(-50%) rotate(-18deg)', opacity: ci(f, 0, 4) * ci(f, 12, 18, 1, 0)}} />
      <div style={{width: 1180, height: 590, transform: `scale(${zoom})`, transformOrigin: '17% 50%', clipPath: `inset(0 ${open}% 0 0)`}}>
        <Img src={staticFile('brand/wordmark-t.png')} style={{width: '100%', height: '100%'}} />
      </div>
      <div style={{position: 'absolute', top: 760, fontFamily, fontSize: 46, fontWeight: 600, letterSpacing: '-0.02em', color: K.text2, opacity: tag, transform: `translateY(${(1 - tag) * 16}px)`}}>
        Your AI payroll team.
      </div>
      <Label kinds={['illustration']} />
      <span style={{display: 'none'}}>{fps}</span>
    </AbsoluteFill>
  );
};

/* ---------- 03 PULL ---------- */
const SOURCES = [
  {n: 'Jobber', l: 'J', c: '#2E9E58', what: 'jobs · time entries'},
  {n: 'QuickBooks', l: 'qb', c: '#2CA01C', what: 'expenses · costs'},
  {n: 'Gusto', l: 'G', c: '#F45D48', what: 'workers · pay schedule'},
];
export const Pull: React.FC<P> = ({dur}) => {
  const f = useCurrentFrame();
  const target = {x: 1290, y: 520};
  const n = useSpring(40);
  const count = Math.round(ci(f, 40, 40 + 3.2 * FPS, 0, 42));
  return (
    <AbsoluteFill>
      <Background />
      <Headline kicker="Step 1 · Gather" title="Every record for the pay period, in one place." />
      {SOURCES.map((s, i) => {
        const p = useSpring(8 + i * 6);
        const y = 330 + i * 200;
        return (
          <React.Fragment key={s.n}>
            <Card style={{position: 'absolute', left: 140, top: y, width: 430, height: 150, display: 'flex', alignItems: 'center', gap: 22, padding: '0 28px', opacity: p, transform: `translateX(${(1 - p) * -80}px)`}}>
              <div style={{width: 76, height: 76, borderRadius: 20, background: s.c, color: '#fff', fontSize: 34, fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{s.l}</div>
              <div>
                <div style={{fontSize: 30, fontWeight: 700, letterSpacing: '-0.02em'}}>{s.n}</div>
                <div style={{fontSize: 19, color: K.muted}}>{s.what}</div>
              </div>
              <div style={{marginLeft: 'auto', width: 12, height: 12, borderRadius: 12, background: K.green, boxShadow: `0 0 0 ${4 + Math.sin(f / 6 + i) * 3}px ${K.greenTint}`}} />
            </Card>
            {/* streaming records */}
            {Array.from({length: 9}).map((_, k) => {
              const start = 24 + i * 6 + k * 9;
              const t = ci(f, start, start + 34, 0, 1);
              if (t <= 0 || t >= 1) return null;
              const sx = 580;
              const sy = y + 75;
              const cx = (sx + target.x) / 2;
              const cy = sy + (target.y - sy) * 0.2 - 60;
              const bx = (1 - t) * (1 - t) * sx + 2 * (1 - t) * t * cx + t * t * (target.x - 260);
              const by = (1 - t) * (1 - t) * sy + 2 * (1 - t) * t * cy + t * t * target.y;
              return <div key={k} style={{position: 'absolute', left: bx, top: by, width: 46, height: 12, borderRadius: 6, background: s.c, opacity: 0.85 * Math.sin(t * Math.PI), transform: 'translate(-50%,-50%)'}} />;
            })}
          </React.Fragment>
        );
      })}
      <Card style={{position: 'absolute', left: target.x - 260, top: 330, width: 560, height: 550, padding: 40, opacity: n, transform: `scale(${0.9 + 0.1 * n})`}}>
        <div style={{fontSize: 16, fontWeight: 700, letterSpacing: '0.1em', color: K.muted}}>SEP 28 – OCT 11 · PAYDAY FRI, OCT 16</div>
        <div style={{fontSize: 44, fontWeight: 800, letterSpacing: '-0.03em', marginTop: 14}}>Pay period</div>
        <div style={{marginTop: 30, display: 'grid', gap: 18}}>
          {[
            [`${count}`, 'timesheets'],
            [`${Math.min(4, Math.round(count / 10))}`, 'workers'],
            [`${Math.min(3, Math.round(count / 14))}`, 'jobs'],
          ].map(([v, l]) => (
            <div key={l} style={{display: 'flex', alignItems: 'baseline', gap: 14, background: K.inset, borderRadius: 18, padding: '16px 22px'}}>
              <span style={{fontSize: 46, fontWeight: 800, fontVariantNumeric: 'tabular-nums', letterSpacing: '-0.03em'}}>{v}</span>
              <span style={{fontSize: 24, color: K.muted}}>{l}</span>
            </div>
          ))}
        </div>
      </Card>
      <Label kinds={['synthetic']} note="Pilot Co" />
      <span style={{display: 'none'}}>{dur}</span>
    </AbsoluteFill>
  );
};

/* ---------- 04 AUDIT + ROUTE ---------- */
const ROWS = [
  ['Worker A', 'Sep 29', '7h 50m', 'Job 01', ''],
  ['Worker B', 'Sep 30', '8h 10m', 'Job 02', ''],
  ['Worker A', 'Oct 1', '2h 14m', 'Job 01', 'Scheduled on Job 02'],
  ['Worker C', 'Oct 1', '6h 30m', 'Job 02', ''],
  ['Worker D', 'Oct 2', '3h 05m', 'Job 03', 'Off-site, no parent job'],
  ['Worker B', 'Oct 2', '8h 00m', 'Job 01', ''],
  ['Worker C', 'Oct 3', '7h 45m', 'Job 02', ''],
];
export const Audit: React.FC<P> = ({dur}) => {
  const f = useCurrentFrame();
  const scan = ci(f, 12, 12 + 2.2 * FPS, 0, 1);
  const people = [
    {n: 'Ops lead', y: 360, c: K.blue},
    {n: 'Owner', y: 720, c: '#8E44D9'},
  ];
  const issues = [
    {t: 'Shift on Oct 1 is on Job 01, scheduled on Job 02', who: 0, at: 2.6},
    {t: 'Job 03 disposal run: which parent job?', who: 0, at: 3.1},
    {t: 'Manager pool overhead split: your decision', who: 1, at: 3.6},
  ];
  const merge = ci(f, 5.4 * FPS, 6.4 * FPS);
  return (
    <AbsoluteFill>
      <Background />
      <Headline kicker="Step 2 · Audit" title="Finds what’s missing. Knows who to ask." />
      <Card style={{position: 'absolute', left: 90, top: 260, width: 780, padding: '18px 0', overflow: 'hidden'}}>
        {ROWS.map((r, i) => {
          const flagged = !!r[4] && scan > (i + 0.5) / ROWS.length;
          return (
            <div key={i} style={{display: 'grid', gridTemplateColumns: '170px 120px 120px 1fr', alignItems: 'center', padding: '16px 30px', fontSize: 22, borderBottom: i < ROWS.length - 1 ? `1px solid ${K.line}` : 'none', background: flagged ? K.orangeTint : 'transparent'}}>
              <span style={{fontWeight: 600}}>{r[0]}</span>
              <span style={{color: K.muted}}>{r[1]}</span>
              <span style={{fontVariantNumeric: 'tabular-nums'}}>{r[2]}</span>
              <span style={{display: 'flex', gap: 10, alignItems: 'center'}}>
                {r[3]}
                {flagged ? <Pill color={K.orangeText} bg="#FFE7C7" size={15}>{r[4]}</Pill> : null}
              </span>
            </div>
          );
        })}
        <div style={{position: 'absolute', left: 0, right: 0, top: 18 + scan * 7 * 61, height: 4, background: `linear-gradient(90deg, transparent, ${K.blue}, transparent)`, opacity: scan > 0 && scan < 1 ? 1 : 0, boxShadow: `0 0 24px ${K.blue}`}} />
      </Card>
      {people.map((p, i) => {
        const s = useSpring(2.2 * FPS + i * 4);
        return (
          <div key={p.n} style={{position: 'absolute', left: 1620, top: p.y, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, opacity: s, transform: `scale(${0.7 + 0.3 * s})`, fontFamily}}>
            <div style={{width: 110, height: 110, borderRadius: 110, background: p.c, color: '#fff', fontSize: 44, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: `0 0 0 10px ${p.c}22`}}>{p.n[0]}</div>
            <div style={{fontSize: 24, fontWeight: 700, color: K.text}}>{p.n}</div>
          </div>
        );
      })}
      {issues.map((it, i) => {
        const a = ci(f, it.at * FPS, it.at * FPS + 18);
        const p = people[it.who];
        const baseY = 300 + i * 150;
        const toMerged = it.who === 0 ? merge : 0;
        const y = interpolate(toMerged, [0, 1], [baseY, 330 + (i === 0 ? 0 : 70)]);
        const x = 950 + a * 20;
        return (
          <React.Fragment key={i}>
            <svg style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 1080, pointerEvents: 'none'}}>
              <path d={`M ${x + 560} ${y + 50} C ${x + 620} ${y + 50}, 1560 ${p.y + 55}, 1620 ${p.y + 55}`} stroke={p.c} strokeWidth={3} fill="none" strokeDasharray="600" strokeDashoffset={600 * (1 - ci(f, it.at * FPS + 10, it.at * FPS + 30))} opacity={0.55} />
            </svg>
            <Card style={{position: 'absolute', left: x, top: y, width: 560, padding: '20px 24px', opacity: a, transform: `translateX(${(1 - a) * 60}px)`, borderRadius: 22}}>
              <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
                <Pill color={K.orangeText} bg={K.orangeTint} size={14}>{it.who === 0 ? 'Needs an answer' : 'Policy decision'}</Pill>
                <span style={{fontSize: 16, color: K.muted}}>→ {p.n}</span>
              </div>
              <div style={{fontSize: 22, fontWeight: 600, marginTop: 8, lineHeight: 1.25}}>{it.t}</div>
            </Card>
          </React.Fragment>
        );
      })}
      {merge > 0.5 ? (
        <div style={{position: 'absolute', left: 1000, top: 520, opacity: ci(f, 6.2 * FPS, 6.8 * FPS)}}>
          <Pill color={K.blue2} bg={K.tint} size={20}>2 questions · 1 grouped message to the Ops lead</Pill>
        </div>
      ) : null}
      <Label kinds={['synthetic']} note="seeded issues" />
      <span style={{display: 'none'}}>{dur}</span>
    </AbsoluteFill>
  );
};

/* ---------- 05–11 LIVE LOOP: app + Band + phone ---------- */
type Msg = {who: 'audit' | 'resolution' | 'payroll' | 'owner'; time?: string; text: string; to?: string; seg: string; at: number; decision?: boolean};
const AG = {
  audit: {n: 'pp-audit', c: '#7B61FF'},
  resolution: {n: 'pp-resolution', c: '#C99A06'},
  payroll: {n: 'pp-payroll', c: '#E5484D'},
  owner: {n: 'Owner', c: K.green},
} as const;
// Exact Band room text (captured 2:16 PM), owner's name replaced.
const MSGS: Msg[] = [
  {who: 'audit', text: 'please take this case.', to: 'resolution', seg: '05', at: 0.8},
  {who: 'resolution', time: '1:16 PM', text: '[handoff.accepted] resolution owns exc_d06fba51f7. Drafting a question; send waits for owner approval.', to: 'audit', seg: '05', at: 3.2},
  {who: 'resolution', time: '1:16 PM', text: '[decision.requested] Owner decision: send 2 question(s) to the allowlisted test handle. Reply ‘approve msg_batch_95601f6f3ab8’.', to: 'owner', seg: '06', at: 0.6},
  {who: 'owner', time: '1:32 PM', text: 'approve msg_batch_95601f6f3ab8', to: 'resolution', seg: '06', at: 3.4, decision: true},
  {who: 'resolution', time: '2:07 PM', text: '[correction.applied] corr_a647520203 (job_allocation) applied locally; recompute readiness.', to: 'payroll', seg: '10', at: 3.6},
  {who: 'payroll', time: '2:07 PM', text: '[handoff.accepted] payroll recomputing readiness for exc_611be6d68e.', to: 'resolution', seg: '11', at: 0.6},
];
// Exact iMessage thread (owner's phone, test mode); a personal name in a reply is masked.
type Txt = {me: boolean; text: string; seg: string; at: number; tag?: 'ambiguous' | 'answered'};
const TEXTS: Txt[] = [
  {me: false, seg: '07', at: 1.0, text: 'PayrollPilot (test) for Pilot Co: 2 quick payroll checks.\n1) Already-paid shift on 2026-10-01 is on Job 01 (lawn install) but scheduled on Job 02 (patio build). Which job was this work actually on?\n2) Job 03 (disposal run, off-site) has labor or costs but no revenue and no parent job link. Which parent job is this off-site work under?'},
  {me: true, seg: '07', at: 4.6, text: '1: Job 02\n\n2. It’s under •••’s job', tag: 'answered'},
  {me: true, seg: '08', at: 0.6, text: 'yes', tag: 'ambiguous'},
  {me: false, seg: '08', at: 4.2, text: 'Thanks. To be sure for Pilot Co:\n1) Job 03 (disposal run, off-site) has labor or costs but no revenue and no parent job link. Which parent job is this off-site work under?'},
  {me: true, seg: '09', at: 0.8, text: '03', tag: 'ambiguous'},
  {me: true, seg: '09', at: 2.4, text: 'Job 02 — the patio job. Job 03’s disposal run belongs to Job 02.', tag: 'answered'},
];

const BandPanel: React.FC<{t: number; segStart: (id: string) => number}> = ({t, segStart}) => {
  const shown = MSGS.filter((m) => t >= segStart(m.seg) + m.at);
  const last = shown[shown.length - 1];
  const lastAt = last ? segStart(last.seg) + last.at : 0;
  const pulse = ci(t, lastAt, lastAt + 1.2, 1, 0);
  const order = ['audit', 'resolution', 'payroll', 'owner'] as const;
  const ax = (k: string) => 70 + order.indexOf(k as never) * 140;
  return (
    <Card style={{position: 'absolute', left: 1235, top: 150, width: 620, height: 820, overflow: 'hidden', borderRadius: 26}}>
      <div style={{padding: '22px 26px 10px', display: 'flex', alignItems: 'center', gap: 10}}>
        <div style={{fontSize: 15, fontWeight: 700, letterSpacing: '0.1em', color: K.muted}}>BAND · PRODUCT ROOM</div>
        <div style={{marginLeft: 'auto'}}><Pill color={K.green} bg={K.greenTint} size={13}>live room</Pill></div>
      </div>
      <div style={{position: 'relative', height: 120, margin: '0 10px'}}>
        {order.map((k) => {
          const active = last && (last.who === k || last.to === k) ? pulse : 0;
          return (
            <div key={k} style={{position: 'absolute', left: ax(k) - 36, top: 8, width: 72, textAlign: 'center'}}>
              <div style={{width: 60, height: 60, margin: '0 auto', borderRadius: 60, background: AG[k].c, color: '#fff', fontSize: 24, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: `0 0 0 ${6 + active * 10}px ${AG[k].c}${active > 0.05 ? '33' : '11'}`, transform: `scale(${1 + active * 0.08})`}}>
                {k === 'owner' ? 'O' : AG[k].n.split('-')[1][0].toUpperCase()}
              </div>
              <div style={{fontSize: 14, color: K.text2, marginTop: 6, fontWeight: 600, whiteSpace: 'nowrap', marginLeft: -20, marginRight: -20}}>{AG[k].n}</div>
            </div>
          );
        })}
        {last && last.to ? (
          (() => {
            const p = ci(t, lastAt, lastAt + 0.7);
            const x0 = ax(last.who);
            const x1 = ax(last.to);
            const x = x0 + (x1 - x0) * p;
            return <div style={{position: 'absolute', left: x - 9, top: 30, width: 18, height: 18, borderRadius: 18, background: AG[last.who].c, boxShadow: `0 0 24px ${AG[last.who].c}`, opacity: p < 1 ? 1 : 0}} />;
          })()
        ) : null}
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, top: 170, padding: '0 22px 22px', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', gap: 14}}>
        {shown.slice(-4).map((m) => {
          const a = ci(t, segStart(m.seg) + m.at, segStart(m.seg) + m.at + 0.45);
          return (
            <div key={m.text} style={{display: 'flex', gap: 12, opacity: a, transform: `translateY(${(1 - a) * 24}px)`, background: m.decision ? K.greenTint : K.inset, borderRadius: 18, padding: '14px 16px', boxShadow: m.decision ? `0 0 0 2px ${K.green}55` : 'none'}}>
              <div style={{width: 34, height: 34, flexShrink: 0, borderRadius: 34, background: AG[m.who].c, color: '#fff', fontSize: 15, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{m.who === 'owner' ? 'O' : AG[m.who].n.split('-')[1][0].toUpperCase()}</div>
              <div style={{minWidth: 0}}>
                <div style={{fontSize: 16, fontWeight: 700}}>
                  {AG[m.who].n} <span style={{fontWeight: 400, color: K.faint, fontSize: 14}}>{m.time ?? ''}</span>
                  {m.decision ? <span style={{marginLeft: 8}}><Pill color={K.green} bg="#fff" size={12}>human decision</Pill></span> : null}
                </div>
                <div style={{fontSize: 17, lineHeight: 1.35, color: K.text2, marginTop: 3}}>
                  {m.to ? <span style={{background: `${AG[m.to].c}22`, color: AG[m.to].c === K.green ? K.green : K.text, borderRadius: 6, padding: '1px 6px', marginRight: 6, fontWeight: 600, display: 'inline-block', transform: `scale(${1 + 0.12 * Math.sin(Math.min(1, a) * Math.PI)})`}}>@{AG[m.to].n}</span> : null}
                  {m.text}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};

const Phone: React.FC<{t: number; segStart: (id: string) => number; show: number}> = ({t, segStart, show}) => {
  const shown = TEXTS.filter((m) => t >= segStart(m.seg) + m.at);
  return (
    <div style={{position: 'absolute', left: 1290, top: 110, width: 470, height: 900, borderRadius: 64, background: '#111', padding: 14, boxShadow: K.shadowBig, transform: `translateY(${(1 - show) * 1000}px) rotate(${(1 - show) * 6}deg)`}}>
      <div style={{width: '100%', height: '100%', borderRadius: 52, background: '#fff', overflow: 'hidden', position: 'relative', fontFamily}}>
        <div style={{height: 120, borderBottom: `1px solid ${K.line}`, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-end', paddingBottom: 10, background: '#F9F9FB'}}>
          <Img src={staticFile('brand/mark-t.png')} style={{width: 46, height: 46, objectFit: 'contain'}} />
          <div style={{fontSize: 15, fontWeight: 600, marginTop: 4}}>Payroll Pilot</div>
        </div>
        <div style={{position: 'absolute', left: 0, right: 0, top: 120, bottom: 0, padding: 14, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', gap: 8}}>
          {shown.map((m) => {
            const a = ci(t, segStart(m.seg) + m.at, segStart(m.seg) + m.at + 0.35);
            const tagT = segStart(m.seg) + m.at + 0.9;
            return (
              <div key={m.text} style={{alignSelf: m.me ? 'flex-end' : 'flex-start', maxWidth: '86%', opacity: a, transform: `scale(${0.85 + 0.15 * a})`, transformOrigin: m.me ? '100% 100%' : '0% 100%', position: 'relative'}}>
                <div style={{background: m.me ? '#0A84FF' : '#E9E9EB', color: m.me ? '#fff' : K.text, borderRadius: 20, padding: '9px 13px', fontSize: 15.5, lineHeight: 1.3, whiteSpace: 'pre-wrap'}}>{m.text}</div>
                {m.tag && t > tagT ? (
                  <div style={{position: 'absolute', right: m.me ? 6 : undefined, left: m.me ? undefined : 6, top: -14, transform: `scale(${ci(t, tagT, tagT + 0.25, 1.6, 1)}) rotate(-4deg)`, opacity: ci(t, tagT, tagT + 0.15)}}>
                    <Pill color="#fff" bg={m.tag === 'ambiguous' ? K.orange : K.green} size={13}>{m.tag === 'ambiguous' ? 'Ambiguous' : 'Answered'}</Pill>
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

const MoneyMove: React.FC<{t: number}> = ({t}) => {
  const p = ci(t, 1.6, 3.4);
  const show = ci(t, 0.2, 0.8);
  const fmt = (c: number) => `${c < 0 ? '−' : '+'}$${(Math.abs(c) / 100).toFixed(2)}`;
  return (
    <Card style={{position: 'absolute', left: 170, top: 330, width: 980, padding: 36, opacity: show, transform: `translateY(${(1 - show) * 40}px)`, boxShadow: K.shadowBig}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
        <div style={{fontSize: 15, fontWeight: 700, letterSpacing: '0.1em', color: K.muted}}>PROPOSED CORRECTION · CORR_A647520203</div>
        <div style={{marginLeft: 'auto'}}><Pill color={K.green} bg={K.greenTint} size={18}>Wages: $0.00 change</Pill></div>
      </div>
      <div style={{fontSize: 24, marginTop: 10, color: K.text2}}>Oct 1 shift (te_0014): Job 01 → Job 02</div>
      <div style={{position: 'relative', display: 'flex', gap: 40, marginTop: 26}}>
        {[
          ['Job 01 · lawn install', -20000],
          ['Job 02 · patio build', 20000],
        ].map(([n, c], i) => (
          <div key={n as string} style={{flex: 1, background: K.inset, borderRadius: 22, padding: 26}}>
            <div style={{fontSize: 20, color: K.muted}}>{n}</div>
            <div style={{fontSize: 60, fontWeight: 800, letterSpacing: '-0.04em', fontVariantNumeric: 'tabular-nums', color: p > 0.02 ? (i === 0 ? K.red : K.green) : K.faint}}>{fmt((c as number) * p || (i === 0 ? -0 : 0))}</div>
            <div style={{fontSize: 17, color: K.muted}}>job labor cost</div>
          </div>
        ))}
        <div style={{position: 'absolute', top: 70, left: `${8 + p * 54}%`, width: 120, height: 54, borderRadius: 999, background: K.blue, color: '#fff', fontWeight: 700, fontSize: 22, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 12px 30px -8px rgba(10,122,255,.8)', opacity: p > 0 && p < 1 ? 1 : 0, transform: `translateY(${-Math.sin(p * Math.PI) * 50}px)`}}>$200</div>
      </div>
    </Card>
  );
};

const Activity: React.FC<{t: number}> = ({t}) => {
  const rows = [
    {at: 0.2, i: '✓', c: K.green, txt: 'Approved in the Band room', time: '1:32:23 PM'},
    {at: 1.0, i: '↑', c: K.blue, txt: 'Sent by iMessage · Photon spc-msg-b022a2ba…', time: '1:32:24 PM'},
    {at: 4.6, i: '↓', c: K.orange, txt: 'Ops lead replied', time: '1:32:55 PM', test: true},
  ];
  return (
    <Card style={{position: 'absolute', left: 150, top: 640, width: 1000, padding: '18px 26px', boxShadow: K.shadowBig, opacity: ci(t, 0, 0.4)}}>
      {rows.map((r) => {
        const a = ci(t, r.at, r.at + 0.4);
        return (
          <div key={r.txt} style={{display: 'flex', alignItems: 'center', gap: 16, padding: '10px 0', opacity: a, transform: `translateX(${(1 - a) * 30}px)`}}>
            <div style={{width: 36, height: 36, borderRadius: 11, background: `${r.c}1A`, color: r.c, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 18}}>{r.i}</div>
            <div style={{fontSize: 22, flex: 1}}>{r.txt} {r.test ? <Pill color={K.orangeText} bg={K.orangeTint} size={13}>test reply</Pill> : null}</div>
            <div style={{fontSize: 17, color: K.faint}}>{r.time}</div>
          </div>
        );
      })}
    </Card>
  );
};

const APP_CROP = {x: 560, y: 0, w: 800, h: 1080};
const LOOP: {id: string; clip?: string; clipPan?: [number, number]; startAt?: number; mock: string; pan: [number, number]; zoom: [number, number]; head: string; kicker: string; labels: ('live' | 'synthetic' | 'test' | 'mockup' | 'earlier')[]}[] = [
  {id: '05', clip: '01-home-in-progress.mp4', clipPan: [0, 0.3], mock: 'mock-home.png', pan: [0, 0.12], zoom: [1, 1.04], kicker: 'Step 3 · Ask', head: 'One grouped question, drafted for you.', labels: ['live', 'synthetic']},
  {id: '06', clip: '02-approve-and-send.mp4', clipPan: [0.35, 1], mock: 'mock-home.png', pan: [0.14, 0.16], zoom: [1.04, 1.16], kicker: 'Step 3 · Approve', head: 'You approve the exact text.', labels: ['live']},
  {id: '07', clip: '02-approve-and-send.mp4', clipPan: [1, 1], startAt: 13, mock: 'mock-home.png', pan: [0.16, 0.16], zoom: [1.1, 1.1], kicker: 'Step 4 · Message', head: 'A real iMessage to the person who knows.', labels: ['live', 'test']},
  {id: '08', clip: '03-reply-ambiguous.mp4', mock: 'mock-home.png', pan: [0.16, 0.3], zoom: [1.06, 1], kicker: 'Step 4 · Clarify', head: '“yes” isn’t an answer.', labels: ['live', 'test']},
  {id: '09', clip: '04-clarify-approve.mp4', mock: 'mock-home.png', pan: [0.3, 0.36], zoom: [1, 1], kicker: 'Step 4 · Answer', head: 'A clear answer comes back.', labels: ['live', 'test']},
  {id: '10', clip: '05-answer-and-correction.mp4', mock: 'mock-home.png', pan: [0.4, 0.45], zoom: [1, 1], kicker: 'Step 5 · Correct', head: 'The fix, with its impact.', labels: ['live', 'synthetic']},
  {id: '11', clip: '06-approve-apply-readiness.mp4', mock: 'mock-home.png', pan: [0, 0], zoom: [1.12, 1.12], kicker: 'Step 5 · Recalculate', head: 'Only what changed, changes.', labels: ['live', 'synthetic']},
];

export const Loop: React.FC<{start: number}> = ({start}) => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const segStart = (id: string) => {
    const s = D.timeline.find((x) => x.id === id);
    return s ? s.from - start : 0;
  };
  const curIdx = LOOP.reduce((a, b, i) => (t >= segStart(b.id) ? i : a), 0);
  const cur = LOOP[curIdx];
  const segT = t - segStart(cur.id);
  const segDur = D.timeline.find((x) => x.id === cur.id)?.dur ?? 8;
  const phoneShow = ci(t, segStart('07') - 0.2, segStart('07') + 0.6) * ci(t, segStart('10') - 0.6, segStart('10') + 0.2, 1, 0);
  const W = 1100;
  const H = 780;
  const clip = cur.clip && D.clips[cur.clip];
  const labels = clip ? cur.labels : (['mockup', ...cur.labels.filter((l) => l === 'test')] as const);
  return (
    <AbsoluteFill>
      <Background />
      {LOOP.map((b, i) => (i === curIdx ? <Headline key={b.id} kicker={b.kicker} title={b.head} x={90} y={40} size={44} delay={0} /> : null))}
      <Window x={70} y={170} w={W} h={H} title="PayrollPilot · Pilot Co" tilt={-0.6}>
        {LOOP.map((b, i) => {
          if (i !== curIdx) return null;
          const c = b.clip && D.clips[b.clip];
          const from = Math.round(segStart(b.id) * FPS);
          return (
            <Sequence key={b.id} from={0} layout="none">
              <div style={{position: 'absolute', inset: 0, opacity: ci(segT, 0, 0.35)}}>
                {c && c.kind === 'video' ? (
                  <Media src={`a/clips/${b.clip}`} w={c.w ?? 1920} h={c.h ?? 1080} boxW={W} boxH={H - 44} dur={segDur} video clipDur={c.dur} fit="width" crop={APP_CROP} pan={b.clipPan ?? [0, 0.3]} startAt={b.startAt} />
                ) : (
                  <Media src={`a/${b.mock}`} w={D.files[b.mock]?.w ?? 2560} h={D.files[b.mock]?.h ?? 3000} boxW={W} boxH={H - 44} dur={segDur} pan={b.pan} zoom={b.zoom} origin="50% 20%" />
                )}
              </div>
              <span style={{display: 'none'}}>{from}</span>
            </Sequence>
          );
        })}
      </Window>
      {cur.id === '07' ? <Activity t={segT} /> : null}
      {cur.id === '10' ? <MoneyMove t={segT} /> : null}
      {cur.id === '11' && !clip ? <Readiness t={segT} /> : null}
      <div style={{opacity: 1 - phoneShow}}>
        <BandPanel t={t} segStart={segStart} />
      </div>
      {phoneShow > 0 ? <Phone t={t} segStart={segStart} show={phoneShow} /> : null}
      <Label kinds={labels as never} x={1240} y={40} note={phoneShow > 0.5 ? 'owner’s phone · test mode' : 'Band room · exact messages'} />
    </AbsoluteFill>
  );
};

const Readiness: React.FC<{t: number}> = ({t}) => {
  const lines = [
    {n: 'Employee wages', v: 'unchanged', changes: false},
    {n: 'Job costs · Job 02', v: 'updated · verified', changes: true},
    {n: 'Commission, tips, manager pool', v: 'unchanged', changes: false},
  ];
  const p = ci(t, 2.2, 3.0);
  return (
    <Card style={{position: 'absolute', left: 190, top: 420, width: 940, padding: '22px 30px', boxShadow: K.shadowBig, opacity: ci(t, 0.3, 0.8)}}>
      <div style={{fontSize: 15, fontWeight: 700, letterSpacing: '0.1em', color: K.muted, marginBottom: 6}}>READINESS AFTER APPROVE &amp; APPLY</div>
      {lines.map((l) => (
        <div key={l.n} style={{display: 'flex', alignItems: 'center', gap: 14, padding: '14px 12px', borderRadius: 16, background: l.changes ? `rgba(31,138,59,${0.1 * p})` : 'transparent', boxShadow: l.changes ? `0 0 0 ${2 * p}px rgba(31,138,59,.35)` : 'none'}}>
          <span style={{width: 12, height: 12, borderRadius: 12, background: l.changes ? (p > 0.5 ? K.green : K.orange) : K.faint}} />
          <span style={{fontSize: 24, fontWeight: 600, flex: 1}}>{l.n}</span>
          <span style={{fontSize: 20, color: l.changes && p > 0.5 ? K.green : K.muted, fontWeight: l.changes ? 700 : 400}}>{l.changes ? (p > 0.5 ? l.v : 'waiting on correction') : l.v}</span>
        </div>
      ))}
    </Card>
  );
};

/* ---------- 12–14 UNDER THE HOOD ---------- */
const S = 1.47; // display→source scale of the 2940x1912 captures
const bx = (x: number, y: number, w: number, h: number, text?: string) => ({x: x * S, y: y * S, w: w * S, h: h * S, text});
const BAND_CROP = bx(0, 46, 2000, 1170);
const PEOPLE = [bx(1668, 262, 300, 52, 'O   Owner'), bx(1716, 416, 260, 22, 'owner/pp-resolution'), bx(1716, 485, 260, 22, 'owner/pp-audit'), bx(1716, 555, 260, 22, 'owner/pp-payroll')];
const REDACT: Record<string, ReturnType<typeof bx>[]> = {
  '12-band-chat-handoff.png': [...PEOPLE, bx(879, 352, 176, 30, '@Owner'), bx(879, 579, 176, 30, '@Owner'), bx(879, 729, 176, 30, '@Owner'), bx(652, 478, 186, 36, 'O   Owner')],
  '08-band-room.png': [...PEOPLE, bx(879, 352, 176, 30, '@Owner'), bx(879, 579, 176, 30, '@Owner'), bx(879, 729, 176, 30, '@Owner'), bx(652, 478, 186, 36, 'O   Owner')],
  '09-band-board.png': [...PEOPLE, bx(974, 352, 300, 28, 'pp-resolution: In progress'), bx(974, 499, 300, 28, 'pp-resolution: In progress')],
  '11-band-cost.png': [],
  '13-band-dev-team.png': [],
};
const Shot: React.FC<{file: string; dur: number; pan?: [number, number]; zoom?: [number, number]; origin?: string; title: string}> = ({file, dur, pan = [0, 0.1], zoom = [1, 1.12], origin = '50% 30%', title}) => {
  const c = D.clips[file];
  if (!c) return null;
  return (
    <Window x={160} y={150} w={1600} h={840} title={title} tilt={0.5}>
      <Media src={`a/clips/${file}`} w={c.w ?? 1920} h={c.h ?? 1080} boxW={1600} boxH={796} dur={dur} video={c.kind === 'video'} clipDur={c.dur} pan={pan} zoom={zoom} origin={origin} fit="cover" crop={c.w === 2940 ? BAND_CROP : undefined} boxes={REDACT[file] ?? []} />
    </Window>
  );
};
const Pending: React.FC<{what: string}> = ({what}) => (
  <div style={{position: 'absolute', left: 160, top: 150, width: 1600, height: 840, borderRadius: 26, border: `3px dashed ${K.faint}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily, fontSize: 34, color: K.muted}}>
    {what} · screenshot pending
  </div>
);

export const Room: React.FC<P> = ({dur}) => {
  const f = useCurrentFrame();
  const title = ci(f, 0, 14) * ci(f, 34, 46, 1, 0);
  const file = has('12-band-chat-handoff.png') ? '12-band-chat-handoff.png' : has('08-band-room.png') ? '08-band-room.png' : null;
  return (
    <AbsoluteFill>
      <Background />
      {f > 30 ? (file ? <Shot file={file} dur={dur} title="Band · product room" pan={[0, 0.6]} zoom={[1, 1.3]} origin="55% 40%" /> : <AgentsDiagram />) : null}
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', opacity: title}}>
        <div style={{fontFamily, fontSize: 120, fontWeight: 800, letterSpacing: '-0.05em', color: K.text, transform: `scale(${ci(f, 0, 46, 0.94, 1.04)})`}}>Under the hood</div>
      </AbsoluteFill>
      {f > 30 ? <Label kinds={file ? ['live'] : ['illustration']} note={file ? 'Band Desktop' : 'agents from today’s Band room'} /> : null}
    </AbsoluteFill>
  );
};
const AgentsDiagram: React.FC = () => {
  const f = useCurrentFrame();
  const nodes = [
    {k: 'audit', x: 560, y: 380, role: 'finds & evidences'},
    {k: 'resolution', x: 960, y: 300, role: 'asks & interprets'},
    {k: 'payroll', x: 1360, y: 380, role: 'computes & reports'},
    {k: 'owner', x: 960, y: 760, role: 'human decisions'},
  ] as const;
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', left: 960 - 560, top: 160, width: 1120, height: 820, borderRadius: 400, background: 'rgba(10,122,255,.04)', border: `2px solid rgba(10,122,255,.12)`}} />
      <div style={{position: 'absolute', left: 0, right: 0, top: 560, textAlign: 'center', fontFamily, fontSize: 26, fontWeight: 700, color: K.blue, letterSpacing: '0.1em'}}>ONE SHARED ROOM IN BAND</div>
      {nodes.map((n, i) => {
        const s = useSpring(34 + i * 6, 14);
        const c = AG[n.k].c;
        return (
          <div key={n.k} style={{position: 'absolute', left: n.x - 120, top: n.y - 70, width: 240, textAlign: 'center', fontFamily, transform: `scale(${s})`}}>
            <div style={{width: 120, height: 120, margin: '0 auto', borderRadius: 120, background: c, color: '#fff', fontSize: 46, fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: `0 0 0 ${12 + Math.sin(f / 8 + i) * 4}px ${c}22`}}>{n.k === 'owner' ? 'O' : n.k[0].toUpperCase()}</div>
            <div style={{fontSize: 26, fontWeight: 700, marginTop: 12}}>{AG[n.k].n}</div>
            <div style={{fontSize: 19, color: K.muted}}>{n.role}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

export const BoardCost: React.FC<P> = ({dur}) => {
  const f = useCurrentFrame();
  const half = (dur * FPS) / 2;
  const board = has('09-band-board.png') ? '09-band-board.png' : null;
  const costImg = has('11-band-cost.png') ? '11-band-cost.png' : null;
  const costTxt = D.clips['11-band-usage.txt']?.text;
  const first = f < half;
  return (
    <AbsoluteFill>
      <Background />
      {first ? (
        <Sequence durationInFrames={Math.ceil(half)} layout="none">
          {board ? <Shot file={board} dur={dur / 2} title="Band · work board" pan={[0, 0.1]} zoom={[1, 1.35]} origin="62% 22%" /> : <BoardDiagram />}
          <Label kinds={board ? ['live'] : ['illustration']} note={board ? 'Band work board' : 'board states from today’s Band log'} />
        </Sequence>
      ) : (
        <Sequence from={Math.ceil(half)} layout="none">
          {costImg ? <Shot file={costImg} dur={dur / 2} title="Band · usage & estimated cost" pan={[0.3, 0.9]} zoom={[1, 1.2]} origin="50% 70%" /> : costTxt ? <Terminal text={costTxt} title="band usage agents" /> : <Pending what="Band usage & estimated cost" />}
          <Label kinds={costImg || costTxt ? ['live'] : ['illustration']} note="Band usage · build-team sessions, estimated at list prices" />
        </Sequence>
      )}
    </AbsoluteFill>
  );
};
const BoardDiagram: React.FC = () => {
  const f = useCurrentFrame();
  const cols = ['To-do', 'In progress', 'Done'];
  const pos = interpolate(f, [30, 70, 110, 150], [0, 1, 1, 2], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: (x) => x});
  return (
    <AbsoluteFill>
      {cols.map((c, i) => (
        <Card key={c} style={{position: 'absolute', left: 220 + i * 510, top: 200, width: 460, height: 700, background: 'rgba(255,255,255,.7)', padding: 26}}>
          <div style={{fontSize: 22, fontWeight: 700, color: K.muted, letterSpacing: '0.06em'}}>{c.toUpperCase()}</div>
        </Card>
      ))}
      <Card style={{position: 'absolute', left: 246 + pos * 510, top: 270 - Math.sin((pos % 1) * Math.PI) * 30, width: 408, padding: 22, boxShadow: K.shadowBig}}>
        <div style={{fontSize: 16, color: K.muted}}>#3 · pp-audit → pp-resolution</div>
        <div style={{fontSize: 24, fontWeight: 700, marginTop: 6}}>Case exc_611be6d68e</div>
        <div style={{marginTop: 10}}><Pill color={pos > 1.9 ? K.green : K.blue2} bg={pos > 1.9 ? K.greenTint : K.tint} size={15}>{pos > 1.9 ? 'completed' : pos > 0.9 ? 'in progress' : 'pending'}</Pill></div>
      </Card>
    </AbsoluteFill>
  );
};

export const DevTeam: React.FC<P> = ({dur}) => (
  <AbsoluteFill>
    <Background />
    <Shot file="13-band-dev-team.png" dur={dur} title="Band · build team" />
    <div style={{position: 'absolute', left: 0, right: 0, top: 70, textAlign: 'center', fontFamily, fontSize: 40, fontWeight: 750 as never, letterSpacing: '-0.02em', color: K.text}}>Built by a Claude Code + Codex team coordinated in Band</div>
    <Label kinds={['live']} note="Band Desktop" />
  </AbsoluteFill>
);

/* ---------- 15 COGNEE ---------- */
const COGNEE_LINES: {t: string; c?: string; at: number; flash?: boolean}[] = [
  {t: '# process 1 · pid 28512', c: K.faint, at: 0.6},
  {t: 'memory.write  res_demo02 → dataset pilotco_cases', at: 1.2},
  {t: '  fact: job_03 (off-site disposal) belongs to job_02 (patio build)', c: '#7EE787', at: 2.0},
  {t: 'process exited', c: '#FF7B72', at: 3.4, flash: true},
  {t: '# process 2 · fresh · pid 29126', c: K.faint, at: 4.6},
  {t: 'cognee.recall(CHUNKS, datasets=[pilotco_cases]) → 2 hits', at: 5.4},
  {t: 'apply_recall: ids ✓  company scope ✓  parent job ✓', c: '#7EE787', at: 6.4},
];
const Terminal: React.FC<{text?: string; title: string; lines?: typeof COGNEE_LINES}> = ({text, title, lines}) => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const L = lines ?? (text ?? '').split('\n').slice(0, 22).map((l, i) => ({t: l, at: 0.3 + i * 0.25}));
  return (
    <div style={{position: 'absolute', left: 110, top: 170, width: 1000, height: 760, borderRadius: 22, background: '#16181D', boxShadow: K.shadowBig, overflow: 'hidden', fontFamily: mono}}>
      <div style={{height: 44, display: 'flex', alignItems: 'center', gap: 8, padding: '0 18px', background: '#1E2128'}}>
        {['#FF5F57', '#FEBC2E', '#28C840'].map((c) => <span key={c} style={{width: 13, height: 13, borderRadius: 13, background: c}} />)}
        <span style={{marginLeft: 16, color: '#8B93A1', fontSize: 16}}>{title}</span>
      </div>
      <div style={{padding: '22px 26px', fontSize: 22, lineHeight: 1.65, color: '#E6EDF3', whiteSpace: 'pre-wrap'}}>
        {L.map((l, i) => {
          if (t < l.at) return null;
          const chars = Math.floor((t - l.at) * 70);
          return <div key={i} style={{color: (l as {c?: string}).c ?? '#E6EDF3'}}>{l.t.slice(0, chars)}{chars < l.t.length ? '▍' : ''}</div>;
        })}
      </div>
    </div>
  );
};
export const Memory: React.FC<P> = ({dur}) => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const txt = D.clips['10-cognee-recall.txt']?.text;
  const flashAt = 3.4;
  const flash = ci(t, flashAt, flashAt + 0.1) * ci(t, flashAt + 0.1, flashAt + 0.6, 1, 0);
  const card = useSpring(7.4 * FPS);
  const strike = ci(t, 8.6, 9.3);
  const after = ci(t, 9.3, 9.9);
  const ok = ci(t, 10.6, 11.0);
  return (
    <AbsoluteFill>
      <Background />
      <Headline kicker="Memory · Cognee" title="It remembers the business." x={110} y={60} size={46} delay={0} />
      <Terminal title="payrollpilot.memory · Cognee" lines={COGNEE_LINES} />
      <AbsoluteFill style={{background: `rgba(224,50,63,${0.18 * flash})`, pointerEvents: 'none'}} />
      <Card style={{position: 'absolute', left: 1150, top: 260, width: 680, padding: 36, opacity: card, transform: `translateX(${(1 - card) * 80}px)`, boxShadow: K.shadowBig}}>
        <div style={{fontSize: 15, fontWeight: 700, letterSpacing: '0.1em', color: K.muted}}>NEXT ACTION · LATER JOB 03 COST</div>
        <div style={{position: 'relative', fontSize: 30, fontWeight: 600, marginTop: 18, color: strike > 0.5 ? K.faint : K.text}}>
          Ask ops lead which job
          <div style={{position: 'absolute', left: 0, top: '52%', height: 3, width: `${strike * 100}%`, background: K.red}} />
        </div>
        <div style={{fontSize: 34, fontWeight: 800, letterSpacing: '-0.02em', marginTop: 18, color: K.blue, opacity: after, transform: `translateY(${(1 - after) * 14}px)`}}>→ Propose allocation to job_02, pending owner approval</div>
        <div style={{marginTop: 26, opacity: ok, transform: `scale(${0.9 + 0.1 * ok})`, transformOrigin: 'left center'}}>
          <Pill color={K.green} bg={K.greenTint} size={22}>approval_created: false</Pill>
        </div>
        <div style={{fontSize: 18, color: K.muted, marginTop: 14, opacity: ok}}>Without memory: 0 hits, the case keeps asking.</div>
      </Card>
      <Label kinds={['earlier', 'synthetic']} note="write → exit → fresh process" />
      {txt ? <Label kinds={['live']} note="POST /api/memory/recall-check" x={1150} y={190} /> : null}
      <span style={{display: 'none'}}>{dur}</span>
    </AbsoluteFill>
  );
};

/* ---------- 16 RECAP ---------- */
export const Recap: React.FC<P> = ({dur}) => {
  const c = D.clips['07-ready-summary.mp4'];
  const callouts = [
    {at: 1.4, t: 'Stage 1 · Employee wages', s: 'verified for every worker', c: K.green},
    {at: 2.4, t: 'Stage 2 · each item on its own', s: 'commission · tips · manager pool', c: K.blue},
    {at: 3.6, t: 'Gusto: not prepared', s: 'you confirm the draft · submitting stays with you', c: K.orange},
  ];
  const f = useCurrentFrame();
  const t = f / FPS;
  return (
    <AbsoluteFill>
      <Background />
      <Headline kicker="Step 6 · Recap" title="One recap. You confirm." x={90} y={40} size={44} delay={0} />
      <Window x={70} y={170} w={1100} h={780} title="PayrollPilot · Pilot Co" tilt={-0.6}>
        {c ? (
          <Media src="a/clips/07-ready-summary.mp4" w={c.w ?? 1920} h={c.h ?? 1080} boxW={1100} boxH={736} dur={dur} video clipDur={c.dur} />
        ) : (
          <Media src="a/mock-ready.png" w={D.files['mock-ready.png']?.w ?? 2560} h={D.files['mock-ready.png']?.h ?? 3000} boxW={1100} boxH={736} dur={dur} pan={[0, 0.25]} zoom={[1, 1.06]} />
        )}
      </Window>
      {callouts.map((k) => {
        const a = ci(t, k.at, k.at + 0.45);
        return (
          <Card key={k.t} style={{position: 'absolute', left: 1230, top: 240 + callouts.indexOf(k) * 200, width: 610, padding: '24px 28px', opacity: a, transform: `translateX(${(1 - a) * 60}px)`, borderRadius: 22}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
              <span style={{width: 14, height: 14, borderRadius: 14, background: k.c}} />
              <span style={{fontSize: 28, fontWeight: 700, letterSpacing: '-0.02em'}}>{k.t}</span>
            </div>
            <div style={{fontSize: 21, color: K.muted, marginTop: 6, marginLeft: 26}}>{k.s}</div>
          </Card>
        );
      })}
      <Label kinds={c ? ['live', 'synthetic'] : ['mockup', 'synthetic']} x={1240} y={40} />
    </AbsoluteFill>
  );
};

/* ---------- 17 CLOSE ---------- */
export const Close: React.FC<P> = ({dur}) => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const m = useSpring(0, 16);
  const l1 = useSpring(14);
  const card = ci(t, dur - 4.2, dur - 3.6);
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
      <Background tint={0.7} />
      <div style={{position: 'absolute', top: 210, width: 820, height: 410, transform: `scale(${0.85 + 0.15 * m})`, opacity: m * (1 - card * 0.6)}}>
        <Img src={staticFile('brand/wordmark-t.png')} style={{width: '100%', height: '100%'}} />
      </div>
      <div style={{position: 'absolute', top: 620, textAlign: 'center', fontFamily, fontSize: 54, fontWeight: 750 as never, letterSpacing: '-0.03em', color: K.text, lineHeight: 1.2, opacity: l1 * (1 - card), transform: `translateY(${(1 - l1) * 20}px)`}}>
        From missing information to payroll-ready.
        <br />
        <span style={{color: K.blue}}>With you in control.</span>
      </div>
      <div style={{position: 'absolute', top: 640, textAlign: 'center', fontFamily, fontSize: 40, fontWeight: 600, color: K.text2, lineHeight: 1.4, opacity: card, transform: `translateY(${(1 - card) * 16}px)`}}>
        You approve every message and correction.
        <br />
        PayrollPilot never submits payroll.
      </div>
    </AbsoluteFill>
  );
};
