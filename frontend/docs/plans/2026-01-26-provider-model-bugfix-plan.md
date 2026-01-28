# Provider/Model Selection Bugfix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 4 bugs in the provider/model selection system for agent creation, editing, and cloning.

**Architecture:** Debug-first approach - add console logging to trace data flow, identify exact failure points, then apply minimal fixes. Each bug is isolated but they share common data flow paths.

**Tech Stack:** React, TanStack Query, TypeScript

**Reference:** See `docs/references/provider-model-reference-card.md` for entity relationships and control flows.

---

## Bug Summary

| Bug | Symptom | Component | Priority |
|-----|---------|-----------|----------|
| #3 | Provider not saved when creating agent | CreateAgentDialog | 1 (Foundation) |
| #1 | Model dropdown empty after provider selection | ModelCombobox | 2 |
| #2 | Error when adding custom model | ModelCombobox | 3 |
| #4 | Clone missing provider fields | AgentCloneButton | 4 |

---
---

## Task 2: Debug and Fix Bug #3 - Provider Not Saved

**Files:**
- Modify: `src/components/Agents/AgentForm.tsx` (if issue is here)
- Modify: `src/components/Agents/CreateAgentDialog.tsx` (if issue is here)
- Modify: `src/services/agentService.ts` (if issue is here)



Check that `handleProviderChange` is being called by ProviderSelect:

```typescript
// In ProviderSelect.tsx, verify onChange is called correctly
const handleValueChange = (value: string) => {
  if (value === NONE_VALUE) {
    onChange(null, null)
  } else {
    const provider = providers.find((p) => p.id === value) ?? null
    onChange(value, provider)
  }
}
```

**If the issue is in onChange callback:**

Verify the useEffect dependencies include `selectedProviderId`:

```typescript
useEffect(() => {
  onChange({
    // ... other fields
    provider_type: derivedProviderType,
    user_provider: selectedProviderId,  // <-- Must be here
  })
}, [
  // ... other deps
  selectedProviderId,  // <-- Must be in deps
  onChange,
])
```

**If the issue is in CreateAgentInput type:**

Check `src/services/agentService.ts` for the `CreateAgentInput` type and ensure it includes:

```typescript
export interface CreateAgentInput {
  // ... other fields
  provider_type: LLMProviderType
  user_provider: string | null
}
```

**Step 4: Verify the fix**

Run: `npm run dev`

Actions:
1. Open Create Agent dialog
2. Select a provider
3. Create agent
4. Check Network tab - request body should have `user_provider: "<uuid>"`
5. Edit the created agent - provider dropdown should show the correct selection

Expected: Agent is created with the selected provider saved.

**Step 5: Commit the fix**

```bash
git add <modified-files>
git commit -m "fix: save user_provider when creating agent (Bug #3)"
```

---

## Task 3: Debug and Fix Bug #1 - Model Dropdown Empty

**Files:**
- Modify: `src/components/Agents/providers/ModelCombobox.tsx`
- Possibly: `src/hooks/useLlmCatalog.ts`

**Purpose:** Fix model dropdown not populating after provider selection.

**Step 1: Add debug logging to ModelCombobox**

In `ModelCombobox.tsx`, add logging at the top of the component (after hooks):

```typescript
export default function ModelCombobox({
  value,
  onChange,
  providerType,
  placeholder = "Select a model...",
  disabled = false,
  className,
  popoverWidth = "w-[350px]",
}: ModelComboboxProps) {
  // ... existing state hooks ...

  const {
    modelsByProvider,
    allModels,
    isLoading: catalogLoading,
    // ... rest of destructuring
  } = useLlmCatalog()

  // DEBUG: Log filtering state
  console.log("[ModelCombobox] Filter state:", {
    providerType,
    providerTypeIsUndefined: providerType === undefined,
    modelsByProviderKeys: Object.keys(modelsByProvider),
    modelsForProvider: providerType ? modelsByProvider[providerType]?.length : "N/A",
    allModelsCount: allModels.length,
    catalogLoading,
  })

  // Filter models by provider type if specified
  const filteredModels = providerType
    ? modelsByProvider[providerType] || []
    : allModels

  console.log("[ModelCombobox] filteredModels count:", filteredModels.length)

  // ... rest of component
```

**Step 2: Reproduce and analyze**

Run: `npm run dev`

