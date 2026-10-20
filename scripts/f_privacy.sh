#!/usr/bin/env bash
# F-04 privacy sweep (lane F). Run from anywhere: scripts/f_privacy.sh
# Scans git-tracked files (plus web/dist if present) for phone numbers, API keys, personal email
# domains and private denylist terms; checks .gitignore coverage and that no xlsx is tracked outside
# data/fixtures. Prints file:line plus a MASKED match only; never prints denylist terms or full secrets.
# Exit 0 = clean, 1 = findings.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2

fail=0
section() { printf '\n== %s\n' "$1"; }
ok() { printf '  ok   %s\n' "$1"; }
bad() { printf '  FAIL %s\n' "$1"; fail=1; }

# Tracked text files, plus the built web bundle if it exists (untracked build output still ships).
files=$(git ls-files | grep -vE '\.(png|jpg|jpeg|gif|ico|xlsx|lock|woff2?|ttf|mp4|mov|webm|pdf)$|(^|/)bun\.lock$|package-lock\.json$')
if [ -d web/dist ]; then files="$files"$'\n'"$(find web/dist -type f \( -name '*.js' -o -name '*.html' -o -name '*.css' -o -name '*.json' -o -name '*.map' \))"; fi

mask() { sed -E 's/([A-Za-z0-9+@._-]{3})[A-Za-z0-9+@._-]*([A-Za-z0-9]{2})/\1***\2/g'; }

scan() { # $1 label, $2 extended regex, $3 optional allow regex (matches to ignore)
  local label="$1" re="$2" allow="${3:-}" hits
  hits=$(printf '%s\n' "$files" | tr '\n' '\0' | xargs -0 grep -nIoE "$re" 2>/dev/null || true)
  [ -n "$allow" ] && hits=$(printf '%s\n' "$hits" | grep -vE "$allow" || true)
  hits=$(printf '%s\n' "$hits" | grep -v '^$' || true)
  if [ -z "$hits" ]; then ok "$label: none"; else
    bad "$label: $(printf '%s\n' "$hits" | wc -l | tr -d ' ') hit(s)"
    printf '%s\n' "$hits" | head -20 | while IFS= read -r h; do
      loc=$(printf '%s' "$h" | cut -d: -f1,2); m=$(printf '%s' "$h" | cut -d: -f3- | mask)
      printf '       %s: %s\n' "$loc" "$m"
    done
  fi
}

section "Secrets and contact data"
# E.164 / US phone numbers. Allowed: the NANP 555 range (fiction/test handles such as +15550000012).
# Also allowed: NANP numbers whose area code starts with 0 or 1 (never assignable, e.g. +10000000000 placeholders).
scan "E.164 phone numbers" '\+[1-9][0-9]{9,14}' ':\+1(555|[01][0-9]{2})[0-9]{7}$'
scan "formatted US phone numbers" '\(?[2-9][0-9]{2}\)?[ .-][2-9][0-9]{2}[ .-][0-9]{4}' '555[ .-]'
scan "OpenRouter keys (sk-or-)" 'sk-or-[A-Za-z0-9_-]{8,}'
scan "other API keys (sk-, bu_, ghp_, xox)" '(sk-[A-Za-z0-9]{20,}|bu_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|xox[abp]-[A-Za-z0-9-]{10,})'
scan "personal email addresses" '[A-Za-z0-9._%+-]+@(gmail|yahoo|icloud|hotmail|outlook|me)\.com' 'noreply@anthropic\.com'
scan "assigned secrets in env-style lines" '^[A-Z_]*(KEY|SECRET|TOKEN)=[^[:space:]#]{6,}' '=(change-me|tok|tok-test)$'

section "Private denylist"
if [ -f data/private/denylist.txt ]; then
  n=0; terms=0
  while IFS= read -r term; do
    term=$(printf '%s' "$term" | sed 's/[[:space:]]*$//')
    case "$term" in ''|\#*) continue;; esac
    terms=$((terms+1))
    c=$(printf '%s\n' "$files" | tr '\n' '\0' | xargs -0 grep -nIiwF -- "$term" 2>/dev/null | cut -d: -f1,2 || true)
    if [ -n "$c" ]; then n=$((n+1)); printf '       term #%d found at: %s\n' "$terms" "$(printf '%s' "$c" | head -5 | tr '\n' ' ')"; fi
  done < data/private/denylist.txt
  if [ "$n" -eq 0 ]; then ok "denylist: $terms term(s), no hits"; else bad "denylist: $n of $terms term(s) found (terms not printed)"; fi
else
  printf '  SKIP denylist: data/private/denylist.txt not present (lead supplies it; one term per line)\n'
fi

section ".gitignore coverage"
for p in docs/private/x data/private/x .env backend/.env bridge/.env; do
  if git check-ignore -q "$p"; then ok "ignored: ${p%/x}"; else bad "NOT ignored: ${p%/x}"; fi
done
tracked_private=$(git ls-files docs/private data/private | head -5)
[ -z "$tracked_private" ] && ok "nothing tracked under docs/private or data/private" || bad "tracked private files: $tracked_private"
tracked_env=$(git ls-files | grep -E '(^|/)\.env($|\.)' | grep -v '\.env\.example$' || true)
[ -z "$tracked_env" ] && ok "no .env files tracked" || bad "tracked env files: $tracked_env"

section "Spreadsheets"
xl=$(git ls-files '*.xlsx' '*.xlsm' '*.csv' | grep -v '^data/fixtures/' || true)
[ -z "$xl" ] && ok "no xlsx/csv tracked outside data/fixtures" || bad "tracked spreadsheets outside fixtures: $xl"

section "Result"
if [ "$fail" -eq 0 ]; then echo "  CLEAN"; else echo "  FINDINGS (see FAIL lines)"; fi
exit "$fail"
