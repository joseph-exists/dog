# Dog Backend

The backend is a FastAPI application using SQLModel, Alembic, Postgres/Timescale, Redis, JWT auth, and background services for realtime rooms, agent invocation, git-backed shadow/user repo workflows, Tesser export jobs, and Kennel workspace runtime events.

## Requirements

- Docker for the full stack.
- `uv` for local Python dependency management.
- Python compatible with `backend/pyproject.toml` (`>=3.10,<4.0`; most local work currently targets Python 3.12).

## Run In Docker

From the repo root:

```bash
docker compose up -d --build backend
```

Useful endpoints:

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/utils/health-check/`

## Run Locally

Keep Postgres, Redis, Tesser, Gittin, Kennel, and MCP services in Docker, then run FastAPI locally:

```bash
docker compose stop backend
cd backend
uv sync
uv run fastapi dev app/main.py
```

The backend reads the root `.env` through `app/core/config.py`.

## Code Map

- `app/main.py`: FastAPI app, CORS, lifespan listeners, and API router mounting.
- `app/api/routes/`: HTTP and WebSocket routes.
- `app/models.py`: SQLModel tables and API models.
- `app/crud*.py`: data access helpers.
- `app/services/`: business logic, agent orchestration, realtime publishing, shadow/user repo services, Tesser/Kennel clients, and workers.
- `app/alembic/`: migrations.
- `app/tests/`: pytest suite.
- `scripts/`: container startup, tests, lint, and formatting helpers.
- `docs/DATA_MODEL_RULES.md` and `docs/RULES.md`: local backend modeling and implementation guidance.

## Tests And Checks

```bash
cd backend
uv run pytest
uv run ruff check app
uv run mypy app
```

Inside a running backend container:

```bash
docker compose exec backend bash scripts/tests-start.sh
docker compose exec backend bash scripts/tests-start.sh -x
```

## Migrations

Create and apply migrations from the backend container:

```bash
docker compose exec backend alembic revision --autogenerate -m "Describe change"
docker compose exec backend alembic upgrade head
```

The `prestart` service runs `alembic upgrade head` during normal stack startup.

## Background Work

On startup, `app/main.py` starts in-process listeners for shadow outbox processing, Tesser demo-canvas callbacks, and Kennel events. The Compose stack also runs an `outbox-worker` service for background repo processing. Check environment variables in the root `.env` and `docker-compose.yml` when changing these integrations.

## Related Docs

- [../development.md](../development.md)
- [../docs/agent-services/](../docs/agent-services/)
- [../docs/architecture/](../docs/architecture/)
- [../docs/shadow/](../docs/shadow/)
- [../docs/affordances/](../docs/affordances/)
