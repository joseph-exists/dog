/**
 * User Panel Defaults Service
 *
 * Manages user's global default panel layout.
 * Uses ViewModel pattern - never expose raw API types to components.
 *
 * @see panelService.ts for room-level panel operations
 */

import {
  type UserPanelDefaultsPublic,
  type UserPanelDefaultsUpdate,
  UserPanelsService,
} from "@/client"

import type { PanelConfig } from "./panelService"

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * User panel defaults ViewModel
 *
 * Represents the user's global panel layout preferences.
 * - presetId: Selected system preset (focus, collaborate, etc.)
 * - panels: Custom panel arrangement (used if no preset selected)
 * - reduceMotion: Accessibility preference
 */
export interface UserPanelDefaultsViewModel {
  id: string
  userId: string
  presetId: string | null
  panels: PanelConfig[]
  reduceMotion: boolean
  updatedAt: Date
}

/**
 * Input for updating user panel defaults
 */
export interface UpdateUserPanelDefaultsInput {
  presetId?: string | null
  panels?: PanelConfig[] | null
  reduceMotion?: boolean
}

// Re-export API types for consumers that need them
export type { UserPanelDefaultsPublic, UserPanelDefaultsUpdate }

// ============================================================================
// Mappers
// ============================================================================

/**
 * Convert API response to ViewModel
 */
function toViewModel(
  data: UserPanelDefaultsPublic,
): UserPanelDefaultsViewModel {
  return {
    id: data.id,
    userId: data.user_id,
    presetId: data.preset_id ?? null,
    panels: (data.panels ?? []) as unknown as PanelConfig[],
    reduceMotion: data.reduce_motion,
    updatedAt: new Date(data.updated_at),
  }
}

// ============================================================================
// Service Functions
// ============================================================================

/**
 * Get current user's global panel defaults
 *
 * Returns the user's default panel layout preferences, or null if not set.
 * When null, the system uses built-in defaults (collaborate preset).
 */
export async function getUserPanelDefaults(): Promise<UserPanelDefaultsViewModel | null> {
  const response = await UserPanelsService.getMyPanelDefaults()
  if (!response) return null
  return toViewModel(response)
}

/**
 * Update current user's global panel defaults
 *
 * Sets the user's default panel layout preferences.
 * Can set either a preset ID or custom panels (or both).
 *
 * @param input - Fields to update (partial update supported)
 */
export async function updateUserPanelDefaults(
  input: UpdateUserPanelDefaultsInput,
): Promise<UserPanelDefaultsViewModel> {
  const requestBody: UserPanelDefaultsUpdate = {}

  if (input.presetId !== undefined) {
    requestBody.preset_id = input.presetId
  }
  if (input.panels !== undefined) {
    requestBody.panels = input.panels as unknown as Array<{
      [key: string]: unknown
    }>
  }
  if (input.reduceMotion !== undefined) {
    requestBody.reduce_motion = input.reduceMotion
  }

  const response = await UserPanelsService.updateMyPanelDefaults({
    requestBody,
  })
  return toViewModel(response)
}
