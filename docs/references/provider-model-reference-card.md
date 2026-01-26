# Provider & Model Reference Card

> **Purpose:** Frontend debugging guide for provider/model selection in agent workflows.
> **Audience:** Developers debugging or extending agent provider integration.
> **Last Updated:** 2026-01-26

---

## Quick Reference: Entity Relationships

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PROVIDER & MODEL ENTITY RELATIONSHIPS                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐         ┌─────────────────────┐                   │
│  │  ProviderViewModel  │         │ CatalogModelViewModel│                   │
│  │  (User's Provider)  │         │  (System Catalog)    │                   │
│  ├─────────────────────┤         ├─────────────────────┤                   │
│  │ id: UUID            │         │ id: UUID             │                   │
│  │ name: string        │         │ modelId: string      │◄─┐               │
│  │ provider_type ──────┼────┐    │ displayName: string  │  │               │
│  │ status: verified|   │    │    │ providerType ────────┼──┤               │
│  │   failed|unknown    │    │    │ isDefault: boolean   │  │               │
│  │ is_usable: boolean  │    │    │ capabilities: {...}  │  │               │
│  └─────────────────────┘    │    └─────────────────────┘  │               │
│           │                 │                              │               │
│           │ user selects    │    ┌────────────────────┐   │               │
│           │                 └───►│  LLMProviderType   │◄──┘               │
│           │                      │  (shared enum)     │                   │
│           │                      ├────────────────────┤                   │
│           ▼                      │ "openai"           │                   │
│  ┌─────────────────────┐        │ "anthropic"        │                   │
│  │   AgentViewModel    │        │ "google"           │                   │
│  ├─────────────────────┤        │ "openai_compatible"│                   │
│  │ id: UUID            │        │ "empty"            │◄── no provider    │
│  │ name, slug          │        └────────────────────┘                   │
│  │ provider_type ──────┼────────────────┘                                 │
│  │ user_provider: UUID?├────► links to ProviderViewModel.id              │
│  │ model_name: string  ├────► format: "providerType:modelId"             │
│  │ display_model       │      e.g., "openai:gpt-4o-mini"                 │
│  └─────────────────────┘                                                  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ KEY RELATIONSHIPS:                                                          │
│ • ProviderViewModel.provider_type → filters CatalogModelViewModel options  │
│ • AgentViewModel.user_provider → UUID of ProviderViewModel (or null)       │
│ • AgentViewModel.model_name → "provider_type:model_id" composite string    │
│ • AgentViewModel.provider_type → must match model_name prefix              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Terminology

| Term | Definition | Source |
|------|------------|--------|
| **Provider Type** (LLMProviderType) | The LLM platform enum: openai, anthropic, google, openai_compatible, empty | `LLMProviderType` from `@/client` |
| **User Provider** (ProviderViewModel) | A user's configured API credentials for a provider type. Has status (verified/failed/unknown), name, base_url | `ProviderViewModel` from `llmProviderService.ts` |
| **Catalog Model** (CatalogModelViewModel) | A model definition from the system catalog. Includes capabilities, context window. Can be system or user-created. | `CatalogModelViewModel` from `llmCatalogService.ts` |
| **Model Name** | Composite string identifying a model: "provider_type:model" e.g., "openai:gpt-4o-mini" | `AgentViewModel.model_name` |
| **System Provider** | Backend-configured fallback credentials. Should NOT be used by non-superusers. | Backend config (not a VM) |
| **Empty Provider** | provider_type: "empty" with user_provider: null. Indicates agent has no configured access. | Used when user has no provider configured |

### Common Confusion Points

- **"Provider" alone is ambiguous** - always specify "User Provider" or "Provider Type"
- **model_name contains provider_type as prefix** - they must match
- **user_provider is a UUID reference**, provider_type is an enum value
- **"empty" provider_type ≠ null user_provider** - both should be set together

---

## Control Flow: Adding a User Provider

**Entry Point:** User Settings → LLM Providers tab
**File:** `src/components/UserSettings/LLMProviders.tsx`

```
STEP 1: User clicks "Add Provider"
  File: LLMProviders.tsx
  Action: setIsAddingProvider(true) → opens inline form
            │
            ▼
STEP 2: User fills form
  File: LLMProviders.tsx (AddProviderForm section)
  Fields:
    • provider_type: Select (openai|anthropic|google|openai_compatible)
    • name: Input (required)
    • api_key: Input[password] (required)
    • base_url: Input (optional, for openai_compatible)
    • is_default: Checkbox
    • description: Textarea (optional)
            │
            ▼
STEP 3: User clicks "Add"
  File: LLMProviders.tsx
  Validation: name required, api_key required
  Action: createMutation.mutate(newProvider)
            │
            ▼
STEP 4: Service layer
  File: src/services/llmProviderService.ts
  Method: LlmProviderService.createProvider(data)
  Input: CreateProviderInput (UserLLMProviderCreate)
  Output: ProviderViewModel (transformed from backend response)

  Transformation (in transformProvider):
    • Computes status from last_test_success
    • Computes is_usable from is_enabled && status !== "failed"
    • Computes display_type via getProviderTypeLabel()
            │
            ▼
STEP 5: Cache invalidation & UI update
  File: LLMProviders.tsx (onSettled callback)
  Action: queryClient.invalidateQueries(["llm-providers"])
  Result: Provider list re-fetches, new provider appears
            │
            ▼
STEP 6 (Optional): Test provider connection
  File: LLMProviders.tsx
  Action: testMutation.mutate(provider.id)
  Service: LlmProviderService.testProvider(providerId)
  Result: status updates to "verified" or "failed"
```

**Query Keys:** `LLM_PROVIDER_QUERY_KEYS.providers = ["llm-providers"]`

**Post-condition:** New ProviderViewModel available in providers list, can be selected in AgentForm's ProviderSelect dropdown.

---

## Control Flow: Agent Creation

**Entry Point:** "Create Agent" button → CreateAgentDialog
**File:** `src/components/Agents/CreateAgentDialog.tsx`

```
STEP 1: Dialog opens, AgentForm mounts
  File: src/components/Agents/AgentForm.tsx

  Initial State:
    • name: ""
    • slug: "" (then auto-generated via AgentService.generateSlug())
    • selectedProviderId: null
    • modelName: "openai:gpt-4o-mini" (hardcoded default)
    • derivedProviderType: "empty" (computed from null provider)

  Queries triggered:
    • useQuery(LLM_PROVIDER_QUERY_KEYS.providers) → user's providers
    • useLlmCatalog() inside ModelCombobox → catalog models
            │
            ▼
STEP 2: User selects a Provider (ProviderSelect)
  File: src/components/Agents/ProviderSelect.tsx

  Props received:
    • value: selectedProviderId (null initially)
    • providers: ProviderViewModel[] (from useQuery)
    • onChange: handleProviderChange callback

  User action: Selects provider from dropdown
  Callback: onChange(providerId, providerViewModel)
            │
            ▼
STEP 3: handleProviderChange executes
  File: src/components/Agents/AgentForm.tsx

  Logic:
    setSelectedProviderId(providerId)

    // Reset model if incompatible with new provider
    if (provider) {
      const currentModelType = parseProviderFromModelName(modelName)
      if (currentModelType !== provider.provider_type) {
        setModelName("")  // ◄── RESETS MODEL TO EMPTY
      }
    }

  State after:
    • selectedProviderId: <UUID>
    • selectedProvider: ProviderViewModel (derived)
    • derivedProviderType: provider.provider_type (e.g., "openai")
    • modelName: "" (reset because default was incompatible)
            │
            ▼
STEP 4: ModelCombobox should show filtered models
  File: src/components/Agents/providers/ModelCombobox.tsx

  Props received:
    • value: modelName (now "")
    • onChange: setModelName
    • providerType: selectedProvider?.provider_type (e.g., "openai")

  ⚠️  BUG #1: Model dropdown not populated
  Expected: Show models where model.provider === providerType
  Actual: Dropdown appears empty or shows wrong models
            │
            ▼
STEP 5: User attempts to add custom model (optional path)
  File: src/components/Agents/providers/ModelCombobox.tsx

  ⚠️  BUG #2: Error when adding custom model
  Expected: createCustomModel mutation succeeds, model appears
  Actual: Error displayed in dropdown
            │
            ▼
STEP 6: User fills remaining fields and clicks "Create Agent"
  File: src/components/Agents/CreateAgentDialog.tsx

  formData at this point (from AgentForm onChange):
    {
      name: "My Agent",
      slug: "adj-noun-1234",
      description: "...",
      model_name: "openai:gpt-4o",
      system_prompt: "...",
      participation_mode: "on_mention",
      provider_type: "openai",        ◄── from derivedProviderType
      user_provider: "<UUID>",        ◄── from selectedProviderId
    }
            │
            ▼
STEP 7: handleSubmit builds payload
  File: src/components/Agents/CreateAgentDialog.tsx

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

  ⚠️  BUG #3: Provider not saved
  Expected: Agent created with user_provider = <UUID>
  Actual: Agent created with user_provider = null
            │
            ▼
STEP 8: Service layer
  File: src/services/agentService.ts
  Method: AgentService.createAgent(payload)

  ⚠️  BUG #4: Wrong default for non-superusers
  When user has NO providers and selects "None":
    • provider_type should be: "empty"
    • user_provider should be: null

  Backend behavior (current - WRONG):
    • Falls back to system provider for agent execution
            │
            ▼
STEP 9: Response handling
  File: src/components/Agents/CreateAgentDialog.tsx

  On success:
    • showSuccessToast("Agent created")
    • handleOpenChange(false) - close dialog
    • onSuccess?.(createdAgent)
    • queryClient.invalidateQueries(["agents"])
```

**Files Involved:**
- `CreateAgentDialog.tsx` - Dialog wrapper, submit handling
- `AgentForm.tsx` - Form state, provider/model selection
- `ProviderSelect.tsx` - Provider dropdown
- `ModelCombobox.tsx` - Model selection with filtering
- `agentService.ts` - API call, response transformation
- `llmProviderService.ts` - Provider data fetching
- `llmCatalogService.ts` - Model catalog (via useLlmCatalog hook)

---

## Control Flow: Agent Cloning

**Entry Point:** Agent card/detail → "Clone" button
**File:** `src/components/Agents/AgentCloneButton.tsx`

```
STEP 1: User clicks "Clone" on an agent
  File: AgentCloneButton.tsx

  Props received:
    • agent: AgentViewModel (the source agent to clone)

  Source agent may be:
    • System agent (scope: "system") - no user_provider
    • Personal agent (scope: "personal") - may have user_provider
            │
            ▼
STEP 2: Dialog mounts, generates new slug
  File: AgentCloneButton.tsx

  useEffect: AgentService.generateSlug() → sets newSlug state

  Initial state:
    • newName: `${agent.name} (Copy)`
    • newSlug: <auto-generated>
            │
            ▼
STEP 3: User edits name/slug (optional) and clicks "Clone Agent"
  File: AgentCloneButton.tsx

  Validation:
    • newName.trim() required
    • newSlug.trim() required
            │
            ▼
STEP 4: handleClone builds payload
  File: AgentCloneButton.tsx

  CURRENT IMPLEMENTATION:
  ┌─────────────────────────────────────────────────────────────────┐
  │ const payload: CreateAgentInput = {                             │
  │   name: newName.trim(),                                         │
  │   slug: newSlug.trim(),                                         │
  │   description: agent.description,          ✓ copied             │
  │   model_name: agent.model_name,            ✓ copied             │
  │   system_prompt: agent.system_prompt,      ✓ copied             │
  │   participation_mode: agent.participation_mode, ✓ copied        │
  │   scope: "personal",                       ✓ always personal    │
  │   is_enabled: true,                        ✓ always enabled     │
  │   // ⚠️  MISSING: provider_type                                 │
  │   // ⚠️  MISSING: user_provider                                 │
  │ }                                                               │
  └─────────────────────────────────────────────────────────────────┘

  ⚠️  GAP: Provider fields not copied
  Current behavior:
    • Cloned agent has NO provider_type or user_provider set
    • Backend may default to system provider (Bug #4 territory)

  Expected behavior options:
    A) Copy provider settings from source (if user owns that provider)
    B) Default to "empty" (user must configure provider later)
    C) Show provider selector in clone dialog (like AgentForm)
            │
            ▼
STEP 5: Mutation executes
  File: AgentCloneButton.tsx

  cloneMutation.mutate(payload)
    → AgentService.createAgent(payload)
    → Backend creates new agent

  On success:
    • showSuccessToast(`Cloned as "${clonedAgent.name}"`)
    • handleOpenChange(false)
    • onSuccess?.(clonedAgent)
    • queryClient.invalidateQueries(["agents"])
```

### Clone vs Create Comparison

| Field | Create (AgentForm) | Clone (AgentCloneButton) |
|-------|-------------------|-------------------------|
| name | User enters | "${source.name} (Copy)" |
| slug | Auto-generated | Auto-generated |
| description | User enters | Copied from source |
| model_name | User selects | Copied from source |
| system_prompt | User enters | Copied from source |
| participation_mode | User selects | Copied from source |
| provider_type | Derived from provider | ⚠️ NOT SET |
| user_provider | User selects | ⚠️ NOT SET |
| scope | "personal" | "personal" |
| is_enabled | true | true |

---

## Control Flow: Agent Editing

**Entry Point:** Agent card/detail → "Edit" button
**File:** `src/components/Agents/EditAgentDialog.tsx`

```
STEP 1: User clicks "Edit" on a personal agent
  File: EditAgentDialog.tsx

  Props received:
    • agent: AgentViewModel (the agent to edit)

  Pre-conditions:
    • Only personal agents can be edited (system agents are read-only)
    • canEditAgent(agent, currentUserId, isSuperuser) must be true
            │
            ▼
STEP 2: AgentForm mounts with initialData
  File: src/components/Agents/AgentForm.tsx

  Props:
    • initialData: agent (AgentViewModel)
    • isEditMode: true

  Initial state (from initialData):
    • name: agent.name
    • slug: agent.slug (read-only in edit mode)
    • description: agent.description
    • modelName: agent.model_name
    • systemPrompt: agent.system_prompt
    • participationMode: agent.participation_mode
    • selectedProviderId: agent.user_provider ◄── pre-selects provider

  Derived values:
    • selectedProvider: found from providers by selectedProviderId
    • derivedProviderType: selectedProvider?.provider_type ?? "empty"
            │
            ▼
STEP 3: ProviderSelect shows current provider (if any)
  File: src/components/Agents/ProviderSelect.tsx

  Display:
    • If agent.user_provider exists → shows that provider selected
    • If agent.user_provider is null → shows "None (use system default)"

  ⚠️  EDGE CASE: Provider no longer exists
  If agent.user_provider references a deleted provider:
    • selectedProvider will be null (not found in providers list)
    • Dropdown may show stale UUID or "None"
    • Should show warning: "Configured provider no longer available"
            │
            ▼
STEP 4: ModelCombobox shows current model, filtered by provider
  File: src/components/Agents/providers/ModelCombobox.tsx

  Behavior:
    • Shows current model_name as selected
    • Filters dropdown to selectedProvider's type (if provider set)
    • Shows all models if no provider selected

  Same potential bugs as create mode (Bug #1, Bug #2)
            │
            ▼
STEP 5: User makes changes and clicks "Save Changes"
  File: EditAgentDialog.tsx
            │
            ▼
STEP 6: handleSubmit builds DELTA payload (only changed fields)
  File: EditAgentDialog.tsx

  const payload: UpdateAgentInput = {}

  // Only include fields that changed:
  if (formData.name.trim() !== agent.name)
    payload.name = formData.name.trim()

  if (formData.description !== agent.description)
    payload.description = formData.description || null

  if (formData.model_name !== agent.model_name)
    payload.model_name = formData.model_name

  if (formData.system_prompt !== agent.system_prompt)
    payload.system_prompt = formData.system_prompt || null

  if (formData.participation_mode !== agent.participation_mode)
    payload.participation_mode = formData.participation_mode

  if (formData.provider_type !== agent.provider_type)
    payload.provider_type = formData.provider_type

  if (formData.user_provider !== agent.user_provider)
    payload.user_provider = formData.user_provider

  // Validation: at least one field must change
  if (Object.keys(payload).length === 0) {
    showErrorToast("No changes to save")
    return
  }
            │
            ▼
STEP 7: Service layer
  File: src/services/agentService.ts
  Method: AgentService.updateAgent(agent.id, payload)
  Returns: Updated AgentViewModel
            │
            ▼
STEP 8: Response handling
  File: EditAgentDialog.tsx

  On success:
    • showSuccessToast(`Agent "${updatedAgent.name}" updated`)
    • handleOpenChange(false)
    • onSuccess?.(updatedAgent)
    • queryClient.invalidateQueries(["agents"])
    • queryClient.invalidateQueries(["agent", agent.id])
```

### Edit vs Create Differences

| Aspect | Create | Edit |
|--------|--------|------|
| Initial state | Empty/defaults | From existing agent |
| Slug | Auto-generated | Read-only (cannot change) |
| Payload | All fields | Only changed fields (delta) |
| API method | createAgent | updateAgent |
| Cache invalidation | ["agents"] | ["agents"], ["agent", id] |

---

## Known Issues & Fixes

### Bug #1: Model dropdown not populated after provider selection

**Symptom:** User selects a provider in AgentForm → ModelCombobox shows empty or does not filter to the selected provider's models

**Affected Flows:** Agent Create, Agent Edit

**Root Cause Investigation:**

1. `AgentForm.tsx` (~line 195) - Check providerType prop passed to ModelCombobox
   - Verify: `selectedProvider?.provider_type` is correct value

2. `ModelCombobox.tsx` - Check filtering logic
   - Verify: `useLlmCatalog().modelsByProvider[providerType]` works
   - Check: Is providerType prop being used in the filter?

3. `useLlmCatalog.ts` - Check modelsByProvider structure
   - Verify: Keys match LLMProviderType enum values exactly
   - Check: "openai" vs "OpenAI" case sensitivity

**Fix Location:** `src/components/Agents/providers/ModelCombobox.tsx`

**Verification:**
- [ ] Select provider → models filter to that type
- [ ] Select "None" → all models shown
- [ ] Change provider → models update accordingly

---

### Bug #2: Error when adding custom model in agent create

**Symptom:** User types custom model → clicks "Add as custom model" → error shown

**Affected Flows:** Agent Create, Agent Edit (custom model path)

**Root Cause Investigation:**

1. `ModelCombobox.tsx` - Check createCustomModel call
   - Verify: What params are passed to mutation?

2. `useLlmCatalog.ts` - Check createCustomModel mutation
   - Required params: modelId, displayName, providerId
   - Question: Which providerId is used?
     - selectedProvider?.id (user's provider)?
     - A catalog provider id?
     - null/undefined (causing the error)?

3. `llmCatalogService.ts` - Check createCustomModel API
   - Check: Backend validation requirements

**Likely Cause:** providerId is required by backend but not being passed correctly when user has selected a UserProvider (which is different from a CatalogProvider)

**Fix Location:**
- `src/components/Agents/providers/ModelCombobox.tsx`
- `src/hooks/useLlmCatalog.ts` (if mutation params wrong)

**Verification:**
- [ ] Type custom model name → "Add" option appears
- [ ] Click "Add" → model created successfully
- [ ] New model appears in dropdown and is selectable

---

### Bug #3: Provider not saved when creating agent

**Symptom:** User selects provider → creates agent → agent has user_provider=null

**Affected Flows:** Agent Create

**Root Cause Investigation:**

1. `AgentForm.tsx` - Check onChange callback
   - Verify: `user_provider: selectedProviderId` is included
   - Check: Is selectedProviderId state updating correctly?

2. `CreateAgentDialog.tsx` - Check formData at submit time
   - Add console.log(formData) before payload construction
   - Verify: formData.user_provider has the UUID

3. `CreateAgentDialog.tsx` - Check payload construction
   - Verify: `user_provider: formData.user_provider` is present

4. `agentService.ts` - Check createAgent payload
   - Verify: user_provider is passed to AgentConfigCreate

5. Network tab - Check actual API request
   - Verify: user_provider field in request body

**Fix Location:** Depends on where the value is lost in the chain

**Verification:**
- [ ] Select provider → create agent → agent.user_provider = UUID
- [ ] Edit created agent → provider dropdown shows correct selection
- [ ] API request contains user_provider field

---

### Bug #4: Non-superusers default to system provider instead of "empty"

**Symptom:** User with no providers creates agent → agent can invoke LLM using system-configured credentials (should not be allowed)

**Affected Flows:** Agent Create, Agent Clone

**Root Cause:** Backend falls back to system provider when:
- provider_type is not "empty", OR
- provider_type is missing/null

**Frontend Responsibility:** Ensure `provider_type: "empty"` is sent when:
- User selects "None" in ProviderSelect
- User has no providers configured
- Cloning an agent (currently missing provider fields)

**Investigation Points:**

1. `AgentForm.tsx` - Check derivedProviderType
   - When selectedProviderId is null: derivedProviderType should be "empty"
   - Verify this value flows to formData.provider_type

2. `CreateAgentDialog.tsx` - Check payload
   - When no provider selected: `provider_type: "empty"`, `user_provider: null`

3. `AgentCloneButton.tsx` - Add provider fields
   - Currently MISSING provider_type and user_provider
   - Should set `provider_type: "empty"`, `user_provider: null`

**Fix Locations:**
- `src/components/Agents/AgentCloneButton.tsx` (add provider fields)
- Backend: Reject/restrict agents with non-empty provider_type when user doesn't own a matching provider

**Verification:**
- [ ] Create agent with "None" → provider_type: "empty" in API call
- [ ] Clone agent → provider_type: "empty" in API call
- [ ] Agent with provider_type: "empty" cannot invoke LLM
- [ ] Non-superuser cannot create agent with real provider_type unless they own a matching user_provider

---

### Bug Dependency Chain

```
Bug #1 (models not shown) ──► may cause ──► Bug #2 (custom model error)

Bug #3 (provider not saved) ──► may mask ──► Bug #4 (wrong default)
```

**Recommended Fix Order:**
1. Bug #3 - Fix provider saving (foundation for other fixes)
2. Bug #1 - Fix model dropdown population
3. Bug #2 - Fix custom model creation
4. Bug #4 - Add provider fields to clone + backend validation

---

## Validation Rules

### Frontend Validation (AgentForm / Dialogs)

| Field | Rule | Location |
|-------|------|----------|
| name | Required, non-empty trim | CreateAgentDialog, EditAgentDialog |
| slug | Required, auto-generated (read-only in edit) | CreateAgentDialog |
| model_name | Should match provider_type prefix if provider selected | AgentForm (handleProviderChange) |
| provider_type | Must be valid enum value, "empty" if no provider | AgentForm (derivedProviderType) |
| user_provider | Must be null when provider_type is "empty", Must be valid UUID when provider_type is not "empty" | AgentForm |

### Consistency Rules

| Rule | Enforced Where | Status |
|------|----------------|--------|
| model_name prefix must match provider_type | AgentForm handleProviderChange | ✓ Implemented (resets model) |
| provider_type="empty" requires user_provider=null | AgentForm derivedProviderType logic | ✓ Implemented |
| provider_type!="empty" requires valid user_provider UUID | NOT ENFORCED | ⚠️ MISSING |
| user_provider must reference a provider owned by current user | NOT ENFORCED (frontend) | ⚠️ MISSING (backend should check) |
| Non-superuser cannot use system provider fallback | NOT ENFORCED | ⚠️ MISSING (Bug #4) |

### Expected State Combinations

| Scenario | provider_type | user_provider | Valid? |
|----------|---------------|---------------|--------|
| No provider selected | "empty" | null | ✓ |
| User's OpenAI provider | "openai" | \<UUID\> | ✓ |
| User's Anthropic provider | "anthropic" | \<UUID\> | ✓ |
| Provider type without user_provider | "openai" | null | ✗ INVALID |
| Mismatched type and provider | "openai" | \<anthropic provider\> | ✗ INVALID |
| Empty type with provider set | "empty" | \<UUID\> | ✗ INVALID |

### Validation Gaps to Address

1. **PRE-SUBMIT VALIDATION (Frontend)**
   - Location: `CreateAgentDialog.tsx`, `EditAgentDialog.tsx`
   - Add check: If `provider_type !== "empty" && !user_provider` → error

2. **CLONE VALIDATION (Frontend)**
   - Location: `AgentCloneButton.tsx`
   - Add: Explicit `provider_type: "empty"`, `user_provider: null`

3. **PROVIDER TYPE CONSISTENCY (Frontend)**
   - Location: `AgentForm.tsx`
   - Ensure: provider_type always derived from selected provider
   - Never: Allow manual provider_type that doesn't match user_provider

4. **BACKEND ENFORCEMENT (Backend - out of scope for this doc)**
   - Reject agents where provider_type !== "empty" and user doesn't own a provider matching user_provider
   - Never fall back to system provider for non-superusers

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `src/services/llmProviderService.ts` | User provider CRUD, resolution logic, filtering |
| `src/services/llmCatalogService.ts` | System model catalog, custom model creation |
| `src/services/agentService.ts` | Agent CRUD, agent transformation |
| `src/hooks/useLlmProviders.ts` | Hook for provider operations |
| `src/hooks/useLlmCatalog.ts` | Hook for catalog access |
| `src/components/Agents/CreateAgentDialog.tsx` | Dialog for creating new agents |
| `src/components/Agents/EditAgentDialog.tsx` | Dialog for editing agents |
| `src/components/Agents/AgentForm.tsx` | Shared form for agent creation/edit |
| `src/components/Agents/AgentCloneButton.tsx` | Clone system agents as personal |
| `src/components/Agents/ProviderSelect.tsx` | Provider dropdown selector |
| `src/components/Agents/providers/ModelCombobox.tsx` | Advanced model selector with custom creation |
| `src/components/UserSettings/LLMProviders.tsx` | User settings page for provider management |

---

## Query Keys Reference

| Key | Location | Usage |
|-----|----------|-------|
| `["llm-providers"]` | `LLM_PROVIDER_QUERY_KEYS.providers` | User's configured providers |
| `["llm-catalog", "models", "grouped"]` | `LLM_CATALOG_QUERY_KEYS.modelsGrouped` | Catalog models by provider |
| `["agents"]` | Agent list queries | All agents accessible to user |
| `["agent", id]` | Single agent queries | Specific agent by ID |
