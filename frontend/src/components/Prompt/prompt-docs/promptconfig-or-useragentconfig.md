# PromptConfig + UserAgentConfig Integration Progression Draft

## Goal
Build Prompt Builder, runtime invocation, and future capabilities as one system without drift:
- `PromptConfig` = versioned recipe artifact.
- `UserAgentConfig` = runtime actor identity and provider credential anchor.
- Runtime always executes an effective merged config from a single resolver path.

## Current Baseline (Observed)
1. Prompt artifacts and versioning exist:
- `backend/app/api/routes/prompt_configs.py`
- `backend/app/models.py` (`PromptConfig*` models)
2. Runtime still executes from `UserAgentConfig`:
- `backend/app/services/agent_instance.py`
- `backend/app/services/agent_runner.py`
3. Room-scoped prompt policy storage exists but is not consumed by runner:
- `backend/app/models.py` (`RoomAgentSettings.prompt_config`)
- `backend/app/api/routes/room_agent_settings.py`
- `backend/app/crud.py` (`upsert_room_agent_settings`)
4. Frontend has adapters but no end-to-end runtime connector:
- `frontend/src/components/Prompt/builder/promptBuilderAdapters.ts`
- `frontend/src/routes/_layout/prompt-builder.tsx`

## Target Runtime Resolution Contract
Effective invocation config is produced once per run by:
1. `UserAgentConfig` base
2. Optional bound `PromptConfig` payload (default binding)
3. Optional room/session override payload

Precedence (highest wins):
1. Room/session override
2. Bound PromptConfig payload
3. UserAgentConfig base

Non-overridable by PromptConfig:
1. Provider credentials storage location and ownership checks
2. Agent identity flags (`slug`, scope, visibility, participation role)
3. Safety/system governance fields explicitly marked immutable

## M0 Canonical PromptConfigDraft Contract Table
Status: Draft for implementation using `PromptConfigDraft` in `backend/app/models.py` as canonical.

### Merge Precedence
1. Room/session override payload
2. Bound PromptConfig payload
3. UserAgentConfig base

