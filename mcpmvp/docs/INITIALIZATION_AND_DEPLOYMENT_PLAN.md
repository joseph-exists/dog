# MCPMVP Initialization And Deployment Plan

## Scope

This plan covers how `mcpmvp` servers should be instantiated inside the Dog environment and how Dog-managed agents should discover and call them at runtime.

It is intentionally aligned to the current codebase:

- `mcpmvp/` already contains standalone FastMCP servers.
- `backend/app/models.py` already supports `PromptToolingConfig.mcp`.
- `backend/app/services/prompt_runtime_resolver.py` already carries `tools.mcp` into runtime `tool_config`.
- `backend/app/services/agent_instance.py` does not yet attach MCP servers to runtime agents.
- `docker-compose.yml` does not yet define any `mcpmvp` service(s).

## Current State

### What exists

- `mcpmvp/affordance_server.py`
- `mcpmvp/story_server.py`
- `mcpmvp/affordance_service.py`
- Prompt-builder schema support for:
  - `tools.mcp.servers[].id`
  - `tools.mcp.servers[].require_approval`
- Agent runtime config resolution that preserves `tool_config["mcp"]`

### What does not exist yet

- A container or Compose service for `mcpmvp`
- A backend-owned MCP server registry
- Runtime code that converts `tool_config.mcp` into attached MCP toolsets
- Environment-level health checks for MCP servers
- Deployment wiring in `scripts/build.sh` / `scripts/deploy.sh` via Compose definitions

## Target Architecture

### Principle

MCP servers should run inside Dog infrastructure as managed platform services, not as ad hoc developer-local processes. Agents should not construct MCP definitions themselves. They should receive an allowed MCP server set from Dog runtime resolution.

### Topology

1. `mcpmvp` runs as one or more long-lived services in the Dog Docker/Swarm stack.
2. The backend owns the canonical registry of MCP server descriptors available in this environment.
3. Agent prompt/runtime config selects from that registry by server `id`.
4. `agent_instance.py` resolves the allowed MCP descriptors and attaches them when instantiating the PydanticAI agent.
5. Agents use MCP through Dog runtime, with room/agent policy applied before tool exposure.

### Recommended deployment shape

Start with a single `mcpmvp` container that can expose multiple logical servers.

Why this shape first:

- simplest deployment and operations model
- matches the current `mcpmvp/` package layout
- keeps server definitions versioned with Dog
- avoids premature per-server orchestration

Decompose into separate containers later only if:

- one server needs distinct secrets
- one server has materially different scaling characteristics
- one server becomes unstable or expensive enough to isolate

## Initialization Model

### Environment bootstrap

At stack startup:

1. Core infra starts: `db`, `redis`, `gittin`, `tesser`, `kennel`.
2. `mcpmvp` service starts.
3. `mcpmvp` loads its YAML-backed registries and any local service state.
4. `backend` starts after `mcpmvp` is healthy.
5. Backend loads a static MCP registry describing the in-environment servers.
6. When an agent run is requested, runtime config resolution decides which MCP servers that agent may use.
7. `agent_instance.py` attaches builtin tools, repo tools, and MCP servers into one effective runtime agent.

### Agent initialization contract

The authoritative source of requested MCP access is:

- `PromptConfigDraft.tools.mcp`

The authoritative source of what is actually attachable in this environment should be:

- a backend-owned server registry plus policy checks

That means `tools.mcp` is a request, not trustable raw execution config.

## MCP Registry Contract

### Why a registry is necessary

The frontend and prompt builder currently allow server `id` references, but an `id` alone is not enough for execution. Dog runtime needs a trusted mapping from `id` to connection details.

### Recommended registry shape

Create a backend-owned registry, probably config-backed at first, with entries like:

```json
{
  "id": "affordance",
  "transport": "streamable_http",
  "url": "http://mcpmvp:8080/mcp/affordance",
  "enabled": true,
  "require_approval_default": "never",
  "scopes": ["system", "personal"],
  "tags": ["introspection", "demo-builder"]
}
```

Possible initial homes:

- `backend/app/core/`
- `backend/app/services/`
- a checked-in JSON/YAML file loaded by backend at startup

The first version does not need database persistence.

## Runtime Attachment Plan

### Required backend change

Extend `backend/app/services/agent_instance.py` so that after effective runtime config is resolved, it:

1. reads `effective["tool_config"]["mcp"]`
2. validates requested server ids against the backend registry
3. applies environment and room policy filters
4. constructs MCP tool attachments for the selected servers
5. passes those MCP toolsets into the PydanticAI `Agent(...)` constructor

### Policy order

Recommended allow/deny order:

1. global environment allowlist
2. server enabled flag
3. room-level `tool_policy` override
4. agent-level prompt request (`tools.mcp`)
5. optional approval behavior from prompt config or registry default

