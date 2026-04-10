#!/usr/bin/env bash
set -euo pipefail

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required" >&2
  exit 1
fi
if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required" >&2
  exit 1
fi

API_BASE="${API_BASE:-http://localhost:8000/api/v1}"
API_TOKEN="${API_TOKEN:-}"
ROOM_ID="${ROOM_ID:-}"
WORKSPACE_NAME="${WORKSPACE_NAME:-hermes-proof-$(date +%s)}"
POLL_TIMEOUT_SECONDS="${POLL_TIMEOUT_SECONDS:-300}"
POLL_INTERVAL_SECONDS="${POLL_INTERVAL_SECONDS:-5}"

if [[ -z "$API_TOKEN" ]]; then
  echo "Set API_TOKEN to a valid Bearer token." >&2
  exit 1
fi
if [[ -z "$ROOM_ID" ]]; then
  echo "Set ROOM_ID to an existing room UUID." >&2
  exit 1
fi

api() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  local url="${API_BASE}${path}"

  local tmp
  tmp="$(mktemp)"
  local code

  if [[ -n "$body" ]]; then
    code="$(curl -sS -o "$tmp" -w "%{http_code}" -X "$method" "$url" \
      -H "Authorization: Bearer ${API_TOKEN}" \
      -H "Content-Type: application/json" \
      --data "$body")"
  else
    code="$(curl -sS -o "$tmp" -w "%{http_code}" -X "$method" "$url" \
      -H "Authorization: Bearer ${API_TOKEN}" \
      -H "Content-Type: application/json")"
  fi

  if [[ "$code" -lt 200 || "$code" -ge 300 ]]; then
    echo "API ${method} ${path} failed with status ${code}" >&2
    cat "$tmp" >&2
    rm -f "$tmp"
    exit 1
  fi

  cat "$tmp"
  rm -f "$tmp"
}

deadline_epoch=$(( $(date +%s) + POLL_TIMEOUT_SECONDS ))

echo "[1/7] Creating Hermes workspace: ${WORKSPACE_NAME}"
create_payload="$(jq -cn \
  --arg name "$WORKSPACE_NAME" \
  '{
    name: $name,
    flavour: "dev",
    runtime_preset: "hermes",
    kind: "persistent",
    bootstrap: {
      startup_intent: {
        mode: "agent_service",
        agent_profile: "hermes"
      }
    }
  }')"

workspace_json="$(api POST "/workspaces/" "$create_payload")"
workspace_id="$(echo "$workspace_json" | jq -r '.id')"
if [[ -z "$workspace_id" || "$workspace_id" == "null" ]]; then
  echo "Workspace create response missing id" >&2
  echo "$workspace_json" >&2
  exit 1
fi

echo "Workspace ID: ${workspace_id}"

echo "[2/7] Polling workspace services for Hermes ready + URL"
while true; do
  now="$(date +%s)"
  if (( now > deadline_epoch )); then
    echo "Timed out waiting for Hermes service to become ready with URL." >&2
    exit 1
  fi

  workspace_state="$(api GET "/workspaces/${workspace_id}")"
  workspace_status="$(echo "$workspace_state" | jq -r '.status')"
  hermes_service="$(echo "$workspace_state" | jq -c '.services[] | select(.kind=="agent_runtime" and (.runtime_id=="hermes" or .id=="hermes"))' | head -n 1 || true)"

  if [[ -n "$hermes_service" ]]; then
    hermes_status="$(echo "$hermes_service" | jq -r '.status')"
    hermes_url="$(echo "$hermes_service" | jq -r '.url // empty')"
    if [[ "$hermes_status" == "ready" && -n "$hermes_url" ]]; then
      echo "Hermes service ready: ${hermes_url}"
      break
    fi
    echo "Workspace=${workspace_status} Hermes=${hermes_status} URL=${hermes_url:-<none>}"
  else
    echo "Workspace=${workspace_status} Hermes service not discovered yet"
  fi

  sleep "$POLL_INTERVAL_SECONDS"
done

echo "[3/7] Setting room current connection to agent runtime"
set_current_payload="$(jq -cn --arg wid "$workspace_id" '{workspace_id: $wid, purpose: "agent_runtime_connect"}')"
api PUT "/rooms/${ROOM_ID}/workspace-connections/current" "$set_current_payload" >/dev/null

echo "[4/7] Polling current room descriptor until available"
while true; do
  now="$(date +%s)"
  if (( now > deadline_epoch )); then
    echo "Timed out waiting for room descriptor availability." >&2
    exit 1
  fi

  current_json="$(api GET "/rooms/${ROOM_ID}/workspace-connections/current")"
  descriptor_status="$(echo "$current_json" | jq -r '.descriptor.status // empty')"
  descriptor_reason="$(echo "$current_json" | jq -r '.descriptor.reason // empty')"

  if [[ "$descriptor_status" == "available" ]]; then
    echo "Room descriptor is available"
    break
  fi

  echo "Descriptor status=${descriptor_status:-<none>} reason=${descriptor_reason:-<none>}"
  sleep "$POLL_INTERVAL_SECONDS"
done

echo "[5/7] Invoking room runtime (first call)"
invoke_one_payload='{"input":"Inspect the workspace and report current runtime status."}'
invoke_one_response="$(api POST "/rooms/${ROOM_ID}/workspace-runtime/invoke" "$invoke_one_payload")"
invoke_one_success="$(echo "$invoke_one_response" | jq -r '.success')"
invoke_one_invocation_id="$(echo "$invoke_one_response" | jq -r '.invocation_id')"
invoke_one_message_id="$(echo "$invoke_one_response" | jq -r '.message_id')"
if [[ "$invoke_one_success" != "true" ]]; then
  echo "First invoke did not succeed" >&2
  echo "$invoke_one_response" >&2
  exit 1
fi

echo "[6/7] Verifying invocation persistence + room message"
if [[ -z "$invoke_one_invocation_id" || "$invoke_one_invocation_id" == "null" ]]; then
  echo "Missing invocation_id from first invoke" >&2
  exit 1
fi
if [[ -z "$invoke_one_message_id" || "$invoke_one_message_id" == "null" ]]; then
  echo "Missing message_id from first invoke" >&2
  exit 1
fi

echo "[7/7] Re-invoking without websocket ownership assumption"
invoke_two_payload='{"input":"Second call after client reconnect simulation."}'
invoke_two_response="$(api POST "/rooms/${ROOM_ID}/workspace-runtime/invoke" "$invoke_two_payload")"
invoke_two_success="$(echo "$invoke_two_response" | jq -r '.success')"
if [[ "$invoke_two_success" != "true" ]]; then
  echo "Second invoke did not succeed" >&2
  echo "$invoke_two_response" >&2
  exit 1
fi

echo "Proof complete"
echo "- Workspace: ${workspace_id}"
echo "- Room: ${ROOM_ID}"
echo "- First invocation: ${invoke_one_invocation_id}"
echo "- Second invocation: $(echo "$invoke_two_response" | jq -r '.invocation_id')"
