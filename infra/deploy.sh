#!/usr/bin/env bash
#
# Deploy UNWIND to Cloud Run via `adk deploy`.
#
# The framework has a deploy command, so this wraps it rather than hand-rolling
# a Dockerfile and a `gcloud run deploy`. The only thing this script adds is the
# infrastructure `adk deploy` does not own: the Pub/Sub topics, the Firestore
# indexes, and the rules.
#
# ############################################################################
# [UNVERIFIED] THIS SCRIPT HAS NEVER BEEN RUN.
#
# No GCP credentials existed in the environment where it was written. Every
# command below is written from the documented CLI surface and is unproven.
# Nothing in this repository is deployed. There is no deployed URL.
# ############################################################################

set -euo pipefail

PROJECT_ID="${UNWIND_PROJECT_ID:-}"
REGION="${UNWIND_VERTEX_LOCATION:-us-central1}"
SERVICE_NAME="${UNWIND_SERVICE_NAME:-unwind}"
AGENTS_DIR="${UNWIND_AGENTS_DIR:-agents}"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "UNWIND_PROJECT_ID is not set. Refusing to guess a project." >&2
  exit 2
fi

for binary in gcloud adk; do
  if ! command -v "${binary}" >/dev/null 2>&1; then
    echo "required binary not found: ${binary}" >&2
    exit 2
  fi
done

echo "==> project=${PROJECT_ID} region=${REGION} service=${SERVICE_NAME}"

echo "==> Enabling the four approved services (and nothing else)"
gcloud services enable \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  pubsub.googleapis.com \
  run.googleapis.com \
  --project "${PROJECT_ID}"

echo "==> Pub/Sub topics"
# Topic ids may not contain dots, so the logical names are hyphenated on the
# wire. lib/pubsub.py performs the same mapping; the two must stay in step.
for topic in claim-retracted node-rederive node-scored \
             repair-convened obligation-raised unwind-executed; do
  gcloud pubsub topics describe "${topic}" --project "${PROJECT_ID}" >/dev/null 2>&1 \
    || gcloud pubsub topics create "${topic}" --project "${PROJECT_ID}"
  gcloud pubsub subscriptions describe "${topic}-sub" --project "${PROJECT_ID}" >/dev/null 2>&1 \
    || gcloud pubsub subscriptions create "${topic}-sub" \
         --topic "${topic}" --project "${PROJECT_ID}"
done

echo "==> Firestore indexes"
gcloud firestore indexes create \
  --index-file=infra/indexes.json \
  --project "${PROJECT_ID}" \
  || echo "index creation reported an error (often 'already exists'); continuing"

echo "==> Firestore rules"
gcloud firestore rules release infra/firestore.rules --project "${PROJECT_ID}" \
  || echo "rules release reported an error; check the Firestore console"

echo "==> adk deploy cloud_run"
# --trigger_sources=pubsub registers the /trigger/* endpoints, which is how the
# cascade gets driven by claim.retracted rather than by an HTTP poll.
# --trace_to_cloud lines the deployed service up with lib/telemetry.py's exporter.
adk deploy cloud_run \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --service_name "${SERVICE_NAME}" \
  --app_name unwind \
  --trigger_sources pubsub \
  --trace_to_cloud \
  --with_ui \
  "${AGENTS_DIR}"

echo
echo "==> Deployed. Record the URL printed above; do not infer it."
