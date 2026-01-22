// src/components/Page/registry/pageTemplates.ts
import type { BlockType } from "./blockTypes"

/**
 * A block instance within a page template.
 *
 * When used in page templates (defaultBlocks), `id` and `visibility` are optional
 * and will be assigned defaults when instantiated. When used in actual page instances,
 * all fields should be present.
 */
export interface TemplateBlock {
  /** Unique instance ID (uuid) - assigned when block is instantiated */
  id?: string
  /** Block type identifier */
  type: BlockType
  /** Layout column */
  column: "primary" | "auxiliary"
  /** Sort order within column */
  order: number
  /** Display settings */
  config: Record<string, unknown>
  /** Actual data content for the block */
  content?: Record<string, unknown>
  /** Visibility toggle - defaults to "visible" */
  visibility?: "visible" | "hidden"
}

/**
 * A fully instantiated block with all required fields.
 * Use this type when working with blocks in actual page instances.
 */
export interface InstantiatedBlock {
  /** Unique instance ID (uuid) */
  id: string
  /** Block type identifier */
  type: BlockType
  /** Layout column */
  column: "primary" | "auxiliary"
  /** Sort order within column */
  order: number
  /** Display settings */
  config: Record<string, unknown>
  /** Actual data content for the block */
  content?: Record<string, unknown>
  /** Visibility toggle */
  visibility: "visible" | "hidden"
}

/**
 * A page template definition for preset layouts.
 */
export interface PageTemplate {
  id: string
  label: string
  description: string
  forEntityTypes: string[]
  defaultBlocks: TemplateBlock[]
}

/**
 * Available page templates.
 */
export const pageTemplates: PageTemplate[] = [
  {
    id: "standard",
    label: "Standard Profile",
    description:
      "A complete profile layout with primary content and auxiliary sidebar",
    forEntityTypes: ["user", "agent", "team"],
    defaultBlocks: [
      {
        type: "profileImage",
        column: "primary",
        order: 1,
        config: { shape: "circle", size: "lg" },
      },
      {
        type: "identity",
        column: "primary",
        order: 2,
        config: { showTagline: true },
      },
      { type: "bio", column: "primary", order: 3, config: {} },
      {
        type: "relationships",
        column: "primary",
        order: 4,
        config: { groupByType: true },
      },
      { type: "contact", column: "auxiliary", order: 1, config: {} },
      {
        type: "links",
        column: "auxiliary",
        order: 2,
        config: { layout: "list" },
      },
    ],
  },
  {
    id: "minimal",
    label: "Minimal",
    description: "A simple single-column profile layout",
    forEntityTypes: ["user", "agent", "team"],
    defaultBlocks: [
      {
        type: "profileImage",
        column: "primary",
        order: 1,
        config: { shape: "circle", size: "md" },
      },
      {
        type: "identity",
        column: "primary",
        order: 2,
        config: { showTagline: true },
      },
      { type: "bio", column: "primary", order: 3, config: {} },
      {
        type: "links",
        column: "primary",
        order: 4,
        config: { layout: "grid" },
      },
    ],
  },
  {
    id: "showcase",
    label: "Showcase",
    description: "A visual-focused layout with gallery display",
    forEntityTypes: ["user", "team"],
    defaultBlocks: [
      {
        type: "profileImage",
        column: "primary",
        order: 1,
        config: { shape: "square", size: "lg" },
      },
      {
        type: "identity",
        column: "primary",
        order: 2,
        config: { showTagline: true },
      },
      { type: "gallery", column: "primary", order: 3, config: { columns: 3 } },
      { type: "bio", column: "auxiliary", order: 1, config: {} },
      { type: "links", column: "auxiliary", order: 2, config: {} },
    ],
  },
  {
    id: "agent",
    label: "Agent Profile",
    description: "A specialized layout for AI agents with activity tracking",
    forEntityTypes: ["agent"],
    defaultBlocks: [
      {
        type: "profileImage",
        column: "primary",
        order: 1,
        config: { shape: "square", size: "lg" },
      },
      {
        type: "identity",
        column: "primary",
        order: 2,
        config: { showTagline: true },
      },
      {
        type: "bio",
        column: "primary",
        order: 3,
        config: { allowRichText: true },
      },
      {
        type: "relationships",
        column: "primary",
        order: 4,
        config: { groupByType: true },
      },
      {
        type: "activityFeed",
        column: "auxiliary",
        order: 1,
        config: { maxItems: 5 },
      },
    ],
  },
]

/**
 * Get a page template by ID.
 */
export function getPageTemplate(id: string): PageTemplate | undefined {
  return pageTemplates.find((t) => t.id === id)
}

/**
 * Get all templates available for a specific entity type.
 */
export function getTemplatesForEntityType(
  entityTypeId: string,
): PageTemplate[] {
  return pageTemplates.filter((t) => t.forEntityTypes.includes(entityTypeId))
}

/**
 * Get the default template for an entity type.
 * Prefers entity-specific templates (like "agent" for agents), falls back to "standard".
 */
export function getDefaultTemplate(entityTypeId: string): PageTemplate {
  // First, look for a template that exactly matches the entity type ID
  const entitySpecific = pageTemplates.find((t) => t.id === entityTypeId)
  if (entitySpecific?.forEntityTypes.includes(entityTypeId)) {
    return entitySpecific
  }

  // Fall back to standard template
  const standard = getPageTemplate("standard")
  if (standard) {
    return standard
  }

  // This should never happen, but TypeScript needs a fallback
  return pageTemplates[0]
}
