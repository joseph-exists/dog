/**
 * LLM Provider Service - Data Integration Layer
 *
 * Purpose: Provide a clean, type-safe abstraction over the OpenAPI client
 * for LLM provider and agent settings operations. Transforms backend response
 * models to frontend ViewModels optimized for UI consumption.
 *
 * Architecture:
 * - Wraps OpenAPI client methods
 * - Transforms backend types to ViewModels
 * - Computes derived fields (status, display_type, etc.)
 * - Centralizes model list management
 * - Provides filtering and resolution utilities
 */

import {
  AgentsService,
  type LLMProviderType,
  LlmProvidersService,
  type UserAgentSettingsPublic,
  type UserAgentSettingsUpdate,
  type UserLLMProviderCreate,
  type UserLLMProviderPublic,
  type UserLLMProvidersPublic,
  type UserLLMProviderUpdate,
} from "@/client"
import type { AgentViewModel } from "@/services/agentService"

// ============================================================================
// Type Definitions - ViewModels
// ============================================================================

/**
 * Re-export LLMProviderType for convenience
 */
export type { LLMProviderType } from "@/client"

/**
 * Model option for dropdowns
 */
export interface ModelOption {
  value: string // "openai:gpt-4o"
  label: string // "GPT-4o"
  description: string // "Latest multimodal flagship"
  provider: LLMProviderType
}

/**
 * Provider verification status
 */
export type ProviderStatus = "verified" | "failed" | "unknown"

/**
 * ProviderViewModel - Optimized for UI display
 *
 * Transformations from backend UserLLMProviderPublic:
 * - Parses ISO timestamps to Date objects
 * - Computes display_type from provider_type
 * - Computes status from last_test_success
 * - Computes is_usable from is_enabled and status
 * - Includes compatible_models for the provider type
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
  compatible_models: ModelOption[]
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
 * Resolution result for "what provider/model is this agent actually using?"
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
export type CreateProviderInput = UserLLMProviderCreate

/**
 * Update provider input (wraps backend type)
 */
export type UpdateProviderInput = UserLLMProviderUpdate

/**
 * Update agent settings input
 */
export type UpdateAgentSettingsInput = UserAgentSettingsUpdate

/**
 * Test result from provider test endpoint
 */
export interface TestResult {
  success: boolean
  message: string
}

// ============================================================================
// Static Data - Supported Models
// ============================================================================

/**
 * Supported models by provider type
 * Mirrors backend/app/models.py SUPPORTED_MODELS
 *
 * Future: Replace with backend endpoint GET /api/v1/llm-providers/supported-models
 */
export const SUPPORTED_MODELS: Record<LLMProviderType, ModelOption[]> = {
  openai: [
    {
      value: "openai:gpt-4o",
      label: "GPT-4o",
      description: "Latest multimodal flagship",
      provider: "openai",
    },
    {
      value: "openai:gpt-4o-mini",
      label: "GPT-4o Mini",
      description: "Fast and affordable",
      provider: "openai",
    },
    {
      value: "openai:gpt-4-turbo",
      label: "GPT-4 Turbo",
      description: "Previous generation flagship",
      provider: "openai",
    },
    {
      value: "openai:gpt-3.5-turbo",
      label: "GPT-3.5 Turbo",
      description: "Fast, economical",
      provider: "openai",
    },
    {
      value: "openai:o1",
      label: "o1",
      description: "Advanced reasoning",
      provider: "openai",
    },
    {
      value: "openai:o1-mini",
      label: "o1 Mini",
      description: "Faster reasoning",
      provider: "openai",
    },
  ],
  anthropic: [
    {
      value: "anthropic:claude-sonnet-4-20250514",
      label: "Claude Sonnet 4",
      description: "Latest balanced model",
      provider: "anthropic",
    },
    {
      value: "anthropic:claude-3-5-sonnet-latest",
      label: "Claude 3.5 Sonnet",
      description: "Previous Sonnet",
      provider: "anthropic",
    },
    {
      value: "anthropic:claude-3-5-haiku-latest",
      label: "Claude 3.5 Haiku",
      description: "Fast and affordable",
      provider: "anthropic",
    },
    {
      value: "anthropic:claude-3-opus-latest",
      label: "Claude 3 Opus",
      description: "Most capable",
      provider: "anthropic",
    },
  ],
  google: [
    {
      value: "google:gemini-2.0-flash",
      label: "Gemini 2.0 Flash",
      description: "Latest fast model",
      provider: "google",
    },
    {
      value: "google:gemini-1.5-pro",
      label: "Gemini 1.5 Pro",
      description: "Long context flagship",
      provider: "google",
    },
    {
      value: "google:gemini-1.5-flash",
      label: "Gemini 1.5 Flash",
      description: "Fast and capable",
      provider: "google",
    },
  ],
  openai_compatible: [
    {
      value: "openai:custom",
      label: "Custom Model",
      description: "Enter model name manually",
      provider: "openai_compatible",
    },
  ],
}

