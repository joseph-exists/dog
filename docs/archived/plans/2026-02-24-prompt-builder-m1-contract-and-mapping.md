# Prompt Builder Phase M1: Contract Skeleton + Mapping Spec
> **Status:** Implementation spec (M1)  
> **Date:** 2026-02-24  
> **Depends on:** `docs/plans/2026-02-24-prompt-builder-rfc.md`

## 1. Purpose
This is the concrete M1 follow-up for Prompt Builder.  
It defines the minimum contract skeleton and mapping rules using current exported client types/services:
1. `UserAgentConfigPublic`
2. `UserAccessProviderPublic` / `UserAccessProviderCreate`
3. `LLMModelPublic`
4. `LlmProvidersService` / `LlmCatalogService` / `AgentsService`

## 2. Existing Source Types and Services (Current System)
### 2.1 Agent source object
`frontend/src/client/types.gen.ts`
- `UserAgentConfigPublic`
- Relevant fields:
  - `id`, `owner_id`, `version`
  - `user_access_provider`
  - `provider_type`
  - `model`, `model_id`, `model_name`
  - `system_prompt`, `custom_system_prompt`, `instructions`
  - `tool_config`, `deps_config`, `agent_metadata`

### 2.2 Access-provider source object
`frontend/src/client/types.gen.ts`
- `UserAccessProviderPublic`
- Relevant fields:
  - `id`
  - `name`
  - `base_url`
  - `alpha_provider_type_id`
  - `is_enabled`, `is_default`, `is_validated`

### 2.3 Model source object
`frontend/src/client/types.gen.ts`
- `LLMModelPublic`
- Relevant fields:
  - `id`, `model_id`, `display_name`
  - `primary_provider_type_id`
  - capability flags (`has_json_mode`, `has_function_calling`, etc.)

### 2.4 Available service APIs
`frontend/src/client/sdk.gen.ts`
- `LlmProvidersService.listProviders/getProvider/updateProvider`
- `LlmCatalogService.listModels/listModelsForUap/getModel`
- `AgentsService.getAgent/updateAgent`

## 3. M1 Canonical Prompt Builder Contract (Draft)
M1 defines a frontend domain contract to drive builder work.  
Backend persisted DTO naming can be finalized in API design pass.

```ts
export type PromptProviderKind = "openai_compatible" | "openai" | "anthropic" | "google" | "xai" | "custom";

export type PromptProviderBinding = {
  user_access_provider_id: string | null; // maps to UserAccessProviderPublic.id
  provider_type_id: string | null;        // maps to alpha_provider_type_id
  provider_kind: PromptProviderKind | null;
  base_url: string | null;                // from UAP base_url
  account_label: string | null;           // from UAP name
};

export type PromptModelBinding = {
  model_catalog_id: string | null;        // maps to LLMModelPublic.id
  model_id: string | null;                // maps to LLMModelPublic.model_id
  model_name: string | null;              // maps to UserAgentConfigPublic.model_name/display_name
  model_family: string | null;            // normalized grouping label
};

export type PromptInputPayload =
  | { kind: "simple_text"; text: string }
  | { kind: "messages"; system?: string; messages: Array<{ role: "system" | "user" | "assistant" | "tool"; content: string }> };

export type PromptParamsCommon = {
  temperature?: number | null;
  top_p?: number | null;
  max_output_tokens?: number | null;
  stop?: string[] | null;
  seed?: number | null;
};

export type PromptParamsByProvider =
  | ({ provider_kind: "openai_compatible" | "openai" } & PromptParamsCommon & {
      response_format_json?: boolean | null;
      parallel_tool_calls?: boolean | null;
      reasoning_effort?: "low" | "medium" | "high" | null;
    })
  | ({ provider_kind: "anthropic" } & PromptParamsCommon & {
      top_k?: number | null;
    })
  | ({ provider_kind: "google" | "xai" | "custom" } & PromptParamsCommon);

export type PromptToolingConfig = {
  tool_mode?: "none" | "optional" | "required";
  tool_allowlist?: string[] | null;
  tool_choice?: string | null;
};

export type PromptBuilderMetadata = {
  tags?: string[];
  notes?: string | null;
  template_id?: string | null;
  template_setup?: Record<string, unknown> | null; // mirrors demo-builder checklist persistence pattern
};

export type PromptConfigDraft = {
  id: string;
  owner_id: string | null;
  provider: PromptProviderBinding;
  model: PromptModelBinding;
  input: PromptInputPayload;
  params: PromptParamsByProvider;
  tools?: PromptToolingConfig | null;
  metadata?: PromptBuilderMetadata | null;
};
```

