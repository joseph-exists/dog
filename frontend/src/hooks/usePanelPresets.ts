/**
 * usePanelPresets Hook
 *
 * Provides access to available layout presets.
 *
 * @example
 * ```tsx
 * const { presets, isLoading, getPreset } = usePanelPresets()
 *
 * // Get a specific preset
 * const focusPreset = getPreset("focus")
 * ```
 */

import { useQuery } from "@tanstack/react-query"
import { useMemo } from "react"

import { listPresets, type PresetViewModel } from "@/services/presetService"

// ============================================================================
// Query Keys
// ============================================================================

const QUERY_KEY = ["presets"] as const

// ============================================================================
// Hook
// ============================================================================

export function usePanelPresets() {
  const query = useQuery({
    queryKey: QUERY_KEY,
    queryFn: listPresets,
    // Presets are static, cache aggressively
    staleTime: 1000 * 60 * 60, // 1 hour
  })

  // Create a lookup map for quick access
  const presetMap = useMemo(() => {
    if (!query.data) return new Map<string, PresetViewModel>()
    return new Map(query.data.map((p) => [p.id, p]))
  }, [query.data])

  return {
    /** List of all available presets */
    presets: query.data ?? [],

    /** Loading state */
    isLoading: query.isLoading,

    /** Error state */
    error: query.error,

    /** Get a preset by ID */
    getPreset: (id: string) => presetMap.get(id),

    /** Check if a preset ID is valid */
    isValidPreset: (id: string) => presetMap.has(id),
  }
}
