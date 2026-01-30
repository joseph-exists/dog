/**
 * useLlmProviders Hook
 *
 * Provides access to the user's access providers (API credentials) with computed helpers.
 * Uses TanStack Query for caching and automatic refetching.
 *
 * Note: This hook wraps userAccessProviderService for managing user's API access credentials.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback } from "react"

import {
  type CreateUserAccessProviderInput,
  type UpdateUserAccessProviderInput,
  type UserAccessProviderViewModel,
  UserAccessProviderService,
  USER_ACCESS_PROVIDER_QUERY_KEYS,
} from "@/services/userAccessProviderService"
import { handleError } from "@/utils"
import { showErrorToast, showSuccessToast } from "./useCustomToast"

export interface UseLlmProvidersReturn {
  /** All providers */
  providers: UserAccessProviderViewModel[]
  /** Only enabled providers */
  enabledProviders: UserAccessProviderViewModel[]
  /** Only usable providers (enabled and not failed) */
  usableProviders: UserAccessProviderViewModel[]
  /** Only validated providers */
  validatedProviders: UserAccessProviderViewModel[]
  /** Default provider */
  defaultProvider: UserAccessProviderViewModel | null
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
  createProvider: (data: CreateUserAccessProviderInput) => Promise<UserAccessProviderViewModel>
  /** Update an existing provider */
  updateProvider: (
    providerId: string,
    data: UpdateUserAccessProviderInput,
  ) => Promise<UserAccessProviderViewModel>
  /** Delete a provider */
  deleteProvider: (providerId: string) => Promise<void>
  /** Test a provider */
  testProvider: (providerId: string) => Promise<void>
  /** Set as default provider */
  setDefaultProvider: (providerId: string) => Promise<void>
  /** Mutation states */
  isCreating: boolean
  isUpdating: boolean
  isDeleting: boolean
  isTesting: boolean
}

/**
 * Hook for managing user's access providers (API credentials)
 */
export function useLlmProviders(): UseLlmProvidersReturn {
  const queryClient = useQueryClient()

  // Query for providers list
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: USER_ACCESS_PROVIDER_QUERY_KEYS.providers,
    queryFn: () => UserAccessProviderService.listUserAccessProviders(),
    staleTime: 30000, // 30 seconds
  })

  const providers = data?.providers ?? []

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (input: CreateUserAccessProviderInput) =>
      UserAccessProviderService.createProvider(input),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: USER_ACCESS_PROVIDER_QUERY_KEYS.providers,
      })
      showSuccessToast("Access provider created successfully")
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
      data: UpdateUserAccessProviderInput
    }) => UserAccessProviderService.updateProvider(providerId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: USER_ACCESS_PROVIDER_QUERY_KEYS.providers,
      })
      showSuccessToast("Access provider updated successfully")
    },
    onError: handleError.bind(showErrorToast),
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (providerId: string) =>
      UserAccessProviderService.deleteProvider(providerId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: USER_ACCESS_PROVIDER_QUERY_KEYS.providers,
      })
      showSuccessToast("Access provider deleted successfully")
    },
    onError: handleError.bind(showErrorToast),
  })

  // Test mutation (not yet implemented in backend)
  const testMutation = useMutation({
    mutationFn: async (providerId: string) => {
      try {
        await UserAccessProviderService.testProvider(providerId)
      } catch (error) {
        // Backend endpoint not implemented yet, just log for now
        console.warn("Test provider endpoint not yet implemented:", error)
        throw new Error("Test provider functionality not yet available")
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: USER_ACCESS_PROVIDER_QUERY_KEYS.providers,
      })
      showSuccessToast("Access provider test successful")
    },
    onError: handleError.bind(showErrorToast),
  })

  // Set default mutation
  const setDefaultMutation = useMutation({
    mutationFn: (providerId: string) =>
      UserAccessProviderService.setDefault(providerId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: USER_ACCESS_PROVIDER_QUERY_KEYS.providers,
      })
      showSuccessToast("Default provider updated")
    },
    onError: handleError.bind(showErrorToast),
  })

  // Compute derived values using service utilities
  const enabledProviders = UserAccessProviderService.filterEnabled(providers)
  const usableProviders = UserAccessProviderService.filterUsable(providers)
  const validatedProviders = UserAccessProviderService.filterValidated(providers)
  const defaultProvider = UserAccessProviderService.getDefaultProvider(providers)

  // Stable function references — safe to use in dependency arrays
  const refresh = useCallback(() => refetch(), [refetch])

  const createProvider = useCallback(
    (input: CreateUserAccessProviderInput) => createMutation.mutateAsync(input),
    [createMutation],
  )

  const updateProvider = useCallback(
    (providerId: string, data: UpdateUserAccessProviderInput) =>
      updateMutation.mutateAsync({ providerId, data }),
    [updateMutation],
  )

  const deleteProvider = useCallback(
    async (providerId: string) => {
      await deleteMutation.mutateAsync(providerId)
    },
    [deleteMutation],
  )

  const testProvider = useCallback(
    async (providerId: string) => {
      await testMutation.mutateAsync(providerId)
    },
    [testMutation],
  )

  const setDefaultProvider = useCallback(
    async (providerId: string) => {
      await setDefaultMutation.mutateAsync(providerId)
    },
    [setDefaultMutation],
  )

  return {
    providers,
    enabledProviders,
    usableProviders,
    validatedProviders,
    defaultProvider,
    hasAnyProvider: providers.length > 0,
    hasUsableProvider: usableProviders.length > 0,
    isLoading,
    error: error as Error | null,
    refresh,
    createProvider,
    updateProvider,
    deleteProvider,
    testProvider,
    setDefaultProvider,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    isTesting: testMutation.isPending,
  }
}

export default useLlmProviders
