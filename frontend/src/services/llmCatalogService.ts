/**
 * LLM Catalog Service - System Provider & Model Catalog
 *
 * Purpose: Provide read-only access to the system-wide LLM provider and model catalog.
 * This is the source of truth for available models and their capabilities.
 *
 * Architecture:
 * - Wraps OpenAPI client methods for /llm-catalog endpoints
 * - Transforms backend types to ViewModels optimized for UI
 * - No authentication required (public catalog)
 * - Long cache times (staleTime: Infinity) since catalog rarely changes
 */

import {
  LlmCatalogService as ApiCatalogService,
  type LLMModelPublic,
  type LLMModelsGrouped,
  type LLMProviderPublic,
  type LLMProviderWithModels,
} from "@/client"

// ============================================================================
// Type Definitions - ViewModels
// ============================================================================

/**
 * Provider type name (dynamic, sourced from catalog)
 */
export type LLMProviderType = string

/**
 * Model option for dropdowns - maintains backwards compatibility
 * with existing components using value format "provider:model_id"
 */
export interface ModelOption {
  /** Composite value: "openai:gpt-4o" */
  value: string
  /** Human-readable: "GPT-4o" */
  label: string
  /** Short description */
  description: string
  /** Provider type this model belongs to */
  provider: LLMProviderType
  /** Whether this is the default model for the provider */
  isDefault?: boolean
  /** Whether this is a system (catalog) model vs user-created */
  isSystem?: boolean
  /** Model capabilities */
  capabilities?: {
    vision: boolean | null
    functionCalling: boolean | null
    streaming: boolean | null
    jsonMode: boolean | null
  }
  /** Context window size */
  contextWindow?: number | null
}

/**
 * Display info for a model - used for graceful fallback display
 */
export interface ModelDisplayInfo {
  /** Display label */
  label: string
  /** Whether this is a custom (user-created) model */
  isCustom: boolean
  /** Whether this model is deprecated */
  isDeprecated: boolean
}

/**
 * CatalogProviderViewModel - Provider with model count
 */
export interface CatalogProviderViewModel {
  id: string
  name: string
  providerType: LLMProviderType
  description: string | null
  baseUrl: string | null
  isEnabled: boolean
  isSystem: boolean
  modelCount: number
  createdAt: Date
  updatedAt: Date
}

/**
 * CatalogModelViewModel - Model with full capabilities
 */
export interface CatalogModelViewModel {
  id: string
  providerId: string
  modelId: string
  displayName: string
  description: string | null
  contextWindow: number | null
  isDefault: boolean
  isEnabled: boolean
  isDeprecated: boolean
  isSystem: boolean
  sortOrder: number
  hasVision: boolean | null
  hasFunctionCalling: boolean | null
  hasStreaming: boolean | null
  hasJsonMode: boolean | null
  providerType: LLMProviderType | null
  providerName: string | null
  createdAt: Date
  updatedAt: Date
}

/**
 * CatalogGroupedViewModel - Providers with nested models
 */
export interface CatalogGroupedViewModel {
  providers: Array<
    CatalogProviderViewModel & { models: CatalogModelViewModel[] }
  >
  totalModels: number
}

/**
 * Display labels for provider types
 */
export const PROVIDER_TYPE_LABELS: Record<LLMProviderType, string> = {
  empty: "",
  openai: "OpenAI",
  anthropic: "Anthropic",
  google: "Google",
  openai_compatible: "OpenAI Compatible",
}

// ============================================================================
// Transformation Functions
// ============================================================================

/**
 * Normalize provider type string to lowercase LLMProviderType
 * Handles case-insensitive backend data (e.g., "OPENAI" -> "openai")
 */
function normalizeProviderType(
  providerType: string | null | undefined
): LLMProviderType {
  const normalized = providerType?.trim().toLowerCase()
  return normalized || "unknown"
}

/**
 * Get display label for provider type
 */
