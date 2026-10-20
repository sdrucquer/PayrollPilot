// Frozen identity: design/DESIGN.md, FROZEN 1:40 PM; design/home.html.
export const inter = '-apple-system, BlinkMacSystemFont, "SF Pro Text", Inter, system-ui, sans-serif';
export const display = '-apple-system, BlinkMacSystemFont, "SF Pro Display", Inter, system-ui, sans-serif';
export const mono = 'ui-monospace, "SF Mono", monospace';
export const C = {
  bg: '#F2F2F7', surface: '#FFFFFF', surface2: '#F5F5F8',
  border: 'rgba(0,0,0,.05)', text: '#1C1C1E', muted: '#6E6E73', faint: '#8E8E93',
  accent: '#0A7AFF', accent2: '#0066D6', steel: '#0A7AFF', sand: '#0066D6',
  ready: '#1F8A3B', pending: '#9A4D00', partial: '#D97A00', blocked: '#E0323F',
  seeded: '#9A4D00', chipBg: '#E8F1FF', chipFg: '#0066D6',
  uiCanvas: '#F2F2F7', uiCard: '#FFFFFF', uiText: '#1C1C1E', uiMuted: '#6E6E73',
  uiLine: 'rgba(0,0,0,.08)', uiAccent: '#0A7AFF', uiAccent2: '#0066D6',
  stageAccent: '#0A7AFF',
};
export const cardShadow = '0 1px 2px rgba(0,0,0,.03), 0 20px 48px -28px rgba(20,20,40,.22), 0 0 0 1px rgba(0,0,0,.03)';
export const FPS = 30;
export const W = 1920;
export const H = 1080;
export const s = (sec: number) => Math.round(sec * FPS);
