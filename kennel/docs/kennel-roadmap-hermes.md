Title: Hermes Workspace Roles \& Control Plane Integration
Status: Draft
Audience: platform engineers \& infra engineers
Author: josep
Reviewers: \<TBD>
Last updated: 2026-04-10

***

## 1. Problem statement

Our platform provisions ephemeral and persistent multi-user LXC workspaces inside Docker containers, with user interaction exclusively **through our web application** (websocket and HTTP). We want to integrate Hermes Agent as a core runtime primitive while maintaining clear **separation of concerns**:

- The **control plane** owns:
    - workspace lifecycle and isolation (LXC/Docker)
    - role selection (interactive CLI vs API server vs messaging gateway)
    - configuration rendering and secrets management
    - network policy and authentication
    - attach/request routing for browsers and backend services
- **Hermes** owns:
    - agent orchestration and tools
    - terminal backend behavior
    - memory, sessions, and gateway semantics
    - API server semantics

Hermes configuration is split across two files in `~/.hermes/`:[^1][^2]

- `config.yaml` — all non-secret behavioral settings: model, terminal backend and cwd, memory, display, compression, etc.
- `.env` — secrets and env-only switches, including provider API keys and API server settings; mode `0600`.

Configuration precedence is: CLI args > `config.yaml` > `.env` > built-in defaults.[^1]

The Hermes API server is enabled and configured via environment variables (`API_SERVER_ENABLED`, `API_SERVER_HOST`, `API_SERVER_PORT`, `API_SERVER_KEY`, `API_SERVER_CORS_ORIGINS`, `API_SERVER_MODEL_NAME`), and runs alongside other platforms (including the gateway) when enabled.  Messaging gateway sessions and transcripts are stored in `~/.hermes/state.db` and `~/.hermes/sessions/`.[^3][^4][^5]

We need a **concrete architecture and contracts** so LLM engineers can:

- Implement a role-aware workspace launcher.
- Generate correct `config.yaml` and `.env` per role.
- Integrate Hermes with our websocket/API surfaces safely.
- Evolve the system without entangling Hermes internals with our control plane.

***

## 2. Goals \& non-goals

### 2.1 Goals

- Define a **role model** for Hermes in our platform:
    - `interactive-cli` (persistent CLI environment, accessed via websocket).
    - `api-server` (OpenAI-compatible HTTP server for our backend/frontends).
    - `gateway` (Hermes messaging gateway for external platforms; optional).
- Specify a **control-plane contract**:
    - Workspace spec schema.
    - Render rules for `~/.hermes/config.yaml` and `~/.hermes/.env`.
    - Filesystem layout and persistence guarantees.
- Define a **startup supervisor** and health model:
    - Single active Hermes role process per workspace.
    - Role-specific commands and readiness semantics.
- Provide implementation-ready **interfaces and flow diagrams**.


### 2.2 Non-goals

- Implement Hermes itself or modify its codebase.
- Build new Hermes tools or MCP servers.
- Define user-facing UX; this RFC is internal.

***

## 3. Hermes background (relevant pieces)

### 3.1 Directory layout

Hermes keeps all configuration and state under `~/.hermes/`:[^2][^1]

```text
~/.hermes/
├── config.yaml          # Non-secret settings (model, terminal, display, memory, tools)
├── .env                 # API keys and secrets (mode 0600)
├── auth.json            # OAuth provider credentials (optional)
├── SOUL.md              # Agent identity/system prompt slot
├── memories/            # Persistent memory (MEMORY.md, USER.md, etc.)
├── skills/              # Agent-created skills
├── cron/                # Scheduled jobs
├── sessions/            # Gateway sessions (JSONL transcripts, sessions index)
├── logs/                # Logs (errors.log, gateway.log)
└── state.db             # SQLite store for session metadata
```

- Secrets (API keys, bot tokens, passwords) must live in `.env`.[^2][^1]
- Behavioral settings (model, terminal backend, compression, memory, tools) must live in `config.yaml`.[^1][^2]