### Field Contract
| Field Path | Owner | Runtime Class | Merge Rule | `null` Semantics | PromptConfig Allowed to Override? | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `provider.user_access_provider_id` | Shared (UAC anchor + PromptConfig request) | Runtime-authoritative | Replace scalar | `null` means inherit from lower layer | Yes (subject to ownership/enablement checks) | Must pass UserAccessProvider ownership + enabled checks. |
| `provider.provider_type_id` | Derived/runtime | Runtime-derived | Derived after provider resolution | n/a | No direct override | Computed from selected provider/catalog in hydration/resolver. |
| `provider.provider_kind` | PromptConfig | Runtime-authoritative | Replace scalar | `null` means infer/retain | Yes | Must be validated against selected provider/model compatibility. |
| `provider.base_url` | UserAgentConfig/UserAccessProvider | Infrastructure binding | Replace only from trusted source | `null` means provider default | No (from PromptConfig) | Credentials and base URL are trust-boundary concerns. |
| `provider.account_label` | Derived/runtime | Metadata-derived | Replace scalar | `null` means unknown | No direct override | Display-only/hydration value. |
| `model.model_catalog_id` | PromptConfig | Runtime-authoritative | Replace scalar | `null` means unresolved catalog mapping | Yes | Resolver may map to/from `model_id`. |
| `model.model_id` | PromptConfig | Runtime-authoritative | Replace scalar | `null` invalid at final resolve | Yes | Required before invoke. |
| `model.model_name` | PromptConfig (optional) | Metadata/runtime-assist | Replace scalar | `null` means derive from catalog | Yes | Cosmetic unless runtime fallback needs it. |
| `model.model_family` | Derived/runtime | Metadata-derived | Derived | n/a | No direct override | Derived from model id/catalog. |
| `input.kind` | PromptConfig | Runtime-authoritative | Replace scalar | `null` invalid, normalize to default | Yes | Enum: `simple_text`/`messages`. |
| `input.text` | PromptConfig | Runtime-authoritative | Replace scalar | `null` normalize to `""` for simple text mode | Yes | Used when `input.kind=simple_text`. |
| `input.system` | PromptConfig | Runtime-authoritative | Replace scalar | `null` means no system content | Yes | Used when `input.kind=messages`. |
| `input.messages` | PromptConfig | Runtime-authoritative | Replace array (no deep merge) | `null` normalize to `[]` | Yes | Full replace avoids ambiguous message interleaving. |
| `params.provider_kind` | PromptConfig | Runtime-authoritative | Replace scalar | `null` means infer from provider | Yes | Must warn/error on mismatch. |
| `params.temperature` | PromptConfig | Runtime-authoritative | Replace scalar | `null` means provider/model default | Yes | Range validation required. |
| `params.top_p` | PromptConfig | Runtime-authoritative | Replace scalar | `null` means provider/model default | Yes | Range validation required. |
| `params.max_output_tokens` | PromptConfig | Runtime-authoritative | Replace scalar | `null` means model default | Yes | Required for deterministic budget control. |
| `params.stop` | PromptConfig | Runtime-authoritative | Replace array | `null` means no stop constraints | Yes | Normalize + dedupe list. |
| `params.seed` | PromptConfig | Runtime-authoritative | Replace scalar | `null` means nondeterministic | Yes | Provider support varies. |
| `params.response_format_json` | PromptConfig | Runtime-authoritative | Replace scalar | `null` means no forced JSON mode | Yes | Candidate for upgrade to richer structured format object. |
| `params.parallel_tool_calls` | PromptConfig | Runtime-authoritative | Replace scalar | `null` means provider default | Yes | Maps to Responses API/pydantic-ai settings. |
| `params.reasoning_effort` | PromptConfig | Runtime-authoritative | Replace scalar | `null` means model default | Yes | Support matrix varies by model/provider. |
| `params.top_k` | PromptConfig | Runtime-authoritative | Replace scalar | `null` means no `top_k` override | Yes | Primarily Anthropic-style parameter. |
| `tools.tool_mode` | PromptConfig | Runtime-authoritative | Replace scalar | `null` normalize to `none` | Yes | Values: `none`, `optional`, `required`. |
| `tools.tool_allowlist` | PromptConfig request + UAC ceiling | Runtime-authoritative | Intersect allowlists | `null` means inherit | Yes (bounded) | Effective list = intersection with trusted upper-bound allowlist. |
| `tools.tool_choice` | PromptConfig | Runtime-authoritative | Replace scalar/object | `null` means model decides | Yes | Upgrade shape from free string to typed object recommended. |
| `metadata.tags` | PromptConfig | Metadata-only | Replace array | `null` means none | Yes | Not required for runtime invoke. |
| `metadata.notes` | PromptConfig | Metadata-only | Replace scalar | `null` means none | Yes | Authoring/ops notes. |
| `metadata.template_id` | PromptConfig | Metadata-only | Replace scalar | `null` means none | Yes | Template provenance only. |
| `metadata.template_setup` | PromptConfig | Metadata-only | Replace object | `null` means none | Yes | Builder UX state; not runtime-authoritative. |
| `metadata.extensions.*` (reserved) | PromptConfig | Metadata extension | Replace object by namespace key | `null` clears namespace | Yes | Reserved for future non-breaking expansion. |

### Out of Scope for PromptConfig Override (UserAgentConfig / Policy Layer)
1. Agent identity and participation controls (`slug`, `is_enabled`, `is_coordinator`, `participation_mode`, visibility/scope).
2. Provider credential material and secret resolution paths.
3. Privilege ceilings and trust-boundary policy (`authorized MCP servers`, privilege sets, hard tool ceilings).
4. Infrastructure bindings (tenant-specific connector credentials, memory backend credentials/endpoints).

## M0 Spec Cross-Check (OpenAI Responses + PydanticAI)
Reviewed against:
1. OpenAI Responses API reference: https://platform.openai.com/docs/api-reference/responses
2. OpenAI remote MCP/connectors guide: https://platform.openai.com/docs/guides/tools-remote-mcp
3. PydanticAI OpenAI model settings/API:
   1. https://ai.pydantic.dev/models/openai/
   2. https://ai.pydantic.dev/api/models/openai/

### Critical Gaps to Address or Reserve in M0
1. Structured output format is under-specified.
- Current: `params.response_format_json: bool`.
- Gap: OpenAI supports richer response format controls (`text`/`json_object`/`json_schema` with schema metadata).
- M0 action: reserve typed field shape (for example `params.response_format` object) while keeping backward compatibility with boolean.

