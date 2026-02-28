
## Prompt Runtime Integration Checklist (Tracked)

### M0: Freeze Contracts (No Runtime Behavior Change)
- [x] Publish canonical `PromptConfigDraft` contract and merge precedence in docs.
- [x] Mark fields as runtime-authoritative vs metadata-only.
- [x] Add reserved namespace for builder-only metadata.
- [x] Confirm frontend/backend field parity:
  - [x] `frontend/src/components/Prompt/builder/promptBuilderSchema.ts`
  - [x] `backend/app/models.py` (`PromptConfigDraft`, `PromptParams`, `PromptToolingConfig`)
- [x] Add/refresh contract tests for schema parity and normalization.

### M0: Critical Gap Tickets (Do Now)
- [x] Replace boolean `params.response_format_json` with typed structure support while keeping compatibility:
  - [x] Add canonical `params.response_format` shape (`text` / `json_object` / `json_schema`).
  - [x] Keep `params.response_format_json` as deprecated input alias.
  - [x] Add normalization rule: map legacy boolean into typed shape.
  - [x] Add validation rule for schema payload shape and provider/model support.
- [x] Add OpenAI conversation continuation field reservation:
  - [x] Add `params.openai.previous_response_id` (or approved equivalent namespaced path).
  - [ ] Add resolver pass-through and validation for provider kind compatibility.
  - [ ] Add docs for when continuation id is retained vs cleared.
- [x] Add typed built-in/MCP tool config sections:
  - [x] Add `tools.builtin` object section (provider-specific built-in tool controls).
  - [x] Add `tools.mcp` object section (servers, allowed tools, approval policy request).
  - [x] Keep `tools.tool_allowlist` for compatibility; define precedence with new sections.
  - [ ] Add security check contract: effective MCP/tool access must be intersected with trusted allowlists from UserAgentConfig/policy layer.
- [x] Add explicit tool execution limit control:
  - [x] Add `tools.max_tool_calls` (or approved location).
  - [x] Add range validation and fallback defaults.
  - [x] Add compatibility mapping for existing orchestration controls.
- [x] Add provider-namespaced reasoning extension surface:
  - [x] Reserve `params.openai.reasoning.*` extension object.
  - [x] Add allowlist validation of supported keys.
  - [ ] Add warning behavior for unsupported provider/model combinations.
- [x] Type `tools.tool_choice` as structured union:
  - [x] Replace free string contract with typed union/object model.
  - [x] Keep string parsing compatibility in normalizer for old drafts.
  - [x] Add schema + UI validator alignment tests.
- [ ] Add schema + compatibility test coverage for all critical gaps:
  - [x] Frontend schema normalize/round-trip tests.
  - [x] Backend model validation tests.
  - [x] Draft migration tests from legacy payloads.
  - [ ] Contract snapshot fixtures for M0 reference payloads.

### M0: Implementation Order (Exact File-Level Patch Plan)
- [x] Step 1: Backend canonical contract types and validators
  - [x] Patch `backend/app/models.py`:
    - [x] Extend `PromptParams` with typed `response_format`, `openai` extension, and alias normalization from `response_format_json`.
    - [x] Extend `PromptToolingConfig` with typed/normalized `tool_choice`, `max_tool_calls`, `builtin`, `mcp`.
    - [x] Add strict field validators for new payload shapes.
- [x] Step 2: Frontend canonical schema parity + normalization
  - [x] Patch `frontend/src/components/Prompt/builder/promptBuilderSchema.ts`:
    - [x] Add new field types mirroring backend contract.
    - [x] Add compatibility normalizers (`response_format_json` -> `response_format`, string `tool_choice` -> named object).
    - [x] Add semantic validators for `response_format` capability checks and `tools.max_tool_calls`.
- [x] Step 3: Capability hook normalization parity
  - [x] Patch `frontend/src/components/Prompt/builder/promptBuilderCapabilityRegistry.ts`:
    - [x] Normalize extended tools payload shape.
    - [x] Add semantic hook checks for `max_tool_calls`.
- [x] Step 4: Adapter compatibility updates
  - [x] Patch `frontend/src/components/Prompt/builder/promptBuilderAdapters.ts`:
    - [x] Map structured `tool_choice` back to existing agent payload contract safely.
