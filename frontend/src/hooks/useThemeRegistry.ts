/**
 * useThemeRegistry Hook
 *
 * Manages theme CRUD operations and user bindings with React Query.
 * Provides functions to list, create, update, delete themes and manage bindings.
 *
 * @example
 * ```tsx
 * // List available themes for a picker
 * const { availableThemes, isLoading } = useAvailableThemes("page")
 *
 * // Manage user bindings
 * const { setBinding, clearBinding, userBindings } = useUserThemeBindings()
 * setBinding({ contextKey: "page:story", slot: "page", themeId: "abc123" })
 *
 * // Full theme management
 * const { createTheme, updateTheme, deleteTheme } = useThemeManagement()
 * ```
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import {
  type CreateThemeInput,
  clearUserBinding,
  createTheme,
  deleteTheme,
  getAvailableThemes,
  getUserBindings,
  listThemes,
  type SetBindingInput,
  setUserBinding,
  type ThemeBindingViewModel,
  type ThemeCategory,
  type ThemeScope,
  type ThemeSlot,
  type ThemeViewModel,
  type UpdateThemeInput,
  updateTheme,
} from "@/services/themeService"

import { themeBindingKeys } from "./useThemeBinding"

// ============================================================================
// Query Keys
// ============================================================================

export const themeRegistryKeys = {
  all: ["themes"] as const,
  lists: () => [...themeRegistryKeys.all, "list"] as const,
  list: (filters?: { category?: ThemeCategory; scope?: ThemeScope }) =>
    [...themeRegistryKeys.lists(), filters] as const,
  available: (category: ThemeCategory) =>
    [...themeRegistryKeys.all, "available", category] as const,
  detail: (id: string) => [...themeRegistryKeys.all, "detail", id] as const,
}

// ============================================================================
// Available Themes Hook (for pickers)
// ============================================================================

export interface UseAvailableThemesResult {
  /** Themes available for this category */
  themes: ThemeViewModel[]
  /** Loading state */
  isLoading: boolean
  /** Error state */
  error: Error | null
  /** Refetch themes */
  refetch: () => void
}

/**
 * Get themes available for binding in a category
 *
 * This is the primary hook for theme pickers - returns all themes
 * the current user can select from.
 *
 * @param category - Theme category (page, card, syntax, motion)
 */
export function useAvailableThemes(
  category: ThemeCategory,
): UseAvailableThemesResult {
  const query = useQuery({
    queryKey: themeRegistryKeys.available(category),
    queryFn: () => getAvailableThemes(category),
    staleTime: 5 * 60 * 1000,
  })

  return {
    themes: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  }
}

// ============================================================================
// Theme List Hook
// ============================================================================

export interface UseThemeListOptions {
  category?: ThemeCategory
  scope?: ThemeScope
  includeSystem?: boolean
  skip?: number
  limit?: number
}

export interface UseThemeListResult {
  /** List of themes */
  themes: ThemeViewModel[]
  /** Total count (for pagination) */
  count: number
  /** Loading state */
  isLoading: boolean
  /** Error state */
  error: Error | null
  /** Refetch themes */
  refetch: () => void
}

/**
 * List themes with optional filters
 *
 * @param options - Filter and pagination options
 */
export function useThemeList(
  options?: UseThemeListOptions,
): UseThemeListResult {
  const query = useQuery({
    queryKey: themeRegistryKeys.list({
      category: options?.category,
      scope: options?.scope,
    }),
    queryFn: () => listThemes(options),
    staleTime: 5 * 60 * 1000,
  })

  return {
    themes: query.data?.themes ?? [],
    count: query.data?.count ?? 0,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  }
}

// ============================================================================
// User Bindings Hook
// ============================================================================

export interface UseUserThemeBindingsResult {
  /** User's current bindings */
  bindings: ThemeBindingViewModel[]
  /** Loading state */
  isLoading: boolean
  /** Error state */
  error: Error | null

  /** Set a binding (creates or updates) */
  setBinding: (input: SetBindingInput) => void
  /** Set a binding (async) */
  setBindingAsync: (input: SetBindingInput) => Promise<ThemeBindingViewModel>
  /** Whether a set operation is pending */
  isSettingBinding: boolean

