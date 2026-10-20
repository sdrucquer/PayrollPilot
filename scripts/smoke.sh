#!/usr/bin/env bash
# Smoke the backend: health, load the synthetic cycle, audit, list exceptions.
set -euo pipefail
BASE="${PP_BASE:-http://127.0.0.1:8000}"
FIXTURE="${1:-cycle_synthetic_v1}"
echo "# health"; curl -sf "$BASE/api/health"; echo
echo "# load $FIXTURE"
CYCLE=$(curl -sf -X POST "$BASE/api/cycles/load" -H 'content-type: application/json' -d "{\"source\":\"fixture\",\"name\":\"$FIXTURE\"}")
ID=$(printf '%s' "$CYCLE" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
echo "cycle id: $ID"
echo "# audit"; curl -sf -X POST "$BASE/api/cycles/$ID/audit" | python3 -c 'import json,sys; print(len(json.load(sys.stdin)["exceptions"]), "exceptions")'
echo "# events"; curl -sf "$BASE/api/events?cycle_id=$ID" | python3 -c 'import json,sys; print([e["type"] for e in json.load(sys.stdin)])'
