/**
 * Theme Service
 *
 * Manages theme registry and bindings via the API.
 * Uses ViewModel pattern - transforms API types to frontend-friendly interfaces.
 *
 * @see useThemeBinding.ts for resolution hook
 * @see useThemeRegistry.ts for theme CRUD hook
 */

import {
  type BatchResolveThemeRequest,
  type ResolutionSource,
  type ResolvedThemeResponse,
  type ThemeBindingCreate,
  type ThemeBindingPublic,
  ThemeBindingsService,
  type ThemeCategory,
  type ThemeCreate,
  type ThemePublic,
  type ThemeScope,
  type ThemeSlot,
  ThemesService,
  type ThemeUpdate,
  // type BatchResolvedThemesResponse,
} from "@/client"

// ============================================================================
// Type Definitions - ViewModels
// ============================================================================

/**
 * Theme ViewModel
 *
 * Represents a theme definition with frontend-friendly types.
 */
export interface ThemeViewModel {
  id: string
  name: string
  description: string | null
  category: ThemeCategory
  scope: ThemeScope
  ownerId: string | null
  isSystem: boolean
  tokens: Record<string, unknown>
  createdAt: Date
  updatedAt: Date
}

/**
 * Theme binding ViewModel
 */
export interface ThemeBindingViewModel {
  id: string
  bindingType: "user_pref" | "authored"
  ownerId: string
  contextKey: string
  slot: ThemeSlot
  themeId: string
  createdAt: Date
  updatedAt: Date
}

/**
 * Resolved theme result
 */
export interface ResolvedTheme {
  theme: ThemeViewModel | null
  source: ResolutionSource
  contextKeyMatched: string | null
}

/**
 * Batch resolved themes result (keyed by slot)
 */
export type BatchResolvedThemes = {
  [K in ThemeSlot]?: ResolvedTheme
}

/**
 * Input for creating a theme
 */
export interface CreateThemeInput {
  name: string
  description?: string
  category: ThemeCategory
  scope?: ThemeScope
  tokens: Record<string, unknown>
}

/**
 * Input for updating a theme
 */
export interface UpdateThemeInput {
  name?: string
  description?: string
  scope?: ThemeScope
  tokens?: Record<string, unknown>
}

/**
 * Input for setting a user binding
 */
export interface SetBindingInput {
  contextKey: string
  slot: ThemeSlot
  themeId: string
}

/**
 * Entity context for authored binding resolution
 */
export interface EntityContext {
  entityType: string
  entityId: string
  ownerId: string
}

// Re-export API types for consumers
export type { ThemeCategory, ThemeScope, ThemeSlot, ResolutionSource }

// ============================================================================
// Mappers
// ============================================================================

/**
 * Convert API theme to ViewModel
 */
function themeToViewModel(data: ThemePublic): ThemeViewModel {
  return {
    id: data.id,
    name: data.name,
    description: data.description ?? null,
    category: data.category,
    scope: data.scope ?? "personal",
    ownerId: data.owner_id,
    isSystem: data.is_system,
    tokens: (data.tokens ?? {}) as Record<string, unknown>,
    createdAt: new Date(data.created_at),
    updatedAt: new Date(data.updated_at),
  }
}

/**
 * Convert API binding to ViewModel
 */
function bindingToViewModel(data: ThemeBindingPublic): ThemeBindingViewModel {
  return {
    id: data.id,
    bindingType: data.binding_type,
    ownerId: data.owner_id,
    contextKey: data.context_key,
    slot: data.slot,
    themeId: data.theme_id,
    createdAt: new Date(data.created_at),
    updatedAt: new Date(data.updated_at),
  }
}

/**
 * Convert API resolved theme to ViewModel
 */
function resolvedToViewModel(data: ResolvedThemeResponse): ResolvedTheme {
  return {
    theme: data.theme ? themeToViewModel(data.theme) : null,
    source: data.source,
    contextKeyMatched: data.context_key_matched ?? null,
  }
}

// ============================================================================
// Theme Registry Service Functions
// ============================================================================

/**
 * List all themes visible to the current user
 */
export async function listThemes(options?: {
  category?: ThemeCategory
  scope?: ThemeScope
  includeSystem?: boolean
  skip?: number
  limit?: number
}): Promise<{ themes: ThemeViewModel[]; count: number }> {
  const response = await ThemesService.listAllThemes({
    category: options?.category,
    scope: options?.scope,
    includeSystem: options?.includeSystem,
    skip: options?.skip,
    limit: options?.limit,
  })
  return {
    themes: response.data.map(themeToViewModel),
    count: response.count,
  }
}

/**
 * Get available themes for a category (for theme pickers)
 */
export async function getAvailableThemes(
  category: ThemeCategory,
): Promise<ThemeViewModel[]> {
  const response = await ThemesService.getAvailableThemes({ category })
  return response.map(themeToViewModel)
}

/**
 * Get a single theme by ID
 */
export async function getTheme(themeId: string): Promise<ThemeViewModel> {
  const response = await ThemesService.getTheme({ themeId })
  return themeToViewModel(response)
}

/**
 * Create a new theme
 */
