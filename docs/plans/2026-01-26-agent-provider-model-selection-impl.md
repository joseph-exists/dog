# Agent Provider & Model Selection - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add provider selection dropdown to agent create/edit dialogs, with model filtering based on selected provider.

**Architecture:** Provider-first flow - user selects from their configured providers, then model dropdown filters to compatible models. No provider = show full catalog (aspirational selection). Uses existing `LlmProviderService` for provider data and `ModelCombobox` for model selection.

**Tech Stack:** React, TypeScript, TanStack Query, shadcn/ui Select component

**Design Doc:** `docs/plans/2026-01-26-agent-provider-model-selection-design.md`

---

## Task 1: Update AgentFormData Interface

**Files:**
- Modify: `frontend/src/components/Agents/AgentForm.tsx:62-69`

**Step 1: Add provider fields to AgentFormData interface**

Update the interface at line 62-69:

```typescript
export interface AgentFormData {
  name: string
  slug: string
  description: string
  model_name: string
  system_prompt: string
  participation_mode: ParticipationMode
  // NEW: Provider selection fields
  provider_type: LLMProviderType   // "openai" | "anthropic" | "google" | "openai_compatible" | "empty"
  user_provider: string | null     // UUID of user's provider, or null
}
```

**Step 2: Add import for LLMProviderType**

Add to imports section (around line 37):

```typescript
import type { LLMProviderType } from "@/client"
```

**Step 3: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit 2>&1 | grep -E "(AgentForm|AgentFormData)" | head -10`

Expected: Errors about missing properties in `onChange` calls (this is correct - we'll fix in next task)

**Step 4: Commit**

```bash
git add frontend/src/components/Agents/AgentForm.tsx
git commit -m "feat(agents): add provider fields to AgentFormData interface"
```

---

## Task 2: Add Provider State and Query to AgentForm

**Files:**
- Modify: `frontend/src/components/Agents/AgentForm.tsx`

**Step 1: Add TanStack Query import**

Add to imports:

```typescript
import { useQuery } from "@tanstack/react-query"
```

**Step 2: Add provider service imports**

Add to imports:

```typescript
import {
  LlmProviderService,
  LLM_PROVIDER_QUERY_KEYS,
  type ProviderViewModel,
} from "@/services/llmProviderService"
```

**Step 3: Add provider state after existing state declarations (around line 99)**

After the `participationMode` state, add:

```typescript
  // Provider selection state
  const [selectedProviderId, setSelectedProviderId] = useState<string | null>(
    initialData?.user_provider ?? null
  )

  // Fetch user's configured providers
  const { data: providersData, isLoading: providersLoading } = useQuery({
    queryKey: LLM_PROVIDER_QUERY_KEYS.providers,
    queryFn: () => LlmProviderService.listProviders(),
  })

  const providers = providersData?.providers ?? []

  // Find selected provider object for derived values
  const selectedProvider = providers.find((p) => p.id === selectedProviderId) ?? null

  // Derive provider_type from selection (or "empty" if none)
  const derivedProviderType: LLMProviderType = selectedProvider?.provider_type ?? "empty"
```

**Step 4: Update the onChange effect to include provider fields**

Update the effect at line 121-138 to include provider fields:

```typescript
  // Notify parent of changes
  useEffect(() => {
    onChange({
      name,
      slug,
      description,
      model_name: modelName,
      system_prompt: systemPrompt,
      participation_mode: participationMode,
      provider_type: derivedProviderType,
      user_provider: selectedProviderId,
    })
  }, [
    name,
    slug,
    description,
    modelName,
    systemPrompt,
    participationMode,
    derivedProviderType,
    selectedProviderId,
    onChange,
  ])
```

**Step 5: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit 2>&1 | grep "AgentForm" | head -5`

Expected: No errors in AgentForm.tsx (dialogs may still have errors)

**Step 6: Commit**

```bash
git add frontend/src/components/Agents/AgentForm.tsx
git commit -m "feat(agents): add provider state and query to AgentForm"
```

---

## Task 3: Create ProviderStatusBadge Component

**Files:**
- Create: `frontend/src/components/Agents/ProviderStatusBadge.tsx`