/**
 * All models flattened into a single array
 */
export const ALL_MODELS: ModelOption[] = Object.values(SUPPORTED_MODELS).flat()

/**
 * Display labels for provider types
 */
export const PROVIDER_TYPE_LABELS: Record<LLMProviderType, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  google: "Google",
  openai_compatible: "OpenAI Compatible",
}

// ============================================================================
// Transformation Functions
// ============================================================================

/**
 * Get display label for provider type
 */
export function getProviderTypeLabel(type: LLMProviderType): string {
  return PROVIDER_TYPE_LABELS[type] || type
}

/**
 * Extract provider type from model name
 * "openai:gpt-4o" -> "openai"
 * "anthropic:claude-3-sonnet" -> "anthropic"
 */
export function extractProviderType(modelName: string): LLMProviderType | null {
  const prefix = modelName.split(":")[0]
  if (prefix === "openai" || prefix === "anthropic" || prefix === "google") {
    return prefix as LLMProviderType
  }
  return null
}

/**
 * Format model name for display
 * "openai:gpt-4o-mini" -> "GPT 4o Mini"
 */
export function formatModelName(modelName: string | null | undefined): string {
  if (!modelName) return "Default"

  // Try to find in SUPPORTED_MODELS first
  const model = ALL_MODELS.find((m) => m.value === modelName)
  if (model) return model.label

  // Fallback: extract model part after provider prefix
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
 * Transform backend UserLLMProviderPublic to ProviderViewModel
 */
function transformProvider(provider: UserLLMProviderPublic): ProviderViewModel {
  const status = computeStatus(
    provider.last_test_success ?? null,
    provider.last_tested_at ?? null,
  )

  return {
    id: provider.id,
    name: provider.name,
    provider_type: provider.provider_type,
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
    display_type: getProviderTypeLabel(provider.provider_type),
    status,
    compatible_models: SUPPORTED_MODELS[provider.provider_type] || [],
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
  // Model Operations
  // ==========================================================================

  /**
   * Get supported models map (static until backend endpoint exists)
   */
  getSupportedModels(): Record<LLMProviderType, ModelOption[]> {
    return SUPPORTED_MODELS
  },

  /**
   * Get all models as a flat list
   */
  getAllModels(): ModelOption[] {
    return ALL_MODELS
  },

  /**
   * Get models for a specific provider type
   */
  getModelsForProvider(providerType: LLMProviderType): ModelOption[] {
    return SUPPORTED_MODELS[providerType] || []
  },

  /**
   * Find a model by its value
   */
  findModel(modelValue: string): ModelOption | undefined {
    return ALL_MODELS.find((m) => m.value === modelValue)
  },

  /**
   * Extract provider type from model name
   */
  extractProviderType,

  /**
   * Format model name for display
   */
  formatModelName,

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
    const result: Record<LLMProviderType, ProviderViewModel[]> = {
      openai: [],
      anthropic: [],
      google: [],
      openai_compatible: [],
    }

    for (const provider of providers) {
      result[provider.provider_type].push(provider)
    }

    return result
  },
}

// ============================================================================
// Query Keys for TanStack Query
// ============================================================================

export const LLM_PROVIDER_QUERY_KEYS = {
  providers: ["llm-providers"] as const,
  provider: (id: string) => ["llm-providers", id] as const,
  supportedModels: ["llm-supported-models"] as const,
  agentSettings: (agentId: string) => ["agent-settings", agentId] as const,
}