2. Responses server-side conversation continuation is missing.
- Gap: `previous_response_id` (and pydantic-ai `openai_previous_response_id`) is not represented.
- M0 action: add reserved field in `metadata.extensions.openai.previous_response` or `params.openai.previous_response_id`.

3. Built-in tool configuration surface is missing.
- Gap: OpenAI/PydanticAI support built-in tool parameter objects (`openai_builtin_tools`) and MCP tool config (`allowed_tools`, `require_approval`, server descriptors).
- M0 action: reserve `tools.builtin` and `tools.mcp` typed sections; do not force everything through `tool_allowlist`.

4. Tool limit controls are missing.
- Gap: Responses supports controls like `max_tool_calls`.
- M0 action: add reserved `tools.max_tool_calls` (or `params.max_tool_calls`) for deterministic orchestration.

5. Reasoning controls are partially represented.
- Current includes `reasoning_effort`.
- Gap: PydanticAI exposes related controls such as reasoning summary and reasoning id handling.
- M0 action: reserve provider-namespaced reasoning fields (for example `params.openai.reasoning_summary`).

6. `tool_choice` typing is too loose.
- Current: free string.
- Gap: provider APIs often require typed tool choice modes and specific tool selectors.
- M0 action: evolve to typed union object; preserve string parsing for compatibility.

### Conclusion from Spec Review
1. `PromptConfigDraft` remains the correct canonical contract.
2. We should implement M0 with strict current fields plus reserved typed extension slots so M5 expansion does not require breaking schema changes.
3. Resolver (M1) should perform provider-specific capability checks to downgrade or reject unsupported fields with stable error codes.


## Milestones

### M0: Freeze Contracts (No Runtime Behavior Change)
Deliverables:
1. Contract doc for `PromptConfigDraft` semantics and merge precedence.
2. Reserved namespaced field for builder-only metadata.
3. Compatibility table: which fields are runtime-authoritative vs metadata-only.

Files:
1. `frontend/src/components/Prompt/builder/promptBuilderSchema.ts`
2. `backend/app/models.py` (`PromptConfigDraft`, `PromptParams`, `PromptToolingConfig`)
3. `frontend/src/components/Prompt/prompt-docs/prompt-builder-user-expectations-reference-card.md`

Acceptance:
1. Frontend schema and backend model fields are aligned and documented.
2. No new capability field merges without contract entry.

### M1: Build Backend Resolver Service (Feature-Flagged)
Deliverables:
1. New resolver service: `resolve_effective_prompt_config(...)`.
2. Deterministic merge order and normalization pipeline.
3. Diagnostics endpoint for previewing effective config without invoking agent.

Suggested files:
1. `backend/app/services/prompt_runtime_resolver.py` (new)
2. `backend/app/api/routes/prompt_configs.py` (preview endpoint)
3. `backend/app/services/agent_instance.py` (wire-in under flag later)

Acceptance:
1. Unit tests for merge precedence and conflict behavior.
2. Snapshot tests for input combinations and resulting effective payload.

### M2: Add Binding Surface (Agent-Level)
Deliverables:
1. Add optional `prompt_config_id` and `prompt_config_version_policy` to agent model.
2. API update path for binding/unbinding.
3. UI controls to bind a PromptConfig to an agent without overwriting agent base fields.

Suggested files:
1. `backend/app/models.py` (`UserAgentConfig*`)
2. `backend/app/api/routes/agent_routes.py`
3. `frontend/src/routes/_layout/prompt-builder.tsx` or agent-edit surface
4. `frontend/src/components/Prompt/builder/promptBuilderAdapters.ts`

Acceptance:
1. Binding is persisted and readable.
2. Existing agents continue running unchanged when unbound.

### M3: Add Room/Session Temporary Attach
Deliverables:
1. Extend room agent settings payload to reference PromptConfig ID/version or inline override payload.
2. Resolver consumes room-level override source.
3. Clear UX for temporary attach and rollback.

Suggested files:
1. `backend/app/models.py` (`RoomAgentSettings*`)
2. `backend/app/api/routes/room_agent_settings.py`
3. `backend/app/crud.py` (validation + upsert logic)
4. frontend room settings UI surface

Acceptance:
1. Per-room prompt override does not mutate base agent binding.
2. Removing override returns effective config to bound/default state.

### M4: Runtime Cutover (Behind Flag)
Deliverables:
1. Agent invocation path resolves effective config before model/tool init.
2. Legacy direct-read behavior remains as fallback flag for one release.
3. Invocation telemetry includes config source provenance.

