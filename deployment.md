# Dog Deployment

Dog can be deployed with Docker Compose behind Traefik. The production-oriented Compose path expects service hostnames such as `api.<domain>`, `dashboard.<domain>`, `git.<domain>`, and `kennel.<domain>`.

This guide is intentionally high level. Review `docker-compose.yml`, `docker-compose.traefik.yml`, and your environment before using it for a public deployment, especially because Kennel runs privileged LXC workloads.

## Production Shape

The stack includes:

- `db`: TimescaleDB/Postgres
- `redis`: pub/sub and worker coordination
- `backend`: FastAPI API
- `frontend`: built React console
- `outbox-worker`: repo/versioning background processor
- `tesser`: export worker
- `gittin`: Gogs git service
- `kennel`: runtime environment API
- `mcpmvp`: affordance/story-builder prototype service

Traefik routes public traffic to the services using labels in the Compose files.

## Prerequisites

- A server with Docker Engine and Docker Compose.
- DNS records pointing your domain and wildcard subdomains at the server.
- A Docker network named `traefik-public` when using an external Traefik proxy.
- Secrets and deployment variables supplied by environment variables or a secure `.env` mechanism.
- Host support for Kennel if you enable it: privileged containers, cgroups, LXC support, and any required GPU/device mappings.

## Public Traefik

Create the public network once on the server:

```bash
docker network create traefik-public
```

Set Traefik environment variables:

```bash
export USERNAME=admin
export PASSWORD='change-this'
export HASHED_PASSWORD="$(openssl passwd -apr1 "$PASSWORD")"
export DOMAIN=example.com
export EMAIL=admin@example.com
```

Start the public Traefik stack:

```bash
docker compose -f docker-compose.traefik.yml up -d
```

For local-only HTTP routing, use the local Traefik overrides instead of attempting Let's Encrypt on localhost:

```bash
docker compose \
  -f docker-compose.traefik.yml \
  -f docker-compose.traefik.local.yml \
  up -d
```

## Application Environment

Set at least:

- `ENVIRONMENT=production`
- `DOMAIN`
- `PROJECT_NAME`
- `STACK_NAME`
- `FRONTEND_HOST`
- `BACKEND_CORS_ORIGINS`
- `SECRET_KEY`
- `FIRST_SUPERUSER`
- `FIRST_SUPERUSER_PASSWORD`
- `POSTGRES_SERVER`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `REDIS_PORT`
- `KENNEL_SECRET`
- `SHADOW_*` values for shadow repo/versioning behavior
- `USER_REPO_*` values for user repo workflows
- `TESSER_*` channel/worker settings, if overriding defaults
- SMTP values if password recovery or email notifications are enabled
- `SENTRY_DSN`, if using Sentry outside local development

Generate a strong secret when needed:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Deploy The Stack

For a production-like Compose deployment:

```bash
docker compose -f docker-compose.yml up -d --build
```

If the server uses a separate public Traefik network, make sure the stack and proxy agree on the `traefik-public` network. Do not rely on `docker-compose.override.yml` in production; it is for local development ports and build args.

Check status:

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f tesser
docker compose logs -f kennel
```

## Local Routed Mode

If you are testing routed hostnames locally, include the local HTTP override and, when you also want direct localhost ports, include the dev override last:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.traefik.yml \
  -f docker-compose.traefik.local.yml \
  -f docker-compose.local-http.yml \
  -f docker-compose.override.yml \
  up -d --build
```

Use one access pattern consistently:

- direct local: `http://localhost:5173` and `http://localhost:8000`
- routed local: `http://dashboard.<local-domain>` and `http://api.<local-domain>`

Mixing direct and routed URLs can break auth, cookies, and CORS.

## Expected URLs

Replace `example.com` with your domain.

- Frontend: `https://dashboard.example.com`
- Backend API: `https://api.example.com`
- Backend API docs: `https://api.example.com/docs`
- Gittin: `https://git.example.com`
- Kennel: `https://kennel.example.com`
- Traefik dashboard, if exposed by the public Traefik stack: `https://traefik.example.com`

## GitHub Actions

The repository contains GitHub workflow configuration, but treat it as deployment scaffolding. Before relying on it, verify the current workflow files under `.github/workflows/` and ensure the required secrets match the current environment variables above.

Common secrets include:

- `DOMAIN_PRODUCTION`
- `DOMAIN_STAGING`
- `STACK_NAME_PRODUCTION`
- `STACK_NAME_STAGING`
- `EMAILS_FROM_EMAIL`
- `FIRST_SUPERUSER`
- `FIRST_SUPERUSER_PASSWORD`
- `POSTGRES_PASSWORD`
- `SECRET_KEY`

Add any newer service secrets, such as `KENNEL_SECRET`, `SHADOW_*`, or `USER_REPO_*`, if the workflow deploys those services.
