# User Repo Frontend Reference

## Audience

Frontend engineer building the full user-facing repository management experience for platform-managed `dog/*` repos, using the platform UI as the only user interface.

## Product Boundary

- Users do not interact with Gogs directly.
- The frontend must never construct or rely on direct Gogs API calls.
- The frontend must treat Gogs as opaque backend infrastructure.
- The backend owns authorization, provisioning, import, and repo metadata normalization.
- The initial import workflow is HTTPS source URL only.
- The initial import target is the repository's `main` branch as a platform convention.

## Current Backend Contract

### Create Import

`POST /api/v1/user-repos/`

Request body:

```json
{
  "source_repo_url": "https://github.com/example/project.git",
  "display_name": "optional override",
  "slug": "optional-override",
  "description": "optional",
  "is_private": false
}
```

Response: **`202 Accepted`**

```json
{
  "id": "uuid",
  "import_status": "importing",
  "...": "other fields"
}
```

Behavior:

- Returns **immediately** with `202 Accepted` — does not block on Gogs.
- Creates a persisted platform repo record with `import_status: importing`.
- Queues an async job for backend-managed provisioning/import through Gogs.
- The async worker processes the job with automatic retry on transient failures.
- Returns `422` for invalid source URLs (validated before queuing).

**Important:** The response will always have `import_status: importing`. The frontend must poll to detect completion.

### List Repos

`GET /api/v1/user-repos/`

Returns the current user's repos only.

### Get Repo

`GET /api/v1/user-repos/{repo_id}`

Returns a single repo record if the current user owns it or is a superuser.

## Current Frontend State

The frontend now has more than list/detail/import-status UX.

Current repo viewer surfaces include:

- repo list and import flow
- registry-backed repo detail view
- real `repoOverview` and `repoImportStatus` panels
- implemented but capability-gated `repoExplorer` and `fileViewer` panels
- local repo layout editing with duplicate panel instances and per-panel `config_json`

Important implication:

- the viewer architecture is already in place
- the main blocker is backend read-contract wiring for user-repo tree/blob access
- once those reads exist, the frontend can activate explorer/viewer behavior without another major redesign

## Important Response Fields

The frontend should rely on these fields from `UserRepoPublic`:

- `id`: stable platform repo identity
- `slug`: platform-facing normalized identifier
- `display_name`: user-facing name
- `description`
- `source_repo_url`: original external source URL
- `source_branch`: backend branch intent, currently `main`
- `import_status`: `pending`, `importing`, `ready`, or `failed`
- `import_error`: backend-provided failure summary when import fails
- `imported_at`: timestamp when provisioning/import completed successfully
- `gogs_repo_name`: internal managed repo name in `dog`
- `gogs_repo_id`: internal forge repo id when available
- `gogs_full_name`: internal org-qualified name
- `gogs_html_url`: internal forge URL, useful for backend/operator debugging but not primary UI navigation
- `is_private`
- `created_at`
- `updated_at`

## Frontend Responsibilities

### Import Creation UX

- Collect an HTTPS repository URL.
- Optionally allow user override of display name, slug, description, and privacy.
- Validate obvious client-side mistakes for faster UX, but treat backend validation as authoritative.
- Surface backend `422` messages directly for invalid input.

### Import Status UX

- Repo creation is **always asynchronous** — the `POST` response will always have `import_status: importing`.
- After create, route the user into repo detail or repo list state that can reflect:
  - `importing` — provisioning in progress
  - `ready` — successfully imported
  - `failed` — import failed (check `import_error`)
- **Poll `GET /user-repos/{repo_id}`** after create until terminal state (`ready` or `failed`).
- Suggested polling interval: 2-3 seconds initially, backing off to 5-10 seconds for longer imports.
- Large repository imports from external sources may take 30+ seconds.

### Failure UX

- Show `import_error` directly but clearly as platform-managed import feedback.
- Preserve the failed repo in UI state instead of assuming it vanished.
- **The backend automatically retries transient failures** (network issues, timeouts) with exponential backoff.
- Only permanent failures (auth errors, invalid URLs, org not found) result in `failed` status.
- A repo marked `failed` will not be retried automatically — user-initiated retry is a future enhancement.

### Repo Management Surface

The component suite should be organized around platform objects, not forge concepts. The frontend should think in terms of:

- imported repo list
- repo detail
- import state
- import failure
- downstream operations on managed repos

Avoid designing around:

- org switching
- raw Gogs ownership
- direct branch management in v1
- direct clone credentials

### Repo Viewer Surface

The frontend repo detail surface now supports panel-based viewing, including repeatable explorer and file-viewer instances.

Frontend implications for backend contracts:

- explorer and file viewer are not singleton assumptions
- multiple instances may exist at once for the same repo
- instances may share selection state or use isolated selection state
- panel instances may target different paths or different viewer modes

Backend implication:

- tree/blob reads must be safe for concurrent, stateless use by multiple panel instances

## Known Behavioral Constraints

### Backend Contract Is Stronger Than Underlying Forge Semantics

The user story is "clone only main branch without history, branches, or other context", but Gogs migration support may not fully enforce that by itself.

Frontend implication:

- Do not promise low-level Git semantics that the backend has not separately exposed as guaranteed metadata.
- Present the workflow as "import into platform workspace" rather than as a direct raw Git clone verb if exact Git fidelity matters in copy.

### `source_branch`

The backend persists `source_branch = main` as the current platform convention. Do not expose branch selection UI until the backend contract supports it.

### Viewer Read Semantics

The frontend should not infer Git semantics the backend has not explicitly decided to preserve.

