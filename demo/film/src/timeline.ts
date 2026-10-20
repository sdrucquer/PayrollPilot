// Seconds. Mirrors the table in demo/script.md.
export const T = {
  coldOpen: [0, 3.2],
  montage: [3.2, 15.2],
  turn: [15.2, 24],
  logo: [24, 32],
  how: [32, 50.5],
  b1: [50.5, 65],
  b2: [65, 83],
  b3: [83, 100],
  b4: [100, 115],
  b5: [115, 129],
  b6: [129, 146],
  b7: [146, 160.5],
  status: [160.5, 168.5],
  close: [168.5, 175],
} as const;
export const TOTAL = 175;
