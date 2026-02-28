# Repo Structuring

This document captures the current repo taxonomy and the decisions needed to implement deterministic provisioning in Gogs.

## Organizations

### `shadow`

System-internal shadow repositories live under the `shadow` organization.

- These repos are not user-owned.
- They are system-internal by default.
- Limited portions of their contents may be exposed through backend transforms.
- Full raw repo contents are not part of the normal user-facing surface.
- Ownership in Gogs stays stable after creation.

### `dog`

User-visible platform repos live under the `dog` organization.

- These repos are associated with platform users.
- Individual users are not direct Gogs owners of these repos.
- They are separate from shadow repos and should not share provisioning logic or naming assumptions.
- They are user visible in the Gogs UI.
- Ownership in Gogs stays stable after creation.

### Operator-Owned Repos

There is a third category for internal, non-shadow repos owned directly by operators or administrators.

- Example: `josep-repo-alpha`
- These do not need implementation work yet.
- They should be treated as distinct from both `shadow` and `dog` repos.

## Global Rules

- Repo paths do not encode environment such as `dev`, `staging`, or `prod`.
- The first generated repo name is permanent.
- Repo ownership in Gogs remains stable even if the associated application object changes hands.

## Shadow Repo Naming

Shadow repos should use immutable, opaque, deterministic names:

```text
shadow/{entity_type}-{entity_uuid}
```

Examples:

```text
shadow/agent-38c2f6cb-bce2-4e0e-b91e-19c9eec82a8a
shadow/story-3e26d320-732b-437b-b875-e03880364fe8
shadow/room-45957458-55f5-4a8a-9619-8de790deacee
```

This gives us:

- deterministic generation from application data
- no rename pressure when titles or labels change
- no slug collision problems
- easy reverse mapping from repo name back to entity
- simple provisioning through the Gogs API

## User Repo Naming

User-visible repos live under `dog`, but the exact naming rule is still open.

Requirements:

- user visible names should be understandable
- cleanup and reverse mapping should still be possible
- the scheme should tolerate duplicate or changing slugs

Open options:

- `dog/{slug}`
- `dog/{user_id}-{slug}`
- `dog/{slug}-{user_id}`
- `dog/{stable_repo_id}-{slug}`

Current leaning:

- keep a readable slug
- include a stable short identifier in the repo name

Chosen format:

```text
dog/{slug}-{short_id}
```

Where:

- `slug` is normalized to a repo-safe lowercase slug
- `short_id` is a stable short prefix derived from the platform UUID

## Shadow Access Model

Shadow repos are backend-managed infrastructure.

- Provisioning should be done by backend or service accounts, not end users.
- Dedicated service accounts may be used around shadow repo operations.
- Any user-facing access to shadow data should go through backend services and transforms.

## Questions Already Answered

- Should repo paths encode environment? No.
- Should shadow repos live in a dedicated org? Yes, `shadow`.
- Should user repos live in a separate org? Yes, `dog`.
- Should ownership in Gogs stay stable? Yes.
- Should shadow repo names be immutable? Yes.
- Should shadow repos be user visible by default? No.

## Questions Still Open

- What exact naming rule should `dog` user-visible repos use?
- Should shadow provisioning use one shared service account or one dedicated account per entity type or workflow?
- What metadata should be stored in Gogs versus in the application DB for reverse lookup and cleanup?
- Should existing local shadow repos be migrated into matching Gogs repos immediately or only when first touched by the new provisioning path?

## Implementation Consequence

The next backend slice should assume:

1. Shadow repo names are generated as `{entity_type}-{entity_uuid}` under `shadow`.
2. Shadow repos are provisioned before first remote push.
3. User-visible repos under `dog` are a separate feature track and should not be coupled to shadow repo implementation.
