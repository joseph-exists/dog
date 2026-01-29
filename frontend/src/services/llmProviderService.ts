/**
 * LLM Provider Service - User Provider Configuration Layer
 *
 * Purpose: Manage user's access provider configurations (API keys, custom endpoints).
 * This service handles UserAccessProvider entities - the user's configured access providers.
 *
 * For the system-wide model catalog (available models, capabilities), use llmCatalogService.
 *
 * Architecture:
 * - Wraps OpenAPI client methods for /llm-providers endpoints
 * - Transforms backend types to ViewModels
 * - Computes derived fields (status, display_type, is_usable)
 * - Provides filtering and resolution utilities
 */


// # deleted classes
// # class UserAgentSettingsBase(SQLModel):
// # ->  into UserAgentConfigBase
// # class UserAgentSettingsCreate(UserAgentSettingsBase):
// # ->  into UserAgentConfigCreate(UserAgentConfigBase)
// # class UserAgentSettingsUpdate(SQLModel):
// # ->  into UserAgentConfigUpdate(SQLModel):
// # class UserAgentConfigSettings(UserAgentSettingsBase, table=True):
// # ->  into UserAgentConfig(UserAgentConfigBase, table=True) tablename "user_agent_configs"
// # class UserAgentConfigSettingsPublic(UserAgentSettingsBase):
// # ->  into UserAgentConfigPublic(UserAgentConfigBase)
// #  class UserAgentSettingsListPublic(SQLModel):
// # -> into UserAgentConfigsPublic(SQLModel):


import {
  AgentsService,
  LlmProvidersService,
  type UserAgentConfigsPublic,
  type UserAgentConfigPublic,
  type UserAgentConfigUpdate,
  type UserAccessProviderCreate,
  type UserAccessProviderPublic,
  type UserAccessProvidersPublic,
  type UserAccessProviderUpdate,
} from "@/client"
import type { AgentViewModel } from "@/services/agentService"
import {
  getProviderTypeLabel,
  type LLMProviderType,
} from "@/services/llmCatalogService"

// TODO: REMOVE THIS COMMENT ONLY AFTER LLMCATALOGSERVICE IS REFACTORED AND VALIDATED -
// TODO: REMEMBER THAT EVERYTHING IS SHIFTING TO THIE 


// ============================================================================
// Re-exports from Catalog Service
// ============================================================================

/**
 * Re-export types and utilities from catalog service for convenience
 */
export type { LLMProviderType } from "@/services/llmCatalogService"
export type { ModelOption } from "@/services/llmCatalogService"
export { getProviderTypeLabel, PROVIDER_TYPE_LABELS } from "@/services/llmCatalogService"


// ============================================================================
// Type Definitions - ViewModels
// ============================================================================

/**
 * Provider verification status
 */
export type ProviderStatus = "verified" | "failed" | "unknown"

/**
 * ProviderViewModel - User's configured provider optimized for UI display
 *
 * Transformations from backend UserLLMProviderPublic:
 * - Parses ISO timestamps to Date objects
 * - Computes status from last_test_success
 * - Computes is_usable from is_enabled and status
 */
export interface ProviderViewModel {
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

  // Computed fields
  display_type: string // "OpenAI", "Anthropic", etc.
  status: ProviderStatus
  is_usable: boolean // is_enabled && status !== "failed"
}

/**
 * UserAgentSettingsViewModel - Optimized for UI display
 */
