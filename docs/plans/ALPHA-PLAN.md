## Concrete Implementation Checklist

### A. Kennel (runtime truth + readiness)

1. Update Hermes runtime service contract  
File: [kennel/src/server.py](/home/josep/dog/kennel/src/server.py)  
- Ensure `SERVICE_PROFILE_DEFAULTS["hermes"]` remains:
  - `kind="agent_runtime"`
  - `transport_kind="websocket"`
  - `protocol="ws"`
  - `port=4319`
  - `path="/"`  
- Add inline comment that this endpoint is backend-routed for room runtime invoke.

2. Harden launcher and mode env defaults  
File: [kennel/src/server.py](/home/josep/dog/kennel/src/server.py)  
- In `_hermes_runtime_files()`:
  - keep `~/.hermes/config.yaml`, `~/.hermes/.env`, `~/.hermes/hermes-agent`
  - add explicit mode vars in launcher:
    - `DOG_WORKSPACE_AGENT_HERMES_RUNTIME_MODE=gateway_ws`
    - `DOG_WORKSPACE_AGENT_HERMES_HOST` default `0.0.0.0`
    - `DOG_WORKSPACE_AGENT_HERMES_PORT` default `4319`
  - keep optional override:
    - `DOG_WORKSPACE_AGENT_HERMES_GATEWAY_CMD`
- Include API-mode placeholders in `.env` (off by default):
  - `API_SERVER_ENABLED=false`
  - `API_SERVER_HOST=127.0.0.1`
  - `API_SERVER_PORT=8642`
  - `API_SERVER_KEY=`

3. Improve startup/readiness diagnostics  
File: [kennel/src/server.py](/home/josep/dog/kennel/src/server.py)  
- When Hermes PID running but port not listening, include targeted readiness message text mentioning port `4319` and `/tmp/hermes.log`.
- Preserve current non-destructive file write guard (directory collision cleanup).

4. Tests  
Files:
- [kennel/tests/test_runtime_profiles.py](/home/josep/dog/kennel/tests/test_runtime_profiles.py)
- [kennel/tests/test_agent_runtime_invoke.py](/home/josep/dog/kennel/tests/test_agent_runtime_invoke.py)  
Add/verify:
- Hermes service defaults are websocket/4319/path `/`.
- Hermes launcher contains mode/env defaults and gateway command path.
- Unsupported transport rejection test uses non-hermes custom runtime.
- Directory-collision and file-mode tests still pass.

---

### B. Backend (orchestration + room semantics)

1. Clarify descriptor semantics for agent runtime  
File: [backend/app/services/room_workspace_connection_service.py](/home/josep/dog/backend/app/services/room_workspace_connection_service.py)  
- Keep `available` gating on `ready + url`.
- Update reason strings/comments for `agent_runtime_connect` to say “backend-routable runtime endpoint,” not browser-only implication.
- Ensure pending reasons explicitly call out “runtime healthy but no routed endpoint yet.”

2. Keep backend-owned invoke lifecycle  
Files:
- [backend/app/api/routes/rooms.py](/home/josep/dog/backend/app/api/routes/rooms.py)
- [backend/app/services/room_workspace_runtime_orchestrator.py](/home/josep/dog/backend/app/services/room_workspace_runtime_orchestrator.py)
- [backend/app/services/room_workspace_runtime_execution_service.py](/home/josep/dog/backend/app/services/room_workspace_runtime_execution_service.py)  
Tasks:
- No transport ownership change: room WS remains observer.
- Ensure invocation metadata includes type-friendly markers:
  - `runtime_status`
  - `runtime_tool_progress`
  - `runtime_output`
  - `runtime_error`
  in enrichment payload where feasible (without schema migration).

3. Verify Hermes adapter mapping stays default backend-routed invoke  
File: [backend/app/services/room_workspace_runtime_orchestrator.py](/home/josep/dog/backend/app/services/room_workspace_runtime_orchestrator.py)  
- Confirm `"hermes"` resolves to `KennelRoutedRoomWorkspaceRuntimeAdapter`.
- Add comment describing why this decouples room websocket ownership.

4. Tests  
Files:
- [backend/app/tests/services/test_room_workspace_runtime_orchestrator.py](/home/josep/dog/backend/app/tests/services/test_room_workspace_runtime_orchestrator.py)
- [backend/app/tests/services/test_room_workspace_runtime_target_resolution.py](/home/josep/dog/backend/app/tests/services/test_room_workspace_runtime_target_resolution.py)
- [backend/app/tests/api/routes/test_room_workspace_runtime_invoke.py](/home/josep/dog/backend/app/tests/api/routes/test_room_workspace_runtime_invoke.py)  
Add/verify:
- Hermes runtime target with ws URL becomes invokable via backend route.
- Pending target (no URL) fails with explicit resolution reason.
- Invoke path persists invocation record + emits room agent message.
- Room invoke still works independent of websocket client connection.

