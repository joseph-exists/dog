/**
 * LLM Catalog Service - System Provider & Model Catalog
 *
 * Purpose: Provide read-only access to the system-wide LLMProviderType and model catalog.
 * This is 'a' source of truth for LLMProviderType:model associations for known UserAccessProviders.
 * For example: there is a known set of LLMProviderType and Model associations for OpenAI, Anthropic, and Google when they are both the UserAccessProvider && the LLMProviderType.  
 * However, there are many LLMProviderType <> Model associations which are unknown. 
 *
 * 
 * Architecture:
 * - Wraps OpenAPI client methods for /llm-catalog endpoints
 * - Transforms backend types to ViewModels optimized for UI
 * - authentication needed (public catalog but only for authenticated users)
 * - Long cache times (staleTime: Infinity) since catalog rarely changes
 */

// these need to be list and aggregation functions ONLY.
// they don't block anything, they don't fail - if there's not a return, send back a 'nothing'
// we need to manage the empty case on the frontend and the backend at all times.
// a user may have their own local/handrolled system, which has no providertype, and they are their own user access provider.
// we need to allow that case -
// this is to help users, not break or block them.



import {
  LlmCatalogService as ApiCatalogService,
  type LLMModelPublic,
  type LLMModelsGrouped,
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
 * Human-readable labels for known LLMProviderType values
 * Graceful fallback: If type not in this map, display the type as-is
 */
export const PROVIDER_TYPE_LABELS: Record<string, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  google: "Google AI",
  azure_openai: "Azure OpenAI",
  ollama: "Ollama",
}

/**
 * Get display label for a provider type
 * Returns the type itself if not found in labels (graceful fallback for custom types)
 *
 * @param providerType - The LLMProviderType to get a label for
 * @returns Human-readable label
 */
export function getProviderTypeLabel(providerType: LLMProviderType): string {
  return PROVIDER_TYPE_LABELS[providerType] || providerType
}

/**
 * Model option for dropdowns - maintains backwards compatibility
 * with existing components using value format "provider:model_id"
 */
export interface ModelOption {

  value: string
  label: string
  description: string
  provider: LLMProviderType // this is the API spec provider
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


// ============================================================================
// Transformation Functions
// ============================================================================

/**
 * Transform backend UserAccessProviderPublic to CatalogProviderViewModel
 *
 * Note: Currently using UserAccessProviderPublic until backend catalog types are fully implemented.
 * TODO: Update to use LLMProviderTypePublic when backend catalog endpoints are ready.
 */
function transformProvider(
  provider: UserAccessProviderPublic,
): CatalogProviderViewModel {
  return {
    id: provider.id,
    name: provider.name,
    providerType: provider.provider_type ?? "unknown",
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
function transformLLMProviderTypeWithModels(
  provider: LLMProviderTypeWithModels,
): CatalogProviderViewModel & { models: CatalogModelViewModel[] } {
  return {
    id: provider.id,
    name: provider.name,
    providerType: provider.provider_type // this is the API spec provider
    description: provider.description ?? null,
    baseUrl: provider.base_url ?? null, // 
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
}

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
    },
  },
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
