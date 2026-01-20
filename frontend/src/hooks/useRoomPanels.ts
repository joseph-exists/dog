/**
 * useRoomPanels Hook
 *
 * Manages room panel configuration with React Query.
 * Handles resolving, updating, and toggling between
 * room defaults and user overrides.
 *
 * Features:
 * - Fetches resolved panel config for current user
 * - Manages room defaults (owner only)
 * - Manages user overrides
 * - Provides convenience methods for common operations
 *
 * @example
 * ```tsx
 * const { panels, panelSource, setCustomPanels } = useRoomPanels(roomId)
 *
 * // panels = [{ id: "chat", kind: "chat", prominence: "primary" }, ...]
 * // panelSource = "room_defaults" | "user_override" | "type_defaults"
 * ```
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import {
  getMyPanelConfig,
  getResolvedPanels,
  getRoomPanelDefaults,
  type PanelConfig,
  updateMyPanelConfig,
  updateRoomPanelDefaults,
} from "@/services/panelService"

interface UseRoomPanelsOptions {
  /** Whether to fetch panel config (default: true) */
  enabled?: boolean
}

/**
 * Hook for managing room panel configuration
 *
 * @param roomId - The room ID to manage panels for
 * @param options - Configuration options
 */
export function useRoomPanels(
  roomId: string,
  options: UseRoomPanelsOptions = {},
) {
  const { enabled = true } = options
  const queryClient = useQueryClient()

  // Query keys for cache management
  const baseKey = ["rooms", roomId, "panels"] as const
  const defaultsKey = [...baseKey, "defaults"] as const
  const myConfigKey = [...baseKey, "me"] as const

  // Resolved panels for current user
  const resolvedQuery = useQuery({
    queryKey: baseKey,
    queryFn: () => getResolvedPanels(roomId),
    enabled,
  })

  // Room defaults (for owner editing)
  const defaultsQuery = useQuery({
    queryKey: defaultsKey,
    queryFn: () => getRoomPanelDefaults(roomId),
    enabled,
  })

  // User's personal config
  const myConfigQuery = useQuery({
    queryKey: myConfigKey,
    queryFn: () => getMyPanelConfig(roomId),
    enabled,
  })

  // Update room defaults (owner only)
  const updateDefaultsMutation = useMutation({
    mutationFn: (panels: PanelConfig[]) =>
      updateRoomPanelDefaults(roomId, panels),
    onSuccess: () => {
      // Invalidate all panel queries to refresh resolved panels
      queryClient.invalidateQueries({ queryKey: baseKey })
    },
  })

  // Update user's config
  const updateMyConfigMutation = useMutation({
    mutationFn: ({
      panels,
      useRoomDefaults,
    }: {
      panels: PanelConfig[] | null
      useRoomDefaults: boolean
    }) => updateMyPanelConfig(roomId, panels, useRoomDefaults),
    onSuccess: () => {
      // Invalidate all panel queries to refresh resolved panels
      queryClient.invalidateQueries({ queryKey: baseKey })
    },
  })

  return {
    // ========================================================================
    // Resolved panels (what to render)
    // ========================================================================

    /** The effective panel configuration for this user */
    panels: resolvedQuery.data?.panels ?? [],

    /** Where the config came from: "user_override" | "room_defaults" | "type_defaults" */
    panelSource: resolvedQuery.data?.source,

    /** Loading state for resolved panels */
    isLoading: resolvedQuery.isLoading,

    /** Error from fetching resolved panels */
    error: resolvedQuery.error,

    // ========================================================================
    // Room defaults (owner can edit)
    // ========================================================================

    /** Room's default panel config (null if not set) */
    roomDefaults: defaultsQuery.data,

    /** Loading state for room defaults */
    isLoadingDefaults: defaultsQuery.isLoading,

    // ========================================================================
    // User's personal config
    // ========================================================================

    /** User's personal panel override config */
    myConfig: myConfigQuery.data,

    /** Whether user is using room/type defaults */
    isUsingRoomDefaults: myConfigQuery.data?.use_room_defaults ?? true,

    // ========================================================================
    // Mutations
    // ========================================================================

    /** Update room's default panels (owner only) */
    updateRoomDefaults: updateDefaultsMutation.mutate,

    /** Whether room defaults are being updated */
    isUpdatingDefaults: updateDefaultsMutation.isPending,

    /** Update user's personal config */
    updateMyConfig: updateMyConfigMutation.mutate,

    /** Whether user config is being updated */
    isUpdatingMyConfig: updateMyConfigMutation.isPending,

    // ========================================================================
    // Convenience methods
    // ========================================================================

    /**
     * Toggle between using room defaults and personal config
     */
    setUseRoomDefaults: (useDefaults: boolean) => {
      updateMyConfigMutation.mutate({
        panels: (myConfigQuery.data?.panels as PanelConfig[] | null) ?? null,
        useRoomDefaults: useDefaults,
      })
    },

    /**
     * Set a custom panel configuration (automatically disables room defaults)
     */
    setCustomPanels: (panels: PanelConfig[]) => {
      updateMyConfigMutation.mutate({
        panels,
        useRoomDefaults: false,
      })
    },

    /**
     * Reset to room/type defaults
     */
    resetToDefaults: () => {
      updateMyConfigMutation.mutate({
        panels: null,
        useRoomDefaults: true,
      })
    },
  }
}
