# Prompt Builder User Expectations + Guided Walkthrough
> Audience: QA, Product, UX, LLM, and Engineering
> Purpose: set shared expectations for Prompt Builder behavior and provide a practical walkthrough for authoring, validating, and versioning prompt configs.

## 1. What Prompt Builder Should Do Today
1. Let users create and edit a `PromptConfig` with provider, model, input, params, tools, and metadata.
2. Load provider/model options from live catalogs (not hardcoded lists).
3. Show semantic validation issues clearly (errors vs warnings).
4. Support raw JSON fallback editing when guided controls are not enough.
5. Persist working-copy drafts and commit immutable versions.

## 2. What Users Should Expect (Behavior Contract)
1. Save behavior:
- `Save Draft` updates the working copy (`/prompt-configs/{id}/working-copy`).
- Draft save should preserve unsaved semantics and dirty-state transitions.

2. Version behavior:
- `Commit` creates a new immutable version (`/prompt-configs/{id}/versions`).
- Commit increments `latest_version` and resets working copy to clean.

3. Conflict behavior:
- Stale draft writes can return `409` if `base_version` is out of date.
- Expected user flow: refresh working copy, re-apply intent, retry save.

4. Validation behavior:
- Error-level semantic issues block successful save/commit workflows.
- Warning-level issues remain visible but do not block.

5. Dynamic catalog behavior:
- Provider/model entries can change over time without UI contract breakage.
- Existing persisted values should remain readable even if catalog entries shift.

## 3. Guided Walkthrough (Happy Path)
1. Start a draft:
- Open `/prompt-builder`.
- Select provider and model from catalog-backed controls.

2. Author input:
- Use simple text mode first (`input.kind = simple_text`).
- Add system instructions if needed.

3. Tune parameters:
- Start conservative (`temperature`, `top_p`, token budget).
- Add advanced params only when model/provider compatibility is confirmed.

4. Validate:
- Resolve all error-level issues in the semantic panel.
- Keep warning-level issues intentional and documented.

5. Save + version:
- Save draft (working copy).
- Commit with a clear message describing behavior change.

6. Verify:
- Confirm `latest_version` incremented.
- Confirm working copy is clean after commit.

## 4. Guided Walkthrough (Recovery / Edge Cases)
1. `409` conflict on save:
- Cause: stale `base_version` in working-copy write.
- Recovery: reload working copy from server, re-apply changes, retry.

2. Missing provider/model:
- Validation should report required binding issues.
- Recovery: choose valid provider and model, then re-validate.

3. Catalog drift:
- Existing draft references may point to deprecated/changed catalog entries.
- Recovery: rebind to current provider/model IDs while keeping intent.

## 5. QA Acceptance Checklist
1. Create prompt config succeeds and returns `latest_version = 1`.
2. Working copy can be updated and read back accurately.
3. Commit creates version `2+` and marks working copy `has_uncommitted_changes = false`.
4. Stale working-copy write returns `409` with base-version conflict detail.
5. Validation endpoint returns semantic issues for missing provider/model.
6. Guided controls and raw JSON fallback remain in sync (round-trip safe).

## 6. Implementation References
1. Backend API route:
- `backend/app/api/routes/prompt_configs.py`

2. Backend integration tests:
- `backend/app/tests/api/routes/test_prompt_configs.py`

3. Frontend builder route:
- `frontend/src/routes/_layout/prompt-builder.tsx`

4. Frontend schema/registry/adapters:
- `frontend/src/components/Prompt/builder/promptBuilderSchema.ts`
- `frontend/src/components/Prompt/builder/promptBuilderCapabilityRegistry.ts`
- `frontend/src/components/Prompt/builder/promptBuilderAdapters.ts`

5. Frontend unit tests:
- `frontend/tests-unit/prompt-builder-schema.spec.ts`
- `frontend/tests-unit/prompt-builder-adapters.spec.ts`
- `frontend/tests-unit/prompt-builder-capability-registry.spec.ts`
- `frontend/tests-unit/prompt-top-level-editor.spec.tsx`

## 7. Known Gaps (Next Slice)
1. Compare/restore UX for versions (not just commit/list).
2. Richer commit metadata UX and diff preview.
3. Broader provider-model compatibility checks tied to capability requirements.
4. Expanded test coverage for restore flows and catalog drift edge cases.
