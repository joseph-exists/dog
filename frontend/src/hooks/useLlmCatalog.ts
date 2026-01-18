/**
 * useLlmCatalog Hook
 *
 * Provides access to the system-wide LLM provider and model catalog.
 * Uses TanStack Query with infinite cache (catalog rarely changes).
 *
 * This hook returns model options in the format expected by existing
 * components (ModelOption with "provider:model_id" value format).
 */

import { useQuery } from "@tanstack/react-query"

import {
  CATALOG_QUERY_OPTIONS,
  type CatalogGroupedViewModel,
  type CatalogModelViewModel,
  type CatalogProviderViewModel,
  LLM_CATALOG_QUERY_KEYS,
  type LLMProviderType,
  LlmCatalogService,
  type ModelOption,
  PROVIDER_TYPE_LABELS,
} from "@/services/llmCatalogService"

export interface UseLlmCatalogReturn {
  /** Model options grouped by provider type (for dropdowns) */
  modelsByProvider: Record<LLMProviderType, ModelOption[]>
  /** All models as flat array */
  allModels: ModelOption[]
  /** Catalog providers with model counts */
  providers: CatalogProviderViewModel[]
  /** Full grouped data (providers with nested models) */
  grouped: CatalogGroupedViewModel | null
  /** Total model count */
  totalModels: number
  /** Loading state */
  isLoading: boolean
  /** Error state */
  error: Error | null
  /** Get models for a specific provider type */
  getModelsForType: (type: LLMProviderType) => ModelOption[]
  /** Get default model for a provider type */
  getDefaultForType: (type: LLMProviderType) => ModelOption | null
  /** Get provider type label */
  getProviderLabel: (type: LLMProviderType) => string
  /** Find model option by value */
  findModel: (value: string) => ModelOption | undefined
  /** Format model name for display */
  formatModelName: (value: string | null | undefined) => string
}

/**
 * Hook for accessing the LLM catalog
 *
 * Uses infinite staleTime since catalog data rarely changes.
 * Data is fetched once and cached for the session.
 */
export function useLlmCatalog(): UseLlmCatalogReturn {
  // Fetch grouped data (providers with models) - single API call
  const {
    data: grouped,
    isLoading,
    error,
  } = useQuery({
    queryKey: LLM_CATALOG_QUERY_KEYS.modelsGrouped,
    queryFn: () => LlmCatalogService.listModelsGrouped({ isEnabled: true }),
    ...CATALOG_QUERY_OPTIONS,
  })

  // Transform grouped data to provider-keyed ModelOption map
  const modelsByProvider: Record<LLMProviderType, ModelOption[]> = {
    empty: [],
    openai: [],
    anthropic: [],
    google: [],
    openai_compatible: [],
  }

  const providers: CatalogProviderViewModel[] = []

  if (grouped) {
    for (const provider of grouped.providers) {
      const providerType = provider.providerType
      providers.push(provider)
      modelsByProvider[providerType] = provider.models.map((model) =>
        modelToOption(model, providerType),
      )
    }
  }

  // Flatten all models
  const allModels = Object.values(modelsByProvider).flat()

  return {
    modelsByProvider,
    allModels,
    providers,
    grouped: grouped ?? null,
    totalModels: grouped?.totalModels ?? 0,
    isLoading,
    error: error as Error | null,

    getModelsForType: (type: LLMProviderType) => modelsByProvider[type] ?? [],

    getDefaultForType: (type: LLMProviderType) => {
      const models = modelsByProvider[type] ?? []
      return models.find((m) => m.isDefault) ?? models[0] ?? null
    },

    getProviderLabel: (type: LLMProviderType) =>
      PROVIDER_TYPE_LABELS[type] || type,

    findModel: (value: string) => allModels.find((m) => m.value === value),

    formatModelName: LlmCatalogService.formatModelName,
  }
}

/**
 * Transform CatalogModelViewModel to ModelOption
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
    capabilities: {
      vision: model.hasVision,
      functionCalling: model.hasFunctionCalling,
      streaming: model.hasStreaming,
      jsonMode: model.hasJsonMode,
    },
    contextWindow: model.contextWindow,
  }
}

export default useLlmCatalog