**Step 1: Create the component file**

```typescript
/**
 * ProviderStatusBadge Component
 *
 * Displays a small status indicator for provider verification state.
 * - 🟢 verified: Provider tested successfully
 * - 🟡 unknown: Provider not yet tested
 * - 🔴 failed: Provider test failed
 */

import { cn } from "@/lib/utils"
import type { ProviderStatus } from "@/services/llmProviderService"

interface ProviderStatusBadgeProps {
  status: ProviderStatus
  className?: string
}

const statusConfig: Record<ProviderStatus, { icon: string; label: string; colorClass: string }> = {
  verified: {
    icon: "🟢",
    label: "Verified",
    colorClass: "text-green-600",
  },
  unknown: {
    icon: "🟡",
    label: "Not tested",
    colorClass: "text-yellow-600",
  },
  failed: {
    icon: "🔴",
    label: "Failed",
    colorClass: "text-red-600",
  },
}

export function ProviderStatusBadge({ status, className }: ProviderStatusBadgeProps) {
  const config = statusConfig[status]

  return (
    <span
      className={cn("text-sm", config.colorClass, className)}
      title={config.label}
      aria-label={config.label}
    >
      {config.icon}
    </span>
  )
}
```

**Step 2: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit 2>&1 | grep "ProviderStatusBadge"`

Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/Agents/ProviderStatusBadge.tsx
git commit -m "feat(agents): add ProviderStatusBadge component"
```

---

## Task 4: Create ProviderSelect Component

**Files:**
- Create: `frontend/src/components/Agents/ProviderSelect.tsx`

**Step 1: Create the component file**

```typescript
/**
 * ProviderSelect Component
 *
 * Dropdown for selecting user's configured LLM provider.
 *
 * Features:
 * - "None" option for system default / empty provider
 * - Rich display: name + status badge + provider type
 * - Handles loading and empty states gracefully
 *
 * @example
 * <ProviderSelect
 *   value={selectedProviderId}
 *   providers={providers}
 *   isLoading={isLoading}
 *   onChange={(id, provider) => {
 *     setSelectedProviderId(id)
 *   }}
 * />
 */

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"
import type { ProviderViewModel } from "@/services/llmProviderService"
import { AgentProviderBadge } from "./AgentBadge"
import { ProviderStatusBadge } from "./ProviderStatusBadge"

/** Special value for "no provider selected" */
const NONE_VALUE = "__none__"

interface ProviderSelectProps {
  /** Currently selected provider UUID, or null for "None" */
  value: string | null
  /** List of user's configured providers */
  providers: ProviderViewModel[]
  /** Whether providers are still loading */
  isLoading?: boolean
  /**
   * Called when selection changes
   * @param providerId - UUID or null
   * @param provider - Full ProviderViewModel or null
   */
  onChange: (providerId: string | null, provider: ProviderViewModel | null) => void
  /** Disable the dropdown */
  disabled?: boolean
  /** Additional CSS classes */
  className?: string
}

export function ProviderSelect({
  value,
  providers,
  isLoading = false,
  onChange,
  disabled = false,
  className,
}: ProviderSelectProps) {
  // Convert null to special NONE_VALUE for Select component
  const selectValue = value ?? NONE_VALUE

  const handleChange = (newValue: string) => {
    if (newValue === NONE_VALUE) {
      onChange(null, null)
    } else {
      const provider = providers.find((p) => p.id === newValue) ?? null
      onChange(newValue, provider)
    }
  }

  // Find current provider for display
  const currentProvider = value ? providers.find((p) => p.id === value) : null

  return (
    <Select
      value={selectValue}
      onValueChange={handleChange}
      disabled={disabled || isLoading}
    >
      <SelectTrigger className={cn("w-full", className)}>
        <SelectValue placeholder={isLoading ? "Loading providers..." : "Select a provider..."}>
          {currentProvider ? (
            <span className="flex items-center gap-2">
              <ProviderStatusBadge status={currentProvider.status} />
              <span className="truncate">{currentProvider.name}</span>
            </span>
          ) : (
            "None (use system default)"
          )}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {/* None option */}
        <SelectItem value={NONE_VALUE}>
          <span className="text-muted-foreground">None (use system default)</span>
        </SelectItem>

        {/* Separator if there are providers */}
        {providers.length > 0 && (
          <div className="my-1 h-px bg-border" />
        )}

        {/* Provider options */}
        {providers.map((provider) => (
          <SelectItem key={provider.id} value={provider.id}>
            <div className="flex items-center justify-between gap-3 w-full min-w-0">
              <div className="flex items-center gap-2 min-w-0">
                <ProviderStatusBadge status={provider.status} />
                <span className="truncate">{provider.name}</span>
              </div>
              <AgentProviderBadge
                providerType={provider.provider_type}
                className="shrink-0"
              />
            </div>
          </SelectItem>
        ))}

        {/* Empty state hint */}
        {providers.length === 0 && !isLoading && (
          <div className="px-2 py-1.5 text-xs text-muted-foreground">
            No providers configured yet
          </div>
        )}
      </SelectContent>
    </Select>
  )
}
```