### 3.2 API server

The Hermes API server is an OpenAI-compatible HTTP interface. It is configured **only via env vars** today:[^5][^3]


| Variable | Default | Description |
| :-- | :-- | :-- |
| `API_SERVER_ENABLED` | `false` | Enable the API server. |
| `API_SERVER_PORT` | `8642` | HTTP server port. |
| `API_SERVER_HOST` | `127.0.0.1` | Bind address. |
| `API_SERVER_KEY` | *(none)* | Bearer token for API auth; required for network-accessible deployments. |
| `API_SERVER_CORS_ORIGINS` | *(none)* | Comma-separated allowed browser origins. |
| `API_SERVER_MODEL_NAME` | profile name | Name returned by `/v1/models`. [^3] |

Docs emphasize:

- API server uses `127.0.0.1` by default and is safe for local use.[^3]
- For network access, you must set `API_SERVER_KEY` and keep CORS narrow; an unset key effectively allows everything and is only acceptable in local dev.[^5][^3]


### 3.3 Sessions and gateway

Gateway sessions are keyed by platform and user and stored in `~/.hermes/state.db` and `~/.hermes/sessions/`.[^4]

- `state.db` keeps session metadata and messages (FTS5).
- `sessions/` holds JSONL transcripts and a `sessions.json` index mapping logical session keys to IDs.[^4]
- Default `group_sessions_per_user: true` in `config.yaml` ensures group chats are per-user isolated.[^4]

Hermes messaging gateway is a long-running process with multiple platform adapters (Telegram, Discord, WhatsApp, etc.), unified session routing, allowlists, slash commands, hooks, cron ticking, and background maintenance.[^6][^7]

***

## 4. Role model in our platform

We define three roles at the **workspace** level:

```text
WorkspaceRole =
  | "interactive-cli"   # Hermes CLI/TUI backing an interactive shell over websocket
  | "api-server"        # Hermes API server for internal HTTP usage
  | "gateway"           # Hermes messaging gateway for external platforms (optional)
```

Constraints:

- Exactly **one Hermes role process per workspace** at a time.
- All roles share the same `HERMES_HOME` (`~/.hermes`) and `WORKSPACE_ROOT` (`/workspace`) within that workspace.
- The control plane decides the role and renders configuration before starting Hermes.


### 4.1 Capability matrix

| Role | User transport | Hermes process | Session owner | Persistence requirements |
| :-- | :-- | :-- | :-- | :-- |
| interactive-cli | Browser websocket via our app | `hermes` CLI | Our app | `~/.hermes`, `/workspace` |
| api-server | Our backend or internal proxy HTTP | API server via env (`API_SERVER_ENABLED`) and gateway start | Our app / backend | `~/.hermes`, `/workspace` |
| gateway | External messaging/webhook platforms | `hermes gateway` | Hermes | `~/.hermes` (including `sessions/`) |


***

## 5. Control-plane contract

### 5.1 Workspace spec

The control plane produces a **workspace spec** before container startup:

```yaml
workspace_contract:
  version: "v1"
  workspace_id: "ws_123"
  tenant_id: "org_456"
  user_id: "user_789"

  role: "interactive-cli"   # interactive-cli | api-server | gateway

  image_ref: "your/hermes-workspace:tag"

  hermes_home: "/root/.hermes"
  workspace_root: "/workspace"

  network:
    mode: "private"         # private | internal | public (internal usage: private)
    bind_host: "127.0.0.1"
    exposed_ports: []       # set per role when needed

  persistence:
    hermes_home: true       # persistent volume
    workspace_root: true    # persistent volume
    logs: true
    sessions: false         # true for gateway

  secrets_ref:
    provider_bundle: "secret://providers/ws_123"
    role_bundle: "secret://role/ws_123"

  resources:
    cpu: 4
    memory_mb: 8192

  startup:
    supervisor_mode: "single-active-role"
    healthcheck_grace_seconds: 30
    restart_policy: "on-failure"
```


