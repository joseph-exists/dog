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
  type CatalogGroupedViewModel,
  type CatalogModelViewModel,
  type CatalogProviderViewModel,
  getProviderTypeLabel,
  LlmCatalogService,
  type LLMProviderType,
  type ModelDisplayInfo,
  type ModelOption,
} from "@/services/llmCatalogService"

// ============================================================================
// Query Keys - Local to this hook
// ============================================================================

const LLM_CATALOG_QUERY_KEYS = {
  all: ["llm-catalog"] as const,
  modelsGrouped: ["llm-catalog", "models-grouped"] as const,
}

// ============================================================================
// Query Options - Infinite cache for catalog (rarely changes)
// ============================================================================

const CATALOG_QUERY_OPTIONS = {
  staleTime: Infinity,
  gcTime: Infinity,
}

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
  getProviderTypeLabel: (type: LLMProviderType) => string
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

  // Custom model creation mutation
  // TODO: Backend endpoint not yet implemented
  const createMutation = useMutation({
    mutationFn: async (_input: CreateCustomModelInput): Promise<ModelOption> => {
      // Backend /llm-catalog/models endpoint not yet implemented
      console.warn("useLlmCatalog: createCustomModel not yet implemented - backend endpoint needed")

      // For now, throw an error
      throw new Error("Custom model creation not yet available - backend catalog not implemented")

      // TODO: When backend ready, implement:
      // 1. Find provider by _input.providerType in grouped.providers
      // 2. Call LlmCatalogService.createCustomModel()
      // 3. Transform to ModelOption format
      // 4. Return result
    },
    onSuccess: () => {
      // Invalidate catalog cache to include new custom model
      queryClient.invalidateQueries({ queryKey: LLM_CATALOG_QUERY_KEYS.all })
    },
  })

  // Memoize derived data — stable when `grouped` is stable (TanStack Query
  // preserves data reference between renders when data hasn't changed)
  const { modelsByProvider, allModels, derivedProviders } = useMemo(() => {
    const byProvider: Record<LLMProviderType, ModelOption[]> = {}
    const provs: CatalogProviderViewModel[] = []

    if (grouped) {
      for (const provider of grouped.providers) {
        const providerType = provider.providerType
        provs.push(provider)
        byProvider[providerType] = (byProvider[providerType] ?? []).concat(
          provider.models.map((model) => modelToOption(model, providerType)),
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
    (value: string): ModelDisplayInfo => {
      // Check if model is in catalog
      const model = allModels.find((m) => m.value === value)

      if (model) {
        return {
          label: model.label,
          isCustom: !model.isSystem,
          isDeprecated: false, // TODO: Add deprecated flag when backend supports it
        }
      }

      // Graceful fallback for unknown models
      return {
        label: value,
        isCustom: true,
        isDeprecated: false,
      }
    },
    [allModels],
  )

  const createCustomModel = useCallback(
    (input: CreateCustomModelInput) => createMutation.mutateAsync(input),
    [createMutation],
  )

  const formatModelName = useCallback(
    (value: string | null | undefined): string => {
      if (!value) return ""

      // Check if model is in catalog - if so, use catalog label
      const model = allModels.find((m) => m.value === value)
      if (model) return model.label

      // Graceful fallback: return the value as-is
      // (catalog service would do the same since it's not yet implemented)
      return value
    },
    [allModels],
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
    getProviderTypeLabel,
    findModel,
    formatModelName,
    isInCatalog,
    isCustomModel,
    getModelDisplayInfo,
    createCustomModel,
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
