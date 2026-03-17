# backend/app/main.py — add to lifespan
# from app.services.kennel_event_listener import listen as kennel_listen

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     asyncio.create_task(kennel_listen())
#     yield


# ## The full request flow
# ```
# POST /workspaces
#   │
#   ├─ DB: Workspace(status=provisioning) created   → 202 returned to client
#   │
#   └─ background task: _provision()
#        │
#        ├─ kennel POST /envs          → job_id
#        ├─ poll /jobs/{job_id}        → done
#        ├─ kennel POST /envs/{n}/inject → workspace config applied
#        └─ DB: status=ready, ws_token set

# GET /workspaces/{id}                 → client polls until status=ready
#   │
#   └─ status: "ready"

# GET /workspaces/{id}/terminal        → {"terminal_url": "wss://kennel.domain/..."}
#   │
#   └─ frontend opens WebSocket directly to kennel via Traefik
#      (backend is out of the hot path for streaming)