### 5.2 Filesystem layout

Every workspace must satisfy Hermes’ expected layout:[^2][^1]

NOTE: this is satisfied by installation.

```text
/root/.hermes/
├── config.yaml
├── .env
├── auth.json           # optional
├── SOUL.md             # optional
├── memories/
├── skills/
├── cron/
├── sessions/
├── logs/
└── state.db

/workspace/             # user project and agent tools cwd
```

Persistence rules:

- **Always** persist `/root/.hermes` for non-ephemeral workspaces (interactive and gateway) to retain config, SOUL, memory, and logs.[^1][^4]
- Persist `/workspace` for user files and tool output.
- For `gateway`, treat `sessions/` and `state.db` as critical, and ensure they are backed by a persistent volume.[^4]

***

## 6. Config generation

### 6.1 `config.yaml` (non-secret behavior)

We generate `config.yaml` from a **base template** plus a **role overlay**. Hermes docs specify that `config.yaml` is the primary file for model, terminal, display, memory, and tools.[^2][^1]

#### 6.1.1 Base template

```yaml
# /root/.hermes/config.yaml
profile_name: "{{ profile_name }}"     # e.g. workspace_id or derived
model: "{{ model_ref }}"               # e.g. anthropic/claude-opus-4
provider: "{{ provider_name }}"        # e.g. anthropic, openai

terminal:
  backend: local                       # hermes terminal backend
  cwd: "{{ workspace_root }}"          # /workspace
  timeout: {{ terminal_timeout_seconds }}
  env_passthrough:
{% for item in terminal_env_passthrough %}
    - "{{ item }}"
{% endfor %}

memory:
  enabled: {{ memory_enabled }}

display:
  streaming: {{ display_streaming }}

compression:
  enabled: {{ compression_enabled }}

privacy:
  redact_pii: {{ redact_pii }}
```

Notes:

- `terminal.backend: local` is selected because Hermes runs inside a dedicated workspace container whose filesystem is already isolated; we do not need nested Docker/SSH by default. Hermes also supports `docker`, `ssh`, `modal`, etc., via the same schema if we add those later.[^8][^1]
- `env_passthrough` must be a policy-controlled allowlist to avoid leaking random env into agent tool sub-processes.[^1]


#### 6.1.2 interactive-cli overlay

```yaml
# overlay for interactive-cli role
memory:
  enabled: true

display:
  streaming: true

terminal:
  backend: local
  cwd: "/workspace"
  timeout: 180
```

- Streaming is useful here when our websocket UI streams incremental output.


#### 6.1.3 api-server overlay

```yaml
# overlay for api-server role
memory:
  enabled: true
display:
  streaming: true
terminal:
  backend: local
  cwd: "/workspace"
  timeout: 180
```

- API server configuration itself remains in `.env` as Hermes currently documents environment variables as the configuration interface for this feature.[^3][^5]


#### 6.1.4 gateway overlay

```yaml
# overlay for gateway role
memory:
  enabled: true
display:
  streaming: true

terminal:
  backend: local
  cwd: "/workspace"
  timeout: 180

privacy:
  redact_pii: true
```

- `privacy.redact_pii` is particularly important for external messaging channels.[^9][^4]


### 6.2 `.env` (secrets and env-only switches)

Hermes expects secrets and API server settings in `.env`. The file should be written with `0600` permissions.[^3][^2][^1]

#### 6.2.1 Base `.env`

