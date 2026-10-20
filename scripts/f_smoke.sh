#!/usr/bin/env bash
# F-03 integrated rehearsal (lane F) against the RUNNING stack: backend :8000, bridge :3001, web :5173.
#
#   scripts/f_smoke.sh --observe       # GET-only: inspect the existing owner-gated loop, no effects
#   scripts/f_smoke.sh                 # MUTATING isolated rehearsal, except send/reply wait
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
SEND=0; OBSERVE=0; OUT=""
while [ $# -gt 0 ]; do
  case "$1" in --send) SEND=1;; --observe) OBSERVE=1;; --out) OUT="$2"; shift;; *) echo "unknown arg $1"; exit 2;; esac; shift
done
[ "$OBSERVE" = 1 ] && [ "$SEND" = 1 ] && { echo "--observe cannot be combined with --send"; exit 2; }
command -v jq >/dev/null || { echo "jq required"; exit 2; }

fails=0; n=0; rows=()
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

# call METHOD PATH [JSON]  -> sets CODE and writes body to $TMP/body
call() {
  local m="$1" p="$2" d="${3:-}" url
  [ "$OBSERVE" = 1 ] && [ "$m" != GET ] && { echo "observation refuses non-GET request" >&2; exit 2; }
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

finish() {
  echo "RESULT: $((n-fails))/$n steps not failed; $fails FAIL"
  if [ -n "$OUT" ]; then
    {
      printf '\n## Rehearsal %s (send=%s, observe=%s)\n\n' "$(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z')" "$SEND" "$OBSERVE"
      [ "$OBSERVE" = 1 ] && printf 'GET-only observation of existing evidence; no new send, reply, approval, correction, workbook or recall was performed. Missing required evidence fails; skipped actions are not proofs.\n\n'
      printf '| # | step | result | http | detail |\n|---|---|---|---|---|\n'
      printf '%s\n' "${rows[@]}"
      printf '\nResult: %d FAIL of %d steps.\n' "$fails" "$n"
    } >> "$OUT"
    echo "transcript appended to $OUT"
  fi
  exit "$fails"
}

echo "PayrollPilot rehearsal $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') send=$SEND observe=$OBSERVE"

if [ "$OBSERVE" = 1 ]; then
  # Never echo response bodies, summaries, contacts, amounts or free text. Provider modes
  # and evidence counts are allowlisted. This path does not create owner approvals.
  observed() {
    if [ "$CODE" = 200 ] && [ "$2" = true ]; then step "$1" PASS "$3"; else step "$1" FAIL "$3"; fi
  }
  call GET /api/health
  observed "backend health" "$(j '.ok == true')" "existing process; no restart"
  call GET /api/comms/health
  observed "active real comms" "$(j '.messaging == "bridge" and .memory == "cognee" and .band == "band_cli" and .llm_key_present == true and .band_room_configured == true')" "requires bridge, Cognee, Band CLI and configured model/room"
  call GET "$BRIDGE/health"
  observed "bridge health" "$(j '.ok == true and .mode == "real"')" "requires real bridge"
  call GET "$WEB/"
  observed "web served" true "HTTP availability only; API-mode UI must be checked separately"
  call GET "/api/cycles/$CYC"
  observed "existing cycle" "$(j --arg id "$CYC" '.id == $id')" "existing cycle; not reloaded or audited"
  call GET "/api/cycles/$CYC/exceptions"
  observed "exception evidence" "$(j 'type == "array" and length > 0 and any(.[]; (.evidence | length) > 0)')" "evidence present; no private record text printed"
  call GET "/api/cycles/$CYC/readiness"
  observed "readiness available" "$(j '(.stage1.state | type) == "string" and (.items | type) == "array"')" "readiness reported; blocked items remain blocked"
  call GET "/api/cycles/$CYC/packet"
  observed "review packet" "$(j '.draft_version != null and .destination == "internal_draft"')" "internal draft only; nothing submitted"
  call GET "/api/events?cycle_id=$CYC&limit=5000"
  if [ "$CODE" = 200 ] && [ "$(j 'type == "array"')" = true ]; then cp "$TMP/body" "$TMP/events"; else echo '[]' > "$TMP/events"; fi
  observed "event trail" "$(j 'type == "array" and length > 0')" "current cycle audit trail"
  recorded() {
    local count
    count=$(jq --arg type "$2" '[.[] | select(.type == $type)] | length' "$TMP/events")
    observed "$1" "$([ "$count" -gt 0 ] && echo true || echo false)" "recorded $2 count=$count; no new action performed"
  }
  recorded "Band handoff evidence" handoff.accepted
  # Correlate a real bridge send to its received and parsed reply, rather than counting
  # unrelated fake/test sends as a live round trip.
  chain=$(jq '[.[] | select(.type == "message.sent" and .refs.messaging_mode == "bridge") | .refs.batch_id] as $sent | [.[] | select(.type == "message.received" and (.refs.batch_id as $b | $sent | index($b))) | .refs.inbound_id] as $inbound | any(.[]; .type == "reply.parsed" and (.refs.inbound_id as $i | $inbound | index($i)))' "$TMP/events")
  observed "recorded live round trip" "$chain" "requires correlated bridge send, inbound and parsed reply"
  recorded "owner approval log" approval.granted
  recorded "correction applied" correction.applied
  recorded "readiness change log" readiness.changed
  recorded "Cognee write log" memory.written
  recalled=$(jq 'any(.[]; .type == "memory.recalled" and .refs.memory_adapter == "cognee")' "$TMP/events")
  observed "Cognee recall log" "$recalled" "requires recorded Cognee adapter; HTTP 200 alone is insufficient"
  applied=$(jq 'any(.[]; .type == "memory.applied" and .refs.proposed.job_id == "job_02" and (.refs.proposed.based_on_resolution_ids | length) > 0)' "$TMP/events")
  observed "memory action change log" "$applied" "requires recorded proposal to job_02 with resolution refs; full before/after proof belongs in C ledger"
  verified=$(jq '[.[] | select(.type == "workbook.generated") | .refs.workbook_id] as $built | any(.[]; .type == "workbook.verified" and (.refs.workbook_id as $w | $built | index($w)))' "$TMP/events")
  observed "workbook verification log" "$verified" "requires matching generated/verified artifact; no workbook generated now"
  CODE=-
  step "new effects" SKIP "owner alone approves; send/apply/export/recall not invoked"
  step "exact T15 comparison" SKIP "use C's captured response before/after and approval_created=false; event counts alone do not establish every T15 condition"
  finish
fi

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

finish
