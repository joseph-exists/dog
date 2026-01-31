/**
 * LLM Catalog Service - System Provider & Model Catalog
 *
 * Purpose: Provide read-only access to the system-wide LLMProviderType and model catalog.
 * This is 'a' source of truth for LLMProviderType:model associations for known UserAccessProviders.
 * For example: there is a known set of LLMProviderType and Model associations for OpenAI, Anthropic,
 * and Google when they are both the UserAccessProvider && the LLMProviderType.
 * However, there are many LLMProviderType <> Model associations which are unknown.
 *
 * Architecture:
 * - Wraps OpenAPI client methods for /llm-catalog endpoints (TODO: when backend implements them)
 * - Transforms backend types to ViewModels optimized for UI
 * - Authentication needed (public catalog but only for authenticated users)
 * - Long cache times (staleTime: Infinity) since catalog rarely changes
 *
 * Design Principles (CRITICAL):
 * - List and aggregation functions ONLY
 * - Never blocks or fails - returns empty arrays/null for unknown data
 * - Allows custom/unknown provider types (returns graceful fallbacks)
 * - Read-only - no create/update/delete operations
 * - Helps users, doesn't break or block them
 *
 * A user may have their own local/hand-rolled system with no providertype,
 * and they are their own user access provider. We need to allow that case.
 *
 * CURRENT STATUS: Minimal implementation with hardcoded labels.
 * Backend /llm-catalog endpoints are not yet fully implemented.
 * TODO: Expand when backend endpoints are ready.
 */

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
 * Model option for dropdowns - simplified format
 * Maintains backwards compatibility with existing UI components
 * Use value format "provider:model_id" for consistency
 * # TODO FIX NOW THAT WE CAN
 * 
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
 * Complete model data from catalog
 * Use this for detailed model information
 * TODO: Implement when backend catalog endpoints are ready
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
 * CatalogProviderViewModel - Provider with model count
 * TODO: Implement when backend catalog endpoints are ready
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
 * CatalogGroupedViewModel - Providers with nested models
 * TODO: Implement when backend catalog endpoints are ready
 */
export interface CatalogGroupedViewModel {
  providers: Array<
    CatalogProviderViewModel & { models: CatalogModelViewModel[] }
  >
  totalModels: number
}

// ============================================================================
// LLM Catalog Service - Public API
// ============================================================================

/**
 * LLM Catalog Service (Minimal Implementation)
 *
 * Backend /llm-catalog endpoints are not yet fully implemented, so this service
 * currently only provides utility functions and returns empty results gracefully.
 *
 * Design principle: This service helps users, never blocks them.
 * Unknown/custom provider types and models are allowed - we provide fallbacks.
 *
 * TODO: Expand with full backend catalog integration when endpoints are ready:
 * - listProviders(options)
 * - listModels(options)
 * - listModelsGrouped(options)
 * - getModel(modelId)
 * - getModelOptionsForType(providerType)
 * - getDefaultModel(providerType)
 */
export const LlmCatalogService = {
  // ==========================================================================
  // Utility Methods (Always Available)
  // ==========================================================================

  /**
   * Get display label for a provider type
   * Graceful: Returns the type itself if not in labels
   */
  getProviderTypeLabel,

  /**
   * Get list of known provider types
   * Returns hardcoded list until backend catalog is ready
   */
  getKnownProviderTypes(): LLMProviderType[] {
    return Object.keys(PROVIDER_TYPE_LABELS)
  },

  /**
   * Check if a provider type is known in the catalog
   * Returns false for custom/unknown types (doesn't block them)
   */
  isKnownProviderType(providerType: LLMProviderType): boolean {
    return providerType in PROVIDER_TYPE_LABELS
  },

  // ==========================================================================
  // Placeholder Methods (TODO: Implement when backend ready)
  // ==========================================================================

  /**
   * List all models (flat list)
   * TODO: Implement when backend /llm-catalog/models endpoint is ready
   * Currently returns empty array gracefully
   */
  async listModels(_options?: {
    providerType?: LLMProviderType
    isEnabled?: boolean
    hasVision?: boolean
    hasFunctionCalling?: boolean
  }): Promise<CatalogModelViewModel[]> {
    console.warn("LlmCatalogService.listModels: Backend catalog not yet implemented, returning empty list")
    return []
  },

  /**
   * List models grouped by provider
   * TODO: Implement when backend /llm-catalog/models/grouped endpoint is ready
   * Currently returns empty result gracefully
   */
  async listModelsGrouped(_options?: {
    providerType?: LLMProviderType
    isEnabled?: boolean
  }): Promise<CatalogGroupedViewModel> {
    console.warn("LlmCatalogService.listModelsGrouped: Backend catalog not yet implemented, returning empty result")
    return { providers: [], totalModels: 0 }
  },

  /**
   * Get a single model by ID
   * TODO: Implement when backend /llm-catalog/models/{id} endpoint is ready
   * Currently returns null gracefully
   */
  async getModel(_modelId: string): Promise<CatalogModelViewModel | null> {
    console.warn("LlmCatalogService.getModel: Backend catalog not yet implemented, returning null")
    return null
  },

  /**
   * Get all models as ModelOption array (for dropdowns)
   * TODO: Implement when backend catalog is ready
   * Currently returns empty object gracefully
   */
  async getModelOptions(): Promise<Record<LLMProviderType, ModelOption[]>> {
    console.warn("LlmCatalogService.getModelOptions: Backend catalog not yet implemented, returning empty object")
    return {}
  },

  /**
   * Get all models as flat ModelOption array
   * TODO: Implement when backend catalog is ready
   * Currently returns empty array gracefully
   */
  async getAllModelOptions(): Promise<ModelOption[]> {
    console.warn("LlmCatalogService.getAllModelOptions: Backend catalog not yet implemented, returning empty array")
    return []
  },

  /**
   * Get models for a specific provider type as ModelOption array
   * TODO: Implement when backend catalog is ready
   * Currently returns empty array gracefully
   */
  async getModelOptionsForType(
    _providerType: LLMProviderType,
  ): Promise<ModelOption[]> {
    console.warn("LlmCatalogService.getModelOptionsForType: Backend catalog not yet implemented, returning empty array")
    return []
  },

  /**
   * Get the default model for a provider type
   * TODO: Implement when backend catalog is ready
   * Currently returns null gracefully
   */
  async getDefaultModel(
    _providerType: LLMProviderType,
  ): Promise<ModelOption | null> {
    console.warn("LlmCatalogService.getDefaultModel: Backend catalog not yet implemented, returning null")
    return null
  },

  /**
   * Format a model name for display
   * Graceful: Returns model name as-is since catalog not yet available
   */
  async formatModelName(modelName: string): Promise<string> {
    // Return as-is until catalog is available
    return modelName
  },
}
