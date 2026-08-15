#!/usr/bin/env bash
# scripts/health_check.sh — lightweight liveness check for the deployed UNWIND service.
#
# Curls the deployed URL, asserts HTTP 200 on /api/healthz, then runs one real
# cascade over SSE and asserts the cascade counter (the "material" field the
# on-screen cull counter is driven by) is actually present in the response.
# Prints a UTC timestamp so the check result can be dated.
#
# This is deliberately lighter than `make deploy-verify`
# (scripts/deploy_verify.py), which additionally drives a real browser and
# asserts screen-vs-cascade counter equality. Use that for full deployment
# verification; use this for a fast "is it still up" check.
#
# Usage: scripts/health_check.sh [URL]
#   URL defaults to the deployed UNWIND service.

set -euo pipefail

URL="${1:-https://unwind-hgeodtazqq-uc.a.run.app}"
URL="${URL%/}"
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

echo "======================================================================"
echo "UNWIND health check — ${TIMESTAMP}"
echo "target: ${URL}"
echo "======================================================================"

# ---- 1. healthz: HTTP 200 --------------------------------------------------
HTTP_CODE="$(curl -s -o /tmp/unwind_healthz_body.$$ -w "%{http_code}" --max-time 20 "${URL}/api/healthz" || echo "000")"
BODY="$(cat /tmp/unwind_healthz_body.$$ 2>/dev/null || true)"
rm -f /tmp/unwind_healthz_body.$$

if [ "${HTTP_CODE}" != "200" ]; then
  echo "[1/2] FAIL — /api/healthz returned HTTP ${HTTP_CODE}"
  echo "${BODY}"
  echo "======================================================================"
  echo "RESULT: FAIL  (${TIMESTAMP})"
  exit 1
fi
echo "[1/2] PASS — /api/healthz returned HTTP 200"
echo "      ${BODY}"

# ---- 2. cascade counter presence ------------------------------------------
STREAM="$(curl -s --max-time 60 "${URL}/api/cascade/stream?pace_ms=0&batch=200")"

if [ -z "${STREAM}" ]; then
  echo "[2/2] FAIL — cascade stream returned no data"
  echo "======================================================================"
  echo "RESULT: FAIL  (${TIMESTAMP})"
  exit 1
fi

# The stream ends with an SSE "done" event carrying the cascade's own totals,
# including "material" — the number the on-screen cull counter must equal.
DONE_LINE="$(printf '%s' "${STREAM}" | grep -A1 '^event: done' | grep '^data: ' | tail -n1)"

if [ -z "${DONE_LINE}" ] || ! printf '%s' "${DONE_LINE}" | grep -q '"material"'; then
  echo "[2/2] FAIL — no cascade counter ('material') found in the stream's done event"
  echo "======================================================================"
  echo "RESULT: FAIL  (${TIMESTAMP})"
  exit 1
fi

MATERIAL="$(printf '%s' "${DONE_LINE}" | sed -n 's/.*"material": *\([0-9]*\).*/\1/p')"
RADIUS="$(printf '%s' "${DONE_LINE}" | sed -n 's/.*"radius": *\([0-9]*\).*/\1/p')"
echo "[2/2] PASS — cascade counter present: radius=${RADIUS} material=${MATERIAL}"

echo "======================================================================"
echo "RESULT: PASS  (${TIMESTAMP})"
echo "======================================================================"