export function getProviderTypeLabel(type: LLMProviderType | null | undefined): string {
  if (!type) return "Unknown"
  const normalized = type.toLowerCase()
  if (PROVIDER_TYPE_LABELS[normalized]) {
    return PROVIDER_TYPE_LABELS[normalized]
  }
  return normalized
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

/**
 * Transform backend LLMProviderPublic to CatalogProviderViewModel
 */
function transformProvider(
  provider: LLMProviderPublic,
): CatalogProviderViewModel {
  return {
    id: provider.id,
    name: provider.name,
    providerType: normalizeProviderType(provider.provider_type),
    description: provider.description ?? null,
    baseUrl: provider.base_url ?? null,
    isEnabled: provider.is_enabled ?? true,
    isSystem: provider.is_system ?? true,
    modelCount: provider.model_count ?? 0,
    createdAt: new Date(provider.created_at),
    updatedAt: new Date(provider.updated_at),
  }
}

/**
 * Transform backend LLMModelPublic to CatalogModelViewModel
 */
function transformModel(model: LLMModelPublic): CatalogModelViewModel {
  return {
    id: model.id,
    providerId: model.provider_id,
    modelId: model.model_id,
    displayName: model.display_name,
    description: model.description ?? null,
    contextWindow: model.context_window ?? null,
    isDefault: model.is_default ?? false,
    isEnabled: model.is_enabled ?? true,
    isDeprecated: model.is_deprecated ?? false,
    isSystem: model.is_system ?? true,
    sortOrder: model.sort_order ?? 0,
    hasVision: model.has_vision ?? null,
    hasFunctionCalling: model.has_function_calling ?? null,
    hasStreaming: model.has_streaming ?? null,
    hasJsonMode: model.has_json_mode ?? null,
    providerType: model.provider_type ? normalizeProviderType(model.provider_type) : null,
    providerName: model.provider_name ?? null,
    createdAt: new Date(model.created_at),
    updatedAt: new Date(model.updated_at),
  }
}

/**
 * Transform backend LLMProviderWithModels to grouped view model
 */
function transformProviderWithModels(
  provider: LLMProviderWithModels,
): CatalogProviderViewModel & { models: CatalogModelViewModel[] } {
  return {
    id: provider.id,
    name: provider.name,
    providerType: normalizeProviderType(provider.provider_type),
    description: provider.description ?? null,
    baseUrl: provider.base_url ?? null,
    isEnabled: provider.is_enabled ?? true,
    isSystem: provider.is_system ?? true,
    modelCount: provider.model_count ?? provider.models?.length ?? 0,
    createdAt: new Date(provider.created_at),
    updatedAt: new Date(provider.updated_at),
    models: (provider.models ?? []).map(transformModel),
  }
}

/**
 * Transform CatalogModelViewModel to ModelOption for dropdown compatibility
 */
function modelToOption(
  model: CatalogModelViewModel,
  providerType: LLMProviderType,
): ModelOption {
  return {
    value: `${providerType}:${model.modelId}`,
    label: model.displayName,
    description: model.description || "",
    provider: providerType,
    isDefault: model.isDefault,
    isSystem: model.isSystem,
    capabilities: {
      vision: model.hasVision,
      functionCalling: model.hasFunctionCalling,
      streaming: model.hasStreaming,
      jsonMode: model.hasJsonMode,
    },
    contextWindow: model.contextWindow,
  }
}

// ============================================================================
// LLM Catalog Service - Public API
// ============================================================================

export const LlmCatalogService = {
  // ==========================================================================
  // Provider Operations
  // ==========================================================================

  /**
   * List all catalog providers
   */
  async listProviders(options?: {
    providerType?: LLMProviderType
    isEnabled?: boolean
  }): Promise<CatalogProviderViewModel[]> {
    const response = await ApiCatalogService.listProviders({
      providerType: options?.providerType,
      isEnabled: options?.isEnabled,
    })
    return response.data.map(transformProvider)
  },

  /**
   * Get a single provider by ID
   */
  async getProvider(providerId: string): Promise<CatalogProviderViewModel> {
    const provider = await ApiCatalogService.getProvider({ providerId })
    return transformProvider(provider)
  },

  /**
   * Get models for a specific provider
   */
  async getProviderModels(
    providerId: string,
    options?: { isEnabled?: boolean },
  ): Promise<CatalogModelViewModel[]> {
    const response = await ApiCatalogService.listProviderModels({
      providerId,
      isEnabled: options?.isEnabled,
    })
    return response.data.map(transformModel)
  },

  // ==========================================================================
  // Model Operations
  // ==========================================================================

  /**
   * List all models (flat list)
   */
  async listModels(options?: {
    providerType?: LLMProviderType
    isEnabled?: boolean
    hasVision?: boolean
    hasFunctionCalling?: boolean
  }): Promise<CatalogModelViewModel[]> {
    const response = await ApiCatalogService.listModels({
      providerType: options?.providerType,
      isEnabled: options?.isEnabled,
      hasVision: options?.hasVision,
      hasFunctionCalling: options?.hasFunctionCalling,
    })
    return response.data.map(transformModel)
  },

  /**
   * List models grouped by provider
   */
  async listModelsGrouped(options?: {
    providerType?: LLMProviderType
    isEnabled?: boolean
  }): Promise<CatalogGroupedViewModel> {
    const response: LLMModelsGrouped =
      await ApiCatalogService.listModelsGrouped({
        providerType: options?.providerType,
        isEnabled: options?.isEnabled,
      })
    return {
      providers: response.providers.map(transformProviderWithModels),
      totalModels: response.total_models,
    }
  },

  /**
   * Get a single model by ID
   */
  async getModel(modelId: string): Promise<CatalogModelViewModel> {
    const model = await ApiCatalogService.getModel({ modelId })
    return transformModel(model)
  },

  // ==========================================================================
  // Utility Methods - ModelOption Format (Backwards Compatible)
  // ==========================================================================

  /**
   * Get all models as ModelOption array (for dropdowns)
   * Returns models grouped by provider type
   */
  async getModelOptions(): Promise<Record<LLMProviderType, ModelOption[]>> {
    const grouped = await this.listModelsGrouped({ isEnabled: true })

    const result: Record<LLMProviderType, ModelOption[]> = {}

    for (const provider of grouped.providers) {
      const providerType = provider.providerType
      result[providerType] = (result[providerType] ?? []).concat(
        provider.models.map((model) => modelToOption(model, providerType)),
      )
    }

    return result
  },

  /**
   * Get all models as flat ModelOption array
   */
  async getAllModelOptions(): Promise<ModelOption[]> {
    const byProvider = await this.getModelOptions()
    return Object.values(byProvider).flat()
  },

  /**
   * Get models for a specific provider type as ModelOption array
   */
  async getModelOptionsForType(
    providerType: LLMProviderType,
  ): Promise<ModelOption[]> {
    const models = await this.listModels({ providerType, isEnabled: true })
    return models.map((model) => modelToOption(model, providerType))
  },

  /**
   * Get the default model for a provider type
   */
  async getDefaultModel(
    providerType: LLMProviderType,
  ): Promise<ModelOption | null> {
    const models = await this.listModels({ providerType, isEnabled: true })
    const defaultModel = models.find((m) => m.isDefault)
    if (!defaultModel) return null
    return modelToOption(defaultModel, providerType)
  },

  // ==========================================================================
  // Static Utilities (No API calls)
  // ==========================================================================

  /**
   * Get provider type label
   */
  getProviderTypeLabel,

  /**
   * Extract provider type from composite model value
   * "openai:gpt-4o" -> "openai"
   */
  extractProviderType(modelValue: string): LLMProviderType | null {
    const prefix = modelValue.split(":")[0]
    return prefix ? normalizeProviderType(prefix) : null
  },

  /**
   * Extract model ID from composite value
   * "openai:gpt-4o" -> "gpt-4o"
   */
  extractModelId(modelValue: string): string {
    return modelValue.split(":").slice(1).join(":") || modelValue
  },

  /**
   * Format model value for display (fallback when model not in catalog)
   * "openai:gpt-4o-mini" -> "GPT 4o Mini"
   */
  formatModelName(modelValue: string | null | undefined): string {
    if (!modelValue) return "Default"

    // Extract model part after provider prefix
    const modelPart = modelValue.split(":").pop() || modelValue

    // Convert kebab-case to Title Case
    return modelPart
      .replace(/-/g, " ")
      .replace(/\b\w/g, (char) => char.toUpperCase())
  },

  // ==========================================================================
  // Custom Model Operations (Authenticated)
  // ==========================================================================

  /**
   * Create a custom model for the current user
   */
  async createCustomModel(data: {
    modelId: string
    displayName?: string
    providerId: string
    description?: string
  }): Promise<CatalogModelViewModel> {
    const response = await ApiCatalogService.createCustomModel({
      requestBody: {
        model_id: data.modelId,
        display_name: data.displayName || data.modelId,
        provider_id: data.providerId,
        description: data.description,
      },
    })
    return transformModel(response)
  },

  /**
   * List current user's custom models
   */
  async listCustomModels(options?: {
    providerType?: LLMProviderType
  }): Promise<CatalogModelViewModel[]> {
    const response = await ApiCatalogService.listCustomModels({
      providerType: options?.providerType,
    })
    return response.data.map(transformModel)
  },

  // ==========================================================================
  // Display Helpers
  // ==========================================================================

  /**
   * Get display info for a model value, with graceful fallback
   * Returns label, isCustom, and isDeprecated for UI rendering
   */
  getModelDisplayInfo(
    modelValue: string,
    catalog: ModelOption[],
  ): ModelDisplayInfo {
    const match = catalog.find((m) => m.value === modelValue)
    if (match) {
      return {
        label: match.label,
        isCustom: match.isSystem === false,
        isDeprecated: false, // TODO: add isDeprecated to ModelOption when needed
      }
    }
    // Fallback for completely unknown models
    return {
      label: this.formatModelName(modelValue),
      isCustom: true,
      isDeprecated: false,
    }
  },
}

// ============================================================================
// Query Keys for TanStack Query
// ============================================================================

export const LLM_CATALOG_QUERY_KEYS = {
  /** All catalog data */
  all: ["llm-catalog"] as const,
  /** Provider list */
  providers: ["llm-catalog", "providers"] as const,
  /** Single provider */
  provider: (id: string) => ["llm-catalog", "providers", id] as const,
  /** Provider's models */
  providerModels: (id: string) =>
    ["llm-catalog", "providers", id, "models"] as const,
  /** Model list (flat) */
  models: ["llm-catalog", "models"] as const,
  /** Models grouped by provider */
  modelsGrouped: ["llm-catalog", "models", "grouped"] as const,
  /** Single model */
  model: (id: string) => ["llm-catalog", "models", id] as const,
  /** Model options (for dropdowns) */
  modelOptions: ["llm-catalog", "model-options"] as const,
  /** User's custom models */
  customModels: ["llm-catalog", "custom-models"] as const,
}

// ============================================================================
// Recommended Query Options
// ============================================================================

/**
 * Default query options for catalog data
 * Catalog is essentially static - use very long cache times
 *
 * NOTE: Changed staleTime to 1 hour to allow cache refresh after bug fixes.
 * If catalog becomes truly static, can increase back to Infinity.
 */
export const CATALOG_QUERY_OPTIONS = {
  staleTime: 1000 * 60 * 60, // 1 hour (was Infinity - reduced to allow cache refresh)
  gcTime: 1000 * 60 * 60 * 24, // 24 hours
  refetchOnWindowFocus: false,
  refetchOnMount: false,
  refetchOnReconnect: false,
}
