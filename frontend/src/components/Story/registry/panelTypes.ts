// src/components/Story/registry/panelTypes.ts

import type { LucideIcon } from "lucide-react"
import {
  BookOpen,
  Bot,
  Bug,
  MessageSquare,
  Palette,
  Play,
  Users,
} from "lucide-react"

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * Panel kind identifier.
 *
 * ADDING NEW PANELS:
 * 1. Add the kind here
 * 2. Add a PanelTypeDefinition in the appropriate section below
 * 3. Update panelService.ts if backend integration needed
 * 4. Create the panel component in the appropriate feature folder
 */
export type PanelKind =
  //
  | "chat"
  | "canvas"
  | "a2ui"
  | "participantPanel"
  | "debug"
  // Story panels
  | "storyEditor"
  | "storyRuntime"
  | "storyPlayer"
  | "storyDebug"

/**
 * Where the panel appears in the layout.
 * - primary: Main content area (larger, side-by-side)
 * - auxiliary: Secondary column (smaller, stacked)
 */
export type PanelProminence = "primary" | "auxiliary"

/**
 * Which Page constructs can use this panel.
 * Used for filtering available panels in layout dialogs.
 */
export type PanelContext = "room" | "story" | "universal"

/**
 * Permission level required to use a panel.
 * - none: No special permissions (anyone can use)
 * - participant: Must be a participant in the context (room member, etc.)
 * - owner: Must own the entity (room owner, story author)
 * - admin: Must be admin or superuser
 */
export type PanelPermission = "none" | "participant" | "owner" | "admin"

/**
 * Entity cardinality - what the panel operates on.
 * - single: Operates on one entity (e.g., agent.$agentId page)
 * - collection: Operates on a group of entities (e.g., agents listing page)
 * - either: Can work in both contexts
 */
export type EntityCardinality = "single" | "collection" | "either"

/**
 * Panel type definition for the registry.
 *
 * REQUIRED FIELDS: kind, label, description, icon, defaultProminence, contexts
 * OPTIONAL FIELDS: permission, dependencies, cardinality, relational
 */
export interface PanelTypeDefinition {
  /** Unique panel kind identifier */
  kind: PanelKind
  /** Display name shown in UI */
  label: string
  /** Brief description for tooltips/help */
  description: string
  /** Icon from lucide-react */
  icon: LucideIcon
  /** Default prominence when adding to layout */
  defaultProminence: PanelProminence
  /** Which contexts this panel is available in */
  contexts: PanelContext[]

  // --- Extended Metadata ---

  /**
   * Permission required to use this panel.
   * Defaults to "none" if not specified.
   *
   * Examples:
   * - "owner": Only story author can use storyEditor
   * - "participant": Only room members can see chat
   * - "admin": Debug panels for admins only in production
   */
  permission?: PanelPermission

  /**
   * Other panel kinds this panel depends on to be functional.
   * If dependencies not present, panel may show degraded or error state.
   *
   * Example: storyDebug depends on storyPlayer (needs player context)
   */
  dependencies?: PanelKind[]

  /**
   * Whether panel operates on single entity or collection.
   * Defaults to "single" if not specified.
   *
   * Examples:
   * - "single": storyPlayer shows one story
   * - "collection": story grid shows all user's stories
   * - "either": participantPanel works on room or room listing
   */
  cardinality?: EntityCardinality

  /**
   * Whether this panel represents a relationship between entities.
   * If true, panel shows intersection/edge between Entity A and Entity B.
   *
   * Example: A "shared stories" panel showing stories shared between
   * two users would be relational (User A <-> User B).
   */
  relational?: boolean
}

// ============================================================================
// Panel Definitions
// ============================================================================

/**
 * PANEL REGISTRY
 *
 * Organized by primary context. Panels with multiple contexts are placed
 * in their "home" section with contexts array reflecting all valid uses.
 *
 * REQUIREMENTS FOR EACH PANEL:
 * - kind: Must be unique, added to PanelKind type above
 * - label: Short, title-case name (max ~20 chars)
 * - description: One sentence explaining purpose
 * - icon: Must import from lucide-react
 * - defaultProminence: Where it typically belongs
 * - contexts: Array of valid contexts (never empty)
 */