export interface UserAgentSettingsViewModel {
  id: string
  user_id: string
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

/**
 * Resolution result for "what access provider/API provider type /model is this agentconfig actually using?"
 # TODO: add access provider association.
 # Remember: LLMProviderType is API Type - what kind of API does this model support?
 # Remember: UserAccessProvider is the access provider to that API.
 # Remember: Model is the model that the agent will be talking to at the other end of that API.
 # Remember: AgentConfig is not the Agent - it's the config that is used to structure the conversation 
*/
export interface ProviderResolution {
  mode: "system_default" | "user_provider"
  provider: ProviderViewModel | null
  model: string
  model_display: string
  status: ProviderStatus | "system"
}

/**
 * Paginated providers response
 */
export interface PaginatedProviders {
  providers: ProviderViewModel[]
  total_count: number
}

/**
 * Create provider input (wraps backend type)
 */
export type CreateProviderInput = UserAccessProviderCreate

/**
 * Update provider input (wraps backend type)
 */
export type UpdateProviderInput = UserAccessProviderUpdate

/**
 * Update agent settings input
 */
export type UpdateAgentSettingsInput = UserAgentConfigUpdate

/**
 * Test result from provider test endpoint
 */
export interface TestResult {
  success: boolean
  message: string
}

// ============================================================================
// Transformation Functions
// ============================================================================

/**
 * Extract provider type from model name
 * "openai:gpt-4o" -> "openai"
 * "anthropic:claude-3-sonnet" -> "anthropic"
 */
export function extractProviderType(modelName: string): LLMProviderType | null {
  const prefix = modelName.split(":")[0]
  return prefix ? normalizeProviderType(prefix) : null
}

/**
 * Format model name for display (fallback when catalog not available)
 * "openai:gpt-4o-mini" -> "GPT 4o Mini"
 *
 * For richer formatting with catalog data, use LlmCatalogService.formatModelName
 * or the useLlmCatalog hook's formatModelName method.
 */
export function formatModelName(modelName: string | null | undefined): string {
  if (!modelName) return "Default"

  // Extract model part after provider prefix
  const modelPart = modelName.split(":").pop() || modelName

  // Convert kebab-case to Title Case
  return modelPart
    .replace(/-/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

/**
 * Compute provider status from test results
 */
function computeStatus(
  lastTestSuccess: boolean | null,
  lastTestedAt: string | null,
): ProviderStatus {
  if (lastTestedAt === null) return "unknown"
  return lastTestSuccess ? "verified" : "failed"
}

/**
 * Normalize provider type name to lowercase for consistent UI grouping.
 */
function normalizeProviderType(
  providerType: string | null | undefined,
): LLMProviderType {
  const normalized = providerType?.trim().toLowerCase()
  return normalized || "unknown"
}

/**
 * Transform backend UserLLMProviderPublic to ProviderViewModel
 */
function transformProvider(provider: UserLLMProviderPublic): ProviderViewModel {
  const status = computeStatus(
    provider.last_test_success ?? null,
    provider.last_tested_at ?? null,
  )

  const providerType = normalizeProviderType(provider.provider_type)

  return {
    id: provider.id,
    name: provider.name,
    provider_type: providerType,
    base_url: provider.base_url ?? null,
    is_enabled: provider.is_enabled ?? true,
    is_default: provider.is_default ?? false,
    description: provider.description ?? null,
    created_at: new Date(provider.created_at),
    updated_at: new Date(provider.updated_at),
    last_tested_at: provider.last_tested_at
      ? new Date(provider.last_tested_at)
      : null,
    last_test_success: provider.last_test_success ?? null,

    // Computed fields
    display_type: getProviderTypeLabel(providerType),
    status,
    is_usable: (provider.is_enabled ?? true) && status !== "failed",
  }
}

/**
 * Transform backend UserAgentSettingsPublic to UserAgentSettingsViewModel
 */
function transformAgentSettings(
  settings: UserAgentSettingsPublic,
): UserAgentSettingsViewModel {
  return {
    id: settings.id,
    user_id: settings.user_id,
    agent_config_id: settings.agent_config_id,
    model_name_override: settings.model_name_override ?? null,
    provider_id: settings.provider_id ?? null,
    custom_system_prompt: settings.custom_system_prompt ?? null,
    is_favorite: settings.is_favorite ?? false,
    created_at: new Date(settings.created_at),
    updated_at: new Date(settings.updated_at),

    // Computed fields
    is_using_system_default: !settings.provider_id,
  }
}

// ============================================================================
// LLM Provider Service - Public API
// ============================================================================

export const LlmProviderService = {
  // ==========================================================================
  // Provider CRUD Operations
  // ==========================================================================

  /**
   * List user's LLM providers
   */
  async listProviders(options?: {
    skip?: number
    limit?: number
  }): Promise<PaginatedProviders> {
    const response: UserLLMProvidersPublic =
      await LlmProvidersService.listProviders({
        skip: options?.skip ?? 0,
        limit: options?.limit ?? 100,
      })

    return {
      providers: response.data.map(transformProvider),
      total_count: response.count,
    }
  },

  /**
   * Get a single provider by ID
   */
  async getProvider(providerId: string): Promise<ProviderViewModel> {
    const provider = await LlmProvidersService.getProvider({ providerId })
    return transformProvider(provider)
  },

  /**
   * Create a new provider
   */
  async createProvider(data: CreateProviderInput): Promise<ProviderViewModel> {
    const provider = await LlmProvidersService.createProvider({
      requestBody: data,
    })
    return transformProvider(provider)
  },

  /**
   * Update an existing provider
   */
  async updateProvider(
    providerId: string,
    data: UpdateProviderInput,
  ): Promise<ProviderViewModel> {
    const provider = await LlmProvidersService.updateProvider({
      providerId,
      requestBody: data,
    })
    return transformProvider(provider)
  },

  /**
   * Delete a provider
   */
  async deleteProvider(providerId: string): Promise<void> {
    await LlmProvidersService.deleteProvider({ providerId })
  },

  /**
   * Test a provider connection
   */
  async testProvider(providerId: string): Promise<TestResult> {
    const result = await LlmProvidersService.testProvider({ providerId })
    return {
      success: true,
      message: result.message,
    }
  },

  // ==========================================================================
  // User Agent Settings
  // ==========================================================================

  /**
   * Get user's settings for an agent
   * Returns null if no settings configured
   */
  async getAgentSettings(
    agentId: string,
  ): Promise<UserAgentSettingsViewModel | null> {
    try {
      const settings = await AgentsService.getMyAgentSettings({ agentId })
      if (!settings) return null
      return transformAgentSettings(settings)
    } catch (error) {
      // Return null if settings don't exist (404 from API)
      // Re-throw other errors
      if (error && typeof error === "object" && "status" in error) {
        const apiError = error as { status: number }
        if (apiError.status === 404) {
          return null
        }
      }
      throw error
    }
  },

  /**
   * Update user's settings for an agent (creates if not exists)
   */
  async updateAgentSettings(
    agentId: string,
    data: UpdateAgentSettingsInput,
  ): Promise<UserAgentSettingsViewModel> {
    const settings = await AgentsService.updateMyAgentSettings({
      agentId,
      requestBody: data,
    })
    return transformAgentSettings(settings)
  },

  /**
   * Delete user's settings for an agent (resets to defaults)
   */
  async deleteAgentSettings(agentId: string): Promise<void> {
    await AgentsService.deleteMyAgentSettings({ agentId })
  },

  // ==========================================================================
  // Resolution Helpers
  // ==========================================================================

  /**
   * Resolve what provider/model an agent is actually using
   *
   * Priority:
   * 1. User's settings provider_id -> use that provider
   * 2. No provider_id -> system default
   *
   * Model:
   * 1. User's model_name_override -> use that
   * 2. Agent's model_name -> use that
   */
  resolveProviderForAgent(
    agent: AgentViewModel,
    settings: UserAgentSettingsViewModel | null,
    providers: ProviderViewModel[],
  ): ProviderResolution {
    // Determine effective model
    const effectiveModel =
      settings?.model_name_override || agent.model_name || "openai:gpt-4o-mini"

    // Find display name for model
    const modelDisplay = formatModelName(effectiveModel)

    // If user has a provider set in settings
    if (settings?.provider_id) {
      const provider = providers.find((p) => p.id === settings.provider_id)
      if (provider) {
        return {
          mode: "user_provider",
          provider,
          model: effectiveModel,
          model_display: modelDisplay,
          status: provider.status,
        }
      }
    }

    // System default
    return {
      mode: "system_default",
      provider: null,
      model: effectiveModel,
      model_display: modelDisplay,
      status: "system",
    }
  },

  // ==========================================================================
  // Filtering Utilities
  // ==========================================================================

  /**
   * Filter providers by type
   */
  filterByType(
    providers: ProviderViewModel[],
    type: LLMProviderType,
  ): ProviderViewModel[] {
    return providers.filter((p) => p.provider_type === type)
  },

  /**
   * Filter to only enabled providers
   */
  filterEnabled(providers: ProviderViewModel[]): ProviderViewModel[] {
    return providers.filter((p) => p.is_enabled)
  },

  /**
   * Filter to only usable providers (enabled and not failed)
   */
  filterUsable(providers: ProviderViewModel[]): ProviderViewModel[] {
    return providers.filter((p) => p.is_usable)
  },

  /**
   * Get the default provider for a given type
   */
  getDefaultForType(
    providers: ProviderViewModel[],
    type: LLMProviderType,
  ): ProviderViewModel | null {
    const typeProviders = this.filterByType(providers, type)
    return typeProviders.find((p) => p.is_default) || typeProviders[0] || null
  },

  /**
   * Group providers by type
   */
  groupByType(
    providers: ProviderViewModel[],
  ): Record<LLMProviderType, ProviderViewModel[]> {
    const result: Record<LLMProviderType, ProviderViewModel[]> = {}

    for (const provider of providers) {
      if (!result[provider.provider_type]) {
        result[provider.provider_type] = []
      }
      result[provider.provider_type].push(provider)
    }

    return result
  },

  // ==========================================================================
  // Utility Functions (Re-exported)
  // ==========================================================================

  extractProviderType,
  formatModelName,
  getProviderTypeLabel,
}

// ============================================================================
// Query Keys for TanStack Query
// ============================================================================

export const LLM_PROVIDER_QUERY_KEYS = {
  providers: ["llm-providers"] as const,
  provider: (id: string) => ["llm-providers", id] as const,
  agentSettings: (agentId: string) => ["agent-settings", agentId] as const,
}