**Step 2: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit 2>&1 | grep "ProviderSelect"`

Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/Agents/ProviderSelect.tsx
git commit -m "feat(agents): add ProviderSelect dropdown component"
```

---

## Task 5: Add Provider Dropdown to AgentForm UI

**Files:**
- Modify: `frontend/src/components/Agents/AgentForm.tsx`

**Step 1: Import ProviderSelect**

Add to imports:

```typescript
import { ProviderSelect } from "./ProviderSelect"
```

**Step 2: Add provider change handler with model reset logic**

After the state declarations, add:

```typescript
  /**
   * Handle provider selection change.
   * Resets model if incompatible with new provider type.
   */
  const handleProviderChange = useCallback(
    (providerId: string | null, provider: ProviderViewModel | null) => {
      setSelectedProviderId(providerId)

      // Reset model if incompatible with new provider
      if (provider) {
        const currentModelProviderType = parseProviderFromModelName(modelName)
        if (currentModelProviderType && currentModelProviderType !== provider.provider_type) {
          setModelName("") // Reset - user must re-select
        }
      }
      // If provider cleared (null), keep model (aspirational selection)
    },
    [modelName]
  )
```

**Step 3: Add Provider Selector UI section**

Insert this block BEFORE the Model Selector section (before line 183):

```typescript
      {/* Provider Selector */}
      <div className="space-y-2">
        <Label htmlFor="agent-provider">Provider</Label>
        <ProviderSelect
          value={selectedProviderId}
          providers={providers}
          isLoading={providersLoading}
          onChange={handleProviderChange}
        />
        <p className="text-xs text-muted-foreground">
          {selectedProvider
            ? `Using your "${selectedProvider.name}" credentials`
            : "Select a provider to use your own API credentials"}
        </p>
      </div>
```

**Step 4: Update ModelCombobox to filter by selected provider**

Update the ModelCombobox section (around line 192-203) to use the selected provider type:

```typescript
      {/* Model Selector */}
      <div className="space-y-2">
        <Label htmlFor="agent-model">Model</Label>
        {selectedProvider && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Filtered to:</span>
            <AgentProviderBadge providerType={selectedProvider.provider_type} />
          </div>
        )}
        <ModelCombobox
          value={modelName}
          onChange={setModelName}
          providerType={selectedProvider?.provider_type}
          placeholder="Select a model..."
        />
        <p className="text-xs text-muted-foreground">
          {selectedProvider
            ? `Models compatible with ${selectedProvider.display_type}`
            : "All catalog models (select a provider to filter)"}
        </p>
      </div>
```

**Step 5: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -10`

Expected: May have dialog errors (fixed in next tasks), but no AgentForm errors

**Step 6: Commit**

```bash
git add frontend/src/components/Agents/AgentForm.tsx
git commit -m "feat(agents): add provider dropdown to AgentForm UI"
```

---

## Task 6: Update CreateAgentDialog Payload

**Files:**
- Modify: `frontend/src/components/Agents/CreateAgentDialog.tsx`

**Step 1: Update the payload in handleSubmit**

Find the `handleSubmit` function and update the payload (around line 96-106):

```typescript
    const payload: CreateAgentInput = {
      name: formData.name.trim(),
      slug: formData.slug.trim(),
      description: formData.description.trim() || null,
      model_name: formData.model_name || undefined,
      provider_type: formData.provider_type,
      user_provider: formData.user_provider,
      system_prompt: formData.system_prompt.trim() || null,
      participation_mode: formData.participation_mode,
      scope: "personal",
      is_enabled: true,
    }
