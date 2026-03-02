#!/bin/sh
set -eu

jobs_root="${TESSER_JOBS_ROOT:-/data/jobs}"
core_timeout="${TESSER_CORE_TIMEOUT_SECONDS:-180}"
export_timeout="${TESSER_EXPORT_TIMEOUT_SECONDS:-600}"

bridge_id="${TESSER_BRIDGE_WORKER_ID:-tesser-bridge}"
core_id="${TESSER_CORE_WORKER_ID:-tesser-worker-core}"
export_id="${TESSER_EXPORT_WORKER_ID:-tesser-worker-export}"

cleanup() {
  code=$?
  trap - EXIT INT TERM
  for pid in ${bridge_pid:-} ${core_pid:-} ${export_pid:-}; do
    if [ -n "${pid}" ]; then
      kill "$pid" 2>/dev/null || true
    fi
  done
  for pid in ${bridge_pid:-} ${core_pid:-} ${export_pid:-}; do
    if [ -n "${pid}" ]; then
      wait "$pid" 2>/dev/null || true
    fi
  done
  exit "$code"
}

trap cleanup EXIT INT TERM

TESSER_WORKER_ID="$bridge_id" python -m tesserax_service.redis_bridge &
bridge_pid=$!

TESSER_WORKER_ID="$core_id" python -m tesserax_service.worker \
  --jobs-root "$jobs_root" \
  --runtime-profile core \
  --default-timeout-seconds "$core_timeout" &
core_pid=$!

TESSER_WORKER_ID="$export_id" python -m tesserax_service.worker \
  --jobs-root "$jobs_root" \
  --runtime-profile export \
  --default-timeout-seconds "$export_timeout" &
export_pid=$!

while :; do
  for pid in "$bridge_pid" "$core_pid" "$export_pid"; do
    if ! kill -0 "$pid" 2>/dev/null; then
      exit 1
    fi
  done
  sleep 1
done
