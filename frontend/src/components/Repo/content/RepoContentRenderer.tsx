import { FileCode2, FileText, GitCommitHorizontal, Route } from "lucide-react"
import {
  type ContentVariant,
  ContentRenderer,
} from "@/components/Page/primitives/ContentRenderer"
import { Badge } from "@/components/ui/badge"
import { BlockContainer } from "@/components/Page/primitives/BlockContainer"
import type { RepoContentRendererProps } from "./types"

function formatBytes(value?: number) {
  if (typeof value !== "number" || !Number.isFinite(value)) return null
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / (1024 * 1024)).toFixed(1)} MB`
}

function resolveTitle({
  title,
  path,
  filename,
}: {
  title?: string
  path?: string
  filename?: string
}) {
  if (title) return title
  if (filename) return filename
  if (path) return path.split("/").filter(Boolean).at(-1) ?? path
  return "Repository Content"
}

function resolveVariant(variant?: ContentVariant): ContentVariant {
  return variant ?? "card"
}

export function RepoContentRenderer({
  content,
  chrome = "default",
  title,
  subtitle,
  variant,
  className,
  ...rest
}: RepoContentRendererProps) {
  const options = content.metadata?.options
  const sizeBytes = options?.sizeBytes
  const truncationReason = options?.truncationReason
  const resolvedVariant = resolveVariant(variant)
  const resolvedTitle = resolveTitle({
    title,
    path: options?.path,
    filename: options?.filename,
  })

  if (chrome === "none") {
    return (
      <ContentRenderer
        {...rest}
        className={className}
        content={content}
        variant={resolvedVariant}
      />
    )
  }

  const metadata =
    chrome === "minimal" ? null : (
      <>
        {options?.path && (
          <Badge variant="outline" className="gap-1 font-mono text-[10px]">
            <Route className="h-3 w-3" />
            {options.path}
          </Badge>
        )}
        {options?.language && (
          <Badge variant="secondary" className="gap-1 text-[10px]">
            <FileCode2 className="h-3 w-3" />
            {options.language}
          </Badge>
        )}
        {formatBytes(sizeBytes) && (
          <Badge variant="secondary" className="text-[10px]">
            {formatBytes(sizeBytes)}
          </Badge>
        )}
        {options?.ref && (
          <Badge variant="outline" className="text-[10px]">
            Ref {options.ref}
          </Badge>
        )}
        {options?.sha && (
          <Badge variant="outline" className="gap-1 font-mono text-[10px]">
            <GitCommitHorizontal className="h-3 w-3" />
            {options.sha.slice(0, 8)}
          </Badge>
        )}
        {options?.isBinary && (
          <Badge variant="outline" className="text-[10px]">
            Binary
          </Badge>
        )}
        {options?.isUnsupportedPreview && (
          <Badge variant="outline" className="text-[10px]">
            Preview limited
          </Badge>
        )}
        {options?.isTruncated && (
          <Badge variant="outline" className="text-[10px]">
            Truncated
          </Badge>
        )}
      </>
    )

  const bodyClassName =
    resolvedVariant === "card" || resolvedVariant === "preview"
      ? "min-h-[220px]"
      : undefined

  return (
    <BlockContainer
      title={resolvedTitle}
      subtitle={
        subtitle ??
        (options?.sourceKind
          ? `Repository ${options.sourceKind} content`
          : "Repository content")
      }
      metadata={metadata}
      className={className}
      bodyClassName={bodyClassName}
      scrollable
      stickyHeader
      density={chrome === "minimal" ? "compact" : "default"}
      emptyState={
        <div className="flex min-h-[140px] items-center justify-center text-sm text-muted-foreground">
          <FileText className="mr-2 h-4 w-4" />
          {options?.isBinary
            ? "Binary preview is not available."
            : options?.isUnsupportedPreview
              ? "This file type is not previewable in the viewer."
              : options?.isTruncated
                ? truncationReason || "Preview was truncated."
                : "No content available."}
        </div>
      }
      isEmpty={
        options?.isBinary === true ||
        options?.isUnsupportedPreview === true ||
        content.value == null ||
        content.value === ""
      }
    >
      <ContentRenderer
        {...rest}
        content={content}
        variant={resolvedVariant}
        className="h-full"
      />
    </BlockContainer>
  )
}
