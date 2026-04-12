Title: Hermes Workspace Roles \& Control Plane Integration
Status: Draft, revised against current kennel implementation
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

### 1.1 Current implementation reality check

Hermes is not a greenfield integration in `kennel`. The current implementation already includes a kennel-owned Hermes runtime path, so the roadmap below needs to be read as a refactor/expansion plan rather than an initial design.

What already exists in code today:

- A first-class `runtime_preset: "hermes"` mapped to flavour `hermes-agent` and bootstrap profile `hermes_agent_runtime`.
- Rebuildable Hermes flavours in [src/flavours.py](/home/josep/dog/kennel/src/flavours.py): `dev-hermes` (legacy alias), `hermes-agent`, and `hermes-agent-dev`.
- A Hermes provisioner in [provision/04-hermes.sh](/home/josep/dog/kennel/provision/04-hermes.sh) that preinstalls Hermes into the base flavour chain.
- Hermes runtime file generation in [src/server.py](/home/josep/dog/kennel/src/server.py) for:
  - `/home/dev/.hermes/config.yaml`
  - `/home/dev/.hermes/.env`
  - `/home/dev/.hermes/hermes-agent-launcher`
- Inject-time file permission handling in [src/server.py](/home/josep/dog/kennel/src/server.py) that already treats `.env` as `0600` and launcher scripts as executable.
- A kennel-owned bootstrap profile that starts Hermes as a background websocket gateway service on port `4319`, registers it as declared service `hermes`, and exposes readiness/discovery through `GET /envs/{name}/services`.
- Runtime invocation support through `POST /envs/{name}/agent-runtimes/{service_id}/invoke`, which means kennel already has an agent-runtime control surface beyond raw terminal attach.
- Tests in [tests/test_runtime_profiles.py](/home/josep/dog/kennel/tests/test_runtime_profiles.py) that lock in the Hermes preset/profile/runtime-file behavior.

What does not exist yet:

- A first-class role model separating `interactive-cli`, `api-server`, and `gateway`.
- A supervisor process or workspace status API inside the container.
- A kennel-owned interactive Hermes PTY flow.
- A first-class Hermes API-server profile or routing contract.
- Persistent mount semantics specifically for Hermes home/session storage beyond the container/env model already used by kennel.


### 1.2 Where this proposal diverges from current reality

Hermes's proposal appears to have been produced with limited visibility into the current codebase. The most important deltas are:

- It describes Hermes integration as if kennel still only had metadata hooks. That is stale; kennel already owns a runnable Hermes preset/profile path.
- It assumes a new PID 1 supervisor should be the starting point. Today kennel starts Hermes from inject-time bootstrap steps and tracks the process through the service manifest plus PID/port probing.

- It treats API-server and gateway roles as symmetric design targets. In reality, only the websocket gateway path is implemented today; API mode is present only as disabled placeholders in `.env`.
- It frames configuration rendering as a new capability. Kennel already renders and writes runtime-owned files for Hermes during inject.

The rest of this document therefore should be interpreted as a proposed evolution from the current `gateway_ws` implementation, not as a clean-sheet architecture.

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

Implementation note: kennel currently implements only a single concrete Hermes runtime mode, effectively a `gateway`-style websocket runtime exposed as service `hermes` on port `4319`. The three-role model below is a target-state abstraction, not the current runtime matrix.

We define three roles at the **workspace** level:

```text
WorkspaceRole =
  | "interactive-cli"   # Hermes CLI/TUI backing an interactive shell over websocket
  | "api-server"        # Hermes API server for internal HTTP usage
  | "gateway"           # Hermes messaging gateway for external platforms (optional)
```

Constraints:

- Exactly **one Hermes role process per workspace** at a time.
- All roles share the same `HERMES_HOME` (`/home/dev/.hermes`) and `WORKSPACE_ROOT` (`/home/dev/workspace`) within that workspace.
- The control plane decides the role and renders configuration before starting Hermes.


### 4.1 Capability matrix

