# Dog Development

This repository is designed to run as a Docker Compose stack, with the option to run the backend or frontend natively while dependent services stay in Docker.

## Start The Stack

From the repository root:

```bash
docker compose up -d --build
```

Useful local URLs:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`
- Gittin/Gogs: `http://localhost:3001`
- Kennel API: `http://localhost:8090`
- MailCatcher, when the `test` profile is running: `http://localhost:1080`

Check service status and logs:

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f tesser
```

The first boot can take a while because the database health check, migrations, images, and background services need to settle.

## Services

- `db`: TimescaleDB/Postgres database.
- `redis`: pub/sub for realtime room events, worker channels, Tesser requests, and Kennel events.
- `prestart`: runs backend startup work such as migrations before the API starts.
- `backend`: FastAPI application.
- `frontend`: production-built Vite app served in Docker on port `5173`.
- `outbox-worker`: background processing for shadow repos and user repo writes.
- `tesser`: SVG/canvas export worker backed by Redis.
- `gittin`: local Gogs service for git-backed workflows.
- `kennel`: LXC runtime environment service.
- `mcpmvp`: affordance/story-builder prototype service: very fast mcp with progressive elaboration.

- `mailcatcher` and `playwright`: optional test-profile services.

## Run One App Natively

Keep dependencies in Docker and run the app you are editing locally.

Frontend:

```bash
docker compose stop frontend
cd frontend
npm install
npm run dev
```

Backend:

```bash
docker compose stop backend
cd backend
uv sync
uv run fastapi dev app/main.py
```

The default local ports match the Docker ports, so the rest of the stack should continue to work.

## Compose Files

- `docker-compose.yml`: full stack definition.
- `docker-compose.override.yml`: local development overrides loaded automatically by `docker compose`; maps ports and sets local build args.
- `docker-compose.traefik.yml`: routed deployment/proxy configuration.
- `docker-compose.traefik.local.yml`: local Traefik helper configuration.
- `docker-compose.local-http.yml`: local HTTP label overrides for routed development.

If you pass explicit `-f` files, Compose no longer auto-loads `docker-compose.override.yml`. Include it last when you still want the direct localhost ports:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.traefik.yml \
  -f docker-compose.traefik.local.yml \
  -f docker-compose.local-http.yml \
  -f docker-compose.override.yml \
  up -d --build
```

Use one browser access pattern consistently. Direct local development uses `localhost:5173` and `localhost:8000`; routed Traefik development uses hostnames such as `dashboard.localhost` and `api.localhost`. Mixing them can cause auth, cookie, and CORS confusion.

## Environment

The root `.env` is read by Compose and by the backend settings. Important local variables include:

- `PROJECT_NAME`
- `DOMAIN`
- `FRONTEND_HOST`
- `BACKEND_CORS_ORIGINS`
- `SECRET_KEY`
- `FIRST_SUPERUSER`
- `FIRST_SUPERUSER_PASSWORD`
- `POSTGRES_*`
- `REDIS_PORT`
- `KENNEL_SECRET`
- `SHADOW_*`
- `USER_REPO_*`
- `TESSER_*`

Use strong secrets outside local development. `copy.env.txt` is a historical example and should not be treated as a secure template.

## Tests And Checks

Backend:

```bash
cd backend
uv run pytest
uv run ruff check app
```

Frontend:

```bash
cd frontend
npm run typecheck
npm run build
npm run test:unit
```

End-to-end tests through Docker:

```bash
docker compose --profile test run --rm playwright npx playwright test
```

## Migrations

Alembic migrations live in `backend/app/alembic`.

```bash
docker compose exec backend alembic revision --autogenerate -m "Describe change"
docker compose exec backend alembic upgrade head
```

The `prestart` service runs migrations during normal stack startup.

## Generated Client

When backend OpenAPI changes, regenerate the frontend client:

```bash
./scripts/generate-client.sh
```

You can also run `npm run generate-client` from `frontend/` after placing an `openapi.json` there.
