// Mirror of docs/contracts/CONTRACTS.md v1.1 (sections 0-5). Lane D keeps this in sync.
// The UI never computes money: every *_cents value is rendered as given, null renders as a dash.
import { z } from 'zod'

export const Provenance = z.enum(['real', 'cached', 'synthetic', 'seeded_issue', 'test_reply'])
export type Provenance = z.infer<typeof Provenance>

const cents = z.number().int().nullable()

export const SourceRef = z.object({
  system: z.enum(['jobber', 'gusto', 'quickbooks', 'owner_export', 'fixture']),
  record_id: z.string(),
  url: z.string().nullable(),
  captured_at: z.string(),
  snapshot_id: z.string(),
})
export type SourceRef = z.infer<typeof SourceRef>

export const SourceCoverage = z.object({
  system: z.string(),
  dataset: z.enum(['time_entries', 'jobs', 'workers', 'expenses', 'payments', 'payroll_runs', 'rates']),
  range_start: z.string(),
  range_end: z.string(),
  filters: z.record(z.string(), z.unknown()),
  record_count: z.number().int().nullable(),
  complete: z.boolean(),
  incomplete_reason: z.enum(['pagination_cut', 'permission', 'not_attempted', 'export_only']).nullable(),
  captured_at: z.string(),
  snapshot_id: z.string(),
  method: z.enum(['browser_use', 'api', 'owner_export', 'fixture']),
})
export type SourceCoverage = z.infer<typeof SourceCoverage>

export const StageState = z.object({
  state: z.enum(['not_started', 'collecting', 'auditing', 'resolving', 'review_ready', 'owner_approved']),
  scope_note: z.string(),
  unresolved_count: z.number().int(),
  dollars_affected_cents: cents,
})
export type StageState = z.infer<typeof StageState>

export const PayrollCycle = z.object({
  id: z.string(),
  contract_version: z.literal('1'),
  policy_version: z.string(),
  company_label: z.string(),
  company_ref: SourceRef.nullable(),
  period_start: z.string(),
  period_end: z.string(),
  payday: z.string().nullable(),
  business_tz: z.string(),
  workweeks: z.array(z.object({ start: z.string(), end: z.string() })),
  existing_run_status: z.enum(['unknown', 'none', 'draft', 'submitted', 'paid']),
  coverage: z.array(SourceCoverage),
  stage1: StageState,
  stage2: StageState,
  destination: z.enum(['not_prepared', 'internal_draft', 'external_draft_verified', 'submitted_verified', 'paid_verified']),
  provenance: Provenance,
})
export type PayrollCycle = z.infer<typeof PayrollCycle>

export const Worker = z.object({
  id: z.string(),
  display_name: z.string(),
  identity_status: z.enum(['verified', 'ambiguous', 'duplicate_profiles', 'unmatched']),
  payment_route: z.enum(['gusto', 'manual', 'unknown']),
  provenance: Provenance,
})
export type Worker = z.infer<typeof Worker>

export const Blocker = z.object({ code: z.string(), label: z.string(), exception_id: z.string().nullable() })
export type Blocker = z.infer<typeof Blocker>

export const Readiness = z.object({
  state: z.enum(['ready', 'partial', 'pending', 'blocked', 'not_meaningful']),
  scope: z.string(),
  blockers: z.array(Blocker),
  unknown_amount: z.boolean(),
  calculation_version: z.string(),
  last_computed_at: z.string(),
})
export type Readiness = z.infer<typeof Readiness>

export const CompKind = z.enum(['wages', 'quote_commission', 'marketing', 'tip', 'manager_pool'])
export type CompKind = z.infer<typeof CompKind>

export const CompensationItem = z.object({
  id: z.string(),
  cycle_id: z.string(),
  kind: CompKind,
  worker_id: z.string().nullable(),
  job_id: z.string().nullable(),
  policy_version: z.string(),
  inputs: z.record(z.string(), z.unknown()),
  computed: z.record(z.string(), z.unknown()).nullable(),
  readiness: Readiness,
  obligation_ids: z.array(z.string()),
  provenance: Provenance,
})
export type CompensationItem = z.infer<typeof CompensationItem>

