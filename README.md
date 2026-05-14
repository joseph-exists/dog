# Dog

Core Features: Demos Available for all functionality.

## Core Product Systems

Agent management centers on creating, configuring, cloning, and adding agents as extensible, portable, and tunable configuration code. Agents can carry provider/model settings, participation modes, coordinator status, and runtime tool flags, then enter rooms as operators, specialists, coordinators, or UI-producing actors. The main current journey is documented in [Room + Agents](./docs/affordances/journeys/room-agents.md), with deeper runtime context in [Agent -> Story Runtime](./docs/affordances/journeys/agent-story-runtime.md).

Chat rooms are the collaborative runtime container: they combine (1-n) human participants, 1-n agent participants, streaming messages, debug surfaces, participant panels, AG-UI/A2UI output, and optional workspace/repo context. User messages can trigger active room agents, coordinator agents run before regular agents, and agent output returns to the same room stream; A2A mention/tool behavior can then invoke follow-on agents where enabled. The room-agent behavior and visible affordances are mapped in [Room + Agents](./docs/affordances/journeys/room-agents.md), while the call hierarchy is summarized in [Agent / Story / Room Coupling And Redundancy Analysis](./docs/affordances/journeys/agent-story-room-coupling-analysis.md).

The story state machine starts as authored story logic: nodes, choices, state schema, conditions, and transitions. Once attached to a room, that story can become a shared, revisioned room runtime that users can start, advance, rewind, reset, and inspect; this shared runtime is distinct from local preview/player simulations. Agents in a story-backed room can read the current runtime context, including current node, available choices, path, and story state, as described in [Story -> Room Runtime](./docs/affordances/journeys/story-room-runtime.md) and [Agent -> Story Runtime](./docs/affordances/journeys/agent-story-runtime.md).

User access providers act as provider gateways: user-scoped LLM credentials, model registrations, and provider/model choices that let agents run against different backends without hard-coding access into the agent definition itself. The current model supports user-created/custom models, provider-bound catalog entries, and mixed-provider room participation; the provider setup direction is captured in [UserAccessProvider Enhancements Design](./docs/archived/plans/2026-03-08-user-access-provider-enhancements-design.md), while the custom model registration path is outlined in [User Model Registration](./docs/unsort/user-model-provider-registration.md) and validated from the room side in [Mixed Provider Room](./docs/affordances/walkthroughs/room-agents/05-mixed-provider-room.md).

The Shadow system provides durable, git-backed runtime memory for important application entities and their relationships. Rooms, stories, agents, personas, models, and user LLM providers can be snapshotted into service-owned git repos, then read back as invisible agent context with DB fallback and prompt-friendly summaries. This makes runtime state and configuration replayable, pinnable, and inspectable by backend services without exposing git mechanics to users; see [Shadow Overview](./docs/shadow/shadow-overview.md), [Shadow Milestone 2 Technical Specification](./docs/shadow/ShadowPhase2Milestone2_TechnicalSpec.md), and the runtime coupling notes in [Agent / Story / Room Coupling And Redundancy Analysis](./docs/affordances/journeys/agent-story-room-coupling-analysis.md).

Repos are platform-managed user repositories backed by Gittin/Gogs but exposed through Dog-owned authorization and product APIs. Users can import external repositories, browse trees/files/READMEs, inspect capability metadata, delete or cancel imports, and commit file mutations through backend-controlled write paths once a repo is `READY`. The service boundary deliberately separates lifecycle/provisioning in [user_repo_service.py](./backend/app/services/user_repo_service.py), product-facing read projections in [user_repo_view_service.py](./backend/app/services/user_repo_view_service.py), and async import work in [user_repo_outbox_worker.py](./backend/app/services/user_repo_outbox_worker.py); the user-facing surface is summarized in [Repos](./docs/affordances/surfaces/repos.md), with management direction in [User Repo Management](./docs/archived/plans/user-repo-management.md).

Projects are user-owned collaboration containers for grouping resources, allocating access, and giving related work a shared home. A project can attach stories, demos, rooms, repos, agents, workspaces, and other resources through `ProjectResource`, while direct and persona-mediated sharing flow through access grants, persona groups, and effective-role checks. The current product surface supports project creation, metadata editing, resource attach/detach, direct access grants, and persona collaboration groups; see [Projects](./docs/affordances/surfaces/projects.md), [Projects Container Plan](./docs/archived/plans/2026-03-06-projects-container.md), [projects.py](./backend/app/api/routes/projects.py), and [crud_projects.py](./backend/app/crud_projects.py).

