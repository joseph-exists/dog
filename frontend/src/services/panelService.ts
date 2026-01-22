/**
 * Panel Configuration Service
 *
 * Manages room panel configuration - resolving, updating,
 * and managing user overrides vs room defaults.
 *
 * Architecture:
 * - Wraps OpenAPI client methods for panel configuration
 * - Provides strongly-typed PanelConfig interface
 * - Handles the layered resolution: user override → room defaults → type defaults
 *
 * @see backend/app/crud_panels.py for resolution logic
 */

import {
  type ResolvedPanelConfig,
  type RoomPanelDefaultsPublic,
  RoomPanelsService,
  type UserRoomPanelConfigPublic,
} from "@/client"

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * Panel configuration item
 *
 * Represents a single panel in the room layout.
 * - id: unique identifier for this panel instance
 * - kind: the panel type (determines which component renders)
 * - prominence: where the panel appears in the layout
 */
export interface PanelConfig {
  id: string
  kind:
    | "chat"
    | "storyEditor"
    | "storyRuntime"
    | "agentPanel"
    | "debug"
    | "canvas"
    | "a2ui"
    | "participantPanel"
  prominence: "primary" | "auxiliary"
}

/**
 * Resolved panel configuration with source tracking
 *
 * The source tells us where the configuration came from:
 * - user_override: User has custom config for this room
 * - room_defaults: Using room owner's defaults
 * - type_defaults: Using built-in defaults for room type
 */
export interface ResolvedPanels {
  panels: PanelConfig[]
  source: "user_override" | "room_defaults" | "type_defaults"
}

// Re-export API types for consumers that need them
export type {
  ResolvedPanelConfig,
  RoomPanelDefaultsPublic,
  UserRoomPanelConfigPublic,
}

// ============================================================================
// Service Functions
// ============================================================================

/**
 * Get resolved panel configuration for current user
 *
 * Returns the effective panel layout based on the layered resolution:
 * 1. User's personal override (if set and not using defaults)
 * 2. Room owner's defaults (if set)
 * 3. Built-in type defaults (chat, story, workspace)
 */
export async function getResolvedPanels(
  roomId: string,
): Promise<ResolvedPanels> {
  const response = await RoomPanelsService.getResolvedPanels({ roomId })
  // Cast through unknown since API returns generic dict array
  const panels = (response.panels ?? []) as unknown as PanelConfig[]
  return {
    panels,
    source: response.source as ResolvedPanels["source"],
  }
}

/**
 * Get room's default panel configuration
 *
 * Returns the configuration set by the room owner, or null if not set.
 * When null, the room uses built-in type defaults.
 */
export async function getRoomPanelDefaults(
  roomId: string,
): Promise<RoomPanelDefaultsPublic | null> {
  return await RoomPanelsService.getRoomDefaults({ roomId })
}

/**
 * Update room's default panel configuration (owner only)
 *
 * Sets the default panel layout for all participants in this room.
 * Only the room owner can call this endpoint.
 *
 * @throws ApiError with 403 if not room owner
 */
export async function updateRoomPanelDefaults(
  roomId: string,
  panels: PanelConfig[],
): Promise<RoomPanelDefaultsPublic> {
  // Cast to API expected type (generic dict array)
  const requestBody = panels as unknown as Array<{ [key: string]: unknown }>
  return await RoomPanelsService.updateRoomDefaults({
    roomId,
    requestBody,
  })
}

/**
 * Get current user's panel config override
 *
 * Returns the user's personal override for this room, or null if not set.
 * Check `use_room_defaults` to see if they're using room defaults.
 */
export async function getMyPanelConfig(
  roomId: string,
): Promise<UserRoomPanelConfigPublic | null> {
  return await RoomPanelsService.getMyPanelConfig({ roomId })
}

/**
 * Update current user's panel config
 *
 * Sets the user's personal panel layout for this room.
 *
 * @param roomId - Room to update config for
 * @param panels - Panel configuration (null to clear and use defaults)
 * @param useRoomDefaults - If true, ignore panels and use room/type defaults
 */
export async function updateMyPanelConfig(
  roomId: string,
  panels: PanelConfig[] | null,
  useRoomDefaults: boolean,
): Promise<UserRoomPanelConfigPublic> {
  // Cast to API expected type (generic dict array or null)
  const requestBody = panels as unknown as Array<{
    [key: string]: unknown
  }> | null
  return await RoomPanelsService.updateMyPanelConfig({
    roomId,
    requestBody,
    useRoomDefaults,
  })
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Check if a panel kind is valid
 */
export function isValidPanelKind(kind: string): kind is PanelConfig["kind"] {
  return [
    "chat",
    "storyEditor",
    "storyRuntime",
    "agentPanel",
    "debug",
    "canvas",
    "a2ui",
    "participantPanel",
  ].includes(kind)
}

/**
 * Get display name for a panel kind
 */
export function getPanelDisplayName(kind: PanelConfig["kind"]): string {
  const names: Record<PanelConfig["kind"], string> = {
    chat: "Chat",
    storyEditor: "Story Editor",
    storyRuntime: "Story Runtime",
    agentPanel: "Agents",
    debug: "Debug",
    canvas: "Canvas",
    a2ui: "Agent UI",
    participantPanel: "Participants",
  }
  return names[kind]
}