```dotenv
# /root/.hermes/.env

# Provider API keys (at least one required for Hermes startup)
OPENAI_API_KEY={{ OPENAI_API_KEY }}
OPENROUTER_API_KEY={{ OPENROUTER_API_KEY }}
ANTHROPIC_API_KEY={{ ANTHROPIC_API_KEY }}

# Optional provider-specific settings
OPENAI_BASE_URL={{ OPENAI_BASE_URL }}
CUSTOM_PROVIDER_API_KEY={{ CUSTOM_PROVIDER_API_KEY }}

# Workspace identity (for our own wrappers/instrumentation)
HERMES_WORKSPACE_ID={{ workspace_id }}
HERMES_TENANT_ID={{ tenant_id }}
HERMES_USER_ID={{ user_id }}
HERMES_WORKSPACE_ROLE={{ role }}

# Paths
HERMES_HOME=/root/.hermes
WORKSPACE_ROOT=/workspace
```


#### 6.2.2 interactive-cli overlay

```dotenv
# overlay for interactive-cli
API_SERVER_ENABLED=false
```

- Explicitly disable API server in this role.


#### 6.2.3 api-server overlay

```dotenv
# overlay for api-server
API_SERVER_ENABLED=true
API_SERVER_HOST=127.0.0.1
API_SERVER_PORT={{ api_server_port }}           # default 8642
API_SERVER_KEY={{ API_SERVER_KEY }}             # required for any network access
API_SERVER_MODEL_NAME={{ api_server_model_name }}

# Browser-origin access, only if absolutely necessary
API_SERVER_CORS_ORIGINS={{ API_SERVER_CORS_ORIGINS }}
```

- Hermes docs require `API_SERVER_KEY` for network-accessible deployments and recommend keeping host at `127.0.0.1` and restricting CORS for safety.[^10][^5][^3]


#### 6.2.4 gateway overlay

```dotenv
# overlay for gateway
API_SERVER_ENABLED={{ gateway_exposes_api_server }}
API_SERVER_HOST=127.0.0.1
API_SERVER_PORT={{ api_server_port }}
API_SERVER_KEY={{ API_SERVER_KEY }}

# Platform integration secrets
TELEGRAM_BOT_TOKEN={{ TELEGRAM_BOT_TOKEN }}
DISCORD_BOT_TOKEN={{ DISCORD_BOT_TOKEN }}
SLACK_BOT_TOKEN={{ SLACK_BOT_TOKEN }}
WHATSAPP_TOKEN={{ WHATSAPP_TOKEN }}
SIGNAL_TOKEN={{ SIGNAL_TOKEN }}
MATRIX_TOKEN={{ MATRIX_TOKEN }}

# Webhook config if used
WEBHOOK_PORT={{ WEBHOOK_PORT }}
WEBHOOK_SECRET={{ WEBHOOK_SECRET }}
```

- Hermes environment-variable reference includes both API server and webhook settings for gateway deployments.[^5]

***

## 7. Startup supervisor

We will run a **workspace supervisor** as PID 1 inside each workspace container instead of Hermes directly. The supervisor enforces invariants and exports a clean status API to the control plane.

### 7.1 Responsibilities

- Validate `config.yaml`, `.env`, mounts, and required env variables.
- Start **exactly one Hermes process** for the current role.
- Implement a health model appropriate to the role (PTY vs HTTP vs gateway).
- Handle graceful shutdown and restarts based on policy.
- Surface status changes (phase, pid, health) to the control plane.


### 7.2 Input to supervisor

Supervisor config (e.g. JSON file or environment) derived from `workspace_contract`:

```json
{
  "workspace_id": "ws_123",
  "role": "interactive-cli",
  "hermes_home": "/root/.hermes",
  "workspace_root": "/workspace",
  "config_path": "/root/.hermes/config.yaml",
  "env_path": "/root/.hermes/.env",
  "healthcheck_grace_seconds": 30,
  "restart_policy": "on-failure"
}
```


### 7.3 Supervisor phases

```text
init            -> render-check -> preflight -> starting -> ready
ready           -> degraded (if health check fails but process alive)
ready/degraded  -> stopping -> stopped
*               -> failed (on startup or fatal error)
```


### 7.4 Preflight checks

