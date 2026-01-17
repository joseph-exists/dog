
  Key Features:
  - Service layer with ProviderViewModel and UserAgentSettingsViewModel following established patterns
  - Composable ProviderModelSelector component for reuse across create/edit/settings
  - Clear visual distinction between "System Default" and "Your API Key"
  - Extensibility hooks for future rules, usage tracking, and cost estimation

  Backend Requirements:
  - None blocking - existing endpoints are sufficient
  - Nice to have: GET /api/v1/llm-providers/supported-models endpoint for dynamic model lists

  Implementation: 10 files across 5 phases, building from service foundation up to integrated components.

─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 Ready to code?

 Here is Claude's plan:
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
 Agent Provider Selector & LlmProviderService - Frontend Architecture

 Overview

 Design a frontend-centric architecture for managing LLM providers and allowing users to customize which provider/model agents
 use. The design prioritizes extensibility for future features (rulesets, conditionals, usage tracking) while following
 established patterns.

 ---
 Requirements Summary

 From frontend/src/components/Agents/current-agent-provider-selector.md:

 1. Users can have multiple API keys per provider type (or none - fallback to system)
 2. Per-agent provider/model selection stored in UserAgentSettings
 3. Different agents can use different providers/models in the same room
 4. Shared agents show original config but others can customize via clone
 5. Model changes trigger ShadowClone/version updates (backend concern)
 6. Design must be extensible for future rulesets/conditionals

 ---
 Current State

 Working Infrastructure

 - LLMProviders.tsx - Provider management UI (add/test/delete)
 - UserLLMProvider backend model with test status tracking
 - UserAgentSettings backend model (model_name_override, provider_id, custom_system_prompt)
 - LlmProvidersService SDK endpoints (CRUD + test)
 - AgentsService.getMyAgentSettings/updateMyAgentSettings endpoints

 Gaps to Fill

 - AgentModelSettings.tsx - Empty stub file
 - AgentProviderSelector.tsx - Empty stub file
 - AgentForm.tsx - Hardcoded AVAILABLE_MODELS (marked "BAD BAD BAD")
 - No llmProviderService.ts - missing ViewModel layer
 - No centralized model list management

 ---
 Architecture Design

 1. Service Layer: llmProviderService.ts

 Following agentService.ts patterns with ViewModels and transformations.

 ViewModels:

 export type LLMProviderType = "openai" | "anthropic" | "google" | "openai_compatible"

 export interface ModelOption {
   value: string           // "openai:gpt-4o"
   label: string           // "GPT-4o"
   description: string     // "Latest multimodal flagship"
   provider: LLMProviderType
 }

 export interface ProviderViewModel {
   id: string
   name: string
   provider_type: LLMProviderType
   base_url: string | null
   is_enabled: boolean
   is_default: boolean
   created_at: Date
   updated_at: Date
   last_tested_at: Date | null
   last_test_success: boolean | null

   // Computed fields
   display_type: string                    // "OpenAI", "Anthropic", etc.
   status: "verified" | "failed" | "unknown"
   compatible_models: ModelOption[]
   is_usable: boolean                      // is_enabled && status !== "failed"
 }

 export interface UserAgentSettingsViewModel {
   id: string
   agent_config_id: string
   model_name_override: string | null
   provider_id: string | null
   custom_system_prompt: string | null
   is_favorite: boolean
   created_at: Date
   updated_at: Date

   // Computed fields
   is_using_system_default: boolean
 }

 // Resolution result for "what provider/model is this agent actually using?"
 export interface ProviderResolution {
   mode: "system_default" | "user_provider"
   provider: ProviderViewModel | null
   model: string
   model_display: string
   status: "verified" | "failed" | "unknown" | "system"
 }

 Service API:

 export const LlmProviderService = {
   // Provider CRUD (wraps SDK)
   listProviders(): Promise<PaginatedProviders>
   getProvider(providerId: string): Promise<ProviderViewModel>
   createProvider(data: CreateProviderInput): Promise<ProviderViewModel>
   updateProvider(providerId: string, data: UpdateProviderInput): Promise<ProviderViewModel>
   deleteProvider(providerId: string): Promise<void>
   testProvider(providerId: string): Promise<TestResult>

   // Model operations
   getSupportedModels(): SupportedModelsMap  // Static until backend endpoint exists
   getModelsForProvider(providerType: LLMProviderType): ModelOption[]
   extractProviderType(modelName: string): LLMProviderType | null

   // User agent settings
   getAgentSettings(agentId: string): Promise<UserAgentSettingsViewModel | null>
   updateAgentSettings(agentId: string, data: UpdateSettingsInput): Promise<UserAgentSettingsViewModel>
   deleteAgentSettings(agentId: string): Promise<void>

   // Resolution helpers
   resolveProviderForAgent(
     agent: AgentViewModel,
     settings: UserAgentSettingsViewModel | null,
     providers: ProviderViewModel[]
   ): ProviderResolution

   // Filtering utilities
   filterByType(providers: ProviderViewModel[], type: LLMProviderType): ProviderViewModel[]
   filterEnabled(providers: ProviderViewModel[]): ProviderViewModel[]
   getDefaultForType(providers: ProviderViewModel[], type: LLMProviderType): ProviderViewModel | null
 }

 2. Model List Strategy

 Immediate: Embed SUPPORTED_MODELS constant in service (mirrors backend models.py)

 const SUPPORTED_MODELS: SupportedModelsMap = {
   openai: [
     { value: "openai:gpt-4o", label: "GPT-4o", description: "Latest flagship" },
     { value: "openai:gpt-4o-mini", label: "GPT-4o Mini", description: "Fast & affordable" },
     // ... from backend SUPPORTED_MODELS
   ],
   anthropic: [...],
   google: [...],
   openai_compatible: [
     { value: "openai_compatible:custom", label: "Custom Model", description: "Specify in settings" }
   ]
 }

 Future: Backend endpoint GET /api/v1/llm-providers/supported-models returns dynamic list.

 3. Hooks

 useLlmProviders.ts:
 function useLlmProviders(): {
   providers: ProviderViewModel[]
   isLoading: boolean
   enabledProviders: ProviderViewModel[]
   defaultByType: Record<LLMProviderType, ProviderViewModel | null>
   hasAnyProvider: boolean
   refresh: () => void
 }

 useAgentSettings.ts:
 function useAgentSettings(agentId: string): {
   settings: UserAgentSettingsViewModel | null
   isLoading: boolean
   effectiveModel: string
   effectiveModelDisplay: string
   isUsingSystemDefault: boolean
   provider: ProviderViewModel | null
   updateSettings: (data: Partial<UpdateSettingsInput>) => Promise<void>
   resetToDefaults: () => Promise<void>
   isUpdating: boolean
 }

 4. Components

 New Component: ProviderModelSelector.tsx

 Core composable component for selecting provider and model.

 interface ProviderModelSelectorProps {
   providerId: string | null              // null = system default
   modelName: string | null               // null = use agent default
   agentDefaultModel: string              // Context: what model does agent default to
   onProviderChange: (providerId: string | null) => void
   onModelChange: (modelName: string | null) => void
   showModelOverride?: boolean            // Default: true
   showProviderStatus?: boolean           // Default: true
   disabled?: boolean
   size?: "default" | "compact"
 }

 Behavior:
 1. "System Default" option always available
 2. User's providers grouped by type with verification badges
 3. Model dropdown filtered by selected provider's type
 4. Clear visual distinction: system default vs user provider

 Implement: AgentModelSettings.tsx

 Full settings panel for agent detail page "My Settings" tab.

 - Provider selection via ProviderModelSelector
 - Model override toggle
 - Custom system prompt textarea
 - Favorite toggle
 - Save/Reset buttons

 Implement: AgentProviderSelector.tsx

 Lightweight provider-only selector for inline use (e.g., room settings).

 Update: AgentForm.tsx

 Replace hardcoded AVAILABLE_MODELS with ProviderModelSelector integration.

 5. Visual Design

 System Default State:
 ┌─────────────────────────────────────┐
 │ Provider: [System Default ▾]        │
 │ ┌─────────────────────────────────┐ │
 │ │ ○ Using system API key          │ │
 │ │   Model: GPT-4o Mini            │ │
 │ └─────────────────────────────────┘ │
 └─────────────────────────────────────┘

 User Provider State:
 ┌─────────────────────────────────────┐
 │ Provider: [My OpenAI ▾]    ✓ Verified│
 │ Model: [GPT-4o ▾]                   │
 │ ┌─────────────────────────────────┐ │
 │ │ 🔑 Using your API key           │ │
 │ └─────────────────────────────────┘ │
 └─────────────────────────────────────┘

 ---
 Backend Requirements

 Required (Blocking)

 None - existing endpoints are sufficient for MVP.

 Requested (Nice to Have)

 1. GET /api/v1/llm-providers/supported-models
   - Returns SUPPORTED_MODELS from backend
   - Allows model list updates without frontend deployment
   - Response: { models_by_provider: Record<LLMProviderType, ModelInfo[]> }
 2. Extend UserAgentSettings response with resolution:
   - Include resolved provider name when provider_id is set
   - Include effective model (override or agent default)
   - Saves frontend from multiple queries to resolve

 Future Considerations (Extensibility)

 The architecture is designed to accommodate these without breaking changes:

 1. Usage Tracking - Add usage_metrics to provider/settings
 2. Cost Estimation - Add estimated_cost to model options
 3. Provider Rules - Add rules array to settings with conditions/actions
 4. Rate Limits - Add rate_limit_status to provider

 ---
 Query Keys

 const QUERY_KEYS = {
   providers: ["llm-providers"],
   provider: (id: string) => ["llm-providers", id],
   supportedModels: ["llm-supported-models"],
   agentSettings: (agentId: string) => ["agent-settings", agentId],
 }

 ---
 Implementation Plan

 Phase 1: Service Foundation

 1. Create src/services/llmProviderService.ts
   - ViewModels and transformations
   - SUPPORTED_MODELS constant
   - Provider CRUD wrappers
   - Agent settings wrappers

 Phase 2: Hooks

 2. Create src/hooks/useLlmProviders.ts
 3. Create src/hooks/useAgentSettings.ts

 Phase 3: Core Components

 4. Create src/components/Agents/providers/ProviderStatusBadge.tsx
 5. Create src/components/Agents/providers/ProviderModelSelector.tsx

 Phase 4: Integration

 6. Implement src/components/Agents/AgentModelSettings.tsx
 7. Implement src/components/Agents/AgentProviderSelector.tsx
 8. Update src/components/Agents/AgentForm.tsx - remove hardcoded models

 Phase 5: Polish

 9. Update barrel exports in src/components/Agents/index.ts
 10. Add SystemDefaultIndicator.tsx for clear visual feedback

 ---
 Files to Create/Modify
 ┌───────────────────────────────────────────────────────────┬───────────┬───────────────────────────────┐
 │                           File                            │  Action   │            Purpose            │
 ├───────────────────────────────────────────────────────────┼───────────┼───────────────────────────────┤
 │ src/services/llmProviderService.ts                        │ CREATE    │ Service layer with ViewModels │
 ├───────────────────────────────────────────────────────────┼───────────┼───────────────────────────────┤
 │ src/hooks/useLlmProviders.ts                              │ CREATE    │ Provider data hook            │
 ├───────────────────────────────────────────────────────────┼───────────┼───────────────────────────────┤
 │ src/hooks/useAgentSettings.ts                             │ CREATE    │ Agent settings hook           │
 ├───────────────────────────────────────────────────────────┼───────────┼───────────────────────────────┤
 │ src/components/Agents/providers/ProviderStatusBadge.tsx   │ CREATE    │ Status indicator              │
 ├───────────────────────────────────────────────────────────┼───────────┼───────────────────────────────┤
 │ src/components/Agents/providers/ProviderModelSelector.tsx │ CREATE    │ Core selector                 │
 ├───────────────────────────────────────────────────────────┼───────────┼───────────────────────────────┤
 │ src/components/Agents/AgentModelSettings.tsx              │ IMPLEMENT │ Full settings panel           │
 ├───────────────────────────────────────────────────────────┼───────────┼───────────────────────────────┤
 │ src/components/Agents/AgentProviderSelector.tsx           │ IMPLEMENT │ Inline selector               │
 ├───────────────────────────────────────────────────────────┼───────────┼───────────────────────────────┤
 │ src/components/Agents/AgentForm.tsx                       │ MODIFY    │ Use dynamic models            │
 ├───────────────────────────────────────────────────────────┼───────────┼───────────────────────────────┤
 │ src/components/Agents/index.ts                            │ MODIFY    │ Export new components         │
 └───────────────────────────────────────────────────────────┴───────────┴───────────────────────────────┘
 ---
 Verification

 1. Type Check: npx tsc --noEmit passes
 2. Lint: npm run lint passes
 3. Manual Testing:
   - Create agent with custom model selection
   - Configure provider in user settings
   - Select user provider for agent in "My Settings"
   - Verify "System Default" vs "Your API Key" indicators
   - Test with 0 providers (system default only)
   - Test with multiple providers of same type
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌

 Requested permissions:
   · Bash(prompt: run TypeScript type check)
   · Bash(prompt: run linter)

 Would you like to proceed?