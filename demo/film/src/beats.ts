import {Prov} from './components/Chip';

export type Segment = {
  from: number; // seconds, absolute
  to: number;
  title: string;
  layout: 'screen' | 'split';
  screen?: string; // footage file in public/footage
  phone?: string;
  route?: string;
  chip: {kind: Prov; text?: string};
  pending: string[]; // what the shot must show (rendered only while footage is missing)
};
export type Section = {key: 'magic' | 'engine' | 'result'; kicker: string; segments: Segment[]};

const APP = 'localhost:5173 · PayrollPilot';

// Chips are the PLANNED labels. Lane E downgrades a chip (PLAYBACK, NOT SHOWN) per demo/evidence-matrix.md before the final render.
export const SECTIONS: Section[] = [
  {
    key: 'magic', kicker: 'THE PRODUCT',
    segments: [
      {from: 25, to: 35, title: 'Audit finds an issue', layout: 'screen', screen: 'm1-detect.mov', route: APP, chip: {kind: 'SEEDED ISSUE', text: 'synthetic data · real app'},
        pending: ['Frozen one-column home: hero, approval, progress, activity; separate stage readiness', 'Details: Oct 1 shift on Job 01, scheduled on Job 02', 'Details: observed vs expected, evidence, wages none / job costing']},
      {from: 35, to: 42, title: 'Handed to Resolution, in Band', layout: 'screen', screen: 'm2-band-handoff.mov', route: 'Band Desktop', chip: {kind: 'REAL', text: 'Band Desktop'},
        pending: ['pp-audit posts the case card', 'pp-resolution accepts it', 'Board task moves to in progress']},
      {from: 42, to: 48.5, title: 'The owner approves the exact text', layout: 'screen', screen: 'm3-approve.mov', route: APP, chip: {kind: 'REAL', text: 'approval bound to text hash'},
        pending: ['Two questions, masked recipient, linked issues, hash', 'Approve and send']},
      {from: 48.5, to: 54, title: 'A real iMessage', layout: 'split', screen: 'm3-approve.mov', phone: 'm3-phone.mov', route: APP, chip: {kind: 'REAL', text: 'Photon iMessage · test mode'},
        pending: ['Batch sent, provider status', 'Phone: the message arrives (no number visible)']},
      {from: 54, to: 63, title: '“yes” is not an answer', layout: 'split', screen: 'm4-clarify.mov', phone: 'm4-phone.mov', route: APP, chip: {kind: 'TEST REPLY', text: 'owner answering as Ops lead'},
        pending: ['Both questions ambiguous → Clarify', 'Follow-up approved and sent', 'Phone: “yes”, then the follow-up arrives']},
      {from: 63, to: 70, title: 'The answer lands in the case', layout: 'split', screen: 'm5-answer.mov', phone: 'm5-phone.mov', route: APP, chip: {kind: 'TEST REPLY', text: 'parsed into the right case'},
        pending: ['Both answered: Job 02; quote shown', 'Phone: the clear reply']},
      {from: 70, to: 81, title: 'A local correction, approved', layout: 'screen', screen: 'm6-correction.mov', route: APP, chip: {kind: 'REAL', text: 'deterministic calc · synthetic data'},
        pending: ['Before/after: Oct 1 shift Job 01 → Job 02', 'Impact: wages $0.00 · job labor moves', 'Approve correction → Apply → one item changes']},
      {from: 81, to: 92, title: 'A fresh process. A remembered answer.', layout: 'screen', screen: 'm7-cognee.mov', route: 'Cognee · earlier cross-process proof', chip: {kind: 'PLAYBACK', text: 'verified earlier run · synthetic case'},
        pending: ['Earlier cross-process proof; live services stay running', 'memory.recalled → memory.applied for Job 03 cost', 'Next action: “ask ops lead which job” → “propose allocation to job_02 pending owner approval”']},
      {from: 92, to: 100, title: 'The corrected review', layout: 'screen', screen: 'm8-review.mov', route: APP, chip: {kind: 'REAL', text: 'internal draft · synthetic data'},
        pending: ['Stage 1 expansion: per-worker table after the correction', 'Destination: internal draft · Gusto not prepared']},
    ],
  },
  {
    key: 'engine', kicker: 'UNDER THE HOOD',
    segments: [
      {from: 111, to: 123, title: 'One room. One board. Every handoff.', layout: 'screen', screen: 'e2-band.mov', route: 'Band Desktop', chip: {kind: 'REAL', text: 'Band Desktop'},
        pending: ['Room: pp-audit, pp-resolution, pp-payroll + owner', 'Board task: pending → in progress → completed', '[decision.requested] and the owner’s reply']},
      {from: 123, to: 135, title: 'Metered agents. Memory without permission.', layout: 'screen', screen: 'e3-usage-recall.mov', route: APP, chip: {kind: 'REAL', text: 'usage events · recall check'},
        pending: ['Activity log: tokens and cost per agent call', 'Recall check: approval_created false', 'Memory off: case stays insufficient_evidence']},
    ],
  },
  {
    key: 'result', kicker: 'THE RESULT',
    segments: [
      {from: 135, to: 145, title: 'Separate readiness. Honest destination.', layout: 'screen', screen: 'c1-readiness.mov', route: APP, chip: {kind: 'REAL', text: 'workbook file · synthetic data'},
        pending: ['Stage 1 wages and each Stage 2 item with its blocker', 'Export workbook: verified totals, original not updated', 'Gusto: not prepared']},
    ],
  },
];
