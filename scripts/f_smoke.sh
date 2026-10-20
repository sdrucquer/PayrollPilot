#!/usr/bin/env bash
# F-03 integrated rehearsal (lane F) against the RUNNING stack: backend :8000, bridge :3001, web :5173.
#
#   scripts/f_smoke.sh                 # dry run: everything except the real send and the reply wait
#   scripts/f_smoke.sh --send          # also sends ONE real iMessage to the allowlisted test handle and
#                                      #   waits for the owner's reply (REPLY_WAIT seconds, default 240)
#   scripts/f_smoke.sh --send --out tests/integration/REHEARSAL.md   # append a markdown transcript
#
# Each step prints PASS/FAIL/SKIP, the HTTP status and key ids. Nothing here fakes a reply: if no real reply
# arrives in time the inbound steps FAIL with "no reply". Exit code = number of FAILed steps (0 = all pass).
set -u
BASE=${BASE:-http://127.0.0.1:8000}
BRIDGE=${BRIDGE:-http://127.0.0.1:3001}
WEB=${WEB:-http://127.0.0.1:5173}
FIXTURE=${FIXTURE:-cycle_synthetic_v1}
CYC=${CYC:-cyc_synth_v1}
REPLY_WAIT=${REPLY_WAIT:-240}
SEND=0; OUT=""
while [ $# -gt 0 ]; do
  case "$1" in --send) SEND=1;; --out) OUT="$2"; shift;; *) echo "unknown arg $1"; exit 2;; esac; shift
done
command -v jq >/dev/null || { echo "jq required"; exit 2; }

fails=0; n=0; rows=()
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

# call METHOD PATH [JSON]  -> sets CODE and writes body to $TMP/body
call() {
  local m="$1" p="$2" d="${3:-}" url
  case "$p" in http*) url="$p";; *) url="$BASE$p";; esac
  : > "$TMP/body"
  if [ -n "$d" ]; then
    CODE=$(curl -s -m 60 -o "$TMP/body" -w '%{http_code}' -X "$m" -H 'Content-Type: application/json' -d "$d" "$url")
  else
    CODE=$(curl -s -m 60 -o "$TMP/body" -w '%{http_code}' -X "$m" "$url")
  fi
  [ -n "$CODE" ] || CODE=000
}
j() { jq -r "$@" "$TMP/body" 2>/dev/null; }

# step NAME RESULT DETAIL
step() {
  n=$((n+1))
  local name="$1" res="$2" detail="$3"
  [ "$res" = FAIL ] && fails=$((fails+1))
  printf '%2d %-4s %-26s http=%s %s\n' "$n" "$res" "$name" "${CODE:-000}" "$detail"
  rows+=("| $n | $name | $res | ${CODE:-000} | ${detail//|//} |")
}
expect() { # NAME WANT_CODE DETAIL
  if [ "$CODE" = "$2" ]; then step "$1" PASS "$3"; else step "$1" FAIL "$3 :: $(head -c 300 "$TMP/body" | tr '\n' ' ')"; fi
}

echo "PayrollPilot rehearsal $(date '+%Y-%m-%d %H:%M %Z')  send=$SEND  backend=$BASE"

# ---- processes
call GET /api/health
expect "backend health" 200 "integrations=$(j -c '.integrations' ) core=$(j -c '.core // empty')"
call GET "$BRIDGE/health"
expect "bridge health" 200 "$(head -c 160 "$TMP/body" | tr '\n' ' ')"
call GET "$WEB/"
expect "web served" 200 "$(grep -o '<title>[^<]*' "$TMP/body" | head -1 | sed 's/<title>//')"

# ---- load + audit
call POST /api/cycles/load "{\"source\":\"fixture\",\"name\":\"$FIXTURE\"}"
expect "load cycle" 200 "cycle=$(j .id) provenance=$(j .provenance) destination=$(j .destination)"
call POST "/api/cycles/$CYC/audit"
expect "audit" 200 "exceptions=$(j '.exceptions | length')"
call GET "/api/cycles/$CYC/exceptions"
APA=$(j '[.[] | select(.category=="already_paid_allocation")][0].id')
OFF=$(j '[.[] | select(.category=="offsite_link")][0].id')
[ -n "$APA" ] && [ "$APA" != null ] && step "exceptions" PASS "already_paid_allocation=$APA offsite_link=$OFF" \
  || step "exceptions" FAIL "already_paid_allocation not found"
call GET /api/cycles/$CYC/readiness
expect "readiness before" 200 "stage1=$(j .stage1.state) items=$(j -c '[.items[] | {(.id): .readiness.state}] | add')"
R_BEFORE=$(j -c '.stage1')

# ---- handoff + draft + approve + send (C-05 routes)
call POST "/api/exceptions/$APA/handoff"
expect "handoff audit->resolution" 200 "$(j -c '.event.type // .type // empty') band=$(j -c '.band // empty' | head -c 80)"
call POST /api/messages/draft "{\"exception_ids\":[\"$APA\"]}"
BATCH=$(j .id); HASH=$(j ".target_version // .text_hash")
expect "draft question" 200 "batch=$BATCH recipient=$(j .actual_recipient_masked) chars=$(j '.text | length')"
call POST /api/approvals "{\"kind\":\"message_send\",\"target_id\":\"$BATCH\",\"target_version\":\"$HASH\",\"scope_text\":\"Send this exact text to the allowlisted test recipient\"}"
expect "approve send" 200 "approval=$(j .id) state=$(j .state)"

