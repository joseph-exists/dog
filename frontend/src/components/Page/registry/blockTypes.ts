// src/components/Page/registry/blockTypes.ts

/**
 * Available block types for pages.
 *
 * NOTE: Block rendering is handled directly by PageShell via switch statement,
 * not through the registry's component field. This allows type-safe props for
 * each block type. The registry is used for metadata (labels, descriptions,
 * configSchema) to drive block pickers and settings UIs.
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
  /** Unique identifier */
  id: BlockType
  /** Display label */
  label: string
  /** Description of the block */
  description: string
  /** Configuration schema for block settings */
  configSchema: Record<string, ConfigFieldSchema>
  /** Whether this block displays dynamic data (tables, charts) */
  isDataBlock?: boolean
}

export const blockTypes: BlockTypeDefinition[] = [
  {
    id: "profileImage",
    label: "Profile Image",
    description: "Display a profile image with configurable shape and size",
    configSchema: {
      shape: {
        type: "select",
        label: "Shape",
        default: "circle",
        options: ["circle", "square"],
      },
      size: {
        type: "select",
        label: "Size",
        default: "md",
        options: ["sm", "md", "lg"],
      },
    },
  },
  {
    id: "identity",
    label: "Identity",
    description: "Display name and optional tagline",
    configSchema: {
      showTagline: {
        type: "boolean",
        label: "Show Tagline",
        default: true,
      },
    },
  },
  {
    id: "bio",
    label: "Bio",
    description: "Display biography or description text",
    configSchema: {
      maxLength: {
        type: "number",
        label: "Max Length",
        default: 500,
      },
      allowRichText: {
        type: "boolean",
        label: "Allow Rich Text",
        default: false,
      },
    },
  },
  {
    id: "contact",
    label: "Contact",
    description: "Display contact information",
    configSchema: {
      showEmail: {
        type: "boolean",
        label: "Show Email",
        default: true,
      },
      showPhone: {
        type: "boolean",
        label: "Show Phone",
        default: false,
      },
    },
  },
  {
    id: "links",
    label: "Links",
    description: "Display a list of links",
    configSchema: {
      layout: {
        type: "select",
        label: "Layout",
        default: "list",
        options: ["list", "grid"],
      },
    },
  },
  {
    id: "relationships",
    label: "Relationships",
    description: "Display relationships to other entities",
    configSchema: {
      groupByType: {
        type: "boolean",
        label: "Group by Type",
        default: true,
      },
      maxVisible: {
        type: "number",
        label: "Max Visible",
        default: 10,
      },
    },
  },
  {
    id: "activityFeed",
    label: "Activity Feed",
    description: "Display recent activity",
    configSchema: {
      maxItems: {
        type: "number",
        label: "Max Items",
        default: 5,
      },
    },
  },
  {
    id: "gallery",
    label: "Gallery",
    description: "Display an image gallery",
    configSchema: {
      columns: {
        type: "number",
        label: "Columns",
        default: 3,
      },
      lightbox: {
        type: "boolean",
        label: "Enable Lightbox",
        default: true,
      },
    },
  },
  {
    id: "dataTable",
    label: "Data Table",
    description: "Display data in a table format",
    configSchema: {
      title: {
        type: "string",
        label: "Title",
        default: "",
      },
      dataSource: {
        type: "string",
        label: "Data Source",
        default: "",
      },
      columns: {
        type: "columnConfig",
        label: "Columns",
        default: [],
      },
      maxRows: {
        type: "number",
        label: "Max Rows",
        default: 10,
      },
    },
    isDataBlock: true,
  },
  {
    id: "chart",
    label: "Chart",
    description: "Display data as a chart",
    configSchema: {
      title: {
        type: "string",
        label: "Title",
        default: "",
      },
      chartType: {
        type: "select",
        label: "Chart Type",
        default: "bar",
        options: ["bar", "line", "pie", "area"],
      },
      dataSource: {
        type: "string",
        label: "Data Source",
        default: "",
      },
    },
    isDataBlock: true,
  },
]

/**
 * Get block type definition by ID
 */
export function getBlockType(id: BlockType): BlockTypeDefinition | undefined {
  return blockTypes.find((b) => b.id === id)
}

/**
 * Get all standard (non-data) blocks
 */
export function getStandardBlocks(): BlockTypeDefinition[] {
  return blockTypes.filter((b) => !b.isDataBlock)
}

/**
 * Get all data blocks (tables, charts)
 */
export function getDataBlocks(): BlockTypeDefinition[] {
  return blockTypes.filter((b) => b.isDataBlock)
}
