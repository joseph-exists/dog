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
        id: "template-standard-profileImage",
        type: "profileImage",
        column: "primary",
        order: 1,
        config: { shape: "circle", size: "lg" },
        content: { imageUrl: "", alt: "" },
        visibility: "visible",
      },
      {
        id: "template-standard-identity",
        type: "identity",
        column: "primary",
        order: 2,
        config: { showTagline: true },
        content: { name: "", tagline: "" },
        visibility: "visible",
      },
      {
        id: "template-standard-bio",
        type: "bio",
        column: "primary",
        order: 3,
        config: {},
        content: { text: "" },
        visibility: "visible",
      },
      {
        id: "template-standard-relationships",
        type: "relationships",
        column: "primary",
        order: 4,
        config: { groupByType: true },
        content: { items: [] },
        visibility: "visible",
      },
      {
        id: "template-standard-contact",
        type: "contact",
        column: "auxiliary",
        order: 1,
        config: {},
        content: { email: "", phone: "" },
        visibility: "visible",
      },
      {
        id: "template-standard-links",
        type: "links",
        column: "auxiliary",
        order: 2,
        config: { layout: "list" },
        content: { items: [] },
        visibility: "visible",
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
        id: "template-minimal-profileImage",
        type: "profileImage",
        column: "primary",
        order: 1,
        config: { shape: "circle", size: "md" },
        content: { imageUrl: "", alt: "" },
        visibility: "visible",
      },
      {
        id: "template-minimal-identity",
        type: "identity",
        column: "primary",
        order: 2,
        config: { showTagline: true },
        content: { name: "", tagline: "" },
        visibility: "visible",
      },
      {
        id: "template-minimal-bio",
        type: "bio",
        column: "primary",
        order: 3,
        config: {},
        content: { text: "" },
        visibility: "visible",
      },
      {
        id: "template-minimal-links",
        type: "links",
        column: "primary",
        order: 4,
        config: { layout: "grid" },
        content: { items: [] },
        visibility: "visible",
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
        id: "template-showcase-profileImage",
        type: "profileImage",
        column: "primary",
        order: 1,
        config: { shape: "square", size: "lg" },
        content: { imageUrl: "", alt: "" },
        visibility: "visible",
      },
      {
        id: "template-showcase-identity",
        type: "identity",
        column: "primary",
        order: 2,
        config: { showTagline: true },
        content: { name: "", tagline: "" },
        visibility: "visible",
      },
      {
        id: "template-showcase-gallery",
        type: "gallery",
        column: "primary",
        order: 3,
        config: { columns: 3 },
        content: { images: [] },
        visibility: "visible",
      },
      {
        id: "template-showcase-bio",
        type: "bio",
        column: "auxiliary",
        order: 1,
        config: {},
        content: { text: "" },
        visibility: "visible",
      },
      {
        id: "template-showcase-links",
        type: "links",
        column: "auxiliary",
        order: 2,
        config: {},
        content: { items: [] },
        visibility: "visible",
      },
    ],
  },
  {
    id: "agent",
    label: "Agent Profile",
    description: "A specialized layout for AI agents with activity tracking",
    forEntityTypes: ["agent"],
    defaultBlocks: [
      {
        id: "template-agent-profileImage",
        type: "profileImage",
        column: "primary",
        order: 1,
        config: { shape: "square", size: "lg" },
        content: { imageUrl: "", alt: "" },
        visibility: "visible",
      },
      {
        id: "template-agent-identity",
        type: "identity",
        column: "primary",
        order: 2,
        config: { showTagline: true },
        content: { name: "", tagline: "" },
        visibility: "visible",
      },
      {
        id: "template-agent-bio",
        type: "bio",
        column: "primary",
        order: 3,
        config: { allowRichText: true },
        content: { text: "" },
        visibility: "visible",
      },
      {
        id: "template-agent-relationships",
        type: "relationships",
        column: "primary",
        order: 4,
        config: { groupByType: true },
        content: { items: [] },
        visibility: "visible",
      },
      {
        id: "template-agent-activityFeed",
        type: "activityFeed",
        column: "auxiliary",
        order: 1,
        config: { maxItems: 5 },
        content: {},
        visibility: "visible",
      },
    ],
  },
  {
    id: "persona",
    label: "Persona Profile",
    description: "A profile layout for personas with domains and traits",
    forEntityTypes: ["persona"],
    defaultBlocks: [
      {
        id: "template-persona-identity",
        type: "identity",
        column: "primary",
        order: 1,
        config: { showTagline: true },
        content: { name: "", tagline: "" },
        visibility: "visible",
      },
      {
        id: "template-persona-bio",
        type: "bio",
        column: "primary",
        order: 2,
        config: { allowRichText: true },
        content: { text: "" },
        visibility: "visible",
      },
      {
        id: "template-persona-domains",
        type: "domains",
        column: "primary",
        order: 3,
        config: { showHierarchy: true },
        content: {
          generalDomain: "",
          specificDomain: "",
          generalDomainHigh: "",
          specificDomainHigh: "",
        },
        visibility: "visible",
      },
      {
        id: "template-persona-traits",
        type: "traits",
        column: "primary",
        order: 4,
        config: { layout: "badges", maxVisible: 12 },
        content: { items: [] },
        visibility: "visible",
      },
      {
        id: "template-persona-qualities",
        type: "qualities",
        column: "primary",
        order: 5,
        config: { layout: "badges", maxVisible: 12 },
        content: { items: [] },
        visibility: "visible",
      },
      {
        id: "template-persona-relationships",
        type: "relationships",
        column: "auxiliary",
        order: 1,
        config: { groupByType: true },
        content: { items: [] },
        visibility: "visible",
      },
    ],
  },
  {
    id: "archetype",
    label: "Archetype Profile",
    description:
      "A profile layout for archetypes with editable traits and qualities",
    forEntityTypes: ["archetype"],
    defaultBlocks: [
      {
        id: "template-archetype-identity",
        type: "identity",
        column: "primary",
        order: 1,
        config: { showTagline: true },
        content: { name: "", tagline: "" },
        visibility: "visible",
      },
      {
        id: "template-archetype-bio",
        type: "bio",
        column: "primary",
        order: 2,
        config: { allowRichText: true },
        content: { text: "" },
        visibility: "visible",
      },
      {
        id: "template-archetype-domains",
        type: "domains",
        column: "primary",
        order: 3,
        config: { showHierarchy: true },
        content: {
          generalDomain: "",
          specificDomain: "",
          generalDomainHigh: "",
          specificDomainHigh: "",
        },
        visibility: "visible",
      },
      {
        id: "template-archetype-traits",
        type: "traits",
        column: "primary",
        order: 4,
        config: { layout: "badges", maxVisible: 12 },
        content: { items: [] },
        visibility: "visible",
      },
      {
        id: "template-archetype-qualities",
        type: "qualities",
        column: "primary",
        order: 5,
        config: { layout: "badges", maxVisible: 12 },
        content: { items: [] },
        visibility: "visible",
      },
      {
        id: "template-archetype-personas",
        type: "personas",
        column: "auxiliary",
        order: 1,
        config: { layout: "list", maxVisible: 10, showAddButton: false },
        content: {},
        visibility: "visible",
      },
    ],
  },
  {
    id: "quality",
    label: "Quality Profile",
    description: "A profile layout for qualities with linked traits and usage",
    forEntityTypes: ["quality"],
    defaultBlocks: [
      {
        id: "template-quality-identity",
        type: "identity",
        column: "primary",
        order: 1,
        config: { showTagline: true },
        content: { name: "", tagline: "" },
        visibility: "visible",
      },
      {
        id: "template-quality-bio",
        type: "bio",
        column: "primary",
        order: 2,
        config: { allowRichText: true },
        content: { text: "" },
        visibility: "visible",
      },
      {
        id: "template-quality-traits",
        type: "traits",
        column: "primary",
        order: 3,
        config: { layout: "badges", maxVisible: 12 },
        content: { items: [] },
        visibility: "visible",
      },
      {
        id: "template-quality-usedBy",
        type: "usedBy",
        column: "auxiliary",
        order: 1,
        config: { maxVisible: 10 },
        content: {},
        visibility: "visible",
      },
    ],
  },
  {
    id: "trait",
    label: "Trait Profile",
    description:
      "A profile layout for traits with linked qualities and usage",
    forEntityTypes: ["trait"],
    defaultBlocks: [
      {
        id: "template-trait-identity",
        type: "identity",
        column: "primary",
        order: 1,
        config: { showTagline: true },
        content: { name: "", tagline: "" },
        visibility: "visible",
      },
      {
        id: "template-trait-bio",
        type: "bio",
        column: "primary",
        order: 2,
        config: { allowRichText: true },
        content: { text: "" },
        visibility: "visible",
      },
      {
        id: "template-trait-qualities",
        type: "qualities",
        column: "primary",
        order: 3,
        config: { layout: "badges", maxVisible: 12 },
        content: { items: [] },
        visibility: "visible",
      },
      {
        id: "template-trait-usedBy",
        type: "usedBy",
        column: "auxiliary",
        order: 1,
        config: { maxVisible: 10 },
        content: {},
        visibility: "visible",
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
