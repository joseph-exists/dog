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
import { useCallback, useMemo } from "react"

import {
  CATALOG_QUERY_OPTIONS,
  type CatalogGroupedViewModel,
  type CatalogModelViewModel,
  type CatalogProviderViewModel,
  LLM_CATALOG_QUERY_KEYS,
  type LLMProviderType,
  LlmCatalogService,
  type ModelDisplayInfo,
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
  /** Get display info for a model with graceful fallback */
  getModelDisplayInfo: (value: string) => ModelDisplayInfo
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

  // Custom model creation mutation - connected to backend
  const createMutation = useMutation({
    mutationFn: async (input: CreateCustomModelInput): Promise<ModelOption> => {
      // DEBUG: Log input and provider lookup
      console.log("[useLlmCatalog] createCustomModel input:", input)
      console.log("[useLlmCatalog] grouped providers:", grouped?.providers.map(p => ({
        id: p.id,
        name: p.name,
        providerType: p.providerType,
      })))

      // Find the provider ID for the given provider type
      // Fall back to openai_compatible if exact match not found
      const provider = grouped?.providers.find(
        (p) => p.providerType === input.providerType,
      ) ?? grouped?.providers.find(
        (p) => p.providerType === "openai_compatible",
      )

      console.log("[useLlmCatalog] Found provider:", provider ? {
        id: provider.id,
        providerType: provider.providerType,
      } : "NOT FOUND")

      if (!provider) {
        throw new Error(`No provider found for type: ${input.providerType}`)
      }

      // Create the model via backend
      const model = await LlmCatalogService.createCustomModel({
        modelId: input.modelId,
        displayName: input.displayName,
        providerId: provider.id,
        description: input.description,
      })

      // Transform to ModelOption format
      return {
        value: `${input.providerType}:${model.modelId}`,
        label: model.displayName,
        description: model.description || "",
        provider: input.providerType,
        isDefault: false,
        isSystem: false,
      }
    },
    onSuccess: () => {
      // Invalidate catalog cache to include new custom model
      queryClient.invalidateQueries({ queryKey: LLM_CATALOG_QUERY_KEYS.all })
    },
  })

  // Memoize derived data — stable when `grouped` is stable (TanStack Query
  // preserves data reference between renders when data hasn't changed)
  const { modelsByProvider, allModels, derivedProviders } = useMemo(() => {
    const byProvider: Record<LLMProviderType, ModelOption[]> = {
      empty: [],
      openai: [],
      anthropic: [],
      google: [],
      openai_compatible: [],
    }
    const provs: CatalogProviderViewModel[] = []

    if (grouped) {
      for (const provider of grouped.providers) {
        const providerType = provider.providerType
        provs.push(provider)
        byProvider[providerType] = provider.models.map((model) =>
          modelToOption(model, providerType),
        )
      }
    }

    return {
      modelsByProvider: byProvider,
      allModels: Object.values(byProvider).flat(),
      derivedProviders: provs,
    }
  }, [grouped])

  // Stable utility functions — safe to use in dependency arrays
  const getModelsForType = useCallback(
    (type: LLMProviderType) => modelsByProvider[type] ?? [],
    [modelsByProvider],
  )

  const getDefaultForType = useCallback(
    (type: LLMProviderType) => {
      const models = modelsByProvider[type] ?? []
      return models.find((m) => m.isDefault) ?? models[0] ?? null
    },
    [modelsByProvider],
  )

  const findModel = useCallback(
    (value: string) => allModels.find((m) => m.value === value),
    [allModels],
  )

  const isInCatalog = useCallback(
    (value: string) => allModels.some((m) => m.value === value),
    [allModels],
  )

  const isCustomModel = useCallback(
    (value: string) => {
      const model = allModels.find((m) => m.value === value)
      return model ? model.isSystem === false : true
    },
    [allModels],
  )

  const getModelDisplayInfo = useCallback(
    (value: string) => LlmCatalogService.getModelDisplayInfo(value, allModels),
    [allModels],
  )

  const createCustomModel = useCallback(
    (input: CreateCustomModelInput) => createMutation.mutateAsync(input),
    [createMutation],
  )

  return {
    modelsByProvider,
    allModels,
    providers: derivedProviders,
    grouped: grouped ?? null,
    totalModels: grouped?.totalModels ?? 0,
    isLoading,
    error: error as Error | null,
    getModelsForType,
    getDefaultForType,
    getProviderLabel,
    findModel,
    formatModelName: LlmCatalogService.formatModelName,
    isInCatalog,
    isCustomModel,
    getModelDisplayInfo,
    createCustomModel,
    isCreatingCustomModel: createMutation.isPending,
  }
}

/** Pure lookup — no React state dependencies, always stable */
function getProviderLabel(type: LLMProviderType): string {
  return PROVIDER_TYPE_LABELS[type] || type
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

export default useLlmCatalog
