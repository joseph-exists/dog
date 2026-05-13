# Dog

Dog is a local-first product workspace for rooms, stories, personas, agents, demos, and repo-backed workspaces.  the repository  contains a full application stack with a FastAPI API, React console, realtime event transport, git-backed entity/versioning services, SVG/canvas export workers, and sandboxed runtime environments using lxc for fast launching dev environments with gpu passthrough.  Note: the current kennel implementation is meant for local/owned infra only that is secured by other means. 

## What Is Here

- `backend/`: FastAPI, SQLModel, Alembic, Postgres/Timescale, Redis, auth, event streaming, room/story/persona/project APIs, agent invocation services, shadow/user repo services, workspace orchestration, and integrations with Tesser, Gittin, Kennel, and MCP services.

- `frontend/`: Vite + React + TypeScript console using TanStack Router/Query, Tailwind, Radix/shadcn-style components, generated OpenAPI client code, story/page/demo/room/workspace screens, and Playwright tests.
- `tesser/`: Python `tesserax` SVG/animation/rendering library plus a Redis-backed export service used by demos and canvas workflows.

- `kennel/`: LXC-based runtime environment service for creating and managing workspace/runtime containers.

- `gittin/`: Gogs-based git service used for shadow repos and user repo workflows.

- `mcpmvp/`: small FastAPI/MCP prototype service for affordance and story-builder surfaces.

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