## 4. Version/History Model (M1 Contract Skeleton)
```ts
export type PromptConfigVersionSnapshot = {
  id: string;
  prompt_config_id: string;
  version: number;
  parent_version_id?: string | null;
  commit_message?: string | null;
  created_at: string;
  created_by: string;
  payload: PromptConfigDraft;
};

export type PromptConfigWorkingCopy = {
  prompt_config_id: string;
  base_version: number | null;
  payload: PromptConfigDraft;
  has_uncommitted_changes: boolean;
  updated_at: string;
};
```

M1 acceptance: explicit draft vs committed snapshot exists in the API/domain model, even if initial UI compare is basic.

## 5. Mapping Rules From Existing Types
### 5.1 `UserAgentConfigPublic` -> `PromptConfigDraft`
1. Provider binding
- `provider.user_access_provider_id = agent.user_access_provider ?? null`
- `provider.provider_type_id = null` initially; hydrate from selected UAP (`alpha_provider_type_id`)
- `provider.base_url/account_label` resolved from matching `UserAccessProviderPublic`

2. Model binding
- `model.model_id = agent.model_id ?? agent.model ?? null`
- `model.model_name = agent.model_name ?? null`
- `model.model_catalog_id` resolved by model catalog lookup (if available)

3. Input payload
- `input.kind = "messages"` initially for compatibility
- `input.system = agent.custom_system_prompt ?? agent.system_prompt ?? ""`
- if `agent.instructions` exists, append as user-authored guidance block

4. Params/tools
- seed from `agent.tool_config`/`deps_config` when recognized
- unknown keys preserved in advanced JSON fallback bucket (M1 requirement)

### 5.2 `UserAccessProviderPublic` hydration rules
1. `provider_type_id = alpha_provider_type_id ?? null`
2. `base_url = base_url ?? null`
3. `account_label = name`
4. semantic warning when `is_enabled === false` or `is_validated === false`

### 5.3 `LLMModelPublic` hydration rules
1. model defaults derive from capability flags:
- enable structured output controls when `has_json_mode`
- enable tool controls when `has_function_calling`
2. semantic warning when selected model’s `primary_provider_type_id` mismatches selected UAP provider type

## 6. M1 Semantic Validation Rules (Required)
1. `provider.user_access_provider_id` required.
2. selected UAP must be enabled.
3. provider/model compatibility must pass:
- `UAP.alpha_provider_type_id` aligns with model’s `primary_provider_type_id` (or allowed override policy).
4. `input` must include usable text.
5. numeric parameter ranges must be enforced (temperature/top_p/max_output_tokens/etc).
6. unknown advanced params never hard-fail by default; emit warning unless policy disallows.

Save gating:
1. errors block save
2. warnings remain visible and non-blocking

## 7. M1 API Surface Proposal (Backend Contract Direction)
Use names as placeholders for API discussion.

1. Config lifecycle
- `GET /prompt-configs/{id}`
- `POST /prompt-configs`
- `PATCH /prompt-configs/{id}`

