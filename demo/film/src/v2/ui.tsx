import React from 'react';
import {AbsoluteFill, continueRender, delayRender, Easing, Freeze, Img, interpolate, OffthreadVideo, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import data from '../generated/demo.json';

// Fonts ship in public/fonts (OFL); the render browser has no Google Fonts access.
const loadLocal = (family: string, file: string) => {
  if (typeof document === 'undefined') return;
  const h = delayRender(`font ${family}`);
  const ff = new FontFace(family, `url(${staticFile(file)}) format('woff2')`, {weight: '100 900'});
  ff.load().then((x) => { document.fonts.add(x); continueRender(h); }).catch(() => continueRender(h));
};
loadLocal('InterLocal', 'fonts/inter-latin-wght.woff2');
loadLocal('JBMono', 'fonts/jetbrains-mono-latin-wght.woff2');
export const fontFamily = 'InterLocal, Inter, system-ui, sans-serif';
export const D = data as unknown as {
  total: number;
  timeline: {id: string; from: number; dur: number; voAt: number; text: string}[];
  vo: Record<string, {file: string; dur: number; source: string}>;
  files: Record<string, {w: number; h: number}>;
  clips: Record<string, {kind: 'image' | 'video' | 'text'; dur?: number; w?: number; h?: number; text?: string}>;
  voSource: string;
};
export const seg = (id: string) => D.timeline.find((s) => s.id === id);
export const has = (f: string) => !!D.clips[f];

// Frozen identity tokens (design/DESIGN.md).
export const K = {
  bg0: '#F5F5F8', bg1: '#EEEEF3', card: '#FFFFFF', inset: '#F5F5F8', text: '#1C1C1E', text2: '#3A3A3C', muted: '#6E6E73', faint: '#8E8E93',
  blue: '#0A7AFF', blue2: '#0066D6', brand: '#035DFF', tint: '#E8F1FF', green: '#1F8A3B', greenTint: '#E6F6EA', orange: '#D97A00', orangeText: '#9A4D00',
  orangeTint: '#FFF4E5', red: '#E0323F', redTint: '#FDE8EA', line: 'rgba(0,0,0,.06)',
  shadow: '0 1px 2px rgba(0,0,0,.03), 0 20px 48px -28px rgba(20,20,40,.22), 0 0 0 1px rgba(0,0,0,.03)',
  shadowBig: '0 2px 4px rgba(0,0,0,.04), 0 40px 90px -30px rgba(20,20,60,.35), 0 0 0 1px rgba(0,0,0,.04)',
};
export const mono = 'JBMono, "JetBrains Mono", ui-monospace, "SF Mono", Menlo, monospace';
export const EASE = Easing.bezier(0.2, 0.7, 0.2, 1);
export const ci = (f: number, a: number, b: number, from = 0, to = 1, ease = EASE) =>
  interpolate(f, [a, b], [from, to], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
export const useSpring = (delay = 0, damping = 200, mass = 1) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: f - delay, fps, config: {damping, mass}});
};