export async function createTheme(
  input: CreateThemeInput,
): Promise<ThemeViewModel> {
  const requestBody: ThemeCreate = {
    name: input.name,
    description: input.description,
    category: input.category,
    scope: input.scope,
    tokens: input.tokens,
  }
  const response = await ThemesService.createNewTheme({ requestBody })
  return themeToViewModel(response)
}

/**
 * Update an existing theme
 */
export async function updateTheme(
  themeId: string,
  input: UpdateThemeInput,
): Promise<ThemeViewModel> {
  const requestBody: ThemeUpdate = {}
  if (input.name !== undefined) requestBody.name = input.name
  if (input.description !== undefined)
    requestBody.description = input.description
  if (input.scope !== undefined) requestBody.scope = input.scope
  if (input.tokens !== undefined) requestBody.tokens = input.tokens

  const response = await ThemesService.updateExistingTheme({
    themeId,
    requestBody,
  })
  return themeToViewModel(response)
}

/**
 * Delete a theme
 */
export async function deleteTheme(themeId: string): Promise<void> {
  await ThemesService.deleteExistingTheme({ themeId })
}

// ============================================================================
// Theme Binding Service Functions
// ============================================================================

/**
 * Get current user's theme bindings
 */
export async function getUserBindings(
  contextPrefix?: string,
): Promise<ThemeBindingViewModel[]> {
  const response = await ThemeBindingsService.getMyBindings({
    contextPrefix,
  })
  return response.data.map(bindingToViewModel)
}

/**
 * Set a user preference binding
 */
export async function setUserBinding(
  input: SetBindingInput,
): Promise<ThemeBindingViewModel> {
  const requestBody: ThemeBindingCreate = {
    binding_type: "user_pref",
    context_key: input.contextKey,
    slot: input.slot,
    theme_id: input.themeId,
  }
  const response = await ThemeBindingsService.setMyBinding({ requestBody })
  return bindingToViewModel(response)
}

/**
 * Clear a user preference binding
 */
export async function clearUserBinding(
  contextKey: string,
  slot: ThemeSlot,
): Promise<void> {
  await ThemeBindingsService.clearMyBinding({ contextKey, slot })
}

// ============================================================================
// Theme Resolution Service Functions
// ============================================================================

/**
 * Resolve the effective theme for a context
 *
 * @param slot - Which theme slot to resolve (page, cards, syntax, motion)
 * @param contextPath - Context path segments, e.g., ["page:story", "panel:debug"]
 * @param entityContext - Optional entity context for authored bindings
 */
export async function resolveTheme(
  slot: ThemeSlot,
  contextPath: string[],
  entityContext?: EntityContext,
): Promise<ResolvedTheme> {
  const response = await ThemeBindingsService.resolveSingleTheme({
    slot,
    contextPath: contextPath.join(","),
    entityType: entityContext?.entityType,
    entityId: entityContext?.entityId,
    entityOwnerId: entityContext?.ownerId,
  })
  return resolvedToViewModel(response)
}

/**
 * Resolve multiple theme slots in a single request
 *
 * More efficient when loading a page that needs multiple themes.
 *
 * @param slots - Which slots to resolve
 * @param contextPath - Context path segments
 * @param entityContext - Optional entity context for authored bindings
 */
export async function resolveThemes(
  slots: ThemeSlot[],
  contextPath: string[],
  entityContext?: EntityContext,
): Promise<BatchResolvedThemes> {
  const requestBody: BatchResolveThemeRequest = {
    slots,
    context_path: contextPath,
    entity_context: entityContext
      ? {
          entity_type: entityContext.entityType,
          entity_id: entityContext.entityId,
          owner_id: entityContext.ownerId,
        }
      : undefined,
  }

  const response = await ThemeBindingsService.resolveMultipleThemes({
    requestBody,
  })

  // Transform results
  const result: BatchResolvedThemes = {}
  for (const [slot, resolved] of Object.entries(response.results)) {
    result[slot as ThemeSlot] = resolvedToViewModel(resolved)
  }
  return result
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Convert theme tokens to React inline style object.
 * Only includes CSS custom properties — safe, scoped, no injection risk.
 *
 * Works with both backend themes (from API) and local theme definitions.
 */
export function themeTokensToStyle(
  tokens?: Record<string, unknown>,
): React.CSSProperties | undefined {
  if (!tokens || Object.keys(tokens).length === 0) return undefined

  const style: Record<string, string> = {}
  for (const [key, value] of Object.entries(tokens)) {
    if (value !== undefined && typeof value === "string") {
      style[key] = value
    }
  }

  return style as unknown as React.CSSProperties
}

/**
 * Build a context key from path segments
 */
export function buildContextKey(segments: string[]): string {
  return segments.join("/")
}

/**
 * Parse a context key into path segments
 */
export function parseContextKey(contextKey: string): string[] {
  return contextKey.split("/").filter(Boolean)
}

/**
 * Map ThemeSlot to ThemeCategory
 */
export const slotToCategory: Record<ThemeSlot, ThemeCategory> = {
  page: "page",
  cards: "card",
  syntax: "syntax",
  motion: "motion",
}