SENT_AT=$(date -u +%Y-%m-%dT%H:%M:%S)
if [ "$SEND" = 1 ]; then
  call POST "/api/messages/$BATCH/send"
  expect "send iMessage" 200 "state=$(j .state) provider_message_id=$(j .provider_message_id) provenance=$(j .provenance)"
  call POST "/api/messages/$BATCH/send"
  if [ "$CODE" = 200 ] && [ "$(j .duplicate)" = true ]; then step "retry send is duplicate" PASS "no second send"; \
  else step "retry send is duplicate" FAIL "$(head -c 200 "$TMP/body")"; fi

  echo "   waiting up to ${REPLY_WAIT}s for the owner's real reply..."
  got=""; t=0
  while [ $t -lt "$REPLY_WAIT" ]; do
    call GET "/api/events?cycle_id=$CYC"
    got=$(j "[.[] | select(.type==\"message.received\" and .refs.batch_id==\"$BATCH\")][0].refs.inbound_id")
    [ -n "$got" ] && [ "$got" != null ] && break
    sleep 5; t=$((t+5))
  done
  if [ -n "$got" ] && [ "$got" != null ]; then
    step "real reply received" PASS "inbound=$got after ~${t}s"
    sleep 3
    call GET "/api/events?cycle_id=$CYC"
    step "reply parsed" "$( [ "$(j "[.[] | select(.type==\"reply.parsed\" and .refs.inbound_id==\"$got\")] | length")" -ge 1 ] && echo PASS || echo FAIL)" \
      "$(j "[.[] | select(.refs.inbound_id==\"$got\") | .type] | join(\",\")")"
    call GET "/api/exceptions/$APA"
    expect "exception after reply" 200 "state=$(j '.state // .exception.state') next=$(j '.next_action // .exception.next_action' | head -c 80)"
  else
    step "real reply received" FAIL "no reply within ${REPLY_WAIT}s"
  fi
else
  CODE=-; step "send iMessage" SKIP "dry run; pass --send to text the allowlisted handle"
  step "real reply received" SKIP "dry run"
fi

# ---- correction (T02) + recalc
call POST /api/corrections "{\"kind\":\"job_allocation\",\"cycle_id\":\"$CYC\",\"after\":{\"time_entry_id\":\"te_0014\",\"job_id\":\"job_02\"}}"
CORR=$(j .id); CV=$(j .target_version)
expect "propose correction" 200 "corr=$CORR wages_delta=$(j .calculation_impact.stage1_wages_delta_cents) jobs=$(j -c .calculation_impact.job_costing_delta)"
call POST /api/approvals "{\"kind\":\"local_correction\",\"target_id\":\"$CORR\",\"target_version\":\"$CV\",\"scope_text\":\"Allocate te_0014 to job_02 locally (no source write)\"}"
expect "approve correction" 200 "approval=$(j .id)"
call POST "/api/corrections/$CORR/apply"
expect "apply correction" 200 "state=$(j .correction.state) readiness_changes=$(j '[.readiness_changes[]?.scope] | join(",")')"
call GET /api/cycles/$CYC/readiness
R_AFTER=$(j -c '.stage1')
expect "readiness after" 200 "stage1=$(j .stage1.state) wages_unchanged=$([ "$R_BEFORE" = "$R_AFTER" ] && echo yes || echo NO) quote_job_01=$(j '.items[] | select(.id=="ci_quote_job_01") | .readiness.blockers | length') blockers"

# ---- packet + workbook
call GET /api/cycles/$CYC/packet
DV=$(j .draft_version)
expect "packet" 200 "draft=$DV destination=$(j .destination) stage1_gross_ready_cents=$(j .totals.stage1_gross_ready_cents)"
call POST /api/cycles/$CYC/workbook
if [ "$CODE" = 200 ] && [ "$(j .draft_version)" = "$DV" ] && [ "$(j .original_updated)" = false ]; then
  step "workbook" PASS "id=$(j .id) verified=$(j .verified) sheets=$(j '.sheets | length') same_draft=yes"
else step "workbook" FAIL "$(head -c 300 "$TMP/body")"; fi

# ---- memory recall that changes the next action (T15)
call POST /api/memory/recall-check "{\"query\":\"Which parent job does the off-site disposal run (Job 03) belong to?\",\"exception_id\":\"$OFF\",\"scope\":{\"cycle_id\":\"$CYC\",\"company_label\":\"Pilot Co\"}}"
expect "memory recall-check" 200 "hits=$(j '.hits | length') applied=$(j .applied) before=$(j .next_action_before | head -c 50) after=$(j .next_action_after | head -c 50)"

# ---- event trail sanity
call GET "/api/events?cycle_id=$CYC"
step "event trail" "$( [ "$CODE" = 200 ] && echo PASS || echo FAIL)" \
  "sent=$(j '[.[]|select(.type=="message.sent")]|length') blocked=$(j '[.[]|select(.type=="blocked.unauthorized_instruction")]|length') types=$(j '[.[].type]|unique|length')"

echo "RESULT: $((n-fails))/$n steps not failed; $fails FAIL"
if [ -n "$OUT" ]; then
  {
    printf '\n## Rehearsal %s (send=%s)\n\n| # | step | result | http | detail |\n|---|---|---|---|---|\n' "$(date '+%Y-%m-%d %H:%M %Z')" "$SEND"
    printf '%s\n' "${rows[@]}"
    printf '\nResult: %d FAIL of %d steps.\n' "$fails" "$n"
  } >> "$OUT"
  echo "transcript appended to $OUT"
fi
exit "$fails"