Workspaces are Kennel-backed runtime environments for operating code, terminals, and agent-service/dev presets from inside Dog. The workspace API can spawn, list, start, stop, destroy, and open terminal access for environments; bootstrap intent can reference external URLs, user repos, runtime presets, env vars, runtime files, and generated bootstrap plans. Workspaces can also be attached to projects through the same `ProjectResource(resource_type="workspace")` graph used by other resources, giving project-visible runtime environments without making workspace ownership a separate collaboration system. The main implementation lives in [workspaces.py](./backend/app/api/routes/workspaces.py), [workspace_service.py](./backend/app/services/workspace_service.py), and [workspace_bootstrap_service.py](./backend/app/services/workspace_bootstrap_service.py), with frontend references in [Workspaces Implemented](./frontend/src/components/Workspaces/docs/implemented.md), [Repo And Bootstrap Contract](./frontend/src/components/Workspaces/docs/repo-bootstrap-contract.md), and [Project And Workspace Relationship Note](./frontend/src/components/Workspaces/docs/project-workspace-relationship.md).

Dog is a collaborative product workspace for developing, iterating, and sharing agents and their interfaces. 1-n users and llms in rooms, stories, personas, agents, demos, and repo-backed workspaces. the repository contains a full application stack with a FastAPI API, React console, realtime event transport, git-backed entity/versioning services, SVG/canvas export workers, and sandboxed runtime environments using lxc for fast launching dev environments with gpu passthrough. Note: the current kennel implementation is meant for local/owned infra only that is secured by other means.

## Key Backend Service Groups

The realtime layer is split between the WebSocket route, the per-worker connection manager, and the Redis-backed event fanout helpers. [websocket.py](./backend/app/api/routes/websocket.py) owns the AG-UI-style room session protocol: JWT authentication, room membership checks, handshake/replay, client `message.send` handling, and dispatch into the agent runner. [websocket_manager.py](./backend/app/services/websocket_manager.py) owns live socket bookkeeping on the current worker, room subscription lifecycles, Redis pub/sub listeners, and fanout to connected clients. [event_emitter.py](./backend/app/services/event_emitter.py) is the durable write path for room events and projections, while [realtime_publisher.py](./backend/app/services/realtime_publisher.py) publishes persisted events and ephemeral messages such as streaming token deltas. Reconnects are sequence-aware through [event_replay.py](./backend/app/services/event_replay.py), so Redis delivery can be best-effort without making the event log disposable.

The agent runtime has been deconstructed into slimmer handlers around a facade in [agent_runner.py](./backend/app/services/agent_runner.py). Selection and participation-mode logic live in [agent_selection.py](./backend/app/services/agent_selection.py); room-context acquisition is wrapped by [agent_context.py](./backend/app/services/agent_context.py); prompt assembly lives in [agent_prompt.py](./backend/app/services/agent_prompt.py); provider-backed model and tool wiring is centralized in [agent_instance.py](./backend/app/services/agent_instance.py); streaming and non-streaming execution are split into [agent_runner_streaming.py](./backend/app/services/agent_runner_streaming.py) and [agent_runner_non_streaming.py](./backend/app/services/agent_runner_non_streaming.py).

Supporting modules handle A2A orchestration, event publication, tool calls, typed request/result shapes, error handling, and invocation audit. The intended module boundaries are documented in [Agent Service Modularization](./backend/app/services/service-docs/agent-modularization-outline.md) and the runtime behavior is summarized in [Agent Orchestration Reference](./backend/app/services/service-docs/agent-orchestration-reference.md).

Provider adapters are the gateway layer between user-owned provider credentials and concrete model-provider APIs. [provider_adapters/base.py](./backend/app/services/provider_adapters/base.py) defines the shared contract for connection tests, model listing, account information, standardized result models, and adapter configuration. [provider_adapters/registry.py](./backend/app/services/provider_adapters/registry.py) maps provider type IDs to concrete adapters, decrypts provider keys, builds adapter config, and exposes high-level helpers such as `test_provider_connection`, `list_provider_models`, and `get_provider_account_info`. Concrete adapters currently cover OpenAI, Anthropic, Google, Azure, and OpenAI-compatible/custom providers through [openai_adapter.py](./backend/app/services/provider_adapters/openai_adapter.py), [anthropic_adapter.py](./backend/app/services/provider_adapters/anthropic_adapter.py), [google_adapter.py](./backend/app/services/provider_adapters/google_adapter.py), [azure_adapter.py](./backend/app/services/provider_adapters/azure_adapter.py), and [generic_adapter.py](./backend/app/services/provider_adapters/generic_adapter.py).

Context management is centered on [context_provider.py](./backend/app/services/context_provider.py), which builds the room-aware context agents receive: story metadata, live story runtime projection, recent messages, participants, active agents, room metadata, and extra context items. [context_store.py](./backend/app/services/context_store.py) defines the normalized `ContextItem` shape and pluggable store contract, with in-memory and Redis-backed implementations that support room-wide and agent-scoped context plus deletion and expiry filtering. [shadow_context_loader.py](./backend/app/services/shadow_context_loader.py), [shadow_read_service.py](./backend/app/services/shadow_read_service.py), [shadow_summary_service.py](./backend/app/services/shadow_summary_service.py), and [shadow_summaries.py](./backend/app/services/shadow_summaries.py) add durable Shadow-derived summaries into that context stream. The current context extension design is captured in [Context Provider: Multi-Source Context Extension](./backend/app/services/service-docs/context-provider-extra-contexts.md), with the broader room/story/tool exposure model in [Room Context, Story State, And Tool Exposure](./docs/architecture/RoomContext_StoryState_and_ToolExposure.md).