export const ReadinessResponse = z.object({ stage1: Readiness, items: z.array(CompensationItem), workers: z.record(z.string(), Readiness).nullish() })
export type ReadinessResponse = z.infer<typeof ReadinessResponse>

export const ExceptionCategory = z.enum([
  'missing_job', 'long_shift', 'open_timer', 'overlap', 'duplicate_time', 'unassigned_time', 'schedule_mismatch',
  'identity', 'rate_unconfirmed', 'already_paid_allocation', 'unmatched_cost', 'cost_conflict', 'offsite_link',
  'quote_attribution', 'policy_missing', 'coverage_gap',
])
export const ExceptionState = z.enum([
  'detected', 'investigating', 'awaiting_reply', 'answer_received', 'needs_approval', 'needs_source_verification',
  'resolved', 'conflicting', 'insufficient_evidence', 'escalated',
])
export const PayrollException = z.object({
  id: z.string(),
  cycle_id: z.string(),
  category: ExceptionCategory,
  title: z.string(),
  observed: z.string(),
  expected: z.string(),
  evidence: z.array(SourceRef),
  entity_refs: z.object({
    worker_id: z.string().nullable().optional(),
    time_entry_ids: z.array(z.string()).optional(),
    job_ids: z.array(z.string()).optional(),
    cost_ids: z.array(z.string()).optional(),
    coverage: z.array(z.string()).optional(), // v1.1, for coverage_gap
  }),
  stage_impact: z.object({
    stage1_wages: z.enum(['none', 'blocks_worker', 'blocks_item']),
    stage2_costs: z.enum(['none', 'job_costing', 'commission', 'manager_pool']),
  }),
  dollars_affected_cents: cents,
  intended_respondent_role: z.enum(['ops_lead', 'owner', 'worker', 'quoter', 'accountant']),
  state: ExceptionState,
  next_action: z.string(),
  owner_agent: z.enum(['audit', 'resolution', 'payroll']),
  message_ids: z.array(z.string()),
  resolution_id: z.string().nullable(),
  provenance: Provenance,
  created_at: z.string(),
  updated_at: z.string(),
})
export type PayrollException = z.infer<typeof PayrollException>

export const MessageBatch = z.object({
  id: z.string(),
  cycle_id: z.string(),
  exception_ids: z.array(z.string()),
  intended_respondent_role: z.string(),
  intended_respondent_label: z.string(),
  actual_recipient: z.string(),
  channel: z.literal('imessage'),
  text: z.string(),
  text_hash: z.string(),
  declined_at: z.string().nullish(),
  approval_id: z.string().nullable(),
  state: z.enum(['draft', 'approved', 'sent', 'delivered', 'failed']),
  provider_message_id: z.string().nullable(),
  sent_at: z.string().nullable(),
  provider_status: z.string().nullable(),
  provenance: Provenance,
})
export type MessageBatch = z.infer<typeof MessageBatch>

export const InboundMessage = z.object({
  id: z.string(),
  provider_message_id: z.string(),
  provider_space_id: z.string().optional(),
  sender: z.string(),
  received_at: z.string(),
  raw_text: z.string(),
  correlated_batch_id: z.string().nullable(),
  dedupe_key: z.string(),
  respondent_actual: z.string(),
  respondent_intended_role: z.string(),
  provenance: Provenance,
})
export type InboundMessage = z.infer<typeof InboundMessage>

export const ParsedReply = z.object({
  inbound_id: z.string(),
  answers: z.array(z.object({
    exception_id: z.string(),
    status: z.enum(['answered', 'partial', 'ambiguous', 'conflicting', 'unaddressed']),
    extracted: z.record(z.string(), z.unknown()),
    confidence: z.number(),
    quote: z.string(),
  })),
  needs_clarification: z.array(z.string()),
  model: z.string(),
  schema_version: z.string(),
})
export type ParsedReply = z.infer<typeof ParsedReply>

