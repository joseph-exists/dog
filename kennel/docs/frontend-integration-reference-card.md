# Frontend Integration Reference Card

Use this card when wiring UI flows for user-created kennel workspaces.

## Base Assumptions

- Backend API base: `/api/v1`
- Workspace routes live under: `/api/v1/workspaces`
- All workspace routes require the normal authenticated backend user session / bearer token
- Browser terminal connections do **not** go through the backend after URL issuance

## Core User Flow

1. User submits workspace creation request
2. Frontend calls `POST /api/v1/workspaces/`
3. Backend returns `202 Accepted` with a workspace record in `provisioning`
4. Frontend polls `GET /api/v1/workspaces/{workspace_id}`
5. When `status === "ready"`, frontend requests `GET /api/v1/workspaces/{workspace_id}/terminal`
6. Backend returns `{ "terminal_url": "ws://..." }` or `{ "terminal_url": "wss://..." }`
7. Frontend opens a WebSocket directly to kennel using that URL

## Workspace Status Values

- `provisioning`: container creation / injection in progress
- `ready`: terminal is available
- `stopping`: stop request accepted and being processed
- `stopped`: workspace stopped
- `destroyed`: workspace torn down

## Endpoints

### Create Workspace

`POST /api/v1/workspaces/`

Request body:

```json
{
  "name": "My Dev Box",
  "flavour": "dev",
  "kind": "ephemeral",
  "repo_url": "https://github.com/example/repo.git",
  "ssh_pubkey": "ssh-ed25519 AAAA...",
  "env_vars": {
    "FOO": "bar"
  }
}
```

Response:

- Status: `202 Accepted`
- Body: workspace record

Relevant response fields:

```json
{
  "id": "uuid",
  "owner_id": "uuid",
  "name": "My Dev Box",
  "flavour": "dev",
  "kind": "ephemeral",
  "status": "provisioning",
  "kennel_name": "env-ab12cd34",
  "kennel_job": null,
  "ws_token": null,
  "meta": {
    "repo_url": "https://github.com/example/repo.git",
    "ssh_pubkey": "ssh-ed25519 AAAA...",
    "env_vars": {
      "FOO": "bar"
    }
  },
  "created_at": "2026-03-18T12:34:56Z",
  "updated_at": "2026-03-18T12:34:56Z",
  "terminal_url": null
}
```

### List Workspaces

`GET /api/v1/workspaces/`

Response:

```json
{
  "data": [
    {
      "id": "uuid",
      "name": "My Dev Box",
      "status": "ready"
    }
  ],
  "count": 1
}
```

### Get Workspace

`GET /api/v1/workspaces/{workspace_id}`

Use this for polling after create.

Polling recommendation:

- Poll every `2-3s` while `status === "provisioning"`
- Stop polling when status becomes `ready`, `stopped`, or `destroyed`
- Treat `404` as “workspace unavailable / not owned by current user”

### Get Terminal URL

`GET /api/v1/workspaces/{workspace_id}/terminal`

Success response:

```json
{
  "terminal_url": "ws://localhost:8090/envs/env-ab12cd34/ws?token=..."
}
```

Failure behavior:

- `404`: workspace not found or not owned by current user
- `400`: workspace exists but is not terminal-ready yet

Frontend rule:

- Do not synthesize this URL client-side
- Request it from the backend and use it verbatim

### Stop Workspace

`POST /api/v1/workspaces/{workspace_id}/stop`

Response:

```json
{
  "message": "Workspace stopped"
}
```

### Destroy Workspace

`DELETE /api/v1/workspaces/{workspace_id}`

Response:

```json
{
  "message": "Workspace destroyed"
}
```

## Terminal WebSocket Contract

The kennel terminal websocket is a raw PTY stream, not a JSON event socket.

Implications for frontend implementation:

- Open the websocket URL returned by `/terminal`
- Expect terminal output as binary frames
- Send user keystrokes / terminal input back as binary frames
- Do not expect structured JSON messages

If your terminal library expects text frames, add a small adapter layer that converts between the library’s expected format and websocket binary payloads.

## Minimal Frontend Sequence

```ts
const created = await api.post("/api/v1/workspaces/", payload)
const workspaceId = created.data.id

let workspace = created.data
while (workspace.status === "provisioning") {
  await delay(2500)
  workspace = (await api.get(`/api/v1/workspaces/${workspaceId}`)).data
}

if (workspace.status !== "ready") {
  throw new Error(`Workspace did not become ready: ${workspace.status}`)
}

const terminal = await api.get(`/api/v1/workspaces/${workspaceId}/terminal`)
const ws = new WebSocket(terminal.data.terminal_url)
```

## Environment Notes

- Local default external websocket base URL: `ws://localhost:8090`
- Container-internal backend-to-kennel HTTP base URL: `http://kennel:8090`
- In deployed environments behind Traefik/TLS, expect the terminal URL to become `wss://...`

## Current MVP Notes

- Workspaces are user-owned
- Terminal access is issued only after backend provisioning completes
- Stop and destroy are separate actions
- Injection soft-failures may appear inside `workspace.meta`
