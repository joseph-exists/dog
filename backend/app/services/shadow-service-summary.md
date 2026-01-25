# Shadow Services Reference

The attached files define eight Python modules implementing shadow versioning services for entity persistence via database and Forgejo git repositories. These services handle snapshot creation, outbox processing, reading, summarizing, and context loading with async/sync distinctions visible in function definitions.[^1][^2][^3][^4][^5][^6][^7][^8]

## Services Overview


```
| Service | Primary Role | Key Classes/Functions | Sync/Async Mix | DB Dependencies | External (Forgejo/Redis) |
| :-- | :-- | :-- | :-- | :-- | :-- |
| shadow_exporters.py [^1] | Entity snapshot builders | buildroomsnapshot (sync), buildagentsnapshot (sync) | Sync only | Room, AgentConfig, etc. models | None |
| shadow_context_loader.py [^2] | Context item generation from shadows | buildshadowcontextitems (async), contextitem (sync) | Mixed | AgentConfig, Room models; shadowsummaryservice | None |
| shadow_outbox_worker.py [^3] | Background job processor for commits | processjobjobid (sync), runworker (sync) | Sync only | ShadowOutboxJob, ShadowRepo models; shadowservice | Forgejo API |
| shadow_summary_service.py [^4] | Cached summaries of snapshots | ShadowSummaryService.getlatestsummary (async) | Async primary | ShadowRepo; shadowreadservice | Redis |
| shadow_read_service.py [^5] | Snapshot retrieval (Forgejo/DB fallback) | ShadowReadService.getlatestsnapshot (sync) | Sync only | ShadowRepo, ShadowVersion; shadowservice | Forgejo API |
| shadow_summaries.py [^6] | Snapshot-to-summary transformers | summarizeroomsnapshot (sync), SUMMARYDISPATCH | Sync only | None | None |
| shadow_tasks.py [^7] | Background task enqueuers | shadowroomversionbesteffort (sync) | Sync only | Room, User; shadowservice, buildroomsnapshot | None |
| shadow_service.py [^8] | Core versioning/enqueuing | ShadowService.enqueueentityversion (sync) | Sync only | ShadowRepo, ShadowVersion, etc.; openapiclient | Forgejo API |
```

## Call Hierarchy

```
shadowservice (file:8)  # Central: enqueueentityversion -> ensureshadowrepodbonly -> allocatenextversionnumber
├── createversion (sync) -> Forgejo commit (via getapiclients)
├── enqueueentityversion (sync) -> ShadowVersion(pending) + ShadowOutboxJob(queued)
│   └── Used by: shadowroomversionbesteffort(file:7), exporters indirectly
├── ensureshadowrepo (sync) -> Forgejo repo create/get

shadow_outbox_worker (file:3)  # Polls/claims jobs -> processjobjobid (sync)
├── claimjobs (sync) -> SQL withforupdate/skiplocked
├── processjobjobid (sync) -> acquirerepolease -> ensureforgejorepo -> commitsnapshot
│   -> Via shadowservice.getrepoapi/getservicetoken
│   -> buildroomredissnapshot (sync, room-specific)

shadowreadservice (file:5)  # getlatestsnapshot (sync) -> getshadowrepo -> getlatestcommittedversion
├── getsnapshotfromversion (sync) -> readjsonfilefromforgejo (Forgejo first, DB fallback)
└── Exceptions: ShadowRepoNotFound, ShadowVersionNotFound

shadowsummaryservice (file:4)  # getlatestsummary (async) -> shadowreadservice.getlatestsnapshot (via runsync)
├── summarizewithcache (async) -> SUMMARYDISPATCH (file:6) -> e.g., summarizeroomsnapshot (sync)
└── Redis cache: shadowsummary:{repoid}:{commitsha}

shadow_context_loader (file:2)  # buildshadowcontextitems (async) -> shadowsummaryservice.getlatestsummary (multiple calls)
├── For: room/story/agent/persona/runtime
└── Returns: list[ContextItem] with missing shadow fallbacks

Exporters (file:1)  # buildroomsnapshot (sync) -> model dumps + related queries (participants/bindings)
├── Called by: shadowservice (indirect), shadow_outbox_worker, shadow_tasks
└── Sync builders for room/agent/story/persona/etc.

Summaries (file:6)  # Pure functions: summarizeroom/etc. (sync)
└── Dispatched by shadowsummaryservice

Tasks (file:7)  # shadowroomversionbesteffort (sync) -> buildroomsnapshot -> shadowservice.enqueueentityversionwithowner
```

Control flow is synchronous in core paths (enqueue -> DB pending -> worker poll -> Forgejo commit), with async wrappers in summary/context. Message passing via DB (ShadowOutboxJob status: queued/processing/committed) and Redis (summaries). No direct sync-async mixing beyond session runsync in summary service.[^2][^3][^4][^5][^8]

## Control Flow Markers

