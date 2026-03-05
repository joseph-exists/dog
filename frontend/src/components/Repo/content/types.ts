import type {
  Content,
  ContentMetadata,
  ContentRendererProps,
  ContentVariant,
  FormatSpecificOptions,
} from "@/components/Page/primitives/ContentRenderer"

export type RepoContentSourceKind =
  | "blob"
  | "readme"
  | "generated"
  | "diff"
  | "preview"

export interface RepoContentOptions {
  repoId?: string
  repoSlug?: string
  path?: string
  filename?: string
  language?: string
  sourceKind?: RepoContentSourceKind
  mimeType?: string
  encoding?: string
  sizeBytes?: number
  isBinary?: boolean
  isTruncated?: boolean
  truncationReason?: string
  isUnsupportedPreview?: boolean
  lineCount?: number
  ref?: string
  resolvedFromPath?: string
  sha?: string
}

export interface RepoContentMetadata extends Omit<ContentMetadata, "options"> {
  options?: FormatSpecificOptions & RepoContentOptions
}

export interface RepoRenderableContent extends Content {
  metadata?: RepoContentMetadata
}

export interface RepoBlobContentPayload {
  repoId?: string
  repoSlug?: string
  path: string
  content: string
  language?: string
  mimeType?: string
  encoding?: string
  sizeBytes?: number
  sourceKind?: RepoContentSourceKind
  isBinary?: boolean
  isTruncated?: boolean
  truncationReason?: string
  isUnsupportedPreview?: boolean
  ref?: string
  resolvedFromPath?: string
  sha?: string
}

export interface RepoTextContentOptions
  extends Omit<RepoBlobContentPayload, "content"> {}

export interface RepoContentRendererProps
  extends Omit<ContentRendererProps, "content"> {
  content: RepoRenderableContent
  chrome?: "none" | "minimal" | "default"
  title?: string
  subtitle?: string
  variant?: ContentVariant
}