Suggested files:
1. `backend/app/services/agent_runner.py`
2. `backend/app/services/agent_instance.py`
3. `backend/app/services/agent_prompt.py`

Acceptance:
1. Runtime can execute using resolver output end-to-end.
2. Rollback switch is available and tested.

### M5: Expand Prompt Builder Capabilities Against Contract
Deliverables:
1. Add broader tools/skills/capability controls only through contract-backed fields.
2. Normalize + validate new fields in registry hooks.
3. Version-safe migration behavior for older drafts.

Suggested files:
1. `frontend/src/components/Prompt/builder/promptBuilderCapabilityRegistry.ts`
2. `frontend/src/components/Prompt/builder/promptBuilderSchema.ts`
3. `frontend/src/components/Prompt/builder/PromptTopLevelEditor.tsx`
4. `backend/app/models.py` (`PromptParams`, tooling structs)

Acceptance:
1. Every new field has frontend control, backend model support, and resolver semantics.
2. No agent runtime special cases outside resolver.

### M6: Git Integration as Artifact Workflow
Deliverables:
1. Git push/pull and diff are centered on PromptConfig + companion assets.
2. Commit metadata links git revision to prompt version metadata.
3. Import/export preserves draft + version intent.

Acceptance:
1. Git operations do not require rewriting UserAgentConfig runtime identity fields.
2. Prompt artifacts are portable and replayable.

## Cross-Cutting Guardrails
1. Single resolver rule: runtime must not read raw `prompt_config` blobs directly.
2. Contract tests:
- draft serialization/parsing parity
- merge precedence
- invocation payload snapshot
3. Feature flags:
- `PROMPT_RESOLVER_ENABLED`
- `PROMPT_ROOM_OVERRIDE_ENABLED`
4. Changelog discipline:
- each contract field addition includes migration + fallback behavior.

## Suggested Build Order (Minimal Churn)
1. M0
2. M1
3. M2
4. M4 (flagged, dark launch)
5. M3
6. M5
7. M6

Rationale:
1. Resolver must exist before widespread builder growth.
2. Agent default binding is simpler than room override and establishes first connector.
3. Runtime cutover early (flagged) catches drift before large feature expansion.

## Immediate Next Tickets
1. Add contract table and precedence matrix to this doc and link from Prompt Builder docs index.
2. Create `prompt_runtime_resolver.py` skeleton with deterministic merge function and tests.
3. Add `prompt_config_id` to `UserAgentConfig` models + migration draft.
4. Add preview endpoint: resolve effective config for `{agent_id, room_id?}` without invoking.


Differentiation:

- `UserAgentConfig` owns **identity, trust boundary, credentials, and infrastructure bindings**.
- `PromptConfig` owns **task behavior, strategy, and per-run policy**.

Using that:

1. `a: authorized MCP servers`
- Primary: `UserAgentConfig`
- Why: this is an access-control boundary.
- Optional in `PromptConfig`: requested subset (must be intersected with agent allowlist).

2. `b: embedding connectors`
- Split:
- `UserAgentConfig`: connector credentials/endpoints, tenant bindings.
- `PromptConfig`: whether/how to use embeddings for this recipe (retrieval strategy, top-k, thresholds).

3. `c: privilege sets`
- Primary: `UserAgentConfig` (or room/session policy override).
- Why: privileges are security posture, not recipe content.
- `PromptConfig` can only declare required scopes; runtime enforces intersection.

4. `d: user-memory`
- Split:
- `UserAgentConfig`: memory backend binding, retention class, privacy controls.
- `PromptConfig`: memory usage policy (read/write rules, salience filters, when to consult memory).

5. `e: orchestration controls`
- Split:
- `UserAgentConfig`: actor-level controls (`participation_mode`, coordinator role, max iterations).
- `PromptConfig`: orchestration behavior for this recipe (tool mode, sequencing hints, branching policy).

6. `f: A2A bridge specifiers`
- Split:
- `UserAgentConfig`: trusted bridge endpoints/registries and hard allowlist.
- `PromptConfig`: which peers/capabilities to invoke for this task and invocation style.

If helpful, I can add this as a decision matrix section to [promptconfig-or-useragentconfig.md](/home/josep/dog/frontend/src/components/Prompt/prompt-docs/promptconfig-or-useragentconfig.md).