export const Background: React.FC<{tint?: number}> = ({tint = 1}) => {
  const f = useCurrentFrame();
  const x1 = 30 + Math.sin(f / 140) * 8;
  const y1 = 20 + Math.cos(f / 170) * 6;
  const x2 = 75 + Math.cos(f / 150) * 8;
  const y2 = 80 + Math.sin(f / 190) * 6;
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(900px 700px at ${x1}% ${y1}%, rgba(10,122,255,${0.07 * tint}), transparent 70%), radial-gradient(800px 700px at ${x2}% ${y2}%, rgba(120,90,255,${0.05 * tint}), transparent 70%), linear-gradient(180deg, ${K.bg0}, ${K.bg1})`,
      }}
    />
  );
};

export type LabelKind = 'live' | 'synthetic' | 'test' | 'mockup' | 'earlier' | 'illustration';
const LABELS: Record<LabelKind, [string, string]> = {
  live: ['Real', K.green], synthetic: ['Synthetic data', K.blue], test: ['Test reply', K.orange], mockup: ['Design mockup', '#8E44D9'],
  earlier: ['Recorded earlier today', K.orange], illustration: ['Illustration', K.faint],
};
export const Label: React.FC<{kinds: LabelKind[]; note?: string; x?: number; y?: number}> = ({kinds, note, x = 44, y = 36}) => {
  const p = useSpring(6);
  return (
    <div style={{position: 'absolute', left: x, top: y, display: 'flex', gap: 8, opacity: p, transform: `translateY(${(1 - p) * -8}px)`, zIndex: 50}}>
      {kinds.map((k) => (
        <div key={k} style={{display: 'flex', alignItems: 'center', gap: 8, background: 'rgba(255,255,255,.92)', borderRadius: 999, padding: '7px 14px', boxShadow: K.shadow, fontFamily, fontSize: 15, fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase', color: K.text2}}>
          <span style={{width: 8, height: 8, borderRadius: 8, background: LABELS[k][1]}} />
          {LABELS[k][0]}
        </div>
      ))}
      {note ? <div style={{alignSelf: 'center', fontFamily, fontSize: 15, color: K.muted, marginLeft: 4}}>{note}</div> : null}
    </div>
  );
};

// Narration captions: sentences timed by length across the voice line.
export const Caption: React.FC<{text: string; voAt: number; voDur: number; dur: number}> = ({text, voAt, voDur, dur}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const parts = text.match(/[^.!?:]+[.!?:]?/g)?.map((s) => s.trim()).filter(Boolean) ?? [text];
  const total = parts.reduce((a, s) => a + s.length, 0);
  const span = Math.max(voDur, dur - voAt - 0.6) || 1;
  let acc = voAt;
  const t = f / fps;
  let cur = -1;
  const times = parts.map((s) => {
    const a = acc;
    acc += (s.length / total) * (voDur || span);
    return [a, acc] as const;
  });
  times.forEach(([a], i) => {
    if (t >= a - 0.05) cur = i;
  });
  if (cur < 0 || t > dur - 0.25) return null;
  const [a] = times[cur];
  const p = ci(t, a, a + 0.25);
  return (
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 34, display: 'flex', justifyContent: 'center', zIndex: 60}}>
      <div style={{maxWidth: 1400, padding: '12px 26px', borderRadius: 18, background: 'rgba(28,28,30,.82)', color: '#fff', fontFamily, fontSize: 30, fontWeight: 500, letterSpacing: '-0.01em', lineHeight: 1.3, textAlign: 'center', opacity: p, transform: `translateY(${(1 - p) * 6}px)`}}>
        {parts[cur]}
      </div>
    </div>
  );
};

// Media: image panned/zoomed, or video fitted to the segment (sped up if long, frozen if short).
export type Box = {x: number; y: number; w: number; h: number; text?: string};
export const Media: React.FC<{src: string; w: number; h: number; boxW: number; boxH: number; dur: number; video?: boolean; clipDur?: number; pan?: [number, number]; zoom?: [number, number]; origin?: string; fit?: 'width' | 'cover'; crop?: Box; boxes?: Box[]; startAt?: number}> = ({
  src, w: fullW, h: fullH, boxW, boxH, dur, video, clipDur = 0, pan = [0, 0], zoom = [1, 1], origin = '50% 0%', fit = 'width', crop, boxes = [], startAt = 0,
}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const c = crop ?? {x: 0, y: 0, w: fullW, h: fullH};
  const w = c.w;
  const h = c.h;
  const scaleFit = fit === 'cover' ? Math.max(boxW / w, boxH / h) : boxW / w;
  const dispH = h * scaleFit;
  const dispW = w * scaleFit;
  const p = ci(f, 0, dur * fps, 0, 1, Easing.inOut(Easing.cubic));
  const over = Math.max(0, dispH - boxH);
  const y = -over * interpolate(p, [0, 1], pan);
  const z = interpolate(p, [0, 1], zoom);
  const style: React.CSSProperties = {position: 'absolute', left: (boxW - dispW) / 2, top: 0, width: dispW, height: dispH, transform: `translateY(${y}px) scale(${z})`, transformOrigin: origin, overflow: 'hidden'};
  const inner: React.CSSProperties = {position: 'absolute', left: -c.x * scaleFit, top: -c.y * scaleFit, width: fullW * scaleFit, height: fullH * scaleFit};
  // Redaction boxes, in source pixels: real names and usernames never reach the frame.
  const red = boxes.map((b, i) => (
    <div key={i} style={{position: 'absolute', left: (b.x - c.x) * scaleFit, top: (b.y - c.y) * scaleFit, width: b.w * scaleFit, height: b.h * scaleFit, background: '#FFFFFF', borderRadius: 6 * scaleFit, display: 'flex', alignItems: 'center', fontFamily, fontWeight: 600, fontSize: b.h * 0.58 * scaleFit, color: K.text, paddingLeft: 6 * scaleFit, whiteSpace: 'nowrap', overflow: 'hidden'}}>
      {b.text}
    </div>
  ));
  if (video) {
    const usable = Math.max(0.5, clipDur - startAt - 1.2); // skip trailing black frames
    const rate = Math.min(4, Math.max(1, usable / Math.max(1, dur)));
    const playFrames = Math.max(1, Math.floor((usable * fps) / rate));
    const v = <OffthreadVideo src={staticFile(src)} startFrom={Math.round(startAt * fps)} playbackRate={rate} muted style={{width: '100%', height: '100%'}} />;
    return <div style={style}><div style={inner}>{f >= playFrames ? <Freeze frame={playFrames}>{v}</Freeze> : v}</div>{red}</div>;
  }
  return <div style={style}><Img src={staticFile(src)} style={inner} />{red}</div>;
};

// macOS-style window that tilts in.
export const Window: React.FC<{x: number; y: number; w: number; h: number; title?: string; delay?: number; tilt?: number; children: React.ReactNode}> = ({x, y, w, h, title, delay = 0, tilt = 1, children}) => {
  const f = useCurrentFrame();
  const p = useSpring(delay, 22, 1.1);
  const ry = interpolate(p, [0, 1], [-16 * tilt, -2.5 * tilt]) + Math.sin(f / 70) * 0.5;
  const rx = interpolate(p, [0, 1], [10, 1.5]) + Math.cos(f / 80) * 0.4;
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, height: h, perspective: 2600}}>
      <div style={{width: '100%', height: '100%', transform: `translateY(${(1 - p) * 120}px) rotateY(${ry}deg) rotateX(${rx}deg) scale(${0.92 + 0.08 * p})`, opacity: Math.min(1, p * 1.6), transformStyle: 'preserve-3d'}}>
        <div style={{width: '100%', height: '100%', borderRadius: 22, background: K.card, boxShadow: K.shadowBig, overflow: 'hidden', display: 'flex', flexDirection: 'column'}}>
          <div style={{height: 44, flexShrink: 0, display: 'flex', alignItems: 'center', gap: 8, padding: '0 18px', borderBottom: `1px solid ${K.line}`, background: '#FAFAFC'}}>
            {['#FF5F57', '#FEBC2E', '#28C840'].map((c) => <span key={c} style={{width: 13, height: 13, borderRadius: 13, background: c}} />)}
            <div style={{flex: 1, textAlign: 'center', fontFamily, fontSize: 15, color: K.muted, marginRight: 60}}>{title}</div>
          </div>
          <div style={{position: 'relative', flex: 1, overflow: 'hidden'}}>{children}</div>
        </div>
      </div>
    </div>
  );
};

export const Card: React.FC<{style?: React.CSSProperties; children: React.ReactNode}> = ({style, children}) => (
  <div style={{background: K.card, borderRadius: 28, boxShadow: K.shadow, fontFamily, color: K.text, ...style}}>{children}</div>
);

export const Pill: React.FC<{color: string; bg: string; children: React.ReactNode; size?: number}> = ({color, bg, children, size = 16}) => (
  <span style={{display: 'inline-flex', alignItems: 'center', gap: 6, padding: `${size * 0.3}px ${size * 0.75}px`, borderRadius: 999, background: bg, color, fontFamily, fontSize: size, fontWeight: 600}}>{children}</span>
);

export const Headline: React.FC<{kicker?: string; title: string; x?: number; y?: number; size?: number; delay?: number; align?: 'left' | 'center'}> = ({kicker, title, x = 90, y = 96, size = 52, delay = 4, align = 'left'}) => {
  const p = useSpring(delay);
  const q = useSpring(delay + 5);
  return (
    <div style={{position: 'absolute', left: align === 'center' ? 0 : x, right: align === 'center' ? 0 : undefined, top: y, textAlign: align, fontFamily, zIndex: 20}}>
      {kicker ? <div style={{fontSize: 17, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: K.blue, opacity: p, transform: `translateY(${(1 - p) * 12}px)`}}>{kicker}</div> : null}
      <div style={{fontSize: size, fontWeight: 750 as never, letterSpacing: '-0.03em', color: K.text, marginTop: 6, opacity: q, transform: `translateY(${(1 - q) * 18}px)`}}>{title}</div>
    </div>
  );
};