### Important boundary

Do not let arbitrary prompt payloads provide:

- raw commands
- raw subprocess launch definitions
- arbitrary hostnames or URLs

Prompt payloads should only select from backend-approved server ids.

## Deployment Plan

### Phase 1: make `mcpmvp` deployable

Add:

- `mcpmvp/Dockerfile`
- `mcpmvp` service in `docker-compose.yml`
- health endpoint or a simple startup probe strategy

Recommended first command model:

- run one ASGI process that mounts all MCP endpoints under a shared port

If FastMCP forces one process per server, use either:

- one container running a lightweight supervisor
- separate services like `mcpmvp-affordance`, `mcpmvp-story`

but prefer the single-service shape first.

### Phase 2: define backend registry

Add a backend config source for MCP servers with:

- stable server ids
- transport type
- internal URL
- approval default
- enabled flag

### Phase 3: attach MCP to agents

Implement runtime wiring in `agent_instance.py`.

Minimum acceptance criteria:

- agent with no `tools.mcp` gets no MCP tools
- agent with allowed `tools.mcp.servers=[{"id":"affordance"}]` gets that MCP server attached
- unknown server ids are ignored or rejected deterministically
- disabled servers are never attached

### Phase 4: expose operator visibility

Add logs for:

- requested MCP ids
- attached MCP ids
- rejected MCP ids and reason

Add health visibility for:

- `mcpmvp` container liveness
- backend ability to reach configured MCP endpoints

### Phase 5: deployment hardening

Add:

- timeouts
- retry policy where appropriate
- per-server auth if later needed
- rate limiting or concurrency controls if a server becomes expensive

## Compose And Network Recommendations

### Network assumptions

The backend should call MCP servers over the internal Docker network, not public Traefik routes.

Preferred internal addresses:

- `http://mcpmvp:PORT/...`

Not preferred for backend-to-MCP traffic:

- public `https://` hostnames
- localhost assumptions

### Suggested service dependency

Add `mcpmvp` as a `backend.depends_on` dependency once a health check exists.

That avoids agent runs starting against an unavailable MCP surface during cold boot.

## Configuration Model

### PromptConfig request shape

Prompt configs should continue to use a minimal request shape:

```json
{
  "tools": {
    "tool_mode": "optional",
    "mcp": {
      "servers": [
        { "id": "affordance", "require_approval": "never" },
        { "id": "story", "require_approval": "always" }
      ]
    }
  }
}
```

### Backend-resolved effective shape

Backend should turn that into trusted runtime descriptors using registry data, for example:

```json
{
  "tool_config": {
    "mcp": {
      "servers": [
        {
          "id": "affordance",
          "transport": "streamable_http",
          "url": "http://mcpmvp:8080/mcp/affordance",
          "require_approval": "never"
        }
      ]
    }
  }
}
```

The prompt should not be the source of `url`.

## Recommended Implementation Order

1. Add a deployable `mcpmvp` service.
2. Add a backend MCP registry with trusted descriptors.
3. Wire `agent_instance.py` to attach MCP servers from resolved runtime config.
4. Add tests around prompt resolution plus agent tool attachment.
5. Add operator-facing health and logging.

## Risks And Constraints

### Current documentation drift

`mcpmvp/README.md` still mentions a backend dependency on `localhost:8000`, while `mcpmvp/ARCHITECTURE.md` says these servers should use direct imports and no backend HTTP dependency. The deployment plan should follow `ARCHITECTURE.md`, not the outdated README text.

### PydanticAI integration detail

The repo already stores MCP intent in prompt config, but actual PydanticAI attachment mechanics still need to be implemented. The exact constructor shape should be chosen to match the PydanticAI version pinned in Dog backend.

### Transport choice

If FastMCP’s easiest production transport is stdio rather than HTTP, Dog should still keep the same trust model:

- backend registry owns descriptors
- prompt config selects ids
- backend runtime performs the actual attachment

The transport implementation can change without changing the policy model.

## Definition Of Done

This plan is complete when all of the following are true:

- `mcpmvp` starts inside Dog deployment without manual local setup
- backend has a trusted registry of MCP servers available in this environment
- prompt configs can request MCP servers by `id`
- backend agent initialization attaches only approved MCP servers
- agent runs can successfully call `mcpmvp` tools from within Dog infrastructure
- logs make it obvious which MCP servers were requested, attached, or denied

## Near-Term Build List

- Add `mcpmvp/Dockerfile`
- Add `mcpmvp` service to `docker-compose.yml`
- Add backend MCP registry module
- Add MCP attachment logic in `backend/app/services/agent_instance.py`
- Add tests for MCP runtime attachment
- Update stale `mcpmvp/README.md` text
