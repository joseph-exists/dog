# Shadow Historical Work Plan

This file used to contain the long Milestone 1-3 implementation plan for the earlier Shadow architecture. That plan predated the current local-git runtime and included Forgejo-specific assumptions that are no longer true.

Use these current documents instead:

- [Shadow System Overview](shadow-overview.md)
- [Shadow Outbox Worker](ShadowOutboxWorker.md)
- [Shadow Read Path and Context Provider](ShadowPhase2Milestone2_TechnicalSpec.md)
- [Shadow Implementation Guide](ShadowPhase2Milestone2_ImplementationGuide.md)
- [Shadow Outbox and Repair](ShadowPhase3Milestone3.md)
- [Shadow Models](shadow-models.py.md)

The current implementation is:

- DB-first on the request path: create `ShadowRepo`, pending `ShadowVersion`, and `ShadowOutboxJob`.
- Local-git-first in the worker: commit snapshots under `SHADOW_REPOS_PATH`.
- Optional remote sync: provision/push to Gogs/Gittin only when configured.
- Git-first on reads: load committed snapshots from git, fall back to DB snapshots with `is_stale=True`.

Older milestone discussion should be recovered from git history if needed, rather than used as active documentation.