Because platform-managed repos may sever or rewrite branch/ref/history state after intake:

- tree/blob responses should reflect platform semantics, not assumed upstream semantics
- `ref` values in viewer responses need stable product meaning
- commit/history metadata should only be surfaced when backend contract makes it meaningful

## Data Flow to Assume

1. User submits external HTTPS repository URL.
2. Backend API validates URL, creates a `UserRepo` record with `import_status: importing`.
3. Backend API creates an outbox job and returns `202 Accepted` immediately.
4. **Async**: Outbox worker picks up the job and provisions a `dog/{slug}-{short_id}` repo in Gogs.
5. **Async**: Worker updates import status to `ready` or `failed` on the repo record.
6. Frontend polls until terminal state (`ready` or `failed`).
7. Later repo operations should target platform repo identity, not external repo identity.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│  Backend    │────▶│   Outbox    │────▶│    Gogs     │
│   POST      │     │  API        │     │   Worker    │     │   (gittin)  │
│             │◀────│  202        │     │             │     │             │
│   Poll GET  │────▶│             │◀────│  Update DB  │◀────│   Clone OK  │
│             │◀────│  ready/fail │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

## UX Guidance

- Prefer a task-oriented "Import Repository" flow over exposing forge vocabulary.
- Make status visible in list and detail views.
- Show original source URL in detail view for provenance.
- Use `display_name` as the main label and `slug` as secondary metadata.
- Treat `gogs_*` fields as advanced/internal metadata, not primary UI copy.
- Do not show or request forge credentials in v1.

## Error Handling Guidance

### User-Correctable

- invalid URL
- non-HTTPS URL
- malformed repo path

### Platform/Backend

- import failed due to Gogs provisioning
- org lookup/provisioning mismatch
- source repo inaccessible from backend network path
- backend not configured for user repo provisioning

UI treatment:

- distinguish input errors from platform errors
- keep platform errors inspectable
- avoid blame-oriented copy

## Suggested State Model

At minimum, treat these as distinct UI states:

- empty list
- import form idle
- import submission in flight
- repo record returned with `importing`
- repo record returned with `ready`
- repo record returned with `failed`
- list refresh/polling
- unauthorized/not found

## Integration Notes

- Use backend-generated types from the API schema if available.
- Avoid hand-maintaining enum values where generated types exist.
- Polling is **required** — the API always returns `importing` initially.
- Stop polling on terminal states (`ready` or `failed`).
- If optimistic navigation is used after create, key it by returned `repo_id`.

### Viewer Enablement Notes

The frontend repo viewer is currently waiting on backend support for:

- `user_repo` tree reads
- `user_repo` blob/file reads
- capability exposure for:
  - `hasFileTree`
  - `hasBlobContent`
  - later: `hasCommitHistory`
  - later: `hasSearch`

The detailed backend handoff checklist lives in:

- [`backend/app/services/service-docs/user-repo-viewer-backend-handoff-checklist.md`](/home/josep/dog/backend/app/services/service-docs/user-repo-viewer-backend-handoff-checklist.md)

Minimum backend delivery to activate the current viewer:

1. Support `user_repo` tree reads.
2. Support `user_repo` blob/file reads.
3. Expose route-level capability availability for those reads.
4. Define the meaning of `ref` in viewer responses.
5. Verify real payloads against an imported user repo.

## Polling Reference Implementation

```typescript
// Example polling hook (adapt to your state management)
async function pollForImportCompletion(
  repoId: string,
  options: { maxAttempts?: number; intervalMs?: number } = {}
): Promise<UserRepo> {
  const { maxAttempts = 60, intervalMs = 3000 } = options;

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const repo = await api.get(`/api/v1/user-repos/${repoId}`);

    if (repo.import_status === 'ready') {
      return repo;
    }

    if (repo.import_status === 'failed') {
      throw new Error(repo.import_error || 'Import failed');
    }

    // Still importing — wait and retry
    await new Promise(resolve => setTimeout(resolve, intervalMs));
  }

  throw new Error('Import timed out — check repo status manually');
}

// Usage after POST /user-repos/
const response = await api.post('/api/v1/user-repos/', { source_repo_url });
const repo = await pollForImportCompletion(response.id);
```

**TanStack Query alternative:**

```typescript
// useQuery with refetchInterval that stops on terminal state
const { data: repo } = useQuery({
  queryKey: ['user-repo', repoId],
  queryFn: () => api.get(`/api/v1/user-repos/${repoId}`),
  refetchInterval: (query) => {
    const status = query.state.data?.import_status;
    // Stop polling on terminal states
    if (status === 'ready' || status === 'failed') return false;
    return 3000; // Poll every 3s while importing
  },
});
```

## Files To Understand

- [`backend/app/api/routes/user_repos.py`](/home/josep/dog/backend/app/api/routes/user_repos.py) — API endpoints
- [`backend/app/services/user_repo_service.py`](/home/josep/dog/backend/app/services/user_repo_service.py) — Gogs provisioning logic
- [`backend/app/services/user_repo_outbox_worker.py`](/home/josep/dog/backend/app/services/user_repo_outbox_worker.py) — Async job processor
- [`backend/app/models.py`](/home/josep/dog/backend/app/models.py) — `UserRepo`, `UserRepoOutboxJob` models

## What This Reference Does Not Define

- specific React components
- page layouts
- state library choice
- polling implementation details
- retry UI contract beyond current backend behavior
- final tree/blob response schema details beyond the current handoff checklist

Those should be decided in frontend implementation work, but must remain aligned with the backend contract above.