| Role | User transport | Hermes process | Session owner | Persistence requirements |
| :-- | :-- | :-- | :-- | :-- |
| interactive-cli | Browser websocket via our app | `hermes` CLI | Our app | `/home/dev/.hermes`, `/home/dev/workspace` |
| api-server | Our backend or internal proxy HTTP | API server via env (`API_SERVER_ENABLED`) and gateway start | Our app / backend | `/home/dev/.hermes`, `/home/dev/workspace` |
| gateway | External messaging/webhook platforms | `hermes gateway` | Hermes | `/home/dev/.hermes` (including `sessions/`) |


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

  hermes_home: "/home/dev/.hermes"
  workspace_root: "/home/dev/workspace"

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
/home/dev/.hermes/
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

/home/dev/workspace/    # user project and agent tools cwd
```

Persistence rules:

- **Always** persist `/home/dev/.hermes` for non-ephemeral workspaces (interactive and gateway) to retain config, SOUL, memory, and logs.[^1][^4]
- Persist `/home/dev/workspace` for user files and tool output.
- For `gateway`, treat `sessions/` and `state.db` as critical, and ensure they are backed by a persistent volume.[^4]


***

## 6. Config generation

### 6.1 `config.yaml` (non-secret behavior)

We generate `config.yaml` from a **base template** plus a **role overlay**. Hermes docs specify that `config.yaml` is the primary file for model, terminal, display, memory, and tools.[^2][^1]

#### 6.1.1 Base template

```yaml
# /home/dev/.hermes/config.yaml
profile_name: "{{ profile_name }}"     # e.g. workspace_id or derived
model: "{{ model_ref }}"               # e.g. anthropic/claude-opus-4
provider: "{{ provider_name }}"        # e.g. anthropic, openai

terminal:
  backend: local                       # hermes terminal backend
  cwd: "{{ workspace_root }}"          # /home/dev/workspace
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
  cwd: "/home/dev/workspace"
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
  cwd: "/home/dev/workspace"
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
  cwd: "/home/dev/workspace"
  timeout: 180

privacy:
  redact_pii: true
```

- `privacy.redact_pii` is particularly important for external messaging channels.[^9][^4]


### 6.2 `.env` (secrets and env-only switches)

Hermes expects secrets and API server settings in `.env`. The file should be written with `0600` permissions.[^3][^2][^1]

#### 6.2.1 Base `.env`

```dotenv
# /home/dev/.hermes/.env

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
HERMES_HOME=/home/dev/.hermes
WORKSPACE_ROOT=/home/dev/workspace
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

Current-state note: this entire section is future-state design. Kennel does not currently run a dedicated supervisor as PID 1. The existing startup mechanism is inject-time bootstrap execution plus service-manifest-based readiness tracking in [src/server.py](/home/josep/dog/kennel/src/server.py).

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
  "hermes_home": "/home/dev/.hermes",
  "workspace_root": "/home/dev/workspace",
  "config_path": "/home/dev/.hermes/config.yaml",
  "env_path": "/home/dev/.hermes/.env",
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
- `/home/dev/.hermes/sessions/` exists and is writable.[^4]
- `state.db` either present or creatable.[^4]


### 7.5 Role-specific commands

#### 7.5.1 interactive-cli

```bash
env -i $(cat /home/dev/.hermes/.env | xargs) \
  HERMES_HOME=/home/dev/.hermes \
  HOME=/home/dev \
  bash -lc 'cd /home/dev/workspace && exec hermes'
```

- Supervisor allocates a PTY for this process so our app can multiplex user websockets onto the CLI.
- Health: process alive, PTY attached, optional periodic “ping” via a lightweight CLI command (e.g. `hermes --version`) if we want additional assurance.


#### 7.5.2 api-server

Hermes docs show enabling API server via `.env` and then running the gateway, which starts the API server alongside other platforms.[^6][^3]

```bash
env -i $(cat /home/dev/.hermes/.env | xargs) \
  HERMES_HOME=/home/dev/.hermes \
  HOME=/home/dev \
  bash -lc 'cd /home/dev/workspace && exec hermes gateway'
```

Health probe:

```bash
curl -fsS "http://127.0.0.1:${API_SERVER_PORT}/health" || exit 1
```

- Supervisor treats API health as readiness signal.[^3]


#### 7.5.3 gateway

