"""Pydantic v2 mirror of docs/contracts/CONTRACTS.md sections 1-3 (contract_version "1").

Lead-owned after lane A's first PR. Field names are identical to CONTRACTS.md.
Models use ``extra="allow"`` so fixture fields not yet mirrored are preserved,
never dropped. Money fields are ``int | None`` cents; time fields ``int | None``
minutes. Unknown is ``None``, never ``0``.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

CONTRACT_VERSION = "1"

Provenance = Literal["real", "cached", "synthetic", "seeded_issue", "test_reply"]


class _Model(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


# ---- section 0 ---------------------------------------------------------------
class SourceRef(_Model):
    system: Literal["jobber", "gusto", "quickbooks", "owner_export", "fixture"]
    record_id: str
    url: Optional[str] = None
    captured_at: Optional[str] = None
    snapshot_id: Optional[str] = None


# ---- section 1 ---------------------------------------------------------------
class SourceCoverage(_Model):
    system: str
    dataset: Literal["time_entries", "jobs", "workers", "expenses", "payments", "payroll_runs", "rates"]
    range_start: Optional[str] = None
    range_end: Optional[str] = None
    filters: dict[str, Any] = Field(default_factory=dict)
    record_count: Optional[int] = None
    complete: bool
    incomplete_reason: Optional[Literal["pagination_cut", "permission", "not_attempted", "export_only"]] = None
    captured_at: Optional[str] = None
    snapshot_id: Optional[str] = None
    method: Literal["browser_use", "api", "owner_export", "fixture"]


class StageState(_Model):
    state: Literal["not_started", "collecting", "auditing", "resolving", "review_ready", "owner_approved"] = "not_started"
    scope_note: Optional[str] = None
    unresolved_count: Optional[int] = None
    dollars_affected_cents: Optional[int] = None


class Workweek(_Model):
    start: str
    end: str


class PayrollCycle(_Model):
    id: str
    contract_version: str = CONTRACT_VERSION
    policy_version: Optional[str] = None
    company_label: str = "Pilot Co"
    company_ref: Optional[SourceRef] = None
    period_start: str
    period_end: str
    payday: Optional[str] = None
    business_tz: str = "America/New_York"
    workweeks: list[Workweek] = Field(default_factory=list)
    existing_run_status: Literal["unknown", "none", "draft", "submitted", "paid"] = "unknown"
    coverage: list[SourceCoverage] = Field(default_factory=list)
    stage1: StageState = Field(default_factory=StageState)
    stage2: StageState = Field(default_factory=StageState)
    destination: Literal[
        "not_prepared", "internal_draft", "external_draft_verified", "submitted_verified", "paid_verified"
    ] = "not_prepared"
    provenance: Literal["real", "synthetic"]


class WorkerRate(_Model):
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    rate_cents_per_hour: Optional[int] = None
    category: Literal["hourly", "team_leader", "manual", "unknown"] = "unknown"
    evidence: Optional[SourceRef] = None
    status: Literal["verified", "unconfirmed"] = "unconfirmed"


class Worker(_Model):
    id: str
    display_name: str
    jobber_ref: Optional[SourceRef] = None
    gusto_ref: Optional[SourceRef] = None
    identity_status: Literal["verified", "ambiguous", "duplicate_profiles", "unmatched"] = "unmatched"
    rates: list[WorkerRate] = Field(default_factory=list)
    payment_route: Literal["gusto", "manual", "unknown"] = "unknown"
    provenance: Provenance


class TimeEntry(_Model):
    id: str
    worker_id: str
    job_id: Optional[str] = None
    date: str
    start: Optional[str] = None
    end: Optional[str] = None
    duration_minutes: Optional[int] = None
    approved_in_source: Optional[bool] = None
    open_timer: bool = False
    scheduled_minutes: Optional[int] = None
    paid_status: Literal["paid_prior_cycle", "unpaid", "unknown"] = "unknown"
    paid_ref: Optional[SourceRef] = None
    source_ref: SourceRef
    version_hash: Optional[str] = None
    provenance: Provenance


class QuoterCandidate(_Model):
    worker_id: str
    basis: Literal["salesperson_field", "confirmed_by_owner", "confirmed_by_ops"]


class Job(_Model):
    id: str
    display_name: str
    parent_job_id: Optional[str] = None
    status: Optional[str] = None
    adjusted_invoice_cents: Optional[int] = None
    final_payment_verified: Optional[bool] = None
    quoter_candidates: list[QuoterCandidate] = Field(default_factory=list)
    source_ref: SourceRef
    provenance: Provenance


class CycleAllocation(_Model):
    original_cycle_id: Optional[str] = None
    allocated_cycle_id: Optional[str] = None
    state: Literal["none", "proposed", "approved", "finalized"] = "none"
    finalization_evidence: Optional[SourceRef] = None
    version: int = 1


class Receipt(_Model):
    id: str
    job_id: Optional[str] = None
    amount_cents: Optional[int] = None
    payment_date: Optional[str] = None
    kind: Literal["payment", "deposit", "tip", "refund"]
    status: Literal["succeeded", "failed", "pending"]
    source_ref: SourceRef
    cycle_allocation: Optional[CycleAllocation] = None


class CostRepresentation(_Model):
    kind: Literal["bank", "receipt", "jobber_expense", "reimbursement", "estimate"]
    source_ref: SourceRef
    amount_cents: Optional[int] = None


class JobAllocation(_Model):
    job_id: str
    amount_cents: Optional[int] = None


class EconomicCost(_Model):
    id: str
    amount_cents: Optional[int] = None
    description: Optional[str] = None
    cost_date: Optional[str] = None
    representations: list[CostRepresentation] = Field(default_factory=list)
    job_allocations: list[JobAllocation] = Field(default_factory=list)
    categorized: bool = False
    allocated: bool = False
    included_in_calc: bool = False
    supersedes_cost_id: Optional[str] = None
    conflict: Optional[Literal["amount_mismatch", "job_uncertain"]] = None
    provenance: Provenance


class Settlement(_Model):
    date: str
    amount_cents: int
    reference: Optional[str] = None
    evidence: Optional[SourceRef] = None
    verified: bool = False


class Obligation(_Model):
    id: str
    kind: Literal["wages", "quote_commission", "marketing", "tip", "manager", "reimbursement"]
    worker_id: Optional[str] = None
    job_id: Optional[str] = None
    earning_period: Optional[dict[str, str]] = None
    recognition_cycle_id: Optional[str] = None
    gross_cents: Optional[int] = None
    status: Literal["proposed", "recognized", "settled_partial", "settled"] = "proposed"
    settlements: list[Settlement] = Field(default_factory=list)
    balance_cents: Optional[int] = None


# ---- section 2 ---------------------------------------------------------------
ExceptionCategory = Literal[
    "missing_job", "long_shift", "open_timer", "overlap", "duplicate_time", "unassigned_time", "schedule_mismatch",
    "identity", "rate_unconfirmed", "already_paid_allocation", "unmatched_cost", "cost_conflict", "offsite_link",
    "quote_attribution", "policy_missing", "coverage_gap",
]
ExceptionState = Literal[
    "detected", "investigating", "awaiting_reply", "answer_received", "needs_approval", "needs_source_verification",
    "resolved", "conflicting", "insufficient_evidence", "escalated",
]


class EntityRefs(_Model):
    worker_id: Optional[str] = None
    time_entry_ids: list[str] = Field(default_factory=list)
    job_ids: list[str] = Field(default_factory=list)
    cost_ids: list[str] = Field(default_factory=list)


class StageImpact(_Model):
    stage1_wages: Literal["none", "blocks_worker", "blocks_item"] = "none"
    stage2_costs: Literal["none", "job_costing", "commission", "manager_pool"] = "none"


class PayrollException(_Model):
    """CONTRACTS ``Exception`` (renamed to avoid shadowing the builtin)."""

    id: str
    cycle_id: str
    category: ExceptionCategory
    title: str
    observed: Optional[str] = None
    expected: Optional[str] = None
    evidence: list[SourceRef] = Field(default_factory=list)
    entity_refs: EntityRefs = Field(default_factory=EntityRefs)
    stage_impact: StageImpact = Field(default_factory=StageImpact)
    dollars_affected_cents: Optional[int] = None
    intended_respondent_role: Optional[Literal["ops_lead", "owner", "worker", "quoter", "accountant"]] = None
    state: ExceptionState = "detected"
    next_action: Optional[str] = None
    owner_agent: Literal["audit", "resolution", "payroll"] = "audit"
    message_ids: list[str] = Field(default_factory=list)
    resolution_id: Optional[str] = None
    provenance: Literal["real", "seeded_issue", "synthetic"]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MessageBatch(_Model):
    id: str
    cycle_id: str
    exception_ids: list[str]
    intended_respondent_role: str
    intended_respondent_label: Optional[str] = None
    actual_recipient: str
    channel: Literal["imessage"] = "imessage"
    text: str
    text_hash: str
    approval_id: Optional[str] = None
    state: Literal["draft", "approved", "sent", "delivered", "failed"] = "draft"
    provider_message_id: Optional[str] = None
    sent_at: Optional[str] = None
    provider_status: Optional[str] = None
    provenance: Provenance = "real"


class InboundMessage(_Model):
    id: str
    provider_message_id: str
    provider_space_id: Optional[str] = None
    sender: Optional[str] = None
    received_at: str
    raw_text: str
    correlated_batch_id: Optional[str] = None
    dedupe_key: Optional[str] = None
    respondent_actual: Optional[str] = None
    respondent_intended_role: Optional[str] = None
    provenance: Provenance = "test_reply"


class ParsedAnswer(_Model):
    exception_id: str
    status: Literal["answered", "partial", "ambiguous", "conflicting", "unaddressed"]
    extracted: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    quote: Optional[str] = None


class ParsedReply(_Model):
    inbound_id: str
    answers: list[ParsedAnswer]
    needs_clarification: list[str] = Field(default_factory=list)
    model: Optional[str] = None
    schema_version: str = "1"


class Resolution(_Model):
    id: str
    exception_id: str
    cycle_id: str
    confirmed_facts: dict[str, Any]
    evidence: list[SourceRef] = Field(default_factory=list)
    inbound_ids: list[str] = Field(default_factory=list)
    confirmer_actual: Optional[str] = None
    confirmer_intended_role: Optional[str] = None
    scope: dict[str, Any] = Field(default_factory=dict)
    approved_correction_id: Optional[str] = None
    created_at: Optional[str] = None
    memory_ref: Optional[str] = None


class LocalCorrection(_Model):
    id: str
    resolution_id: Optional[str] = None
    kind: Literal["job_allocation", "rate_confirmation", "cost_link", "identity_merge", "time_confirmation"]
    before: dict[str, Any]
    after: dict[str, Any]
    calculation_impact: Optional[dict[str, Any]] = None
    approval_id: Optional[str] = None
    state: Literal["proposed", "approved", "applied", "invalidated"] = "proposed"
    applied_at: Optional[str] = None


ApprovalKind = Literal["message_send", "local_correction", "source_write", "payroll_draft", "estimate"]


class Approval(_Model):
    id: str
    kind: ApprovalKind
    target_id: str
    target_version: str
    approver: Literal["owner"] = "owner"
    approved_at: str
    scope_text: str
    state: Literal["active", "invalidated"] = "active"
    invalidated_reason: Optional[str] = None


# ---- section 3 ---------------------------------------------------------------
class Blocker(_Model):
    code: str
    label: str
    exception_id: Optional[str] = None


class Readiness(_Model):
    state: Literal["ready", "partial", "pending", "blocked", "not_meaningful"]
    scope: Optional[str] = None
    blockers: list[Blocker] = Field(default_factory=list)
    unknown_amount: bool = False
    calculation_version: Optional[str] = None
    last_computed_at: Optional[str] = None


class CompensationItem(_Model):
    id: str
    cycle_id: str
    kind: Literal["wages", "quote_commission", "marketing", "tip", "manager_pool"]
    worker_id: Optional[str] = None
    job_id: Optional[str] = None
    policy_version: Optional[str] = None
    inputs: dict[str, Any] = Field(default_factory=dict)
    computed: Optional[dict[str, Any]] = None
    readiness: Readiness
    obligation_ids: list[str] = Field(default_factory=list)
    provenance: Literal["synthetic", "real"]


# ---- section 4 ---------------------------------------------------------------
class Event(_Model):
    id: str
    at: str
    cycle_id: Optional[str] = None
    actor: Literal["audit", "resolution", "payroll", "owner", "system", "bridge"]
    type: str
    summary: str
    refs: dict[str, Any] = Field(default_factory=dict)
    usage: Optional[dict[str, Any]] = None
    duration_ms: Optional[int] = None


# ---- section 5 request bodies -------------------------------------------------
class LoadCycleRequest(_Model):
    source: Literal["fixture", "private_snapshot"]
    name: str


class ApprovalRequest(_Model):
    kind: ApprovalKind
    target_id: str
    target_version: str
    scope_text: str


class CorrectionRequest(_Model):
    resolution_id: Optional[str] = None
    kind: Literal["job_allocation", "rate_confirmation", "cost_link", "identity_merge", "time_confirmation"]
    after: dict[str, Any]
