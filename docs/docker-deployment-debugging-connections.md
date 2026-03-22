




note: if CORS failure, review .env files to ensure correct passthrough / env settings


---

sample diagnosis


1. backend returns a terminal websocket URL
2. frontend opens that URL directly in the browser
3. kennel handles the websocket upgrade on `/envs/{name}/ws`

the failing URL observed in the browser was:

`ws://kennel.localhost/envs/env-.../ws?token=...`

the main issue turned out to be local traefik configuration drift:

- the base service labels in `docker-compose.yml` advertise `https` entrypoints and `le` as the certificate resolver
- the local traefik override only defines the `http` entrypoint and does not define the `le` resolver
- when the stack is started without the local HTTP label override, traefik rejects the kennel/frontend/backend/gittin HTTPS routers
- result: `kennel.localhost` does not route to the kennel container, so the browser websocket never reaches kennel
- this explains why kennel shows no websocket activity during the failed connect attempt

traefik errors that confirmed the problem:

- `EntryPoint doesn't exist entryPointName=https`
- `No valid entryPoint for this router`
- `Router uses a nonexistent certificate resolver certificateResolver=le`

verified behavior during debugging:

- backend-to-kennel internal HTTP connectivity is healthy
- provisioning a workspace still works
- browser websocket reachability to `kennel.localhost` is the broken link

---

working local compose invocation

for local development, if we want to preserve the normal direct dev ports and also keep local traefik routing available for kennel websocket access, start the stack with:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.traefik.yml \
  -f docker-compose.traefik.local.yml \
  -f docker-compose.local-http.yml \
  -f docker-compose.override.yml \
  up -d --build
```

why this file set matters:

- `docker-compose.traefik.yml` defines the traefik service
- `docker-compose.traefik.local.yml` switches traefik to local HTTP-only mode
- `docker-compose.local-http.yml` clears the app services' HTTPS router labels so they match local traefik
- `docker-compose.override.yml` restores the normal dev port mappings and local frontend API target:
  - backend on `localhost:8000`
  - frontend on `localhost:5173`
  - frontend built with `VITE_API_URL=http://localhost:8000`

important note:

if `docker compose` is run with explicit `-f` flags and `docker-compose.override.yml` is omitted, compose does not auto-load that override. that causes the stack to lose the normal direct dev ports and causes the frontend build to target `api.localhost` instead of `localhost:8000`.

---

recommended local access pattern

for the default dev workflow, use the direct ports consistently:

- backend docs: `http://localhost:8000/docs`
- frontend: `http://localhost:5173`

the local traefik hostnames should still exist for routed services:

- kennel health: `http://kennel.localhost/health`
- api route: `http://api.localhost`
- dashboard route: `http://dashboard.localhost`

avoid mixing browser sessions between `localhost:*` and `*.localhost` for login flows unless we explicitly want to test the routed path. mixing them can produce cookie/CORS confusion and make auth behavior look flaky even when the stack is healthy.

---

quick verification checklist

after bringing the stack up, verify:

```bash
docker compose ps
curl -I http://localhost:8000/docs
curl -I http://kennel.localhost/health
```

expected:

- `localhost:8000/docs` responds
- `kennel.localhost/health` responds
- clicking workspace terminal connect should now at least reach kennel

---

constraints when rebuilding only part of the stack

rebuilding a single service is fine, but the compose file set must stay the same every time.

rules:

1. always use the same ordered `-f` list that was used to start the stack
2. when rebuilding `backend`, keep `docker-compose.override.yml` in the file list or the rebuilt container may come back with different environment, ports, or command wiring than the rest of the running stack
3. when rebuilding `frontend`, remember that `VITE_API_URL` is a build arg, so the frontend image must be rebuilt with the intended override set or login/API traffic may suddenly target the wrong host
4. when changing traefik labels or route shape, recreate traefik and the affected routed service together
5. when changing websocket host/base-url behavior, rebuild/recreate backend and verify `KENNEL_EXTERNAL_WS_BASE_URL` inside the running backend container

safe examples:

rebuild only backend:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.traefik.yml \
  -f docker-compose.traefik.local.yml \
  -f docker-compose.local-http.yml \
  -f docker-compose.override.yml \
  up -d --build backend
```

rebuild only frontend:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.traefik.yml \
  -f docker-compose.traefik.local.yml \
  -f docker-compose.local-http.yml \
  -f docker-compose.override.yml \
  up -d --build frontend
```

recreate traefik and kennel after route changes:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.traefik.yml \
  -f docker-compose.traefik.local.yml \
  -f docker-compose.local-http.yml \
  -f docker-compose.override.yml \
  up -d --build traefik kennel
```

extra sanity check after backend rebuild:

```bash
docker compose exec -T backend /bin/sh -lc 'printf "%s\n" "$KENNEL_EXTERNAL_WS_BASE_URL"'
```

expected local value:

`ws://kennel.localhost`
