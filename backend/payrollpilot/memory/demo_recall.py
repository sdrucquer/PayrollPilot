"""T15 proof, two separate processes:

  python -m payrollpilot.memory.demo_recall write    # process 1: writes resolution res_01 to Cognee, exits
  python -m payrollpilot.memory.demo_recall recall   # process 2 (fresh): recalls and changes next_action
  python -m payrollpilot.memory.demo_recall recall --no-memory   # control: memory disabled -> asks again

Synthetic ids only (provenance: synthetic). Prints JSON lines for INTEGRATION-FINDINGS.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone

from .apply import ASK_AGAIN, apply_recall

RESOLUTION = {
    "id": "res_01",
    "exception_id": "exc_0001",
    "cycle_id": "cyc_synth01",
    "confirmed_facts": {
        "time_entry_id": "te_0001",
        "job_id": "job_02",
        "offsite_parent_job_id": "job_01",
        "site_note": "work at the off-site disposal location is billed to job_02",
    },
    "evidence": [{"system": "fixture", "record_id": "te_0001"}],
    "inbound_ids": ["msg_in_01"],
    "confirmer_actual": "owner_test_phone",
    "confirmer_intended_role": "ops_lead",
    "scope": {"company_label": "Pilot Co", "cycle_id": "cyc_synth01", "job_ids": ["job_02"], "worker_ids": ["wkr_01"]},
    "created_at": "2026-10-20T13:30:00-07:00",
    "provenance": "synthetic",
}
# Later case: a disposal receipt on the off-site child, job unknown.
LATER_CASE = {
    "exception_id": "exc_0007",
    "cycle_id": "cyc_synth01",
    "category": "unmatched_cost",
    "company_label": "Pilot Co",
    "parent_job_id": "job_01",
    "next_action": ASK_AGAIN,
    "query": "Pilot Co off-site disposal location: which job does off-site work under job_01 belong to?",
}
KNOWN = {"job_ids": {"job_01", "job_02", "job_03"}, "time_entry_ids": {"te_0001"}, "resolution_ids": {"res_01"}}


def log(event: str, **kw) -> None:
    print(json.dumps({"at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"), "pid": os.getpid(), "event": event, **kw}))


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["write", "recall"])
    ap.add_argument("--no-memory", action="store_true")
    ap.add_argument("--dev-fake", action="store_true", help="InMemoryMemory (dev only, NOT Cognee)")
    args = ap.parse_args()

    if args.dev_fake:
        from .base import InMemoryMemory

        mem = InMemoryMemory()
    elif not args.no_memory:
        from .cognee_memory import CogneeMemory

        mem = CogneeMemory()
    else:
        mem = None
    log("start", mode=args.mode, adapter=getattr(mem, "name", "disabled"))

    if args.mode == "write":
        t = time.time()
        ref = await mem.write_resolution(RESOLUTION)
        log("memory.written", memory_ref=ref, resolution_id=RESOLUTION["id"], duration_ms=int((time.time() - t) * 1000))
        return 0

    hits = [] if mem is None else await mem.recall(LATER_CASE["query"], {"company_label": "Pilot Co"})
    log("memory.recalled", query=LATER_CASE["query"], hit_count=len(hits), hits=[h.text for h in hits][:3])
    out = apply_recall(LATER_CASE, hits, KNOWN)
    log("memory.applied" if out["applied"] else "memory.not_applied", exception_id=LATER_CASE["exception_id"], **out)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
