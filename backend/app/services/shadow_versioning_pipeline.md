```mermaid
%% Shadow Versioning Pipeline
%% Focus: enqueue -> outbox worker -> Forgejo + summary readback.
flowchart TD
  A[shadow_room_version_best_effort()] --> B[build_room_snapshot()]
  B --> C[shadow_service.enqueue_entity_version_with_owner()]
  C --> D[("ShadowRepo")]
  C --> E[("ShadowVersion: pending")]
  C --> F[("ShadowOutboxJob: queued")]

  subgraph "Worker"
    G[shadow_outbox_worker.run_worker()] --> H[_process_job()]
    H --> I["Forgejo RepositoryApi"]
    I --> J[("Forgejo repo commit")]
    H --> K[("ShadowVersion: committed")]
  end

  subgraph "Read + Summary"
    L[shadow_read_service.get_latest_snapshot()] --> M[("Forgejo/DB snapshot")]
    M --> N[shadow_summary_service.get_latest_summary()]
    N --> O[shadow_context_loader.build_shadow_context_items()]
    O --> P[build_room_context()]
  end
```
