import {loadFont as loadInter} from '@remotion/google-fonts/Inter';
import {loadFont as loadInterTight} from '@remotion/google-fonts/InterTight';
import {loadFont as loadMono} from '@remotion/google-fonts/JetBrainsMono';

export const inter = loadInter('normal', {weights: ['400', '500', '600', '700'], subsets: ['latin']}).fontFamily;
export const display = loadInterTight('normal', {weights: ['500', '600', '700', '800'], subsets: ['latin']}).fontFamily;
export const mono = loadMono('normal', {weights: ['400', '500'], subsets: ['latin']}).fontFamily;

// Shared identity with the web app: lane D tokens (side-session note, D-01) + docs/DESIGN-DIRECTION.md.
export const C = {
  bg: '#0B0D12',
  surface: '#12141B',
  surface2: '#171A23',
  border: 'rgba(255,255,255,0.08)',
  text: '#E7E9EE',
  muted: '#A3A9B7',
  faint: '#6F7686',
  accent: '#8B9CFF', // indigo
  accent2: '#B79CFF', // violet
  teal: '#38BDAC',
  steel: '#7FA6D9', // title-card gradient start (Wonderlust register)
  sand: '#E2C9A0', // title-card gradient end
  ready: '#4ADE80',
  pending: '#FBBF24',
  partial: '#60A5FA',
  blocked: '#F87171',
  seeded: '#C084FC',
};

export const FPS = 30;
export const W = 1920;
export const H = 1080;
export const s = (sec: number) => Math.round(sec * FPS);