---

### C. Frontend (room UX clarity, minimal churn)

1. Workspace create/runtime copy alignment  
File: [frontend/src/components/Workspaces/panels/WorkspaceCreatePanel.tsx](/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceCreatePanel.tsx)  
- Keep Hermes notes explicit:
  - gateway websocket runtime on `4319`
  - API mode is separate and optional
  - Room runtime availability depends on routable runtime URL.

2. Room workspace panel semantics  
File: [frontend/src/components/Room/panels/WorkspaceConnectionsPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/WorkspaceConnectionsPanel.tsx)  
- For `agent_runtime_connect`, label endpoint as backend-routed runtime endpoint.
- De-emphasize direct `Open` action for agent-runtime rows (or guard by purpose).
- Improve pending helper text to mention websocket listener readiness (`4319`).
- Clarify helper text for Link Service vs Runtime

3. Tests: Deferred until after PoC: (if UI test harness exists)  
Paths (adjust to existing test infra):
- `frontend/src/components/Room/panels/__tests__/WorkspaceConnectionsPanel*.test.*`
- `frontend/src/components/Workspaces/panels/__tests__/WorkspaceCreatePanel*.test.*`  
Cases:
- Shows pending guidance for runtime without URL.
- Enables “Send To Runtime” only when current connection is `active + available + fresh`.
- Hermes helper text mentions ws gateway semantics.

---

### D. Docs / Runbooks (control-flow clarity + future API mode)

1. Hermes runbook split by mode  
File: [frontend/src/components/Workspaces/docs/hermes-agent-workspace-runbook.md](/home/josep/dog/frontend/src/components/Workspaces/docs/hermes-agent-workspace-runbook.md)  
Add explicit sections:
- `Gateway WS Mode` (room execution default)
- `API Server Mode` (OpenAI-compatible HTTP `/v1`, optional)
Include:
- env vars for API mode from Hermes docs
- security note for `0.0.0.0` + API key requirement
- statement that room websocket is not runtime transport owner.

2. Room connection reference update  
File: [frontend/src/components/Workspaces/docs/room-workspace-connection-service-reference.md](/home/josep/dog/frontend/src/components/Workspaces/docs/room-workspace-connection-service-reference.md)  
- Clarify `agent_runtime_connect` is backend-routed runtime connectivity.
- Keep practical `ready + url => available` rule.
- Note Hermes gateway ws endpoint contract.

3. Runtime alignment docs  
Files:
- [kennel/docs/runtime-service-alignment-contract.md](/home/josep/dog/kennel/docs/runtime-service-alignment-contract.md)
- [kennel/docs/runtime-preset-api-reference.md](/home/josep/dog/kennel/docs/runtime-preset-api-reference.md)  
- Ensure hermes entries explicitly document websocket gateway defaults and extension point for API mode.

---

### E. Docker / Traefik (only what’s needed now)

1. Proof path (no extra routing required)  
- Keep runtime invocation server-side backend↔kennel↔workspace.
- No direct browser route to runtime required for room invoke proof.

2. API-mode route (deferred toggle)  
Files (for enabling direct API clients through platform edge):
- [docker-compose.yml](/home/josep/dog/docker-compose.yml)
- [docker-compose.traefik.yml](/home/josep/dog/docker-compose.traefik.yml)
- Traefik labels/routes where runtime APIs are exposed  
Tasks:
- Add guarded route for `/v1` to Hermes API server when enabled.
- Keep disabled by default in proof rollout.

---

### F. End-to-End Proof Test Script

1. Add script/runbook steps  
Suggested file:
- `scripts/prove-hermes-room-runtime.sh`  
Flow:
1. Create workspace (hermes preset + persistent + agent_service/hermes).
2. Poll workspace services until Hermes is `ready` with URL.
3. Set room current connection purpose `agent_runtime_connect`.
4. Poll descriptor until `available`.
5. Invoke room runtime route with input.
6. Assert room message emitted + invocation persisted.
7. Disconnect/reconnect room client, invoke again, assert success.

2. Acceptance checks
- New workspace only (consistent with truncated table).
- No manual runtime terminal intervention required.
- Room invoke path works without room websocket being runtime owner.