- [x] Step 5: Backend API payload regression tests
  - [x] Patch `backend/app/tests/api/routes/test_prompt_configs.py`:
    - [x] Add payload coverage for new fields.
    - [x] Add compatibility case for legacy/new mixed payloads.
- [x] Step 6: Frontend schema/capability regression tests
  - [x] Patch `frontend/tests-unit/prompt-builder-schema.spec.ts`.
  - [x] Patch `frontend/tests-unit/prompt-builder-capability-registry.spec.ts`.
- [x] Step 7: Verification
  - [x] Run `npm run typecheck` in `frontend`.
  - [x] Run targeted backend tests for prompt configs.

### M1: Build Backend Resolver Service 
- [x] Create `backend/app/services/prompt_runtime_resolver.py`.
- [x] Implement deterministic merge order:
  - [x] room/session override
  - [x] bound PromptConfig payload
  - [x] UserAgentConfig base
- [x] Add normalization + validation in resolver output path.
- [x] Add preview/diagnostics endpoint to inspect effective config without invocation.
- [x] Add unit tests and snapshot tests for merge behavior.

### M2: Add Agent-Level Binding Surface
-- NOTE: this should be a fka on PromptConfig I believe.  One UAC may support 'many' PromptConfigs.
- [x] Add optional binding fields on `UserAgentConfig`:
  - [x] `prompt_config_id`
  - [x] `prompt_config_version_policy` (for example `latest` / `pinned`)
  - [x] `prompt_config_version_number`
- [x] Add migration for new columns.
- [x] Add API support in agent routes for bind/unbind.
- [x] Add UI controls to bind/unbind PromptConfig from agent editing flow.
- [x] Verify unbound agents preserve existing runtime behavior.
- [x] Add `PromptConfig.slug` as secondary user-facing identifier.
- [x] Reuse shared slug generation path in PromptConfig create flow.

### M3: Add Room/Session Temporary Attach
- [x] Extend room agent settings to support PromptConfig reference or inline prompt override payload.
- [x] Validate owner/membership and optimistic concurrency for overrides.
- [x] Wire override source into resolver inputs (do not bypass resolver).
- [x] Add clear UI for temporary attach, inspect, and rollback.
- [ ] Verify removing override reverts to agent default binding.

### M4: Runtime Cutover : PARTIALLY CUT FROM SCOPE : LEGACY PATH NO LONGER VALID/REQUIRED AS LONG AS NEW FEATURES ARE FUNCTIONAL AND ALL OLD FEATURES MAINTAINED
- [x] Update invocation flow to resolve effective config before model/tool initialization:
  - [x] `backend/app/services/agent_instance.py`
  - [x] `backend/app/services/agent_runner.py` (indirectly through runtime instantiation path)
- [x] Add provenance logging (which layer supplied each effective field).
- [x] Remove remaining legacy direct-read assumptions outside resolver path.
- [x] Run parity tests against legacy/unbound behavior.

### M5: Expand Prompt Builder Capabilities Against Contract
- [ ] Add new tools/skills/capacity fields only through contract-backed schema fields.
- [ ] Add registry hooks and semantic validators for each new field.
- [ ] Ensure every new capability has:
  - [ ] UI control
  - [ ] backend model support
  - [ ] resolver merge semantics
- [ ] Add migration/compat behavior for old drafts.
- [ ] Add end-to-end tests from draft -> save -> resolve -> invoke.

### M6: Finalize Git Integration as Artifact Workflow
- [ ] Scope git operations to PromptConfig + companion assets (skills/tool manifests/templates).
- [ ] Add metadata linkage between git revision and prompt version commit.
- [ ] Add import/export round-trip checks for version integrity.
- [ ] Ensure git workflow does not mutate runtime identity fields on `UserAgentConfig`.

## Cross-Cutting Guardrails
- [x] Enforce single resolver rule: runtime does not read raw `prompt_config` blobs directly.
- [ ] Add contract change checklist requirement for any new field:
  - [ ] schema
  - [ ] validation
  - [ ] resolver semantics
  - [ ] tests
- [ ] Add rollout/rollback playbook for resolver cutover.

## Suggested Execution Order (Minimal Churn)
- [x] Complete M0
- [x] Complete M1
- [x] Complete M2
- [x] Complete M4 runtime hardening
- [ ] Complete M3
- [ ] Complete M5
- [ ] Complete M6

---