Actions:
1. Open Create Agent dialog
2. Select a provider (e.g., OpenAI)
3. Open model dropdown
4. Check console for ModelCombobox logs

Expected to see one of:
- `providerType: "openai"` but `modelsForProvider: 0` → Issue in modelsByProvider
- `providerType: undefined` → ProviderSelect not passing type correctly
- `catalogLoading: true` → Data not loaded yet

**Step 3: Apply fix based on findings**

**If providerType is undefined:**

The issue is in AgentForm passing `selectedProvider?.provider_type` to ModelCombobox.

Check `AgentForm.tsx` line ~271:
```typescript
<ModelCombobox
  value={modelName}
  onChange={setModelName}
  providerType={selectedProvider?.provider_type}  // <-- Could be undefined
  placeholder="Select a model..."
/>
```

If `selectedProvider` is null even after selection, check the `providers.find()` logic:
```typescript
const selectedProvider =
  providers.find((p) => p.id === selectedProviderId) ?? null
```

**If modelsByProvider[type] is empty but allModels is populated:**

Check `useLlmCatalog.ts` modelsByProvider construction. The keys must match exactly:

```typescript
const byProvider: Record<LLMProviderType, ModelOption[]> = {
  empty: [],
  openai: [],        // Must match "openai" exactly
  anthropic: [],     // Must match "anthropic" exactly
  google: [],        // Must match "google" exactly
  openai_compatible: [],
}
```

Verify the provider types from API match these keys (check for case sensitivity).

**If catalogLoading stays true:**

Check Network tab for the catalog API call. May be failing silently.

**Step 4: Verify the fix**

Run: `npm run dev`

Actions:
1. Open Create Agent dialog
2. Select provider
3. Open model dropdown
4. Models should appear filtered to that provider type

Expected: Dropdown shows models matching the provider type.

**Step 5: Commit**

```bash
git add <modified-files>
git commit -m "fix: populate model dropdown after provider selection (Bug #1)"
```

---

## Task 4: Debug and Fix Bug #2 - Custom Model Error

**Files:**
- Modify: `src/hooks/useLlmCatalog.ts:103-135`
- Possibly: `src/components/Agents/providers/ModelCombobox.tsx:149-175`

**Purpose:** Fix error when adding custom model in agent create.

**Step 1: Add debug logging to createCustomModel mutation**

In `useLlmCatalog.ts`, find the `createMutation` (around line 103) and add logging:

```typescript
const createMutation = useMutation({
  mutationFn: async (input: CreateCustomModelInput): Promise<ModelOption> => {
    // DEBUG: Log input and provider lookup
    console.log("[useLlmCatalog] createCustomModel input:", input)
    console.log("[useLlmCatalog] grouped providers:", grouped?.providers.map(p => ({
      id: p.id,
      name: p.name,
      providerType: p.providerType,
    })))

    // Find the provider ID for the given provider type
    const provider = grouped?.providers.find(
      (p) => p.providerType === input.providerType,
    )

    console.log("[useLlmCatalog] Found provider:", provider ? {
      id: provider.id,
      providerType: provider.providerType,
    } : "NOT FOUND")

    if (!provider) {
      throw new Error(`No provider found for type: ${input.providerType}`)
    }

    // ... rest of mutation
  },
  // ... onSuccess
})
```

**Step 2: Reproduce the error**

Run: `npm run dev`

