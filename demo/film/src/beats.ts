import {Prov} from './components/Chip';
import {T} from './timeline';

export type Segment = {
  layout: 'screen' | 'split' | 'phone';
  screen?: string; // footage file in public/footage
  phone?: string;
  route?: string;
  chip: {kind: Prov; text?: string};
  share: number; // fraction of the beat
  pending: string[]; // what the shot must show (shown only while footage is missing)
};
export type Beat = {key: keyof typeof T; n: string; title: string; sub: string; segments: Segment[]};

// Chips are the PLANNED labels. Lane E downgrades a chip (e.g. to PLAYBACK or NOT SHOWN) per demo/evidence-matrix.md before the final render.
export const BEATS: Beat[] = [
  {
    key: 'b1', n: '01', title: 'The cycle board', sub: 'Wages and each Stage 2 item keep separate states',
    segments: [{layout: 'screen', screen: 's1-board.mov', route: 'localhost:5173 · PayrollPilot', chip: {kind: 'SYNTHETIC', text: 'fixture data in the real app'}, share: 1,
      pending: ['Progress strip: Collect → Audit → Resolve → Prepare → Review, agent on each step', 'Stage 1 wages row + three Stage 2 chips with first blocker', 'Chips: Gusto not prepared · synthetic data · test mode']}],
  },
  {
    key: 'b2', n: '02', title: 'Audit hands off to Resolution', sub: 'Through a Band Desktop room, with the owner deciding',
    segments: [
      {layout: 'screen', screen: 's2a-handoff.mov', route: 'localhost:5173 · PayrollPilot', chip: {kind: 'SEEDED ISSUE', text: 'already-paid shift on the wrong job'}, share: 0.4,
        pending: ['Zone 2 row: Oct 1 shift on Job 01, scheduled on Job 02 (seeded)', 'Zone 3: observed vs expected, evidence, wages none / job costing', 'Strip: Audit → Resolution']},
      {layout: 'screen', screen: 's2b-band-room.mov', route: 'Band Desktop · PayrollPilot Cases', chip: {kind: 'REAL', text: 'Band Desktop'}, share: 0.6,
        pending: ['Room with pp-audit, pp-resolution, pp-payroll + owner', 'Case card → accepted reply; board task → completed', 'Owner replies to [decision.requested] in the room']},
    ],
  },
  {
    key: 'b3', n: '03', title: 'One approval, one exact message', sub: 'Then a real iMessage to the owner’s phone',
    segments: [
      {layout: 'screen', screen: 's3a-approve-send.mov', route: 'localhost:5173 · PayrollPilot', chip: {kind: 'REAL', text: 'approval bound to text hash'}, share: 0.55,
        pending: ['Drafted batch: two questions', 'Approval dialog: exact text, masked recipient, hash', 'Approve + Send']},
      {layout: 'split', screen: 's3a-approve-send.mov', phone: 's3b-phone-arrive.mov', route: 'localhost:5173 · PayrollPilot', chip: {kind: 'REAL', text: 'Photon iMessage'}, share: 0.45,
        pending: ['Batch state: sent, provider status', 'Phone: message arrives (no number visible)']},
    ],
  },
  {
    key: 'b4', n: '04', title: '“yes” is not an answer', sub: 'Ambiguous replies get a bounded clarification',
    segments: [
      {layout: 'split', screen: 's4b-clarify.mov', phone: 's4a-phone-vague.mov', route: 'localhost:5173 · PayrollPilot', chip: {kind: 'TEST REPLY', text: 'real transport, owner answering as Ops lead'}, share: 1,
        pending: ['Phone: owner sends “yes”', 'UI: both questions ambiguous → Clarify → new approval', 'Phone + UI: clear answer, extracted job, quote']},
    ],
  },
  {
    key: 'b5', n: '05', title: 'A local correction, approved', sub: 'Wages unchanged. Job costing moves.',
    segments: [{layout: 'screen', screen: 's5-correction.mov', route: 'localhost:5173 · PayrollPilot', chip: {kind: 'REAL', text: 'deterministic calc on synthetic data'}, share: 1,
      pending: ['Before/after: Oct 1 shift Job 01 → Job 02', 'Impact: wages $0.00, job labor moves', 'Approve correction, apply, one card changes']}],
  },
  {
    key: 'b6', n: '06', title: 'Restarted. Still remembers.', sub: 'Payroll Prep recalls a Cognee memory and changes its next action',
    segments: [
      {layout: 'screen', screen: 's6a-restart.mov', route: 'Terminal', chip: {kind: 'REAL', text: 'backend restart'}, share: 0.3,
        pending: ['Backend stopped and started, timestamps visible']},
      {layout: 'screen', screen: 's6b-cognee-recall.mov', route: 'localhost:5173 · PayrollPilot', chip: {kind: 'REAL', text: 'Cognee'}, share: 0.7,
        pending: ['Activity log under the strip: memory.recalled → memory.applied', 'Next action before: ask ops lead which job', 'After: propose allocation to Job 02, needs approval']},
    ],
  },
  {
    key: 'b7', n: '07', title: 'Packet, workbook, honest status', sub: 'Verified against each other. Gusto: not prepared.',
    segments: [
      {layout: 'screen', screen: 's7a-review.mov', route: 'localhost:5173 · PayrollPilot', chip: {kind: 'REAL', text: 'workbook file · synthetic data'}, share: 0.75,
        pending: ['Stage 1 expansion: per-worker packet table', 'Export workbook toast: draft version, original not updated', 'Stage 2 chips with blockers · Gusto: not prepared']},
      {layout: 'screen', screen: 's7b-workbook.mov', route: 'review-workbook.xlsx', chip: {kind: 'REAL', text: 'generated xlsx'}, share: 0.25,
        pending: ['Ledger tabs, one pending tab with its blocker']},
    ],
  },
];
