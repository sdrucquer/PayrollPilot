import {loadFont as loadInter} from '@remotion/google-fonts/Inter';
import {loadFont as loadInterTight} from '@remotion/google-fonts/InterTight';
import {loadFont as loadMono} from '@remotion/google-fonts/JetBrainsMono';

export const inter = loadInter('normal', {weights: ['400', '500', '600', '700'], subsets: ['latin']}).fontFamily;
export const display = loadInterTight('normal', {weights: ['500', '600', '700', '800'], subsets: ['latin']}).fontFamily;
export const mono = loadMono('normal', {weights: ['400', '500'], subsets: ['latin']}).fontFamily;

// Shared identity with the running web app: lane D adopted these tokens (message 1:05 PM).
export const C = {
  bg: '#0B0D12',
  surface: '#12151C',
  surface2: '#171B24',
  border: '#222838',
  text: '#F5F7FA',
  muted: '#8B93A5',
  faint: '#5A6275',
  accent: '#4F7CFF',
  accent2: '#7FA0FF', // in-progress states (lane D)
  steel: '#7FA6D9', // title-card particle gradient start
  sand: '#E2C9A0', // title-card particle gradient end
  ready: '#2ED3A3',
  pending: '#F5B942',
  partial: '#F5B942',
  blocked: '#FF5C6C',
  seeded: '#C084FC',
  chipBg: '#2A3040',
  chipFg: '#C9D1E0',
};

export const FPS = 30;
export const W = 1920;
export const H = 1080;
export const s = (sec: number) => Math.round(sec * FPS);