export const Resolution = z.object({
  id: z.string(),
  exception_id: z.string(),
  cycle_id: z.string(),
  confirmed_facts: z.record(z.string(), z.unknown()),
  evidence: z.array(SourceRef),
  inbound_ids: z.array(z.string()),
  confirmer_actual: z.string(),
  confirmer_intended_role: z.string(),
  scope: z.record(z.string(), z.unknown()),
  approved_correction_id: z.string().nullable(),
  created_at: z.string(),
  memory_ref: z.string().nullable(),
})
export type Resolution = z.infer<typeof Resolution>

export const LocalCorrection = z.object({
  id: z.string(),
  resolution_id: z.string(),
  kind: z.enum(['job_allocation', 'rate_confirmation', 'cost_link', 'identity_merge', 'time_confirmation']),
  before: z.record(z.string(), z.unknown()),
  after: z.record(z.string(), z.unknown()),
  calculation_impact: z.record(z.string(), z.unknown()),
  approval_id: z.string().nullable(),
  state: z.enum(['proposed', 'approved', 'applied', 'invalidated']),
  applied_at: z.string().nullable(),
  target_version: z.string().optional(),
})
export type LocalCorrection = z.infer<typeof LocalCorrection>

export const Approval = z.object({
  id: z.string(),
  kind: z.enum(['message_send', 'local_correction', 'source_write', 'payroll_draft', 'estimate']),
  target_id: z.string(),
  target_version: z.string(),
  approver: z.string(),
  approved_at: z.string(),
  scope_text: z.string(),
  state: z.enum(['active', 'invalidated']),
  invalidated_reason: z.string().nullable(),
})
export type Approval = z.infer<typeof Approval>

export const EventType = z.enum([
  'cycle.created', 'snapshot.captured', 'audit.completed', 'exception.detected', 'exception.state_changed',
  'handoff.requested', 'handoff.accepted', 'message.drafted', 'approval.granted', 'approval.invalidated',
  'message.sent', 'message.delivery_status', 'message.received', 'reply.parsed', 'clarification.needed',
  'resolution.recorded', 'memory.written', 'memory.recalled', 'memory.applied', 'correction.proposed',
  'correction.applied', 'recalc.completed', 'readiness.changed', 'workbook.generated', 'workbook.verified',
  'blocked.unauthorized_instruction', 'budget.exhausted', 'run.stopped',
])
export const PPEvent = z.object({
  id: z.string(),
  at: z.string(),
  cycle_id: z.string(),
  actor: z.enum(['audit', 'resolution', 'payroll', 'owner', 'system', 'bridge']),
  type: EventType,
  summary: z.string(),
  refs: z.record(z.string(), z.unknown()),
  usage: z.object({
    model: z.string(), input_tokens: z.number().int(), output_tokens: z.number().int(), cost_usd: z.number(),
  }).nullable(),
  duration_ms: z.number().int().nullable(),
})
export type PPEvent = z.infer<typeof PPEvent>

export const Health = z.object({
  ok: z.boolean(),
  contract_version: z.string(),
  integrations: z.record(z.string(), z.enum(['tested', 'unverified', 'blocked'])),
})
export type Health = z.infer<typeof Health>

export const WorkbookArtifact = z.object({
  id: z.string(),
  path: z.string(),
  draft_version: z.string(),
  sheets: z.array(z.string()),
  verified_totals: z.record(z.string(), z.unknown()),
  original_updated: z.literal(false),
  note: z.string(),
})
export type WorkbookArtifact = z.infer<typeof WorkbookArtifact>

// GET /api/exceptions/{id}: Exception + messages + resolution + correction.
// The exact message/inbound split is not pinned in CONTRACTS section 5; we accept both shapes.
export const ExceptionDetail = PayrollException.extend({
  messages: z.array(z.unknown()).optional(),
  resolution: Resolution.nullable().optional(),
  correction: LocalCorrection.nullable().optional(),
})
export type ExceptionDetail = z.infer<typeof ExceptionDetail>