export const PANEL_TYPES: PanelTypeDefinition[] = [
  // --------------------------------------------------------------------------
  // Room Panels
  // Panels primarily used in chat rooms and collaborative spaces
  // --------------------------------------------------------------------------
  {
    kind: "chat",
    label: "Chat",
    description: "Real-time messaging with room participants",
    icon: MessageSquare,
    defaultProminence: "primary",
    contexts: ["room"],
    permission: "participant",
    cardinality: "single",
  },
  {
    kind: "canvas",
    label: "Canvas",
    description: "Shared drawing and diagramming space",
    icon: Palette,
    defaultProminence: "primary",
    contexts: ["room"],
    permission: "participant",
    cardinality: "single",
  },
  {
    kind: "a2ui",
    label: "Agent UI",
    description: "Interactive agent interface and controls",
    icon: Bot,
    defaultProminence: "primary",
    contexts: ["room"],
    permission: "participant",
    cardinality: "single",
  },
  {
    kind: "participantPanel",
    label: "Participants",
    description: "List of room participants and their status",
    icon: Users,
    defaultProminence: "auxiliary",
    contexts: ["room"],
    permission: "participant",
    cardinality: "single",
    relational: true, // Shows relationships: Room <-> Users
  },

  // --------------------------------------------------------------------------
  // Story Panels
  // Panels for interactive story authoring and playback
  // --------------------------------------------------------------------------
  {
    kind: "storyEditor",
    label: "Story Editor",
    description: "Node-based story authoring interface",
    icon: BookOpen,
    defaultProminence: "primary",
    contexts: ["room", "story"],
    permission: "owner",
    cardinality: "single",
  },
  {
    kind: "storyRuntime",
    label: "Story Runtime",
    description: "Live story execution and state display",
    icon: Play,
    defaultProminence: "primary",
    contexts: ["room"],
    permission: "participant",
    cardinality: "single",
    dependencies: ["storyEditor"],
  },
  {
    kind: "storyPlayer",
    label: "Story Player",
    description: "Interactive story playback with choices",
    icon: Play,
    defaultProminence: "primary",
    contexts: ["story"],
    permission: "none", // Anyone can play a published story
    cardinality: "single",
  },
  {
    kind: "storyDebug",
    label: "Story Debug",
    description: "Player state, history, and choice debugging",
    icon: Bug,
    defaultProminence: "auxiliary",
    contexts: ["story"],
    permission: "owner", // Only author needs debug info
    cardinality: "single",
    dependencies: ["storyPlayer"],
  },

  // --------------------------------------------------------------------------
  // Universal Panels
  // Panels available across all contexts
  // --------------------------------------------------------------------------
  {
    kind: "debug",
    label: "Debug",
    description: "Development debugging and state inspection",
    icon: Bug,
    defaultProminence: "auxiliary",
    contexts: ["room", "story", "universal"],
    permission: "admin", // Dev/admin only
    cardinality: "either",
  },
]

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get panel type definition by kind
 */
export function getPanelType(kind: PanelKind): PanelTypeDefinition | undefined {
  return PANEL_TYPES.find((p) => p.kind === kind)
}

/**
 * Get display name for a panel kind
 */
export function getPanelDisplayName(kind: PanelKind): string {
  return getPanelType(kind)?.label ?? kind
}

/**
 * Get all panels available for a specific context
 */
export function getPanelsForContext(
  context: PanelContext,
): PanelTypeDefinition[] {
  return PANEL_TYPES.filter(
    (p) => p.contexts.includes(context) || p.contexts.includes("universal"),
  )
}

/**
 * Get panels accessible at a given entity permission level.
 *
 * Pass the user's permission on the CURRENT ENTITY (e.g., are they
 * the owner of this specific story?).
 *
 * Returns panels where required permission <= user's permission.
 */
export function getPanelsForEntityPermission(
  userPermissionOnEntity: PanelPermission,
): PanelTypeDefinition[] {
  const levels: PanelPermission[] = ["none", "participant", "owner", "admin"]
  const userIndex = levels.indexOf(userPermissionOnEntity)

  return PANEL_TYPES.filter((p) => {
    const requiredIndex = levels.indexOf(p.permission ?? "none")
    return requiredIndex <= userIndex
  })
}

/**
 * Get panels accessible for a given system role.
 *
 * Pass the user's SYSTEM-WIDE role (regular user vs admin/superuser).
 * Filters out admin-only panels for regular users.
 */
export function getPanelsForSystemRole(
  role: "user" | "admin",
): PanelTypeDefinition[] {
  if (role === "admin") {
    return PANEL_TYPES // Admins see everything
  }
  // Regular users: exclude admin-only panels
  return PANEL_TYPES.filter((p) => p.permission !== "admin")
}

/**
 * Check if a panel kind is valid
 */
export function isValidPanelKind(kind: string): kind is PanelKind {
  return PANEL_TYPES.some((p) => p.kind === kind)
}

/**
 * Get default panel config for adding to a layout
 */
export function getDefaultPanelConfig(kind: PanelKind):
  | {
      id: string
      kind: PanelKind
      prominence: PanelProminence
    }
  | undefined {
  const panel = getPanelType(kind)
  if (!panel) return undefined

  return {
    id: kind, // Use kind as default id; caller can override
    kind,
    prominence: panel.defaultProminence,
  }
}

/**
 * Get panels that depend on a given panel kind
 */
export function getPanelDependents(kind: PanelKind): PanelTypeDefinition[] {
  return PANEL_TYPES.filter((p) => p.dependencies?.includes(kind))
}

/**
 * Check if all dependencies for a panel are satisfied
 */
export function areDependenciesSatisfied(
  kind: PanelKind,
  activePanelKinds: PanelKind[],
): boolean {
  const panel = getPanelType(kind)
  if (!panel?.dependencies) return true
  return panel.dependencies.every((dep) => activePanelKinds.includes(dep))
}
