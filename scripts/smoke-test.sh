#!/usr/bin/env sh
set -eu
BASE_URL="${1:-http://localhost:8080}"
printf 'Checking %s/health ...\n' "$BASE_URL"
curl --fail --silent --show-error "$BASE_URL/health"
printf '\nChecking status API ...\n'
curl --fail --silent --show-error "$BASE_URL/api/status"
printf '\nChecking metrics ...\n'
curl --fail --silent --show-error "$BASE_URL/metrics" | grep -m 1 'cloudops_http_requests_total'
printf '\nSmoke test passed.\n'
