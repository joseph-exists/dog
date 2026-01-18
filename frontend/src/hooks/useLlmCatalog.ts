/**
 * useLlmCatalog Hook
 *
 * Provides access to the system-wide LLM provider and model catalog.
 * Uses TanStack Query with infinite cache (catalog rarely changes).
 *
 * This hook returns model options in the format expected by existing
 * components (ModelOption with "provider:model_id" value format).
 *
 * Also provides:
 * - Custom model creation mutation
 * - Utility functions for identifying custom vs catalog models
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

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

/**
 * Input for creating a custom model
 */
export interface CreateCustomModelInput {
  /** Model ID as expected by the provider (e.g., "llama3.2:70b") */
  modelId: string
  /** Human-readable display name (e.g., "Llama 3.2 70B") */
  displayName: string
  /** Provider type this model belongs to */
  providerType: LLMProviderType
  /** Optional description */
  description?: string
}

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
  /** Check if a model value is in the catalog */
  isInCatalog: (value: string) => boolean
  /** Check if a model value is a custom (non-catalog) model */
  isCustomModel: (value: string) => boolean
  /** Create a custom model (mutation) */
  createCustomModel: (input: CreateCustomModelInput) => Promise<ModelOption>
  /** Whether custom model creation is in progress */
  isCreatingCustomModel: boolean
}

/**
 * Hook for accessing the LLM catalog
 *
 * Uses infinite staleTime since catalog data rarely changes.
 * Data is fetched once and cached for the session.
 */
export function useLlmCatalog(): UseLlmCatalogReturn {
  const queryClient = useQueryClient()

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

  // Custom model creation mutation
  // TODO: Connect to actual backend endpoint when available
  const createMutation = useMutation({
    mutationFn: async (input: CreateCustomModelInput): Promise<ModelOption> => {
      // For now, create a local ModelOption
      // When backend is ready, this will call:
      // await LlmCatalogService.createCustomModel(input)
      const modelValue = `${input.providerType}:${input.modelId}`
      return {
        value: modelValue,
        label: input.displayName,
        description: input.description || "",
        provider: input.providerType,
        isDefault: false,
      }
    },
    onSuccess: () => {
      // Invalidate catalog cache to include new custom model
      queryClient.invalidateQueries({ queryKey: LLM_CATALOG_QUERY_KEYS.all })
    },
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

  // Utility function to check if a model is in catalog
  const isInCatalog = (value: string): boolean => {
    return allModels.some((m) => m.value === value)
  }

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

    isInCatalog,

    isCustomModel: (value: string) => !isInCatalog(value),

    createCustomModel: (input: CreateCustomModelInput) =>
      createMutation.mutateAsync(input),

    isCreatingCustomModel: createMutation.isPending,
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
