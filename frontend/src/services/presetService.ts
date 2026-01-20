/**
 * Preset Service
 *
 * Provides system presets for panel layouts.
 * Uses ViewModel pattern - never expose raw API types to components.
 *
 * @see userPanelDefaultsService.ts for applying presets to user defaults
 */

import { type PresetResponse, PresetsService } from "@/client"

import type { PanelConfig } from "./panelService"

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * Preset ViewModel
 *
 * Represents a panel layout preset (system or user-created).
 * - id: Preset identifier (e.g., "focus", "collaborate")
 * - name: Display name
 * - description: Brief explanation of the layout
 * - panels: The panel configuration
 * - isSystem: True for built-in presets
 */
export interface PresetViewModel {
  id: string
  name: string
  description: string
  panels: PanelConfig[]
  isSystem: boolean
}

// Re-export API types for consumers that need them
export type { PresetResponse }

// ============================================================================
// Mappers
// ============================================================================

/**
 * Convert API response to ViewModel
 */
function toViewModel(preset: PresetResponse): PresetViewModel {
  return {
    id: preset.id,
    name: preset.name,
    description: preset.description,
    panels: preset.panels as unknown as PanelConfig[],
    isSystem: preset.is_system,
  }
}

// ============================================================================
// Service Functions
// ============================================================================

/**
 * List all available presets
 *
 * Returns system presets and any user-created presets.
 * System presets: focus, collaborate, story_mode, debug, canvas
 */
export async function listPresets(): Promise<PresetViewModel[]> {
  const response = await PresetsService.listPresets()
  return response.presets.map(toViewModel)
}

/**
 * Get a specific preset by ID
 *
 * @param presetId - The preset identifier
 * @throws ApiError with 404 if preset not found
 */
export async function getPreset(presetId: string): Promise<PresetViewModel> {
  const preset = await PresetsService.getPreset({ presetId })
  return toViewModel(preset)
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get icon name for a preset (for UI display)
 */
export function getPresetIcon(
  presetId: string,
): "focus" | "users" | "book-open" | "bug" | "layout" {
  const icons: Record<
    string,
    "focus" | "users" | "book-open" | "bug" | "layout"
  > = {
    focus: "focus",
    collaborate: "users",
    story_mode: "book-open",
    debug: "bug",
    canvas: "layout",
  }
  return icons[presetId] ?? "layout"
}
