# agentService.ts - Systems Review & Recommendations

## Date: 2026-01-29
## Context: UserAccessProvider refactor - aligning ontology across frontend services

---

## ARCHITECTURAL UNDERSTANDING

### The Three-Way Binding Pattern

For a `UserAgentConfig` to produce a working `Agent`, three components must align:

```
UserAgentConfig
├── user_access_provider (UUID) ──> UserAccessProvider (WHERE: endpoint + credentials)
├── provider_type (string) ────────> LLMProviderType (HOW: API message format)
└── model_name (string) ───────────> Model (WHAT: the actual LLM)
```

**Validation Requirements:**
1. ✓ UserAccessProvider must exist, be enabled, and have valid credentials
2. ✓ ProviderType must match the API spec that UserAccessProvider expects
3. ✓ Model must be available at that UserAccessProvider endpoint
4. ✓ Model must support that ProviderType's message format

**Failure Modes (from lines 19-33):**
- No UserAccessProvider → No API to connect to
- Wrong ProviderType:UserAccessProvider → API can't parse messages
- Wrong ProviderType:Model → Model can't process message format
- Wrong UserAccessProvider:Model → API rejects (model not available)

---

## CURRENT STATE ASSESSMENT

### Generated Client Types (source of truth)

From `frontend/src/client/types.gen.ts`:

```typescript
export type UserAgentConfigPublic = {
  id: string
  name?: string | null
  slug?: string | null
  description?: string | null
  user_access_provider?: string | null        // UUID reference to UserAccessProvider
  provider_type?: string | null               // API spec type (openai, anthropic, etc.)
  model_id?: string | null                    // Model identifier
  model_name?: string | null                  // Full model name (may include provider prefix)
  system_prompt?: string | null
  custom_system_prompt?: string | null        // User override
  instructions?: string | null
  tool_config?: Record<string, unknown> | null
  deps_config?: Record<string, unknown> | null
  agent_metadata?: Record<string, unknown> | null
  is_enabled?: boolean | null
  is_clonable?: boolean | null
  is_visible?: boolean | null
  scope?: string | null                       // "system" | "personal"
  participation_mode?: string | null          // "always" | "on_mention" | "manual"
  is_coordinator?: boolean | null
  max_tool_iterations?: number | null
  capabilities?: Array<string> | null
  owner_id: string | null
  created_at: string
  updated_at: string | null
  version: number
}
```

---

## CRITICAL ISSUES

### 🔴 PRIORITY 1: Inconsistent Field Naming
[x] fixed

---

### 🔴 PRIORITY 1: Wrong Input Type in transformAgent

[x] Fixed.
---

### 🟡 PRIORITY 2: Missing Fields in transformAgent

[x] fixed.
---

### 🟡 PRIORITY 2: AgentViewModel Alignment with Backend

**Problem:** AgentViewModel fields don't fully match UserAgentConfigPublic

**Backend has, Frontend AgentViewModel missing:**
- `model_id` - separate from model_name
- `custom_system_prompt` - user override for system_prompt
- `instructions` - large text field
- `is_clonable` - whether config can be cloned
- `is_visible` - visibility setting
- `max_tool_iterations` - iteration limit

**Recommendation:**
- **Decision: Option A**: Add missing fields to AgentViewModel for completeness (these are currently being requested by the design team ASAP)
- **Option B**: Document that AgentViewModel is a slim view, add RichAgentViewModel for full data
- **Option C (Recommended)**: Add fields incrementally as UI features need them

**Justification for Option C:**
- Follows ViewModel pattern (UI-optimized, not 1:1 with backend)
- Keeps service layer focused
- Add fields only when UI components need them
- Prevents premature optimization

---

### 🟢 PRIORITY 3: Remove display_model Computed Field

**Problem:** Line 68, 80, 167 - TODO says remove display_model but it's still implemented

**Current:**
```typescript
export interface AgentViewModel {
  model_name: string
  display_model: string  // TODO: remove the display_model compute, it's clutter.
  // ...
}
```

**Decision: all Recommendations accepted:**

- Remove from AgentViewModel interface (line 80)
- Remove from transformAgent (line 167)
- Remove formatModelName function 

- UI components will handle display formatting via llmCatalogService

**Justification:**
- Service layer shouldn't handle display logic
- Catalog service already has model display capabilities
- Simplifies ViewModel
- Separation of concerns

---

## RECOMMENDATIONS FOR IMPROVEMENT

### 1. Add Inline Documentation for Three-Way Binding

**Location:** After line 33 (after REMEMBER comments)

**Add:**
```typescript
// ARCHITECTURE SUMMARY:
//
// UserAgentConfig stores THREE critical associations:
//   1. user_access_provider (UUID) → Which UserAccessProvider entity to use
//   2. provider_type (string)      → Which API specification format (openai, anthropic, etc.)
//   3. model_name (string)         → Which model to request
//
// When an Agent is instantiated from a UserAgentConfig:
//   - user_access_provider provides: base_url, api_key (WHERE and WITH WHAT CREDENTIALS)
//   - provider_type provides: message format, API schema (HOW to structure requests)
//   - model_name provides: which model to invoke (WHAT to talk to)
//
// All three must be mutually compatible or the Agent will fail.
```