Common to all roles:

- `config.yaml` exists and is readable.[^2][^1]
- `.env` exists and is readable.[^1][^2]
- `HERMES_HOME` exists and is writable.
- `WORKSPACE_ROOT` exists and is writable.
- `HERMES_WORKSPACE_ROLE` in `.env` matches `role` in supervisor config.

For `api-server`:

- `API_SERVER_ENABLED=true`.[^5][^3]
- `API_SERVER_KEY` non-empty.[^3][^5]
- `API_SERVER_HOST` is `127.0.0.1` unless a special policy allows `0.0.0.0`.
- `API_SERVER_PORT` not in use.

For `gateway`:

- At least one platform token present if connectors enabled.
- `~/.hermes/sessions/` exists and is writable.[^4]
- `state.db` either present or creatable.[^4]


### 7.5 Role-specific commands

#### 7.5.1 interactive-cli

```bash
env -i $(cat /root/.hermes/.env | xargs) \
  HERMES_HOME=/root/.hermes \
  HOME=/root \
  bash -lc 'cd /workspace && exec hermes'
```

- Supervisor allocates a PTY for this process so our app can multiplex user websockets onto the CLI.
- Health: process alive, PTY attached, optional periodic “ping” via a lightweight CLI command (e.g. `hermes --version`) if we want additional assurance.


#### 7.5.2 api-server

Hermes docs show enabling API server via `.env` and then running the gateway, which starts the API server alongside other platforms.[^6][^3]

```bash
env -i $(cat /root/.hermes/.env | xargs) \
  HERMES_HOME=/root/.hermes \
  HOME=/root \
  bash -lc 'cd /workspace && exec hermes gateway'
```

Health probe:

```bash
curl -fsS "http://127.0.0.1:${API_SERVER_PORT}/health" || exit 1
```

- Supervisor treats API health as readiness signal.[^3]


#### 7.5.3 gateway

```bash
env -i $(cat /root/.hermes/.env | xargs) \
  HERMES_HOME=/root/.hermes \
  HOME=/root \
  bash -lc 'cd /workspace && exec hermes gateway'
```

Health:

- Process liveness.
- Platform adapter connectivity if we expose any (e.g. logs or status endpoints from gateway, if available).
- Optional: check sessions store accessible (`state.db` openable).[^4]


### 7.6 Supervisor status API

Supervisor should expose status via:

- Structured logs, and optionally
- A local admin HTTP endpoint, e.g. `http://127.0.0.1:9000/status`:

```json
{
  "workspace_id": "ws_123",
  "role": "api-server",
  "phase": "ready",
  "pid": 1234,
  "started_at": "2026-04-10T12:00:00Z",
  "health": {
    "status": "ok",
    "details": "api-server /health OK"
  }
}
```

The control plane watches this and updates workspace status.

***

## 8. Control flow

### 8.1 Provisioning flow

1. **CreateWorkspace request** hits control plane (role, user, tenant, model).
2. **Control plane** resolves:
    - `workspace_id`, `tenant_id`, `user_id`
    - `role` (`interactive-cli` / `api-server` / `gateway`)
    - `model_ref`, `provider_name`
    - network policy and resource class
3. **WorkspaceSpecService** builds `workspace_contract`.
4. **HermesConfigRenderer**:
    - renders `config.yaml` from base + role overlay.
    - gathers secrets (provider bundle, role bundle).
    - renders `.env` from base + role overlay.
5. **Launcher**:
    - creates LXC/Docker workspace container from `image_ref`.
    - mounts persistent volumes for `/root/.hermes` and `/workspace`.
    - writes `config.yaml` and `.env` into `/root/.hermes`.
6. **Supervisor** process starts inside container:
    - loads supervisor config.
    - runs preflight; if failure, surfaces `failed`.
