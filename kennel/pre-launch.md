 On the backend side, terminal URL issuance is now explicitly driven by KENNEL_EXTERNAL_WS_BASE_URL in config.py (line 68) and kennel_client.py (line 61), instead of silently falling back to the internal Docker hostname. I also wired that env var into docker-compose.yml so the backend respects the external value from `.env`, and added a local default in .env (line 26).

The practical behavior change is simple:

backend-to-kennel management calls still use KENNEL_BASE_URL=http://kennel:8090 inside Docker,
browser terminal handoff now uses an explicit external URL,
local default is ws://localhost:8090,
compose fallback is ws://localhost:8090 unless you override it for a routed environment.
Verification: python3 -m py_compile kennel/src/server.py backend/app/core/config.py backend/app/services/kennel_client.py passed.

One thing to keep in mind: if your browser is meant to connect through Traefik over TLS in deployed environments, you’ll want to override `KENNEL_EXTERNAL_WS_BASE_URL` to something like `wss://kennel.${DOMAIN}`. For local development, ws://localhost:8090 is the right default.