---

### 2. Add Validation Note to AgentViewModel

**Location:** Line 73-74 (before AgentViewModel interface)

**Add:**
```typescript
/**
 * AgentViewModel
 *
 * UI-optimized view of UserAgentConfig. This is NOT the Agent itself -
 * it's the configuration template used to instantiate runtime Agents.
 *
 * Critical Associations:
 * - user_access_provider: UUID reference to UserAccessProvider (the access channel)
 * - provider_type: LLMProviderType (the API message format)
 * - model_name: string (the model identifier)
 *
 * ⚠️  VALIDATION: When using this config to create an Agent, validate:
 *     1. UserAccessProvider exists and is enabled
 *     2. ProviderType matches what UserAccessProvider supports
 *     3. Model is available at UserAccessProvider and supports ProviderType
 *
 * See userAccessProviderService for validation utilities (TODO: implement)
 *
 * Transformations from backend UserAgentConfigPublic:
 * - Provides strict union types for scope and participation_mode
 * - Normalizes nullable fields
 * - Parses ISO timestamp strings to Date objects
 * - TODO: Remove display_model (should be handled by UI components)
 */
```

---

### 3. Add Comment to transformAgent Function

**Location:** Line 159 (before transformAgent function)

**Add:**
```typescript
/**
 * Transform backend UserAgentConfigPublic to AgentViewModel
 *
 * ⚠️  INPUT TYPE: Must be UserAgentConfigPublic (API response), NOT UserAgentConfigUpdate
 *
 * Transformations:
 * - Parses created_at, updated_at ISO strings to Date objects
 * - Provides defaults for nullable fields
 * - Casts scope and participation_mode to strict union types
 * - TODO: Remove display_model computation
 *
 * @param agent - Backend UserAgentConfigPublic (from API response)
 * @returns Transformed AgentViewModel optimized for UI
 */
```

---

### 4. Add Comments to CreateAgentInput

**Location:** Line 101-112

**Add:**
```typescript
/**
 * Agent creation input
 *
 * ⚠️  THREE-WAY BINDING: When creating an agent, ensure:
 *     - user_access_provider references a valid, enabled UserAccessProvider
 *     - provider_type matches what that UserAccessProvider supports
 *     - model_name is available at that UserAccessProvider
 *
 * Validation should happen:
 *     - Client-side: Before calling createAgent (via userAccessProviderService utilities)
 *     - Server-side: Backend validates these relationships (will return 400 if invalid)
 */
export interface CreateAgentInput {
  name: string
  slug: string
  description?: string | null
  model_name?: string
  provider_type?: LLMProviderType
  user_access_provider?: string | null  // UUID of UserAccessProvider entity
  system_prompt?: string | null
  participation_mode?: ParticipationMode
  scope?: AgentScope
  is_enabled?: boolean
}
```

---

### 5. Add Comment to createAgent Method

**Location:** Line 312-335

**Add to line 311 (before createAgent method):**
```typescript
  /**
   * Create a new personal agent
   *
   * System agents can only be created by superusers via backend.
   * Personal agents are owned by the creating user.
   * TODO: Cloning of other user's agents and system agents.
   *
   * ⚠️  VALIDATION REQUIRED BEFORE CALLING:
   *     1. Validate user_access_provider exists and is enabled
   *        → Use: userAccessProviderService.getProvider(id)
   *     2. Validate provider_type is supported by that UserAccessProvider
   *        → Use: userAccessProviderService.validateProviderType(providerId, type)
   *     3. Validate model is available for that UserAccessProvider + ProviderType
   *        → Use: llmCatalogService or userAccessProviderService.getAvailableModels(...)
   *
   *     Backend will return 400 Bad Request if validation fails, but client-side
   *     validation provides better UX.
   *
   * @param data - Agent creation parameters
   * @returns Newly created AgentViewModel
   * @throws ApiError - 400 if validation fails, other server errors
   */
```

---

### 6. Fix Line 313-314 Comment

**Location:** Line 313

**Current:**
```typescript
    // TODO: validate the following against the type again
    // PRI 1
```

**Replace with:**
```typescript
    // Build UserAgentConfigCreate from input
    // Note: Backend validation will ensure user_access_provider + provider_type + model_name
    //       form a valid combination. Client-side validation recommended for better UX.
```

---

### 7. Add Comment to Line 322

**Location:** Line 322

**Current:**
```typescript
      provider_type: providerType, // this is the API spec type
```

**Replace with:**
```typescript
      provider_type: providerType, // LLMProviderType - the API message format spec (e.g., "openai", "anthropic")
```

---

## STRUCTURAL RECOMMENDATIONS

### Consider: Add AgentConfigValidation Utilities

**Location:** After utility functions (after line 472)