## What Is Here

- `backend/`: FastAPI, SQLModel, Alembic, Postgres/Timescale, Redis, auth, event streaming, room/story/persona/project APIs, agent invocation services, shadow/user repo services, workspace orchestration, and integrations with Tesser, Gittin, Kennel, and MCP services.

- `frontend/`: Vite + React + TypeScript console using TanStack Router/Query, Tailwind, Radix/shadcn-style components, generated OpenAPI client code, story/page/demo/room/workspace screens, and Playwright tests.
- `tesser/`: Python `tesserax` SVG/animation/rendering library plus a Redis-backed export service used by demos and canvas workflows.

- `kennel/`: LXC-based runtime environment service for creating and managing workspace/runtime containers.

- `gittin/`: Gogs-based git service used for shadow repos and user repo workflows.

- `mcpmvp/`: small FastAPI/MCP prototype service for affordance and story-builder surfaces.  Proof of concept for additional MCP extensibility.

- `docs/`: architecture notes, implementation references, walkthroughs, and archived/exploratory design work.

## Runtime Stack

The default Docker Compose stack includes:

- `db`: TimescaleDB/PostgreSQL 17
- `redis`: Redis pub/sub for realtime events and worker coordination
- `backend`: FastAPI API at `http://localhost:8000`
- `frontend`: built frontend served at `http://localhost:5173`
- `outbox-worker`: background shadow/user repo processing
- `tesser`: Redis-backed SVG/canvas export worker
- `gittin`: local Gogs service at `http://localhost:3001`
- `kennel`: runtime environment API at `http://localhost:8090`
- `mcpmvp`: affordance/story-builder prototype service
- optional `mailcatcher` and `playwright` services under the `test` profile

## Quick Start

1. Create or review the root `.env`.

   `copy.env.txt` is a historical example, not a safe production template. At minimum, set real values for:

   - `SECRET_KEY`
   - `FIRST_SUPERUSER`
   - `FIRST_SUPERUSER_PASSWORD`
   - `POSTGRES_PASSWORD`
   - `KENNEL_SECRET`

2. Start the development stack.

   ```bash
   docker compose up -d --build
   ```

3. Open the app and API docs.

   - Frontend: `http://localhost:5173`
   - API: `http://localhost:8000`
   - Swagger UI: `http://localhost:8000/docs`
   - Gittin: `http://localhost:3001`
   - Kennel: `http://localhost:8090`

4. Watch logs when something is still warming up.

   ```bash
   docker compose logs -f backend
   docker compose logs -f tesser
   docker compose logs -f kennel
   ```

## Local Development

The Docker override maps service ports directly to localhost. You can stop one service and run it natively while the rest of the stack stays in Docker:

```bash
docker compose stop frontend
cd frontend
npm install
npm run dev
```

```bash
docker compose stop backend
cd backend
uv sync
uv run fastapi dev app/main.py
```

More details are in [development.md](./development.md), [backend/README.md](./backend/README.md), and [frontend/README.md](./frontend/README.md).

## Common Commands

```bash
# Start or rebuild the stack
docker compose up -d --build

# Run backend tests
cd backend
uv run pytest

# Run backend linting
cd backend
uv run ruff check app

# Type-check/build the frontend
cd frontend
npm run typecheck
npm run build

# Run frontend Playwright tests through Docker
docker compose --profile test run --rm playwright npx playwright test
```

## Documentation Map

- [development.md](./development.md): local Docker and native development workflows
- [deployment.md](./deployment.md): Docker Compose and Traefik deployment notes
- [docs/README.md](./docs/README.md): guide to the documentation tree
- [docs/affordances/](./docs/affordances/): affordance surfaces and walkthroughs
- [docs/agent-services/](./docs/agent-services/): agent orchestration references
- [docs/architecture/](./docs/architecture/): room/story/context architecture notes
- [docs/demos/](./docs/demos/): demo builder and rendering references
- [docs/shadow/](./docs/shadow/): shadow git/versioning implementation notes
- [tesser/README.md](./tesser/README.md): Tesserax library and export service context
- [kennel/README.md](./kennel/README.md): runtime environment service notes

Many docs under `docs/unsort/`, `docs/archived/`, and older phase folders are design history or work logs. Treat them as references, not authoritative onboarding material, unless a current feature explicitly links to them.

## License

MIT. See [LICENSE](./LICENSE).
