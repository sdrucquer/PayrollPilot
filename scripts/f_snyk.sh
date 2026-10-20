#!/usr/bin/env bash
# Reproduce the frontend dependency scan; nonzero findings are preserved.
# Authenticate first: npx --yes snyk@1.1308.1 auth
set -euo pipefail
umask 077
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
report_path="${1:-$repo_root/data/private/security/snyk-web.raw.json}"
mkdir -p "$(dirname "$report_path")"
cd "$repo_root/web"
npx --yes snyk@1.1308.1 test --dev --file=package-lock.json --json-file-output="$report_path"
