# Agent Provider & Model Selection Design

> **Status:** Ready for implementation
> **Created:** 2026-01-26
> **Scope:** CreateAgentDialog, EditAgentDialog, AgentForm

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PROVIDER & MODEL SELECTION FLOW                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐         ┌──────────────────┐                         │
│  │ Provider Dropdown │ ──────▶ │  Model Dropdown  │                         │
│  └──────────────────┘         └──────────────────┘                         │
│          │                            │                                     │
│          ▼                            ▼                                     │
│  ┌──────────────────┐         ┌──────────────────┐                         │
│  │ None selected    │ ──────▶ │ Show ALL models  │                         │
│  │ provider_type:   │         │ (aspirational)   │                         │
│  │   "empty"        │         │                  │                         │
│  └──────────────────┘         └──────────────────┘                         │
│                                                                             │
│  ┌──────────────────┐         ┌──────────────────┐                         │
│  │ Provider selected│ ──────▶ │ Filter to that   │                         │
│  │ provider_type:   │         │ provider type    │                         │
│  │   from provider  │         │ only             │                         │
│  │ user_provider:   │         │                  │                         │
│  │   provider UUID  │         │                  │                         │
│  └──────────────────┘         └──────────────────┘                         │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ KEY FIELDS:                                                                 │
│   • provider_type: LLMProviderType ("openai"|"anthropic"|"google"|"empty") │
│   • user_provider: string | null (UUID of user's configured provider)      │
│   • model_name: string (e.g., "openai:gpt-4o-mini")                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ SERVICES:                                                                   │
│   • LlmProviderService.listProviders() → user's configured providers       │
│   • LlmCatalogService (via ModelCombobox) → system model catalog           │
│   • AgentService.createAgent/updateAgent → accepts provider fields         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Problem Statement

Users configure their own LLM providers (API keys, custom endpoints) via the web UI. When creating or editing agents, they need to:

1. **Select which of their providers** the agent should use
2. **Select a model** compatible with that provider

Previously, the agent form only exposed model selection from the system catalog, without linking to user-configured providers.

### Terminology Clarification

| Term | Meaning | Service |
|------|---------|---------|
| **User Provider** | User's configured API key/endpoint (e.g., "My OpenAI Key") | `LlmProviderService` |
| **Provider Type** | The underlying LLM platform (openai, anthropic, google, openai_compatible) | Enum in both services |
| **Catalog Model** | A model definition in the system catalog (e.g., gpt-4o-mini) | `LlmCatalogService` |

---

## Design Decisions

### 1. Provider-First Flow

**Decision:** User selects provider first, then model filters accordingly.

**Rationale:** This makes the relationship between "your API key" and "available models" explicit. It naturally constrains choices and prevents confusing combinations.

### 2. Aspirational Model Selection

**Decision:** When no provider selected, show full model catalog (not hidden/disabled).

**Rationale:** Users can "aspire" to use a model before configuring the matching provider. This keeps the form unblocked and educational.

### 3. Provider Change Resets Model

**Decision:** Changing provider resets model selection if incompatible.

**Rationale:** Prevents invalid provider/model combinations. Clean slate when switching contexts.

### 4. Rich Provider Dropdown

**Decision:** Show provider name + status badge + type indicator in dropdown.

**Rationale:** Users need visibility into which providers are working (verified/failed/unknown) at selection time.

### 5. Empty Provider Allowed

**Decision:** Allow agent creation with `provider_type: "empty"` and `user_provider: null`.

**Rationale:** Doesn't block agent creation workflow. Users can configure provider later.

---

## Data Architecture

### AgentFormData Interface Update

```typescript
/**
 * Form data for agent create/edit
 *
 * Provider Selection:
 * - user_provider: UUID of selected UserLLMProvider, or null if none
 * - provider_type: Derived from selected provider, or "empty" if none
 *
 * Model Selection:
 * - model_name: Full model identifier (e.g., "openai:gpt-4o-mini")
 * - When provider selected: filtered to compatible models
 * - When no provider: shows full catalog (aspirational)
 */
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

### State Flow Diagram

```
User Action                    State Change                     UI Effect
───────────────────────────────────────────────────────────────────────────
Form mounts                    Fetch providers list             Populate dropdown
                               (useQuery)

Select provider "X"            selectedProviderId = X.id        Model dropdown filters
                               providerType = X.provider_type   to X.provider_type

Select different provider "Y"  selectedProviderId = Y.id        Model resets if incompatible
                               Check model compatibility        Model dropdown re-filters

Select "None"                  selectedProviderId = null        Model shows full catalog
                               providerType = "empty"

Submit form                    Build payload with:              API call
                               - provider_type
                               - user_provider
                               - model_name
```

---

## Component Specifications

### ProviderSelect Component

```typescript
/**
 * ProviderSelect - Dropdown for selecting user's configured LLM provider
 *
 * Features:
 * - Fetches user's providers via LlmProviderService.listProviders()
 * - Rich display: name + status badge + provider type
 * - "None" option for system default / empty provider
 * - Handles loading and empty states gracefully
 *
 * Status indicators:
 * - 🟢 verified: Provider tested successfully
 * - 🟡 unknown: Provider not yet tested
 * - 🔴 failed: Provider test failed
 *
 * @example
 * <ProviderSelect
 *   value={selectedProviderId}
 *   onChange={(id, provider) => {
 *     setSelectedProviderId(id)
 *     // Handle model reset if needed
 *   }}
 * />
 */
interface ProviderSelectProps {
  /** Currently selected provider UUID, or null for "None" */
  value: string | null

  /**
   * Called when selection changes
   * @param providerId - UUID or null
   * @param provider - Full ProviderViewModel or null (for convenience)
   */
  onChange: (providerId: string | null, provider: ProviderViewModel | null) => void

  /** Disable the dropdown */
  disabled?: boolean

  /** Additional CSS classes */
  className?: string
}
```

### Visual Design

```
Provider dropdown option layout:
┌─────────────────────────────────────────────────┐
│ [Status] Provider Name              [Type Badge]│
│   🟢     My OpenAI Key                 OpenAI   │
└─────────────────────────────────────────────────┘

Full dropdown expanded:
┌─────────────────────────────────────────────────┐
│ ▼ Select a provider...                          │
├─────────────────────────────────────────────────┤
│     None (use system default)                   │
│ ─────────────────────────────────────────────── │
│ 🟢  My OpenAI Key                      OpenAI   │
│ 🟡  Work Azure Endpoint                OpenAI   │
│ 🟢  Personal Claude                  Anthropic  │
│ 🔴  Old Broken Key                     OpenAI   │
└─────────────────────────────────────────────────┘
```

### AgentForm Integration

```typescript
/**
 * AgentForm state additions for provider selection
 *
 * Provider state is managed separately from model state to enable:
 * 1. Independent validation
 * 2. Model reset on provider change
 * 3. Clear data flow to parent components
 */

// New state in AgentForm
const [selectedProviderId, setSelectedProviderId] = useState<string | null>(
  initialData?.user_provider ?? null
)

// Derived provider type (for filtering and payload)
const providerType: LLMProviderType = useMemo(() => {
  if (!selectedProviderId || !providers) return "empty"
  const provider = providers.find(p => p.id === selectedProviderId)
  return provider?.provider_type ?? "empty"
}, [selectedProviderId, providers])

// Provider change handler with model compatibility check
const handleProviderChange = useCallback((
  providerId: string | null,
  provider: ProviderViewModel | null
) => {
  setSelectedProviderId(providerId)

  // Reset model if incompatible with new provider
  if (provider) {
    const currentModelType = extractProviderType(modelName)
    if (currentModelType && currentModelType !== provider.provider_type) {
      setModelName("")  // Reset to empty, user must re-select
    }
  }
  // If provider cleared (null), keep model (aspirational selection)
}, [modelName])
```

---

## File Changes Checklist

### Must Change

- [ ] **`AgentForm.tsx`**
  - Add `selectedProviderId` state
  - Add `ProviderSelect` component (inline or imported)
  - Add provider change handler with model reset logic
  - Update `AgentFormData` interface
  - Update `onChange` callback to include provider fields
  - Fetch providers via `useQuery`

- [ ] **`CreateAgentDialog.tsx`**
  - Update payload to include `provider_type` and `user_provider`

- [ ] **`EditAgentDialog.tsx`**
  - Update payload to include provider fields
  - Add change detection for provider fields

### Optional/New Files

- [ ] **`ProviderSelect.tsx`** (new) - If extracting to reusable component
- [ ] **`useProviders.ts`** (new) - Custom hook for provider fetching if reused elsewhere

### No Changes Needed

- `agentService.ts` - Already has `provider_type` and `user_provider` in types
- `llmProviderService.ts` - Already has `listProviders()` method

---

## Testing Scenarios

### Create Agent Flow

| Scenario | Expected Behavior |
|----------|-------------------|
| No providers configured | Dropdown shows only "None", model shows full catalog |
| Select provider | Model dropdown filters to that provider type |
| Switch provider (compatible model) | Model selection preserved |
| Switch provider (incompatible model) | Model reset to empty |
| Clear provider selection | Model shows full catalog again |
| Submit with no provider | `provider_type: "empty"`, `user_provider: null` |
| Submit with provider | `provider_type: <from provider>`, `user_provider: <UUID>` |

### Edit Agent Flow

| Scenario | Expected Behavior |
|----------|-------------------|
| Agent has provider set | Dropdown pre-selects that provider, model pre-filled |
| Agent has no provider | Dropdown shows "None", model shows current value |
| Change provider | Model resets if incompatible |
| Save with changed provider | Payload includes new provider fields |

---

## Future Considerations

### Not in Scope (YAGNI)

- Provider creation from within agent dialog
- Default provider auto-selection
- Provider health monitoring/auto-fallback
- Model capability filtering (vision, function calling, etc.)

### Possible Future Enhancements

1. **Remember last used provider** - Pre-select user's most recently used provider
2. **Provider recommendations** - Suggest providers based on selected model
3. **Inline provider status refresh** - Test button in dropdown

---

## Implementation Notes

### Query Key for Providers

```typescript
// Recommended: use existing keys from llmProviderService
import { LLM_PROVIDER_QUERY_KEYS } from "@/services/llmProviderService"

// In AgentForm
const { data: providersData, isLoading } = useQuery({
  queryKey: LLM_PROVIDER_QUERY_KEYS.providers,
  queryFn: () => LlmProviderService.listProviders(),
})
```

### Error Handling

- Provider fetch failure: Show dropdown with "None" only, log error
- Empty providers list: Normal state, not an error
- Invalid `user_provider` in edit mode: Show as "Unknown provider" with option to clear

---

## Appendix: Type Definitions

```typescript
// From @/client (auto-generated)
type LLMProviderType = "empty" | "openai" | "anthropic" | "google" | "openai_compatible"

// From @/services/llmProviderService
interface ProviderViewModel {
  id: string
  name: string
  provider_type: LLMProviderType
  base_url: string | null
  is_enabled: boolean
  is_default: boolean
  description: string | null
  created_at: Date
  updated_at: Date
  last_tested_at: Date | null
  last_test_success: boolean | null
  display_type: string      // "OpenAI", "Anthropic", etc.
  status: ProviderStatus    // "verified" | "failed" | "unknown"
  is_usable: boolean        // is_enabled && status !== "failed"
}

// From @/services/agentService
interface CreateAgentInput {
  name: string
  slug: string
  description?: string | null
  model_name?: string
  provider_type?: LLMProviderType  // ← Used by this feature
  user_provider?: string | null     // ← Used by this feature
  system_prompt?: string | null
  participation_mode?: ParticipationMode
  scope?: AgentScope
  is_enabled?: boolean
}
```