```bash
env -i $(cat /home/dev/.hermes/.env | xargs) \
  HERMES_HOME=/home/dev/.hermes \
  HOME=/home/dev \
  bash -lc 'cd /home/dev/workspace && exec hermes gateway'
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
    - mounts persistent volumes for `/home/dev/.hermes` and `/home/dev/workspace`.
    - writes `config.yaml` and `.env` into `/home/dev/.hermes`.
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

1. **Phase 1 – Document and stabilize the existing Hermes path** : COMPLETE.

2. **Phase 2 – Split current gateway runtime from future role model**
    - Extract the current implementation into an explicitly named role/profile, effectively today's `gateway_ws`.
    - Define compatibility rules so existing backend/runtime-preset consumers keep working.
    - Introduce a role contract only after we can map current behavior cleanly onto it.
3. **Phase 3 – Add first-class `api-server` support**
    - Add a distinct Hermes bootstrap profile for API mode rather than overloading the current gateway launcher.
    - Define backend proxy/routing semantics to the per-workspace API server.
    - Add readiness rules and policy checks around `API_SERVER_ENABLED`, `API_SERVER_HOST`, `API_SERVER_PORT`, and `API_SERVER_KEY`.
4. **Phase 4 – Add first-class `interactive-cli` support**
    - Implement a Hermes CLI/TUI startup path with PTY ownership semantics.
    - Decide whether kennel should own PTY lifecycle directly or whether backend continues to own attach semantics.
    - Migrate one interactive flow only after the PTY contract is explicit.
5. **Phase 5 – Evaluate supervisor/migration work**
    - Only after Phases 1-4, decide whether a dedicated supervisor actually improves the system over the current bootstrap + service-manifest model.
    - If yes, migrate deliberately with compatibility for existing presets, paths, and readiness endpoints.
6. **Phase 6 – Hardening and optional gateway expansion**
    - Add metrics, rate limits, observability, and stronger policy validation.
    - Add platform-specific messaging gateway support only if we truly want Hermes-owned external sessions rather than backend-owned runtime invoke flows.

## 12. Failure-case review: current blocking issue

We reviewed the current blocking failure mode against the implemented kennel/backend seam:

- A workspace created with the Hermes agent-runtime preset can reach `WorkspaceStatus.ready`.
- Browser terminal access can succeed.
- The Hermes runtime service can still remain `pending` because port `4319` is not listening.

### 12.1 What this failure means today

This is **not** evidence that the future `interactive-cli` role is broken, because kennel does not implement that role yet.

Today there are two separate execution surfaces:

- Browser terminal access uses kennel's PTY shell endpoint at `GET/WS /envs/{name}/ws`.
- Hermes agent-runtime access uses the kennel-owned `hermes_agent_runtime` bootstrap profile, which is expected to start a websocket gateway service on port `4319`.

So "I can request and connect to the provisioned workspace" only proves the container and terminal path are healthy. It does **not** prove the Hermes runtime path is healthy.

### 12.2 Boundary assessment

The observed `4319` failure is primarily **inside the current kennel/runtime-preset boundary**, not outside it.

Why:

- Backend intentionally delegates Hermes startup to kennel when `runtime_preset: "hermes"` is used.
- Kennel owns the Hermes runtime files, bootstrap profile, launcher command, declared service metadata, and readiness probing for that path.
- Backend/room connection logic then consumes kennel service discovery and correctly reports the runtime as pending when `4319` is not listening.

That means the frontend/backend are mostly surfacing kennel truth here rather than inventing an unrelated failure mode.

### 12.3 Confirmed current implementation failure cases

1. Workspace readiness is not runtime readiness.
   Backend marks the workspace `ready` after inject/bootstrap succeeds, without waiting for the declared Hermes runtime service to become `ready`. This allows a workspace to look provisioned while the Hermes websocket service is still pending or broken.

2. The Hermes launcher can leave a live PID with no listening socket.
   If Hermes cannot actually be executed, the current launcher falls back to `tail -f /dev/null`. That keeps the tracked process alive while guaranteeing that port `4319` never opens.

3. Kennel validates process start, not successful runtime bind.
   Background bootstrap only confirms that the spawned process survives briefly. It does not require Hermes to bind `4319` before bootstrap is treated as successful.

4. The current preset conflates "Hermes runtime" with a gateway websocket implementation.
   The existing preset is effectively `gateway_ws`, while the roadmap's `interactive-cli` role is a different future runtime shape. The naming overlap makes it too easy to assume terminal success implies Hermes runtime success.

5. We do not yet have end-to-end Hermes readiness validation.
   Current tests lock in file generation, launch commands, and readiness messages, but they do not prove that a provisioned Hermes preset actually reaches a listening websocket on `4319`.

### 12.4 Does the current roadmap address this?

Partially, but not completely.

What the roadmap already helps with:

- Phase 2 correctly calls for splitting today's gateway-style runtime from the future role model.
- Phase 4 correctly treats `interactive-cli` as a distinct PTY-backed role rather than assuming it is the same thing as the current websocket gateway preset.

What is still missing from the roadmap for this blocker:

- an explicit rule for when workspace status may become `ready` versus when runtime status must still be `pending`
- failure handling for "PID exists but `4319` never binds"
- explicit operator-facing log and error surfacing for Hermes startup failures
- end-to-end validation of the Hermes preset, not just contract-level unit tests

### 12.5 Plan adjustments required

Before or alongside Phase 2, the plan should explicitly include:

1. Separate the current preset naming from the future role model.
   Treat today's implementation as a gateway-websocket runtime path, not as the general answer for interactive CLI.

2. Gate runtime-backed readiness on actual service readiness.
   A Hermes runtime workspace should not be presented as runtime-ready until kennel service discovery reports the Hermes service as `ready`, not merely started.

3. Fail fast on inert launcher fallback states.
   If Hermes falls through to a non-serving placeholder process, kennel should surface that as failed startup rather than as a merely pending runtime.

4. Add end-to-end Hermes provisioning validation.
   We need a validation path that proves the preset can boot Hermes and bind `4319`, or else records a contract-level failure with a clear reason.

5. Surface the distinction between terminal connectivity and runtime connectivity everywhere.
   Browser terminal success and Hermes runtime success should be treated as separate readiness dimensions in backend and docs.

## 13. API-server extraction context

We are now prioritizing **extracting the current gateway-style Hermes runtime** and replacing the room-runtime connection path with a **Hermes API-server-backed service link** where appropriate.

### 13.1 What primitives already exist

The current codebase already has several useful primitives for this shift:

1. Kennel service discovery already supports multiple protocols.
   Kennel service metadata and discovery support `http`, `https`, `ws`, and `wss`, not just websocket runtimes.

2. Backend workspace service summaries already preserve protocol, URL, transport kind, and readiness.
   The backend can already ingest kennel-discovered services and expose them as typed workspace service summaries.

3. Room workspace connection descriptors already support both:
   - `agent_runtime_connect`
   - `service_connect`

4. Room connection selection already knows how to surface routable HTTP services.
   If a workspace has a ready HTTP service, the connection descriptor layer can already expose it as a room endpoint.

5. Kennel already has an internal runtime invoke seam, but it is runtime-profile-specific.
   `POST /envs/{name}/agent-runtimes/{service_id}/invoke` is a kennel-owned adapter seam for agent runtimes today.

These primitives mean we do **not** need to invent service discovery, URL projection, or room connection descriptors from scratch.

### 13.2 What is missing for Hermes API-server success

The missing pieces are concentrated in the room-runtime execution contract and the kennel Hermes profile set:

1. There is no first-class Hermes API-server bootstrap profile yet.
   The current Hermes preset is still gateway-websocket oriented.

2. Room runtime execution is still websocket-centric.
   The current room runtime execution adapter rejects non-websocket protocols, so it cannot directly consume an HTTP Hermes API-server endpoint yet.

3. Runtime target resolution is hard-coded to `agent_runtime_connect`.
   The current room runtime target path expects an agent-runtime endpoint, not a service-link-backed HTTP endpoint.

4. Kennel does not yet expose a profile-owned Hermes API-server contract.
   We need declared service metadata for API mode, including protocol, port, path, and readiness behavior.

5. We do not yet have an OpenAI-compatible room adapter for Hermes API mode.
   Even if the service were up, the room runtime orchestration layer still needs a request/response adapter that speaks Hermes API-server semantics instead of websocket invocation semantics.

### 13.3 Practical design implication

This suggests a cleaner target architecture:

- `interactive-cli`
  Remains a PTY/browser-terminal concern.
- `gateway`
  Becomes an explicitly separate Hermes messaging/websocket mode.
- `api-server`
  Becomes the preferred room-runtime integration path, likely consumed as a room-visible service endpoint rather than as today's websocket agent-runtime endpoint.

In other words, the room-runtime path should probably stop pretending Hermes is "just another websocket runtime" and instead treat Hermes API mode as an HTTP service with a runtime-specific adapter layered above it.

### 13.4 Required primitives before implementation

Before implementation, we should make these primitives explicit:

1. A kennel Hermes API bootstrap profile.
   Example target: `hermes_api_server`.

2. Declared service metadata for Hermes API mode.
   Example target:
   - `service_name: hermes_api`
   - `kind: agent_runtime` or `kind: custom` with explicit runtime adapter semantics
   - `protocol: http`
   - `port: 8642`
   - `path: /v1/...` or `/health` as appropriate

3. A readiness contract for Hermes API mode.
   Readiness should depend on successful HTTP health probing, not just process liveness.

4. A backend runtime adapter for HTTP-based room execution.
   This may either:
   - extend the current room runtime adapter system to support HTTP runtimes, or
   - treat Hermes API mode as a room `service_connect` endpoint plus a Hermes-specific execution adapter.

5. A target-resolution rule for API-backed room runtimes.
   We need to decide whether room runtime should:
   - continue using `agent_runtime_connect` but allow HTTP transport, or
   - resolve through `service_connect` for API-backed runtimes.

6. Workspace readiness semantics that separate:
   - workspace ready
   - terminal ready
   - runtime ready
   - API service ready

### 13.5 Recommendation

The cleanest next step is:

1. Extract today's Hermes preset into an explicitly named gateway/websocket profile.
2. Add a separate Hermes API-server profile in kennel.
3. Extend backend room runtime orchestration so Hermes API mode is consumed through an HTTP-aware runtime adapter rather than the current websocket-only adapter.
4. Only then decide whether the room connection should resolve Hermes API mode via `agent_runtime_connect` or `service_connect`.

That sequence keeps the role split honest and avoids trying to force the current websocket agent-runtime abstraction to represent two incompatible Hermes runtime shapes at once.

## 14. Concrete implementation checklist

Success criteria for this checklist:

- a user can provision a Hermes server workspace
- the workspace exposes a Hermes API service that becomes actually ready
- the user can attach that workspace to a room
- attach means the room can send a message to Hermes and receive a response back successfully

### 14.1 Recommended target contract

Recommended target for this implementation slice:

- kennel owns a new Hermes API-server bootstrap profile
- the provisioned workspace exposes a ready HTTP Hermes endpoint
- backend room connection resolves that endpoint as the room's current runtime target
- backend room runtime orchestration invokes Hermes through an HTTP adapter, not the websocket adapter

This keeps the future `interactive-cli` role separate and avoids continuing to overload the current gateway websocket path.

### 14.2 Kennel changes

1. Add a dedicated Hermes API-server service profile in [server.py](/home/josep/dog/kennel/src/server.py).
   Changes:
   - extend `SERVICE_PROFILE_DEFAULTS`
   - add a new declared service entry, for example `hermes_api`
   - set:
     - `id`
     - `service_name`
     - `label`
     - `kind="agent_runtime"` or `kind="custom"` if we decide to keep runtime semantics out of kennel invoke
     - `runtime_id="hermes"`
     - `runtime_profile="hermes_api_server"`
     - `transport_kind="http"`
     - `protocol="http"`
     - `port=8642`
     - `path` appropriate to the surfaced base path

2. Add Hermes API runtime file generation in [server.py](/home/josep/dog/kennel/src/server.py).
   Changes:
   - add a new helper next to `_hermes_runtime_files()`, for example `_hermes_api_runtime_files(user: str)`
   - write:
     - `/home/dev/.hermes/config.yaml`
     - `/home/dev/.hermes/.env`
     - `/home/dev/.hermes/hermes-api-launcher`
   - `.env` should explicitly enable:
     - `API_SERVER_ENABLED=true`
     - `API_SERVER_HOST=127.0.0.1` or `0.0.0.0` depending on agreed kennel routing policy
     - `API_SERVER_PORT=8642`
     - `API_SERVER_KEY=...`
   - runtime files should preserve canonical Stage 1 paths:
     - `/home/dev/.hermes`
     - `/home/dev/workspace`

3. Add a new bootstrap profile in [server.py](/home/josep/dog/kennel/src/server.py).
   Changes:
   - extend `_bootstrap_profile_runtime_files()`
   - extend `_bootstrap_profile_plan()`
   - profile name recommendation: `hermes_api_server`
   - startup command should launch Hermes in the documented API-enabled mode, not the current gateway websocket mode
   - background `service_name` should match the new declared service profile, e.g. `hermes_api`

4. Separate the current gateway preset from the future API profile in [server.py](/home/josep/dog/kennel/src/server.py).
   Changes:
   - keep `hermes_agent_runtime` explicitly gateway/websocket oriented, or rename/add alias such as `hermes_gateway_ws`
   - do not reuse the same profile for both websocket gateway and API-server startup

5. Add runtime preset mapping strategy in [server.py](/home/josep/dog/kennel/src/server.py).
   Decision required:
   - either keep `runtime_preset: "hermes"` mapped to API-server mode for room/runtime work
   - or introduce a second preset/profile selection path so backend can choose between:
     - `hermes_gateway`
     - `hermes_api`

   Minimum implementation requirement:
   - backend must be able to request the Hermes API profile deterministically

6. Tighten readiness semantics in [server.py](/home/josep/dog/kennel/src/server.py).
   Changes:
   - extend `_discover_service()`
   - for the Hermes API profile, readiness must depend on HTTP health success, not just PID presence
   - add a helper to probe an internal HTTP endpoint such as:
     - `/health`
     - `/v1/models`
   - keep the returned `url` routable for backend consumption

7. Remove or hard-fail inert fallback states for the new API profile in [server.py](/home/josep/dog/kennel/src/server.py).
   Changes:
   - do not allow `tail -f /dev/null` to count as acceptable startup for the API profile
   - if Hermes is not found or API mode fails to bind, bootstrap should fail clearly

8. Optionally add a distinct launcher script in [server.py](/home/josep/dog/kennel/src/server.py).
   Recommendation:
   - keep `hermes-agent-launcher` for gateway/websocket mode
   - add `hermes-api-launcher` for API mode
   This will make debugging and operator inspection much easier.

9. Add kennel tests for the new profile.
   Files:
   - [test_runtime_profiles.py](/home/josep/dog/kennel/tests/test_runtime_profiles.py)
   - optionally [test_agent_runtime_invoke.py](/home/josep/dog/kennel/tests/test_agent_runtime_invoke.py)
   Required coverage:
   - profile runtime files contain API settings
   - declared service metadata uses `http` and port `8642`
   - readiness logic reflects API health rules
   - failed startup without a listener is surfaced as failure, not indefinite pending

10. Extend provisioning validation.
   Files:
   - [validate_provisioning.py](/home/josep/dog/kennel/scripts/validate_provisioning.py)
   - [provisioning-validation-runbook.md](/home/josep/dog/kennel/docs/provisioning-validation-runbook.md)
   Required coverage:
   - create env with Hermes API profile/preset
   - inject succeeds
   - services endpoint reports Hermes API service as `ready`
   - HTTP health or model endpoint is reachable through kennel-discovered service metadata

### 14.3 Backend workspace provisioning changes

1. Decide how backend requests Hermes API mode in [workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py).
   Changes:
   - update `_resolve_kennel_runtime_preset()` or surrounding normalization logic if needed
   - update `build_workspace_kennel_provisioning_request()`
   - ensure Hermes room/runtime provisioning selects the API bootstrap profile, not the gateway websocket one

2. Update backend startup defaults in [workspace_bootstrap_service.py](/home/josep/dog/backend/app/services/workspace_bootstrap_service.py).
   Changes:
   - revise `AGENT_SERVICE_PROFILES["hermes"]`
   - stop describing Hermes primarily as a websocket launcher on `4319`
   - encode the new expected host/port/env vars for API mode if backend still projects Hermes defaults

3. Align workspace meta projection in [workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py).
   Required outcome:
   - `kennel_inject_request.bootstrap_profile`
   - `declared_services`
   - `bootstrap_workspace_path`
   all reflect Hermes API mode so service discovery and operator debugging remain coherent

4. Stop marking Hermes runtime workspaces as fully runtime-ready before the Hermes API service is actually ready.
   File:
   - [workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py)
   Minimum acceptable behavior:
   - workspace provisioning success may still set `WorkspaceStatus.ready`
   - but room/runtime availability must depend on discovered service readiness, not merely workspace state
   Stronger option:
   - add a richer readiness summary dimension for runtime service readiness

### 14.4 Backend service discovery and connection changes

1. Preserve Hermes API service metadata in [workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py).
   Changes:
   - ensure `_service_summary_from_dict()` correctly retains:
     - `runtime_id="hermes"`
     - `runtime_profile="hermes_api_server"`
     - `transport_kind="http"`
     - `protocol="http"`
     - `url`

2. Decide the room connection purpose for Hermes API mode in [room_workspace_connection_service.py](/home/josep/dog/backend/app/services/room_workspace_connection_service.py).
   Decision:
   - Option A: continue using `agent_runtime_connect`, but allow HTTP endpoints
   - Option B: use `service_connect` for Hermes API mode and build a runtime adapter over service endpoints

   Recommendation:
   - prefer Option A if we want Hermes API mode to remain a first-class room runtime
   - prefer Option B if we want API services and runtimes to share one generic HTTP service-link abstraction

3. Update endpoint selection logic in [room_workspace_connection_service.py](/home/josep/dog/backend/app/services/room_workspace_connection_service.py).
   Changes depend on the decision above:
   - if Option A:
     - allow `agent_runtime_connect` endpoints whose protocol is `http`
     - `_select_runtime_endpoint()` must accept the Hermes API endpoint
   - if Option B:
     - add a parallel resolver for service-backed room runtimes, or generalize `consume_current_room_workspace_runtime_target()`

4. Update room runtime target typing in [room_workspace_connection_service.py](/home/josep/dog/backend/app/services/room_workspace_connection_service.py).
   Changes:
   - `RoomWorkspaceRuntimeTarget` already includes `protocol` and `url`
   - confirm it can represent HTTP targets cleanly
   - if needed, add explicit fields for:
     - auth mode
     - request base path
     - endpoint kind

5. Update tests for runtime target resolution.
   Files:
   - [test_room_workspace_runtime_target_resolution.py](/home/josep/dog/backend/app/tests/services/test_room_workspace_runtime_target_resolution.py)
   Required coverage:
   - Hermes API endpoint can be selected as the room runtime target
   - HTTP protocol targets are accepted by the chosen resolution path

### 14.5 Backend runtime execution changes

1. Add an HTTP-capable runtime adapter in [room_workspace_runtime_orchestrator.py](/home/josep/dog/backend/app/services/room_workspace_runtime_orchestrator.py).
   Recommendation:
   - add a Hermes-specific adapter, e.g. `HermesApiRoomWorkspaceRuntimeAdapter`
   - register it in `_DEFAULT_RUNTIME_ADAPTERS` or `profile_specific_adapters` for:
     - `("hermes", "hermes_api_server")`

2. Implement Hermes API request/response translation.
   Likely file:
   - [room_workspace_runtime_orchestrator.py](/home/josep/dog/backend/app/services/room_workspace_runtime_orchestrator.py)
   or a new dedicated helper module if it gets large

   Required behavior:
   - build an OpenAI-compatible request payload for Hermes API server
   - POST to the discovered Hermes API endpoint
   - normalize Hermes API responses back into `RoomWorkspaceRuntimeInvocationResult`

3. Extend runtime execution beyond websocket-only assumptions.
   Files:
   - [room_workspace_runtime_execution_service.py](/home/josep/dog/backend/app/services/room_workspace_runtime_execution_service.py)
   - [room_workspace_runtime_orchestrator.py](/home/josep/dog/backend/app/services/room_workspace_runtime_orchestrator.py)

   Decision:
   - either keep `room_workspace_runtime_execution_service.py` websocket-only and place Hermes HTTP logic in a separate adapter
   - or generalize it to support both websocket and HTTP execution

   Recommendation:
   - keep websocket execution service focused
   - add a separate Hermes HTTP adapter to avoid mixing incompatible protocols into one low-level executor

4. Update kennel client only if necessary.
   File:
   - [kennel_client.py](/home/josep/dog/backend/app/services/kennel_client.py)

   If backend will invoke Hermes through the discovered service URL directly:
   - no kennel invoke API change is required

   If we want kennel to proxy Hermes API requests:
   - add a new kennel client method and a corresponding kennel HTTP proxy endpoint

   Recommendation:
   - prefer direct backend-to-discovered-service HTTP for the API-server path unless we need kennel to enforce extra auth/routing policy

5. Update room runtime tests.
   Files:
   - [test_room_workspace_runtime_execution_service.py](/home/josep/dog/backend/app/tests/services/test_room_workspace_runtime_execution_service.py)
   - [test_room_workspace_runtime_orchestrator.py](/home/josep/dog/backend/app/tests/services/test_room_workspace_runtime_orchestrator.py)
   - [test_room_workspace_runtime_invoke.py](/home/josep/dog/backend/app/tests/api/routes/test_room_workspace_runtime_invoke.py)

   Required coverage:
   - Hermes API runtime target is accepted
   - backend sends a message to Hermes API mode successfully
   - backend receives and normalizes a response
   - room invocation persists the returned message correctly

### 14.6 Interface and model changes

1. Review backend models in [models.py](/home/josep/dog/backend/app/models.py).
   Relevant types:
   - `RoomWorkspaceConnectionPurpose`
   - `RoomWorkspaceConnectionCapability`
   - `RoomWorkspaceEndpointKind`
   - `RoomWorkspaceEndpointDescriptor`
   - `WorkspaceServiceSummary`

   Potential changes:
   - no model change may be needed if we allow HTTP agent-runtime endpoints
   - if we want clearer semantics, consider introducing:
     - a distinct endpoint kind for API-backed runtime services, or
     - a more explicit runtime transport enum

2. Review kennel service manifest models in [server.py](/home/josep/dog/kennel/src/server.py).
   Relevant types:
   - `DeclaredWorkspaceService`
   - `DiscoveredWorkspaceService`
   Ensure they can represent Hermes API mode without semantic overload.

### 14.7 End-to-end validation checklist

This is the minimum acceptance checklist for implementation completion:

1. Provision Hermes API workspace.
   - backend requests the correct kennel preset/profile
   - kennel inject writes Hermes API runtime files
   - kennel launches Hermes API mode

2. Confirm service readiness.
   - `GET /envs/{name}/services` reports Hermes API service
   - service status is `ready`
   - protocol is `http`
   - URL is populated and routable

3. Attach workspace to room.
   - room connection descriptor becomes `available`
   - descriptor includes the Hermes endpoint selected for room runtime use

4. Send a room runtime message.
   - backend invokes Hermes through the selected API endpoint
   - Hermes returns a successful response
   - response is normalized into room runtime output

5. Receive the room response.
   - the room invocation API returns success
   - a room message is emitted/persisted with the Hermes output

6. Failure handling works.
   - if Hermes process starts but API port never binds, the room connection remains unavailable or pending with a clear reason
   - if Hermes cannot launch, bootstrap or service readiness surfaces an actionable failure

### 14.8 Suggested implementation order

1. Kennel: add Hermes API profile, launcher, declared service, and readiness checks.
2. Kennel: add provisioning validation and unit tests for the new profile.
3. Backend: update provisioning normalization so Hermes room/runtime work requests the API profile.
4. Backend: allow room runtime target resolution to accept the Hermes API endpoint.
5. Backend: add Hermes HTTP runtime adapter and tests.
6. Backend: run end-to-end room attach/message validation.
7. After that, return to gateway extraction cleanup and future `interactive-cli`.

## 15. Phase 1 documentation status

Phase 1 documentation cleanup updated the main Hermes-adjacent kennel docs to match the current implementation and the canonical Stage 1 paths:

- [agent-runtime-environment-state.md](/home/josep/dog/kennel/docs/agent-runtime-environment-state.md)
- [runtime-service-alignment-contract.md](/home/josep/dog/kennel/docs/runtime-service-alignment-contract.md)
- [runtime-preset-api-reference.md](/home/josep/dog/kennel/docs/runtime-preset-api-reference.md)

For future Hermes design work, the implementation in [src/server.py](/home/josep/dog/kennel/src/server.py), [src/flavours.py](/home/josep/dog/kennel/src/flavours.py), and [tests/test_runtime_profiles.py](/home/josep/dog/kennel/tests/test_runtime_profiles.py) should still be treated as the primary source of truth.

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