2. Working copy and versioning
- `GET /prompt-configs/{id}/working-copy`
- `PUT /prompt-configs/{id}/working-copy`
- `POST /prompt-configs/{id}/versions` (commit)
- `GET /prompt-configs/{id}/versions`
- `GET /prompt-configs/{id}/versions/{version_id}`
- `POST /prompt-configs/{id}/working-copy/reset` (from version)

3. Optional compatibility helper
- `POST /prompt-configs/validate` for server-side semantic checks

## 8. Frontend M1 Deliverables
1. `promptBuilderSchema.ts`:
- field specs
- defaults
- constructors
- semantic validators

2. `promptBuilderCapabilityRegistry.ts`:
- capability descriptors
- normalize hooks
- validation hooks
- requirement metadata

3. bootstrap editor route:
- top-level provider/model/input/params sections
- raw JSON fallback
- validation panel
- sticky save/version bar

4. mapping adapter util:
- `mapUserAgentConfigToPromptDraft(...)`
- `hydratePromptDraftProviderAndModel(...)`

### 8.1 Delivery Status Snapshot (2026-02-24)
1. `promptBuilderSchema.ts`: completed
- implemented at `frontend/src/components/Prompt/builder/promptBuilderSchema.ts`
- baseline tests in `frontend/tests-unit/prompt-builder-schema.spec.ts`

2. `promptBuilderCapabilityRegistry.ts`: completed
- implemented at `frontend/src/components/Prompt/builder/promptBuilderCapabilityRegistry.ts`
- baseline tests in `frontend/tests-unit/prompt-builder-capability-registry.spec.ts`

3. Mapping adapter utils: completed
- implemented at `frontend/src/components/Prompt/builder/promptBuilderAdapters.ts`
- includes `mapUserAgentConfigToPromptDraft(...)`, `hydratePromptDraftProviderAndModel(...)`, `buildPromptValidationContext(...)`
- baseline tests in `frontend/tests-unit/prompt-builder-adapters.spec.ts`

4. Bootstrap editor route: partially complete
- implemented at `frontend/src/routes/_layout/prompt-builder.tsx` with:
  - top-level provider/model/input/params sections
  - semantic validation panel
  - provider/model data-backed options using `LlmProvidersService` and `LlmCatalogService`
  - raw JSON fallback editor
  - sticky draft action bar (local save/revert + API save/commit)
  - PromptConfig persistence wiring (`PromptConfigsService` working-copy + version endpoints)
- remaining in this deliverable:
  - richer version UX (compare, targeted restore, commit metadata UX)

5. Prompt top-level editor test coverage: completed
- `frontend/tests-unit/prompt-top-level-editor.spec.tsx`

### 8.2 Recommended Next Slice (Sequencing)
1. P0: complete editor parity in-route
- polish raw JSON fallback and sticky action bar behavior (error deep links, pending states, and API-ready action hooks).

2. P1: wire persistence/version APIs
- connect save/load/commit/reset actions once backend endpoint names and DTO final names are confirmed.

3. P1: extend semantic validation
- add provider/model capability checks for advanced params and surface warning/error severities consistently in UI.
- status: first pass complete (provider-kind mismatch, json-mode support, function-calling support, provider-specific param warnings).

4. P1: add focused UI coverage
- tests for JSON fallback round-trip, dirty-state save gating, and save/commit button enablement.

### 8.3 Concurrent Implementation Buckets
1. Bucket A (Frontend route parity + polish)
- primary files: `frontend/src/routes/_layout/prompt-builder.tsx`
- deliverables:
  - complete JSON fallback polish (parse errors, reset/apply ergonomics, deep link from errors).
  - finalize sticky action bar UX (disabled states, dirty-state messaging, pending indicators).
  - add focused unit coverage for dirty-state and JSON fallback interactions.
- dependency profile: none; execute immediately.

2. Bucket B (Persistence/version API wiring)
- primary files: prompt-config API layer + route mutation wiring.
- deliverables:
  - save draft/load draft/commit/reset actions wired to backend endpoints.
  - query invalidation + optimistic/pending UX states.
  - error-surface mapping from API validation to field and semantic panels.
