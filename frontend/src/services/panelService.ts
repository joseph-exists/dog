/**
 * Panel Configuration Service
 *
 * Manages panel configuration for any Page entity (Room, Story, etc.).
 * Handles the layered resolution: user override → entity defaults → type defaults
 *
 * Architecture:
 * - Types imported from Page/registry/panelTypes (single source of truth)
 * - Routes to appropriate backend service based on entityType
 * - Wraps OpenAPI client methods for panel configuration
 *
 * @see backend/app/crud_panels.py for resolution logic
 */

import {
  type ResolvedPanelConfig,
  type RoomPanelDefaultsPublic,
  RoomPanelsService,
  type UserRoomPanelConfigPublic,
} from "@/client"
import type {
  PanelKind,
  PanelProminence,
} from "@/components/Page/registry/panelTypes"

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * Panel configuration item for layouts.
 * Uses PanelKind from registry as single source of truth.
 */
export interface PanelConfig {
  id: string
  kind: PanelKind
  prominence: PanelProminence
}

/**
 * Supported entity types for panel configuration.
 * Add new types here as backend support is added.
 */
export type PanelEntityType = "room" | "story"

/**
 * Resolved panel configuration with source tracking.
 *
 * The source tells us where the configuration came from:
 * - user_override: User has custom config for this entity
 * - entity_defaults: Using entity owner's defaults
 * - type_defaults: Using built-in defaults for entity type
 */
export interface ResolvedPanels {
  panels: PanelConfig[]
  source: "user_override" | "entity_defaults" | "type_defaults"
}

// Re-export API types for consumers that need them
export type {
  ResolvedPanelConfig,
  RoomPanelDefaultsPublic,
  UserRoomPanelConfigPublic,
}

// Re-export registry helpers for convenience
export {
  getPanelDisplayName,
  isValidPanelKind,
} from "@/components/Page/registry/panelTypes"

// ============================================================================
// Service Functions
// ============================================================================

/**
 * Get resolved panel configuration for current user on an entity.
 *
 * Resolution order:
 * 1. User's personal override (if set)
 * 2. Entity owner's defaults (if set)
 * 3. Built-in type defaults
 *
 * @param entityType - Type of entity (room, story, etc.)
 * @param entityId - ID of the entity
 */
export async function getResolvedPanels(
  entityType: PanelEntityType,
  entityId: string,
): Promise<ResolvedPanels> {
  if (entityType === "room") {
    const response = await RoomPanelsService.getResolvedPanels({
      roomId: entityId,
    })
    // Cast through unknown since API returns generic dict array
    const panels = (response.panels ?? []) as unknown as PanelConfig[]
    // Map room-specific source names to generic ones
    const sourceMap: Record<string, ResolvedPanels["source"]> = {
      user_override: "user_override",
      room_defaults: "entity_defaults",
      type_defaults: "type_defaults",
    }
    return {
      panels,
      source: sourceMap[response.source] ?? "type_defaults",
    }
  }

  // Story: TODO when backend ready
  // For now, return empty with type defaults
  return {
    panels: [],
    source: "type_defaults",
  }
}

/**
 * Get entity's default panel configuration.
 *
 * Returns the configuration set by the entity owner, or null if not set.
 * When null, the entity uses built-in type defaults.
 *
 * @param entityType - Type of entity
 * @param entityId - ID of the entity
 */
export async function getEntityPanelDefaults(
  entityType: PanelEntityType,
  entityId: string,
): Promise<RoomPanelDefaultsPublic | null> {
  if (entityType === "room") {
    return await RoomPanelsService.getRoomDefaults({ roomId: entityId })
  }

  // Story: TODO when backend ready
  return null
}

/**
 * Update entity's default panel configuration (owner only).
 *
 * Sets the default panel layout for all participants/viewers.
 * Only the entity owner can call this endpoint.
 *
 * @param entityType - Type of entity
 * @param entityId - ID of the entity
 * @param panels - Panel configuration to set
 * @throws ApiError with 403 if not entity owner
 */
export async function updateEntityPanelDefaults(
  entityType: PanelEntityType,
  entityId: string,
  panels: PanelConfig[],
): Promise<RoomPanelDefaultsPublic> {
  if (entityType === "room") {
    // Cast to API expected type (generic dict array)
    const requestBody = panels as unknown as Array<{ [key: string]: unknown }>
    return await RoomPanelsService.updateRoomDefaults({
      roomId: entityId,
      requestBody,
    })
  }

  // Story: TODO when backend ready
  throw new Error(
    `Panel defaults not yet supported for entity type: ${entityType}`,
  )
}

/**
 * Get current user's panel config override for an entity.
 *
 * Returns the user's personal override, or null if not set.
 * Check `use_room_defaults` to see if they're using entity defaults.
 *
 * @param entityType - Type of entity
 * @param entityId - ID of the entity
 */
export async function getMyPanelConfig(
  entityType: PanelEntityType,
  entityId: string,
): Promise<UserRoomPanelConfigPublic | null> {
  if (entityType === "room") {
    return await RoomPanelsService.getMyPanelConfig({ roomId: entityId })
  }

  // Story: TODO when backend ready
  return null
}

/**
 * Update current user's panel config for an entity.
 *
 * Sets the user's personal panel layout.
 *
 * @param entityType - Type of entity
 * @param entityId - ID of the entity
 * @param panels - Panel configuration (null to clear and use defaults)
 * @param useDefaults - If true, ignore panels and use entity/type defaults
 */
export async function updateMyPanelConfig(
  entityType: PanelEntityType,
  entityId: string,
  panels: PanelConfig[] | null,
  useDefaults: boolean,
): Promise<UserRoomPanelConfigPublic> {
  if (entityType === "room") {
    // Cast to API expected type (generic dict array or null)
    const requestBody = panels as unknown as Array<{
      [key: string]: unknown
    }> | null
    return await RoomPanelsService.updateMyPanelConfig({
      roomId: entityId,
      requestBody,
      useRoomDefaults: useDefaults,
    })
  }

  // Story: TODO when backend ready
  throw new Error(
    `Panel config not yet supported for entity type: ${entityType}`,
  )
}

// ============================================================================
// Legacy Compatibility Functions
// ============================================================================

/**
 * @deprecated Use getResolvedPanels(entityType, entityId) instead
 */
export async function getResolvedPanelsForRoom(
  roomId: string,
): Promise<ResolvedPanels> {
  return getResolvedPanels("room", roomId)
}

/**
 * @deprecated Use getEntityPanelDefaults(entityType, entityId) instead
 */
export async function getRoomPanelDefaults(
  roomId: string,
): Promise<RoomPanelDefaultsPublic | null> {
  return getEntityPanelDefaults("room", roomId)
}

/**
 * @deprecated Use updateEntityPanelDefaults(entityType, entityId, panels) instead
 */
export async function updateRoomPanelDefaults(
  roomId: string,
  panels: PanelConfig[],
): Promise<RoomPanelDefaultsPublic> {
  return updateEntityPanelDefaults("room", roomId, panels)
}
