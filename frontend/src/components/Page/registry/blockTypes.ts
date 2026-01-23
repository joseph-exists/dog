// src/components/Page/registry/blockTypes.ts

import type { LucideIcon } from "lucide-react"
import {
  Activity,
  BarChart,
  FileText,
  Gem,
  Globe,
  Image,
  Link,
  Mail,
  Smile,
  Sparkles,
  Table,
  User,
  UserCircle,
  Users,
} from "lucide-react"

/**
 * Available block types for pages.
 *
 * NOTE: Block rendering is handled directly by PageShell via switch statement,
 * not through the registry's component field. This allows type-safe props for
 * each block type. The registry is used for metadata (labels, descriptions,
 * icons, defaults) to drive block pickers and settings UIs.
 */
export type BlockType =
  | "profileImage"
  | "identity"
  | "bio"
  | "contact"
  | "links"
  | "relationships"
  | "activityFeed"
  | "gallery"
  | "dataTable"
  | "chart"
  | "personas"
  | "domains"
  | "traits"
  | "qualities"

/**
 * Configuration field types for block settings.
 */
export type ConfigFieldType =
  | "string"
  | "number"
  | "boolean"
  | "select"
  | "columnConfig"

/**
 * Schema for a single configuration field.
 */
export interface ConfigFieldSchema {
  type: ConfigFieldType
  label: string
  default?: unknown
  options?: string[] // For select type
}

/**
 * Block type definition for the registry.
 * Used for metadata to drive block pickers and settings UIs.
 * Actual rendering is handled by PageShell's renderBlock function.
 */
export interface BlockTypeDefinition {
  /** Block type identifier */
  type: BlockType
  /** Display label */
  label: string
  /** Description of the block */
  description: string
  /** Icon component from lucide-react */
  icon: LucideIcon
  /** Default configuration values for block settings */
  defaultConfig: Record<string, unknown>
  /** Default content structure for the block */
  defaultContent: Record<string, unknown>
}

export const BLOCK_TYPES: BlockTypeDefinition[] = [
  {
    type: "profileImage",
    label: "Profile Image",
    description: "Display a profile image with configurable shape and size",
    icon: User,
    defaultConfig: {
      shape: "circle",
      size: "md",
    },
    defaultContent: {
      imageUrl: "",
      alt: "",
    },
  },
  {
    type: "identity",
    label: "Identity",
    description: "Display name and optional tagline",
    icon: UserCircle,
    defaultConfig: {
      showTagline: true,
    },
    defaultContent: {
      name: "",
      tagline: "",
    },
  },
  {
    type: "bio",
    label: "Bio",
    description: "Display biography or description text",
    icon: FileText,
    defaultConfig: {
      maxLength: 500,
      allowRichText: false,
    },
    defaultContent: {
      text: "",
    },
  },
  {
    type: "contact",
    label: "Contact",
    description: "Display contact information",
    icon: Mail,
    defaultConfig: {
      showEmail: true,
      showPhone: false,
    },
    defaultContent: {
      email: "",
      phone: "",
    },
  },
  {
    type: "links",
    label: "Links",
    description: "Display a list of links",
    icon: Link,
    defaultConfig: {
      layout: "list",
    },
    defaultContent: {
      items: [],
    },
  },
  {
    type: "relationships",
    label: "Relationships",
    description: "Display relationships to other entities",
    icon: Users,
    defaultConfig: {
      groupByType: true,
      maxVisible: 10,
    },
    defaultContent: {
      items: [],
    },
  },
  {
    type: "activityFeed",
    label: "Activity Feed",
    description: "Display recent activity",
    icon: Activity,
    defaultConfig: {
      maxItems: 5,
    },
    defaultContent: {},
  },
  {
    type: "gallery",
    label: "Gallery",
    description: "Display an image gallery",
    icon: Image,
    defaultConfig: {
      columns: 3,
      lightbox: true,
    },
    defaultContent: {
      images: [],
    },
  },
  {
    type: "dataTable",
    label: "Data Table",
    description: "Display data in a table format",
    icon: Table,
    defaultConfig: {
      title: "",
      dataSource: "",
      columns: [],
      maxRows: 10,
    },
    defaultContent: {},
  },
  {
    type: "chart",
    label: "Chart",
    description: "Display data as a chart",
    icon: BarChart,
    defaultConfig: {
      title: "",
      chartType: "bar",
      dataSource: "",
    },
    defaultContent: {},
  },
  {
    type: "personas",
    label: "Personas",
    description: "Display persona library for this entity",
    icon: Smile,
    defaultConfig: {
      layout: "grid",
      maxVisible: 6,
      showAddButton: true,
    },
    defaultContent: {},
  },
  {
    type: "domains",
    label: "Domains",
    description: "Display domain expertise areas (general and specific)",
    icon: Globe,
    defaultConfig: {
      showHierarchy: true,
    },
    defaultContent: {
      generalDomain: "",
      specificDomain: "",
      generalDomainHigh: "",
      specificDomainHigh: "",
    },
  },
  {
    type: "traits",
    label: "Traits",
    description: "Display personality traits as badges (fetched from API)",
    icon: Sparkles,
    defaultConfig: {
      layout: "badges",
      maxVisible: 12,
    },
    defaultContent: {
      items: [],
    },
  },
  {
    type: "qualities",
    label: "Qualities",
    description: "Display enabled qualities as badges (fetched from API)",
    icon: Gem,
    defaultConfig: {
      layout: "badges",
      maxVisible: 12,
    },
    defaultContent: {
      items: [],
    },
  },
]

// Legacy export for backward compatibility
export const blockTypes = BLOCK_TYPES

/**
 * Get block type definition by type
 */
export function getBlockType(type: BlockType): BlockTypeDefinition | undefined {
  return BLOCK_TYPES.find((b) => b.type === type)
}

/**
 * Get all standard (non-data) blocks
 */
export function getStandardBlocks(): BlockTypeDefinition[] {
  const dataBlockTypes: BlockType[] = ["dataTable", "chart"]
  return BLOCK_TYPES.filter((b) => !dataBlockTypes.includes(b.type))
}

/**
 * Get all data blocks (tables, charts)
 */
export function getDataBlocks(): BlockTypeDefinition[] {
  const dataBlockTypes: BlockType[] = ["dataTable", "chart"]
  return BLOCK_TYPES.filter((b) => dataBlockTypes.includes(b.type))
}