  /** Clear a binding */
  clearBinding: (contextKey: string, slot: ThemeSlot) => void
  /** Clear a binding (async) */
  clearBindingAsync: (contextKey: string, slot: ThemeSlot) => Promise<void>
  /** Whether a clear operation is pending */
  isClearingBinding: boolean

  /** Refetch bindings */
  refetch: () => void
}

/**
 * Manage user's theme bindings
 *
 * @param contextPrefix - Optional prefix to filter bindings
 */
export function useUserThemeBindings(
  contextPrefix?: string,
): UseUserThemeBindingsResult {
  const queryClient = useQueryClient()

  // Fetch user bindings
  const query = useQuery({
    queryKey: themeBindingKeys.userBindings(contextPrefix),
    queryFn: () => getUserBindings(contextPrefix),
    staleTime: 2 * 60 * 1000,
  })

  // Set binding mutation
  const setMutation = useMutation({
    mutationFn: setUserBinding,
    onSuccess: () => {
      // Invalidate user bindings
      queryClient.invalidateQueries({
        queryKey: themeBindingKeys.userBindings(),
      })
      // Invalidate resolution cache (binding changed)
      queryClient.invalidateQueries({
        queryKey: themeBindingKeys.all,
      })
    },
  })

  // Clear binding mutation
  const clearMutation = useMutation({
    mutationFn: ({
      contextKey,
      slot,
    }: {
      contextKey: string
      slot: ThemeSlot
    }) => clearUserBinding(contextKey, slot),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: themeBindingKeys.userBindings(),
      })
      queryClient.invalidateQueries({
        queryKey: themeBindingKeys.all,
      })
    },
  })

  return {
    bindings: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error,

    setBinding: setMutation.mutate,
    setBindingAsync: setMutation.mutateAsync,
    isSettingBinding: setMutation.isPending,

    clearBinding: (contextKey, slot) =>
      clearMutation.mutate({ contextKey, slot }),
    clearBindingAsync: (contextKey, slot) =>
      clearMutation.mutateAsync({ contextKey, slot }),
    isClearingBinding: clearMutation.isPending,

    refetch: query.refetch,
  }
}

// ============================================================================
// Theme Management Hook (CRUD)
// ============================================================================

export interface UseThemeManagementResult {
  /** Create a new theme */
  createTheme: (input: CreateThemeInput) => void
  /** Create a new theme (async) */
  createThemeAsync: (input: CreateThemeInput) => Promise<ThemeViewModel>
  /** Whether create is pending */
  isCreating: boolean

  /** Update a theme */
  updateTheme: (themeId: string, input: UpdateThemeInput) => void
  /** Update a theme (async) */
  updateThemeAsync: (
    themeId: string,
    input: UpdateThemeInput,
  ) => Promise<ThemeViewModel>
  /** Whether update is pending */
  isUpdating: boolean

  /** Delete a theme */
  deleteTheme: (themeId: string) => void
  /** Delete a theme (async) */
  deleteThemeAsync: (themeId: string) => Promise<void>
  /** Whether delete is pending */
  isDeleting: boolean
}

/**
 * Theme CRUD operations
 *
 * For creating, updating, and deleting user themes.
 */
export function useThemeManagement(): UseThemeManagementResult {
  const queryClient = useQueryClient()

  // Create mutation
  const createMutation = useMutation({
    mutationFn: createTheme,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: themeRegistryKeys.all })
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({
      themeId,
      input,
    }: {
      themeId: string
      input: UpdateThemeInput
    }) => updateTheme(themeId, input),
    onSuccess: (data) => {
      // Update cache for this specific theme
      queryClient.setQueryData(themeRegistryKeys.detail(data.id), data)
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: themeRegistryKeys.lists() })
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: deleteTheme,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: themeRegistryKeys.all })
      // Also invalidate bindings (cascade delete may have occurred)
      queryClient.invalidateQueries({ queryKey: themeBindingKeys.all })
    },
  })

  return {
    createTheme: createMutation.mutate,
    createThemeAsync: createMutation.mutateAsync,
    isCreating: createMutation.isPending,

    updateTheme: (themeId, input) => updateMutation.mutate({ themeId, input }),
    updateThemeAsync: (themeId, input) =>
      updateMutation.mutateAsync({ themeId, input }),
    isUpdating: updateMutation.isPending,

    deleteTheme: deleteMutation.mutate,
    deleteThemeAsync: deleteMutation.mutateAsync,
    isDeleting: deleteMutation.isPending,
  }
}
