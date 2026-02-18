/**
 * useThemeBinding Hook
 *
 * Resolves and caches theme bindings for a given context.
 * Provides the effective theme(s) for page, cards, syntax, and motion slots.
 *
 * @example
 * ```tsx
 * // Resolve a single slot
 * const { theme, source, isLoading } = useThemeBinding("page", ["page:story"])
 *
 * // Resolve multiple slots at once (more efficient)
 * const { themes, isLoading } = useThemeBindings(
 *   ["page", "cards", "syntax"],
 *   ["page:story", "panel:editor"]
 * )
 *
 * // With entity context for authored themes
 * const { theme } = useThemeBinding("cards", ["story:abc123"], {
 *   entityContext: { entityType: "story", entityId: "abc123", ownerId: "user456" }
 * })
 * ```
 */

import { useQuery } from "@tanstack/react-query"

import {
  type BatchResolvedThemes,
  type EntityContext,
  type ResolvedTheme,
  resolveTheme,
  resolveThemes,
  type ThemeSlot,
  type ThemeViewModel,
} from "@/services/themeService"

// ============================================================================
// Query Keys
// ============================================================================

export const themeBindingKeys = {
  all: ["theme-bindings"] as const,
  resolve: (
    slot: ThemeSlot,
    contextPath: string[],
    entityContext?: EntityContext,
  ) =>
    [
      ...themeBindingKeys.all,
      "resolve",
      slot,
      contextPath,
      entityContext,
    ] as const,
  resolveBatch: (
    slots: ThemeSlot[],
    contextPath: string[],
    entityContext?: EntityContext,
  ) =>
    [
      ...themeBindingKeys.all,
      "resolve-batch",
      slots,
      contextPath,
      entityContext,
    ] as const,
  userBindings: (contextPrefix?: string) =>
    [...themeBindingKeys.all, "user", contextPrefix] as const,
}

// ============================================================================
// Single Slot Resolution Hook
// ============================================================================

export interface UseThemeBindingOptions {
  /** Entity context for authored binding resolution */
  entityContext?: EntityContext
  /** Whether to enable the query (default: true) */
  enabled?: boolean
}

export interface UseThemeBindingResult {
  /** The resolved theme, or null if none */
  theme: ThemeViewModel | null
  /** How the theme was resolved */
  source: ResolvedTheme["source"]
  /** Which context key matched (for debugging) */
  contextKeyMatched: string | null
  /** Loading state */
  isLoading: boolean
  /** Error state */
  error: Error | null
  /** Refetch the resolution */
  refetch: () => void
}

/**
 * Resolve a single theme slot for a context
 *
 * @param slot - Which theme to resolve (page, cards, syntax, motion)
 * @param contextPath - Context path segments, e.g., ["page:story", "panel:debug"]
 * @param options - Additional options
 */
export function useThemeBinding(
  slot: ThemeSlot,
  contextPath: string[],
  options?: UseThemeBindingOptions,
): UseThemeBindingResult {
  const query = useQuery({
    queryKey: themeBindingKeys.resolve(
      slot,
      contextPath,
      options?.entityContext,
    ),
    queryFn: () => resolveTheme(slot, contextPath, options?.entityContext),
    enabled: options?.enabled ?? true,
    // Theme bindings change infrequently, cache aggressively
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
  })

  return {
    theme: query.data?.theme ?? null,
    source: query.data?.source ?? "none",
    contextKeyMatched: query.data?.contextKeyMatched ?? null,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  }
}

// ============================================================================
// Multi-Slot Resolution Hook (Batch)
// ============================================================================

export interface UseThemeBindingsOptions {
  /** Entity context for authored binding resolution */
  entityContext?: EntityContext
  /** Whether to enable the query (default: true) */
  enabled?: boolean
}

export interface UseThemeBindingsResult {
  /** Resolved themes keyed by slot */
  themes: BatchResolvedThemes
  /** Get a specific slot's theme */
  getTheme: (slot: ThemeSlot) => ThemeViewModel | null
  /** Get a specific slot's resolution source */
  getSource: (slot: ThemeSlot) => ResolvedTheme["source"]
  /** Loading state */
  isLoading: boolean
  /** Error state */
  error: Error | null
  /** Refetch all resolutions */
  refetch: () => void
}

/**
 * Resolve multiple theme slots at once (batch resolution)
 *
 * More efficient than multiple useThemeBinding calls when you need
 * several slots (e.g., page + cards + syntax for a story editor).
 *
 * @param slots - Which themes to resolve
 * @param contextPath - Context path segments
 * @param options - Additional options
 */
export function useThemeBindings(
  slots: ThemeSlot[],
  contextPath: string[],
  options?: UseThemeBindingsOptions,
): UseThemeBindingsResult {
  const query = useQuery({
    queryKey: themeBindingKeys.resolveBatch(
      slots,
      contextPath,
      options?.entityContext,
    ),
    queryFn: () => resolveThemes(slots, contextPath, options?.entityContext),
    enabled: (options?.enabled ?? true) && slots.length > 0,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  })

  const themes = query.data ?? {}

  return {
    themes,
    getTheme: (slot: ThemeSlot) => themes[slot]?.theme ?? null,
    getSource: (slot: ThemeSlot) => themes[slot]?.source ?? "none",
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  }
}

// ============================================================================
// Convenience Hooks for Common Patterns
// ============================================================================

/**
 * Resolve page and card themes together (common pattern for shells)
 */
export function usePageThemes(
  contextPath: string[],
  options?: UseThemeBindingsOptions,
) {
  return useThemeBindings(["page", "cards"], contextPath, options)
}

/**
 * Resolve all theme slots for a context
 */
export function useAllThemes(
  contextPath: string[],
  options?: UseThemeBindingsOptions,
) {
  return useThemeBindings(
    ["page", "cards", "syntax", "motion"],
    contextPath,
    options,
  )
}