- dependency profile: requires finalized DTO and endpoint naming.

3. Bucket C (Capability depth expansion)
- primary files:
  - `frontend/src/components/Prompt/builder/promptBuilderSchema.ts`
  - `frontend/src/components/Prompt/builder/promptBuilderCapabilityRegistry.ts`
  - `frontend/src/components/Prompt/builder/promptBuilderAdapters.ts`
- deliverables:
  - provider-family-specific parameter field specs.
  - compatibility checks tied to provider/model metadata.
  - richer warning taxonomy for unsupported/forward-compat fields.
- dependency profile: can run in parallel with Bucket B using current metadata stubs, then tighten once API metadata expands.

4. Recommended execution order
- phase 1: finish Bucket A and lock route UX behavior.
- phase 2: run Bucket B and Bucket C concurrently.
- phase 3: stabilization pass with integration tests covering save/commit and capability-level semantics.

## 9. Suggested File Placement (Frontend)
1. `frontend/src/components/Prompt/builder/promptBuilderSchema.ts`
2. `frontend/src/components/Prompt/builder/promptBuilderCapabilityRegistry.ts`
3. `frontend/src/components/Prompt/builder/promptBuilderAdapters.ts`
4. `frontend/src/routes/_layout/prompt-builder.tsx`

## 9.1 Backend Scaffold Status (2026-02-24)
1. PromptConfig model stack scaffolded in `backend/app/models.py`:
- typed draft contract models (`PromptConfigDraft`, provider/model/input/params/tools/metadata)
- persistence tables (`PromptConfig`, `PromptConfigVersion`, `PromptConfigWorkingCopy`)
- public/request models for working copy + version flows.

2. PromptConfig route surface scaffolded in `backend/app/api/routes/prompt_configs.py`:
- lifecycle endpoints (`GET/POST/PATCH /prompt-configs`)
- working copy endpoints (`GET/PUT /prompt-configs/{id}/working-copy`)
- version endpoints (`POST/GET /prompt-configs/{id}/versions`, `GET /prompt-configs/{id}/versions/{version_id}`)
- reset endpoint (`POST /prompt-configs/{id}/working-copy/reset`)
- validation endpoint (`POST /prompt-configs/validate`).

3. Router registration added in `backend/app/api/main.py`.

4. Remaining backend follow-up before production use:
- Alembic migration for prompt-config tables.
- route-level semantic validation hardening parity with frontend rules.
- optimistic concurrency checks (`base_version` mismatch currently returns `409`; request-shape hardening still pending).
- extended integration coverage for reset/validate negative paths and cross-user list filtering.

5. Backend integration tests added:
- `backend/app/tests/api/routes/test_prompt_configs.py`
- covered scenarios:
  - owner/non-owner access control on prompt-config reads
  - working copy -> commit version transition (`latest_version` and dirty-state expectations)
  - optimistic concurrency conflict (`409`) on stale `base_version`

6. User-facing guided reference card added:
- `frontend/src/components/Prompt/prompt-docs/prompt-builder-user-expectations-reference-card.md`

## 10. Acceptance Criteria for M1
1. User can create/edit a prompt draft with provider + model + input + params.
2. Provider/model dropdowns are sourced from existing services:
- `LlmProvidersService`
- `LlmCatalogService`
3. Existing `UserAgentConfigPublic` can be imported into prompt draft with deterministic mapping.
4. Validation catches provider/model incompatibility before save.
5. Draft and commit states are represented in API and UI.
6. All changes preserve compatibility with current generated types and services.

## 11. Open Decisions for Backend + Product
1. Canonical persisted type names (`PromptConfig*`) and endpoint naming.
2. Whether version commit is explicit-only or optional auto-commit on save.
3. Policy for unknown advanced provider parameters (warning vs block by policy).
4. Whether prompt configs are standalone entities or linked 1:n from `UserAgentConfig`.
