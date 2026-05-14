# Shadow Agent Route Integration

Agent route integration should use the current enqueue/outbox flow:

1. Persist the agent domain mutation.
2. Build the snapshot through `backend/app/services/shadow_exporters.py`.
3. Call `ShadowService.enqueue_entity_version(...)`.
4. Let `backend/app/services/shadow_outbox_worker.py` commit the snapshot to local git asynchronously.

Request handlers should not commit directly to git. They should treat Shadow versioning as best-effort around the product write: log failures, preserve the primary user action, and rely on repair modes for missed outbox work.

Related docs:

- [Shadow System Overview](shadow-overview.md)
- [Shadow Outbox Worker](ShadowOutboxWorker.md)
- [Shadow Implementation Guide](ShadowPhase2Milestone2_ImplementationGuide.md)