Actions:
1. Open Create Agent dialog
2. Select a provider (or don't select one)
3. In model dropdown, type a custom model name
4. Click "Add as custom model"
5. Check console for error and logs

**Step 3: Apply fix based on findings**

**If no provider found for type:**

The issue is that `grouped?.providers` contains CatalogProviders (system providers in the catalog), not UserProviders.

When `providerType` is `"openai_compatible"` (for user's custom provider), there may be no matching catalog provider.

**Fix option A:** Default to openai_compatible catalog provider if exists:

```typescript
const provider = grouped?.providers.find(
  (p) => p.providerType === input.providerType,
) ?? grouped?.providers.find(
  (p) => p.providerType === "openai_compatible",
)
```

**Fix option B:** Allow custom models without catalog provider (if backend supports):

Check if backend allows creating custom model with null provider_id.

**If API returns error:**

Check Network tab for the actual error response. May need to handle specific validation errors.

**Step 4: Handle the "no provider selected" case**

In `ModelCombobox.tsx`, the handleCreate function (line ~149) uses:

```typescript
const effectiveProviderType = providerType || "openai_compatible"
```

This defaults to `openai_compatible` when no provider is selected. Verify this matches a catalog provider.

**Step 5: Verify the fix**

Run: `npm run dev`

Actions:
1. Open Create Agent dialog
2. Type custom model name in model dropdown
3. Click "Add as custom model"
4. Model should be created and selected

Expected: Custom model created successfully.

**Step 6: Commit**

```bash
git add <modified-files>
git commit -m "fix: create custom models correctly (Bug #2)"
```

---

## Task 5: Fix Bug #4 - Clone Missing Provider Fields

**Files:**
- Modify: `src/components/Agents/AgentCloneButton.tsx:77-86`

**Purpose:** Add `provider_type` and `user_provider` fields to clone payload.

**Step 1: Update the clone payload**

In `AgentCloneButton.tsx`, find the mutation mutationFn (around line 76) and add provider fields:

```typescript
const mutation = useMutation({
  mutationFn: () => {
    const payload: CreateAgentInput = {
      name: newName.trim(),
      slug: newSlug.trim(),
      description: agent.description,
      model_name: agent.model_name,
      system_prompt: agent.system_prompt,
      participation_mode: agent.participation_mode,
      scope: "personal",
      is_enabled: true,
      // Add provider fields - always default to "empty" for clones
      // User can edit the cloned agent to set their own provider
      provider_type: "empty",
      user_provider: null,
    }
    return AgentService.createAgent(payload)
  },
  // ... rest of mutation
})
```

**Why "empty" instead of copying from source?**

1. System agents (scope: "system") may have provider settings the user doesn't have access to
2. Personal agents may reference a provider the cloning user doesn't own
3. Safest default is "empty" - user must configure provider after cloning

**Step 2: Add LLMProviderType import if needed**

Check if `LLMProviderType` is imported. If not, add:

```typescript
import type { LLMProviderType } from "@/client"
```

Or since we're using the literal "empty", TypeScript may infer it correctly without import.

**Step 3: Verify the fix**

Run: `npm run dev`

Actions:
1. Find a system agent
2. Click "Clone"
3. Create the clone
4. Check Network tab - payload should have `provider_type: "empty"`, `user_provider: null`
5. Edit the cloned agent - provider dropdown should show "None"

Expected: Cloned agent has explicit empty provider, not system fallback.

**Step 4: Commit**

```bash
git add src/components/Agents/AgentCloneButton.tsx
git commit -m "fix: set explicit empty provider when cloning agents (Bug #4)"
```

---

## Task 6: Remove Debug Logging

**Files:**
- Modify: `src/components/Agents/AgentForm.tsx`
- Modify: `src/components/Agents/CreateAgentDialog.tsx`
- Modify: `src/components/Agents/providers/ModelCombobox.tsx`
- Modify: `src/hooks/useLlmCatalog.ts`

**Purpose:** Remove all temporary console.log statements added for debugging.

**Step 1: Remove logging from AgentForm.tsx**

Remove the console.log statement added in Task 1.

**Step 2: Remove logging from CreateAgentDialog.tsx**

Remove the two console.log statements added in Task 1.

**Step 3: Remove logging from ModelCombobox.tsx**

Remove the console.log statements added in Task 3.

**Step 4: Remove logging from useLlmCatalog.ts**

Remove the console.log statements added in Task 4.

**Step 5: Verify no console output**

Run: `npm run dev`

Open Create Agent dialog and verify no debug logs appear in console.

**Step 6: Commit**

```bash
git add src/components/Agents/AgentForm.tsx src/components/Agents/CreateAgentDialog.tsx src/components/Agents/providers/ModelCombobox.tsx src/hooks/useLlmCatalog.ts
git commit -m "chore: remove debug logging after bugfixes"
```

---

## Task 7: Add Validation for Provider/Model Consistency

**Files:**
- Modify: `src/components/Agents/CreateAgentDialog.tsx`
- Modify: `src/components/Agents/EditAgentDialog.tsx`

**Purpose:** Add pre-submit validation to catch invalid provider/model combinations.

**Step 1: Add validation helper function**

Create a validation function (can be in either dialog or a shared utils file):

```typescript
/**
 * Validate provider/model consistency before submission
 */
function validateProviderModelConsistency(
  formData: AgentFormData,
): string | null {
  // Rule: If provider_type is not "empty", user_provider must be set
  if (formData.provider_type !== "empty" && !formData.user_provider) {
    return "Provider type is set but no provider selected"
  }

  // Rule: If user_provider is set, provider_type must not be "empty"
  if (formData.user_provider && formData.provider_type === "empty") {
    return "Provider selected but provider type is empty"
  }

  // Rule: model_name prefix should match provider_type (warning only)
  if (formData.model_name && formData.provider_type !== "empty") {
    const modelPrefix = formData.model_name.split(":")[0]
    if (modelPrefix !== formData.provider_type) {
      console.warn(
        `Model prefix "${modelPrefix}" doesn't match provider_type "${formData.provider_type}"`
      )
      // Don't block submission, just warn
    }
  }

  return null // No errors
}
```

**Step 2: Add validation to CreateAgentDialog handleSubmit**

```typescript
const handleSubmit = () => {
  if (!formData) return

  // Validate required fields
  if (!formData.name.trim()) {
    showErrorToast("Agent name is required")
    return
  }
  if (!formData.slug.trim()) {
    showErrorToast("Agent slug is required")
    return
  }

  // Validate provider/model consistency
  const validationError = validateProviderModelConsistency(formData)
  if (validationError) {
    showErrorToast(validationError)
    return
  }

  // ... rest of submission
}
```

**Step 3: Add same validation to EditAgentDialog**

Apply the same validation pattern to EditAgentDialog's handleSubmit.

**Step 4: Verify validation**

Run: `npm run dev`

Test edge cases:
1. Try to submit with inconsistent provider state (may need to manually trigger via console)
2. Verify error toast appears

**Step 5: Commit**

```bash
git add src/components/Agents/CreateAgentDialog.tsx src/components/Agents/EditAgentDialog.tsx
git commit -m "feat: add validation for provider/model consistency"
```

---

## Task 8: Final Verification

**Purpose:** Comprehensive end-to-end testing of all fixed bugs.

**Step 1: Test Bug #3 fix - Provider saved on create**

1. Open Create Agent dialog
2. Select a provider (e.g., your OpenAI provider)
3. Select a model
4. Fill in name, etc.
5. Create agent
6. Edit the created agent
7. ✅ Verify: Provider dropdown shows the correct selection

**Step 2: Test Bug #1 fix - Model dropdown populates**

1. Open Create Agent dialog
2. Select a provider
3. Open model dropdown
4. ✅ Verify: Only models for that provider type appear
5. Change provider
6. Open model dropdown again
7. ✅ Verify: Models update to new provider type

**Step 3: Test Bug #2 fix - Custom model creation**

1. Open Create Agent dialog
2. Select a provider
3. In model dropdown, type a custom model name (e.g., "my-custom-model")
4. Click "Add as custom model"
5. ✅ Verify: Model is created and selected
6. ✅ Verify: No error appears

**Step 4: Test Bug #4 fix - Clone has explicit empty provider**

1. Find a system agent
2. Click "Clone"
3. Create the clone
4. Edit the cloned agent
5. ✅ Verify: Provider dropdown shows "None (use system default)"
6. ✅ Verify: The clone doesn't have access to LLM if user has no providers

**Step 5: Test edge cases**

1. Create agent with no provider selected → Should save with provider_type: "empty"
2. Edit agent, change provider → Model should reset if incompatible
3. Create agent, select provider, then clear provider → Should work

**Step 6: Run linter**

```bash
npm run lint
```

Fix any linting errors.

**Step 7: Commit any final fixes**

```bash
git add -A
git commit -m "chore: final cleanup after provider/model bugfixes"
```

---

## Summary of Changes

| File | Changes |
|------|---------|
| `AgentForm.tsx` | Debug logging (temporary), verify data flow |
| `CreateAgentDialog.tsx` | Debug logging (temporary), add validation |
| `EditAgentDialog.tsx` | Add validation |
| `AgentCloneButton.tsx` | Add provider_type: "empty", user_provider: null |
| `ModelCombobox.tsx` | Debug logging (temporary), fix filtering if needed |
| `useLlmCatalog.ts` | Debug logging (temporary), fix createCustomModel if needed |

## Expected Outcomes

1. **Bug #3**: Agents save with the selected provider
2. **Bug #1**: Model dropdown shows correct models for selected provider
3. **Bug #2**: Custom models can be created without errors
4. **Bug #4**: Cloned agents have explicit "empty" provider, not system fallback