```

**Step 2: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit 2>&1 | grep "CreateAgentDialog"`

Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/Agents/CreateAgentDialog.tsx
git commit -m "feat(agents): include provider fields in CreateAgentDialog payload"
```

---

## Task 7: Update EditAgentDialog Payload

**Files:**
- Modify: `frontend/src/components/Agents/EditAgentDialog.tsx`

**Step 1: Add provider change detection to handleSubmit**

Find the `handleSubmit` function and add provider change detection after the existing checks (around line 114-116):

```typescript
    if (formData.participation_mode !== agent.participation_mode) {
      payload.participation_mode = formData.participation_mode
    }
    // NEW: Provider field change detection
    if (formData.provider_type !== agent.provider_type) {
      payload.provider_type = formData.provider_type
    }
    if (formData.user_provider !== agent.user_provider) {
      payload.user_provider = formData.user_provider
    }
```

**Step 2: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit 2>&1 | grep "EditAgentDialog"`

Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/Agents/EditAgentDialog.tsx
git commit -m "feat(agents): include provider fields in EditAgentDialog payload"
```

---

## Task 8: Final Verification and Lint Fix

**Files:**
- All modified files

**Step 1: Run full TypeScript check**

Run: `cd frontend && npx tsc --noEmit`

Expected: No errors (0 exit code)

**Step 2: Run linter**

Run: `cd frontend && npm run lint`

Expected: May have auto-fixable issues

**Step 3: Fix lint issues if any**

Run: `cd frontend && npm run lint -- --write`

**Step 4: Final TypeScript check after lint fixes**

Run: `cd frontend && npx tsc --noEmit`

Expected: No errors

**Step 5: Commit any lint fixes**

```bash
git add -A
git commit -m "style: lint fixes for provider selection feature"
```

---

## Task 9: Manual Testing Checklist

**No code changes - manual verification**

**Step 1: Start the dev server**

Run: `cd frontend && npm run dev`

**Step 2: Test Create Agent Dialog**

1. Open Create Agent dialog
2. Verify Provider dropdown appears above Model dropdown
3. Select "None" - verify all models shown
4. Select a provider - verify models filter to that type
5. Select incompatible model first, then change provider - verify model resets
6. Create agent with provider selected - verify API call includes `provider_type` and `user_provider`
7. Create agent with no provider - verify `provider_type: "empty"` and `user_provider: null`

**Step 3: Test Edit Agent Dialog**

1. Edit an existing agent (with no provider)
2. Verify Provider dropdown shows current state (None)
3. Select a provider - verify model filters
4. Save - verify provider fields in API call
5. Edit an agent that has a provider - verify pre-selected

**Step 4: Test Edge Cases**

1. User with no providers - verify dropdown shows only "None" option
2. User with failed provider - verify red status badge visible
3. User with verified provider - verify green status badge visible

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Update AgentFormData interface | AgentForm.tsx |
| 2 | Add provider state and query | AgentForm.tsx |
| 3 | Create ProviderStatusBadge | ProviderStatusBadge.tsx (new) |
| 4 | Create ProviderSelect | ProviderSelect.tsx (new) |
| 5 | Add provider dropdown to UI | AgentForm.tsx |
| 6 | Update CreateAgentDialog payload | CreateAgentDialog.tsx |
| 7 | Update EditAgentDialog payload | EditAgentDialog.tsx |
| 8 | Final verification and lint | All |
| 9 | Manual testing | None (verification) |

**Total estimated time:** 30-45 minutes

**Key dependencies:**
- `@/services/llmProviderService` - Provider fetching
- `@/components/Agents/AgentBadge` - AgentProviderBadge component
- `@/components/Agents/providers/ModelCombobox` - Existing model selector
