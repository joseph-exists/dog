This document describes the Shadow service, its current Forgejo integration, and the intended end-state workflow for versioned entities.

## Purpose

The Shadow service creates git-backed, versioned records of application entities in Forgejo. These "shadow" repos preserve provenance and relationships between objects without exposing Forgejo to end users.

## Current integration

Shadow integration is implemented in `app/services/shadow_service.py` and currently versions:

- **Agents** and **Stories** on create/update
- A dedicated repo per entity, containing JSON snapshots
- Service-account ownership via Forgejo tokens, one per entity type

Related references:

- `.shadow-models.py.md`: ShadowUser, ShadowRepo, ShadowVersion models
- `app/services/shadow_service.py`: versioning service
- `.shadow-agent_routes.py.md`: current integration hooks

Configuration (from `backend/app/core/config.py`):

    # Shadow Forgejo Configuration (git-based entity versioning)
    # All shadow operations are invisible to end users - they never
    # interact with Forgejo directly. Service accounts own all repos.
    SHADOW_ENABLED: bool = True
    SHADOW_FORGEJO_URL: str = "http://localhost:3000/api/v1"
    # Service account tokens (one per entity type)
    SHADOW_USERS_TOKEN: str | None = None   # shadow-users account
    SHADOW_AGENTS_TOKEN: str | None = None  # shadow-agents account
    SHADOW_STORIES_TOKEN: str | None = None # shadow-stories account

## Intended workflow (near-future state)

Example flow using a user and a story:

1. A new user (AliciaRodriguez) creates an account.
2. Asynchronously (via pub/sub worker), a ShadowUser repo is created in Forgejo.
3. The user creates and saves a story (Rabbit Walks).
4. Asynchronously, a ShadowStory repo is created that references the AliciaRodriguez ShadowUser repo.
   - This initial snapshot is Rabbit Walks V1.
   - A reference to the story is added to the user's ShadowUser repo.
5. The user clones the story as "Rabbit Walks Two".
6. Asynchronously, a new ShadowStory repo is created for Rabbit Walks Two.
   - It references the AliciaRodriguez ShadowUser repo and Rabbit Walks V1.
   - A reference is added to the user's ShadowUser repo.
7. The user updates the original Rabbit Walks story.
8. Asynchronously, the original ShadowStory repo receives a new version while retaining earlier versions.
   - The clone ("Rabbit Walks Two") remains pinned to the original version it referenced.
   - The user's ShadowUser repo receives an additional reference for this update.

## Next implementation targets

Extend coverage to Rooms, Agents, Models, and Providers.
