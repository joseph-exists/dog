/**
 * useUserPanelDefaults Hook
 *
 * Manages user's global panel defaults with React Query.
 * Provides the user's default layout that applies to all rooms.
 *
 * @example
 * ```tsx
 * const { defaults, updateDefaults, isLoading } = useUserPanelDefaults()
 *
 * // Apply a preset
 * updateDefaults({ presetId: "focus" })
 *
 * // Set custom panels
 * updateDefaults({ panels: [...], presetId: null })
 * ```
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import {
  getUserPanelDefaults,
  type UpdateUserPanelDefaultsInput,
  updateUserPanelDefaults,
} from "@/services/userPanelDefaultsService"

// ============================================================================
// Query Keys
// ============================================================================

const QUERY_KEY = ["user", "panel-defaults"] as const

// ============================================================================
// Hook
// ============================================================================

export function useUserPanelDefaults() {
  const queryClient = useQueryClient()

  // Fetch user's defaults
  const query = useQuery({
    queryKey: QUERY_KEY,
    queryFn: getUserPanelDefaults,
  })

  // Update mutation
  const mutation = useMutation({
    mutationFn: updateUserPanelDefaults,
    onSuccess: (data) => {
      // Update cache immediately
      queryClient.setQueryData(QUERY_KEY, data)
      // Also invalidate room panels since they might use this default
      queryClient.invalidateQueries({ queryKey: ["rooms"] })
    },
  })

  return {
    /** User's default panel configuration */
    defaults: query.data,

    /** Loading state */
    isLoading: query.isLoading,

    /** Error state */
    error: query.error,

    /** Update defaults */
    updateDefaults: mutation.mutate,

    /** Async update defaults */
    updateDefaultsAsync: mutation.mutateAsync,

    /** Whether update is in progress */
    isUpdating: mutation.isPending,

    /** Convenience: set a preset */
    setPreset: (presetId: string) => {
      mutation.mutate({ presetId, panels: null })
    },

    /** Convenience: set custom panels */
    setCustomPanels: (panels: UpdateUserPanelDefaultsInput["panels"]) => {
      mutation.mutate({ presetId: null, panels })
    },

    /** Convenience: toggle reduce motion */
    setReduceMotion: (reduceMotion: boolean) => {
      mutation.mutate({ reduceMotion })
    },
  }
}