7. **Supervisor** starts Hermes role process.
8. **Supervisor** runs role-specific health check until ready.
9. **Control plane** marks workspace `ready` and stores:
    - websocket attach metadata for `interactive-cli`.
    - internal HTTP endpoint for `api-server` (`http://<container-ip>:API_SERVER_PORT`).

### 8.2 Attach flow (interactive-cli)

1. Browser connects to our app’s websocket endpoint.
2. App authenticates user and resolves workspace selection.
3. App obtains PTY attachment handle from our workspace runtime.
4. App forwards websocket frames (user input) to PTY stdin and PTY stdout back to browser.
5. On reconnect, app reattaches to same PTY if workspace is still alive; if not, the app decides whether to resurrect the workspace or show an error.

Hermes’ gateway session model is not used here; our application is the session owner.[^6][^4]

### 8.3 Request flow (api-server)

1. Browser or backend hits our app’s API.
2. App authenticates user and enforces authorization.
3. App builds OpenAI-compatible request.
4. App sends request to Hermes API server:

```http
POST http://<workspace-ip>:${API_SERVER_PORT}/v1/chat/completions
Authorization: Bearer ${API_SERVER_KEY}
Content-Type: application/json
```

5. Hermes executes the agent and returns HTTP response.
6. App rewraps or forwards response to caller.

Hermes docs show this pattern for integrations like Open WebUI; they also note that server-to-server use does **not** require CORS, so `API_SERVER_CORS_ORIGINS` should be omitted unless browsers connect directly.[^10]

### 8.4 Messaging flow (gateway)

Only if we decide to support it:

1. Platform event (Telegram/Discord/etc.) hits Hermes gateway adapter.
2. Gateway resolves session key, loads session from `state.db` and `sessions/`.[^9][^4]
3. Gateway constructs `AIAgent` and runs conversation.
4. Gateway sends response back via platform adapter.[^6]

Our app is not in the hot path for message delivery here, but we should still ingest logs and metrics via logs or a separate sidecar.

***

## 9. Security \& networking

- **Bind host**: Default `API_SERVER_HOST=127.0.0.1`. Only allow `0.0.0.0` via explicit policy and always with `API_SERVER_KEY`.[^5][^3]
- **API auth**: `API_SERVER_KEY` must be non-empty for any network-accessible use case.[^5][^3]
- **CORS**: Only set `API_SERVER_CORS_ORIGINS` when browsers call Hermes directly. Server-to-server uses should leave it unset.[^10][^3]
- **Secrets**: All provider keys and bot tokens are in `.env`. Never write secrets to `config.yaml` or logs.[^2][^1]
- **Filesystem**: Enforce least privilege; `.env` should be `0600`.[^2]
- **Gateway**: Treat `sessions/` and `state.db` as sensitive since they contain message transcripts and metadata.[^4]

***

## 10. Internal interfaces

### 10.1 WorkspaceSpecService

```ts
type WorkspaceRole = 'interactive-cli' | 'api-server' | 'gateway';

interface WorkspaceSpecInput {
  workspaceId: string;
  tenantId: string;
  userId: string;
  role: WorkspaceRole;
  modelRef: string;
  providerName: string;
  persistence: {
    hermesHome: boolean;
    workspaceRoot: boolean;
  };
}

interface RenderedWorkspaceSpec {
  contract: any;            // workspace_contract JSON
  configYaml: string;
  envContent: string;
}

interface WorkspaceSpecService {
  buildSpec(input: WorkspaceSpecInput): Promise<RenderedWorkspaceSpec>;
}
```


### 10.2 HermesConfigRenderer

```ts
interface HermesConfigRenderer {
  renderConfig(input: WorkspaceSpecInput): string;
  renderEnv(input: WorkspaceSpecInput, secrets: Record<string,string>): string;
}
```


### 10.3 WorkspaceSupervisorAPI