**Recommendation:**
```typescript
// ============================================================================
// Validation Utilities (TODO: Move to userAccessProviderService?)
// ============================================================================

/**
 * Validate that a UserAgentConfig has the minimum required fields
 * for Agent instantiation.
 *
 * This is a CLIENT-SIDE check only. Backend performs authoritative validation.
 *
 * @param config - AgentViewModel or CreateAgentInput to validate
 * @returns Object with isValid flag and array of error messages
 */
export function validateAgentConfig(
  config: AgentViewModel | CreateAgentInput
): { isValid: boolean; errors: string[] } {
  const errors: string[] = []

  if (!config.user_access_provider) {
    errors.push("user_access_provider is required - no API endpoint configured")
  }

  if (!config.provider_type) {
    errors.push("provider_type is required - API message format not specified")
  }

  if (!config.model_name) {
    errors.push("model_name is required - no model selected")
  }

  return {
    isValid: errors.length === 0,
    errors
  }
}

/**
 * Check if an AgentConfig appears ready to instantiate
 *
 * @param agent - AgentViewModel to check
 * @returns Whether config has required fields and is enabled
 */
export function isAgentConfigReady(agent: AgentViewModel): boolean {
  return (
    agent.is_enabled &&
    agent.user_access_provider !== null &&
    agent.provider_type !== null &&
    agent.model_name !== null
  )
}
```

**Note:** These might better belong in userAccessProviderService once it's fully implemented,
since that service will have access to UserAccessProvider data for deeper validation.

---

## RELATIONSHIP TO OTHER SERVICES

### Dependencies (Current)

```
agentService.ts
├── Imports from: @/client (generated OpenAPI client)
├── Imports from: llmCatalogService (LLMProviderType type)
└── Should import from: userAccessProviderService (validation, provider resolution)
```

### Expected Flow (After Refactor)

```
User creates/updates agent config in UI
  ↓
UI Component
  ├─→ userAccessProviderService.listProviders()  // Get available access channels
  ├─→ llmCatalogService.getModelsForProviderType()  // Get available models
  ├─→ validateAgentConfig()  // Client-side validation
  └─→ agentService.createAgent()  // Create with validated data
       ↓
     Backend validates three-way binding
       ↓
     Returns UserAgentConfigPublic
       ↓
     transformAgent() → AgentViewModel → UI
```

### Missing Service Methods (In userAccessProviderService)

For agentService to properly validate, userAccessProviderService needs:

1. `validateProviderType(providerId: string, providerType: LLMProviderType): Promise<boolean>`
2. `getAvailableModels(providerId: string, providerType: LLMProviderType): Promise<ModelOption[]>`
3. `resolveEffectiveProvider(agentConfig: AgentViewModel): Promise<ProviderResolution>`
4. `testConfiguration(providerId: string, providerType: string, model: string): Promise<TestResult>`

---

## SUMMARY OF CHANGES REQUIRED

### Immediate (Before Code Compiles)

1. ✅ Fix `UpdateAgentInput.user_provider` → `user_access_provider` (line 122)
2. ✅ Fix `transformAgent` input type to `UserAgentConfigPublic` (line 160)
3. ✅ Add `owner_id` and `created_at` to transformAgent (lines 160-182)
4. ✅ Fix mapping in updateAgent (line 357)

### High Priority (Architectural Clarity)

5. ✅ Add three-way binding documentation comments (after line 33)
6. ✅ Add detailed AgentViewModel documentation (line 73)
7. ✅ Add transformAgent documentation (line 159)
8. ✅ Add CreateAgentInput documentation (line 101)
9. ✅ Add createAgent validation documentation (line 311)

### Medium Priority (Cleanup)

10. ✅ Remove `display_model` field and computation (lines 68, 80, 167)
11. ✅ Remove or relocate `formatModelName` function (line 151)
12. ✅ Update inline comments for clarity (lines 313, 322)

### Low Priority (Future Enhancement)

13. ⏳ Add validation utilities (after line 472)
14. ⏳ Add missing fields from backend to AgentViewModel (as UI needs them)
15. ⏳ Coordinate with userAccessProviderService for validation flow

---

## NOTES

- **ViewModel Pattern**: AgentViewModel should remain UI-optimized, not 1:1 with backend
- **Validation**: Keep service layer thin - validation logic should live in userAccessProviderService
- **Display Logic**: Remove display formatting from this service, use llmCatalogService + UI components
- **Type Safety**: Generated client types are source of truth - align interfaces with them
- **Scope**: This service is purely for CRUD operations on UserAgentConfig entities, NOT runtime Agent management

---

## QUESTIONS FOR CLARIFICATION

1. **Field Naming**: Should we standardize on `user_access_provider_id` (more explicit) vs `user_access_provider` (current)?
2. **Validation Location**: Should validation utilities live in agentService or userAccessProviderService?
3. **AgentViewModel Completeness**: Should we add all backend fields now, or incrementally as UI needs them?
4. **Display Model**: Should formatModelName be deleted entirely or moved to a shared utility?

---

End of review. Generated: 2026-01-29
