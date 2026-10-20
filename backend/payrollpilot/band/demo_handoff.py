"""Real Band run of the product handoff (synthetic case). Usage:
  PP_BAND_ROOM_ID=<room> python -m payrollpilot.band.demo_handoff [--host-pid PID]
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime

from .cli import CliBand
from .handoff import deliver_to_payroll, handoff_to_resolution, request_owner_decision

EXC = {"id": "exc_0002", "category": "already_paid_allocation", "title": "Paid shift on 10/03 is on the wrong job",
       "stage_impact": {"stage1_wages": "none", "stage2_costs": "job_costing"},
       "intended_respondent_role": "ops_lead", "provenance": "synthetic"}


def log(event, **kw):
    print(json.dumps({"at": datetime.now().astimezone().isoformat(timespec="seconds"), "event": event, **kw}))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host-pid", type=int, default=0)
    args = ap.parse_args()
    band = CliBand()
    if args.host_pid:
        band.ensure_peers(args.host_pid)
    if not band.room_id:
        band.create_room()
    log("band.room", room_id=band.room_id)
    h = handoff_to_resolution(band, EXC)
    log("handoff.accepted" if h["accepted"] else "handoff.not_delivered", **h)
    d = request_owner_decision(band, "msg_batch_spike02", "sha256:0000000000000000", "send 1 question about exc_0002 (synthetic)")
    log("decision.requested", band_message_id=d)
    p = deliver_to_payroll(band, EXC, {"id": "corr_spike02", "kind": "job_allocation"}, h.get("task_uid"))
    log("handoff.payroll", **p)
    log("band.board", board=band.board())


if __name__ == "__main__":
    main()