```ts
type Phase =
  | 'init'
  | 'render-check'
  | 'preflight'
  | 'starting'
  | 'ready'
  | 'degraded'
  | 'stopping'
  | 'stopped'
  | 'failed';

interface WorkspaceStatus {
  workspaceId: string;
  role: WorkspaceRole;
  phase: Phase;
  pid?: number;
  startedAt?: string;
  health: {
    status: 'ok' | 'warn' | 'error';
    details: string;
  };
}

interface WorkspaceSupervisorAPI {
  status(): Promise<WorkspaceStatus>;
  stop(graceSeconds: number): Promise<void>;
  restart(): Promise<void>;
}
```


### 10.4 HermesRoleAdapter

```ts
interface ReadinessProbe {
  type: 'process' | 'http';
  command?: string[];
  url?: string;
}

interface HermesRoleAdapter {
  command(spec: RenderedWorkspaceSpec): string[];
  readiness(spec: RenderedWorkspaceSpec): ReadinessProbe;
  supportsPty(): boolean;
  supportsHttp(): boolean;
}
```


***

## 11. Implementation plan (high-level)

1. **Phase 1 – Skeleton**
    - Implement `WorkspaceSpecService` and `HermesConfigRenderer`.
    - Implement a simple supervisor that can:
        - read spec, run preflight, start `hermes` / `hermes gateway`.
        - expose `/status` endpoint inside workspace.
    - Integrate with existing launcher to mount `/root/.hermes` and `/workspace`.
2. **Phase 2 – interactive-cli**
    - Implement PTY management and websocket bridge.
    - Migrate one “interactive agent” flow to use `interactive-cli` workspaces.
3. **Phase 3 – api-server**
    - Implement HTTP proxy from backend to per-workspace Hermes API server.
    - Migrate one current “agent API” path to `api-server` role.
4. **Phase 4 – gateway (optional)**
    - Add support for selected platforms (Telegram/Discord).
    - Decide whether these run as separate workspaces or as multi-profile Hermes instances; Hermes supports multiple profiles with separate `HERMES_HOME`.[^6]
5. **Phase 5 – hardening**
    - Add metrics, rate limits, and observability.
    - Add policy checks around `API_SERVER_HOST`, `API_SERVER_KEY`, `API_SERVER_CORS_ORIGINS`.[^3][^5]

***

This RFC should give LLM engineers enough detail to implement the control-plane refactor, workspace launcher, and Hermes integration while keeping configuration, secrets, and runtime roles cleanly separated and aligned with Hermes’ documented configuration and architecture.[^6][^1][^5][^3][^4]
<span style="display:none">[^11][^12][^13][^14][^15][^16]</span>

<div align="center">⁂</div>

[^1]: https://hermes-agent.nousresearch.com/docs/user-guide/configuration/

[^2]: https://www.mintlify.com/NousResearch/hermes-agent/user-guide/configuration

[^3]: https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server/

[^4]: https://hermes-agent.nousresearch.com/docs/user-guide/sessions/

[^5]: https://hermes-agent.nousresearch.com/docs/reference/environment-variables

[^6]: https://hermes-agent.nousresearch.com/docs/developer-guide/architecture/

[^7]: https://mranand.substack.com/p/inside-hermes-agent-how-a-self-improving

[^8]: https://nousresearch-hermes-agent.mintlify.app/reference/configuration-options

[^9]: https://www.mintlify.com/NousResearch/hermes-agent/developer-guide/architecture

[^10]: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/open-webui

[^11]: https://www.mintlify.com/NousResearch/hermes-agent/reference/environment-variables

[^12]: https://github.com/NousResearch/hermes-agent/blob/main/cli-config.yaml.example

[^13]: https://www.reddit.com/r/hermesagent/comments/1rt5syt/complete_hermes_agent_setup_guide/

[^14]: https://github.com/NousResearch/hermes-agent/blob/main/.env.example

[^15]: https://github.com/stardomains3/oxproxion/releases

[^16]: https://www.youtube.com/watch?v=UbK2kXygPUY

