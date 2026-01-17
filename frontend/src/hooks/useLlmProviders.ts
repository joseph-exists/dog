/**
 * useLlmProviders Hook
 *
 * Provides access to the user's LLM providers with computed helpers.
 * Uses TanStack Query for caching and automatic refetching.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import {
  type CreateProviderInput,
  LLM_PROVIDER_QUERY_KEYS,
  type LLMProviderType,
  LlmProviderService,
  type ProviderViewModel,
  type UpdateProviderInput,
} from "@/services/llmProviderService"
import { handleError } from "@/utils"
import useCustomToast from "./useCustomToast"

export interface UseLlmProvidersReturn {
  /** All providers */
  providers: ProviderViewModel[]
  /** Only enabled providers */
  enabledProviders: ProviderViewModel[]
  /** Only usable providers (enabled and not failed) */
  usableProviders: ProviderViewModel[]
  /** Default provider for each type */
  defaultByType: Record<LLMProviderType, ProviderViewModel | null>
  /** Providers grouped by type */
  providersByType: Record<LLMProviderType, ProviderViewModel[]>
  /** Whether user has any providers configured */
  hasAnyProvider: boolean
  /** Whether user has any usable providers */
  hasUsableProvider: boolean
  /** Loading state */
  isLoading: boolean
  /** Error state */
  error: Error | null
  /** Refresh providers list */
  refresh: () => void
  /** Create a new provider */
  createProvider: (data: CreateProviderInput) => Promise<ProviderViewModel>
  /** Update an existing provider */
  updateProvider: (
    providerId: string,
    data: UpdateProviderInput,
  ) => Promise<ProviderViewModel>
  /** Delete a provider */
  deleteProvider: (providerId: string) => Promise<void>
  /** Test a provider */
  testProvider: (providerId: string) => Promise<void>
  /** Mutation states */
  isCreating: boolean
  isUpdating: boolean
  isDeleting: boolean
  isTesting: boolean
}

/**
 * Hook for managing user's LLM providers
 */
export function useLlmProviders(): UseLlmProvidersReturn {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  // Query for providers list
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: LLM_PROVIDER_QUERY_KEYS.providers,
    queryFn: () => LlmProviderService.listProviders(),
    staleTime: 30000, // 30 seconds
  })

  const providers = data?.providers ?? []

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (input: CreateProviderInput) =>
      LlmProviderService.createProvider(input),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: LLM_PROVIDER_QUERY_KEYS.providers,
      })
      showSuccessToast("Provider created successfully")
    },
    onError: handleError.bind(showErrorToast),
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({
      providerId,
      data,
    }: {
      providerId: string
      data: UpdateProviderInput
    }) => LlmProviderService.updateProvider(providerId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: LLM_PROVIDER_QUERY_KEYS.providers,
      })
      showSuccessToast("Provider updated successfully")
    },
    onError: handleError.bind(showErrorToast),
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (providerId: string) =>
      LlmProviderService.deleteProvider(providerId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: LLM_PROVIDER_QUERY_KEYS.providers,
      })
      showSuccessToast("Provider deleted successfully")
    },
    onError: handleError.bind(showErrorToast),
  })

  // Test mutation
  const testMutation = useMutation({
    mutationFn: (providerId: string) =>
      LlmProviderService.testProvider(providerId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: LLM_PROVIDER_QUERY_KEYS.providers,
      })
      showSuccessToast("Provider test successful")
    },
    onError: handleError.bind(showErrorToast),
  })

  // Compute derived values
  const enabledProviders = LlmProviderService.filterEnabled(providers)
  const usableProviders = LlmProviderService.filterUsable(providers)
  const providersByType = LlmProviderService.groupByType(providers)

  const defaultByType: Record<LLMProviderType, ProviderViewModel | null> = {
    openai: LlmProviderService.getDefaultForType(providers, "openai"),
    anthropic: LlmProviderService.getDefaultForType(providers, "anthropic"),
    google: LlmProviderService.getDefaultForType(providers, "google"),
    openai_compatible: LlmProviderService.getDefaultForType(
      providers,
      "openai_compatible",
    ),
  }

  return {
    providers,
    enabledProviders,
    usableProviders,
    defaultByType,
    providersByType,
    hasAnyProvider: providers.length > 0,
    hasUsableProvider: usableProviders.length > 0,
    isLoading,
    error: error as Error | null,
    refresh: () => refetch(),
    createProvider: async (input) => {
      return createMutation.mutateAsync(input)
    },
    updateProvider: async (providerId, data) => {
      return updateMutation.mutateAsync({ providerId, data })
    },
    deleteProvider: async (providerId) => {
      await deleteMutation.mutateAsync(providerId)
    },
    testProvider: async (providerId) => {
      await testMutation.mutateAsync(providerId)
    },
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    isTesting: testMutation.isPending,
  }
}

export default useLlmProviders