- **Async functions**: buildshadowcontextitems (file:2), getlatestsummary/getsummarybyversion/etc. (file:4). Use AsyncSession, await session.exec.
- **Sync functions**: All enqueue/createversion/processjob/buildsnapshot (files:1,3,7,8). Use Session, direct .exec/.get.
- **Debug/Optimization Indicators**:
    - Locks: withforupdate/skiplocked (claimjobs), acquirerepolease/releaserepolease (TTL-based).
    - Retries: computebackoff (exponential 1-1800s + jitter), MAXATTEMPTS=25, status retryableerror/dead.
    - Timeouts: requesttimeoutseconds=5.0 (Forgejo reads).
    - Idempotency: versionnumber via ShadowRepoVersionCounter (withforupdate), commitsha pending->committed.
    - Fallbacks: Forgejo read fail -> DB snapshot (isstale=True); missing summary -> ContextItem with reason.[^3][^5]


## Contracts by Service

### shadow_service.py[^8]

**Explicit**: enqueueentityversion(session: Session, user: User, entitytype: str, entityid: UUID, entitydata: dict, message: str) -> ShadowVersion|None. Returns version with status=pending, creates Job queued.
**Implicit**: Assumes entitydata is full JSON-dumpable snapshot; no Forgejo IO (DB-only for enqueue). Raises IntegrityError on counter race (handled in allocatenextversionnumber).
**In**: Session, User (owner/actor), entitydata (dict), message (str).
**Out**: ShadowVersion (pending), ShadowOutboxJob (queued), ShadowRepo (dbonly).

### shadow_outbox_worker.py[^3]

**Explicit**: processjobjobid(jobid: UUID, workerid: str) -> None. Claims lease, commits snapshotjson to Forgejo/{entitytype}.json, updates status=committed.
**Implicit**: Distributed workers via lockedby/LOCKTTLSECONDS=60; classifies errors (fatal vs retryable); builds room Redis snapshot if room.
**In**: Session, job (ShadowOutboxJob processing), shadowversion/srepo.
**Out**: ShadowVersion (commitsha, status=committed), Forgejo file/commit, Attempt record.

### shadow_read_service.py[^5]

**Explicit**: getlatestsnapshot(session: Session, entitytype: str, entityid: UUID) -> ShadowSnapshotResult.
**Implicit**: Forgejo/{entitytype}.json@commitsha first (source=forgejo, isstale=False); DB fallback (source=db, isstale=True).
**In**: Session, entitytype/id.
**Out**: ShadowSnapshotResult (snapshotjson: dict, source, isstale).

### shadow_summary_service.py[^4]

**Explicit**: getlatestsummary(session: Session|AsyncSession, entitytype: str, entityid: UUID) -> ShadowSummaryResult|None (async).
**Implicit**: Cache hit (Redis shadowsummary:{repoid}:{sha}, TTL 120/3600s); SUMMARYDISPATCH[snapshot.entitytype](snapshotjson).
**In**: Session, entitytype/id.
**Out**: ShadowSummaryResult (summary: dict via file:6).

### Others

- **Exporters (file:1)**: buildroomsnapshot(session, roomid) -> dict (schema v1, full relational dump). In: Session/roomid. Out: dict.
- **Context Loader (file:2)**: buildshadowcontextitems (async, roomid, agentslug?, session) -> list[ContextItem]. Calls getlatestsummary x4-5.
- **Summaries (file:6)**: summarizeroom(snapshotjson: dict) -> dict (flattened keys). Pure func.
- **Tasks (file:7)**: shadowroomversionbesteffort(roomid, actorid?, message) -> None (best-effort enqueue).[^6][^7][^1][^2][^4]


## Domains and Dependencies

| Domain | Entities | Shadowed? | Exporter | Summary Func |
| :-- | :-- | :-- | :-- | :-- |
| Room | Room, participants, bindings | Yes | buildroomsnapshot | summarizeroom |
| Agent | AgentConfig, agentpersonas | Yes | buildagentsnapshot | summarizeagent |
| Story | Story, nodes/choices/reqs/statevars | Yes | buildstorysnapshot | summarizestory |
| Persona | Persona, traits/qualities/links | Yes | buildpersonasnapshot | summarizepersona |
| LLM | LLMModel | Yes | buildllmmodelsnapshot | summarizellmmodel |
| Provider | UserLLMProvider | Yes | builduserllmprovidersnapshot | summarizeuserllmprovider |
| Quality/Trait | Quality/Trait, links | Yes | buildqualitysnapshot/buildtraitsnapshot | None |

Cross-service: shadowsummaryservice -> shadowreadservice -> shadowservice (tokens); context_loader -> shadowsummaryservice; worker/tasks/exporters -> shadowservice.[^1][^2][^4][^5][^8]

## Complexity Metrics

Cyclomatic complexity not statically computable without full AST; qualitatively:

- High: processjobjobid (file:3, branches: try/except/classifyerror/acquire/ensure/commit/repair paths ~12).
- Medium: buildshadowcontextitems (file:2, ~8 branches for room/story/agent/persona).
- Low: Pure summaries (file:6, ~2-3).

Recurrence: Worker loop (poll-claim-process-backoff, T(n)=n/BATCHSIZE polls); version alloc (while True counter race, amortized O(1)); no deep recursion observed.[^2][^3]

<div align="center">⁂</div>

[^1]: shadow_exporters.py

[^2]: shadow_context_loader.py

[^3]: shadow_outbox_worker.py

[^4]: shadow_summary_service.py

[^5]: shadow_read_service.py

[^6]: shadow_summaries.py

[^7]: shadow_tasks.py

[^8]: shadow_service.py

