import type { ContentFormat } from "@/components/Page/primitives/ContentRenderer"
import type {
  RepoBlobContentPayload,
  RepoRenderableContent,
  RepoTextContentOptions,
} from "./types"

const imageExtensions = new Set([
  "png",
  "jpg",
  "jpeg",
  "gif",
  "svg",
  "webp",
  "avif",
])
const markdownExtensions = new Set(["md", "mdx", "markdown"])
const jsonExtensions = new Set(["json", "jsonc", "json5"])

function getFileExtension(path: string) {
  const segments = path.split(".")
  if (segments.length < 2) return ""
  return segments.at(-1)?.toLowerCase() ?? ""
}

function getFilename(path: string) {
  return path.split("/").filter(Boolean).at(-1) ?? path
}

export function inferRepoContentFormat(
  path: string,
  mimeType?: string,
): ContentFormat {
  const extension = getFileExtension(path)

  if (mimeType?.startsWith("image/") || imageExtensions.has(extension)) {
    return extension === "svg" ? "svg" : "image"
  }

  if (markdownExtensions.has(extension)) return "markdown"
  if (jsonExtensions.has(extension)) return "json"

  return "code"
}

export function toRepoRenderableContent(
  payload: RepoBlobContentPayload,
): RepoRenderableContent {
  const format = inferRepoContentFormat(payload.path, payload.mimeType)
  const filename = getFilename(payload.path)
  const lineCount = payload.content.split("\n").length

  return {
    format,
    value: payload.content,
    metadata: {
      label: filename,
      variant: "card",
      options: {
        repoId: payload.repoId,
        repoSlug: payload.repoSlug,
        path: payload.path,
        filename,
        language: payload.language,
        sourceKind: payload.sourceKind ?? "blob",
        mimeType: payload.mimeType,
        encoding: payload.encoding,
        sizeBytes: payload.sizeBytes,
        isBinary: payload.isBinary,
        isTruncated: payload.isTruncated,
        truncationReason: payload.truncationReason,
        isUnsupportedPreview: payload.isUnsupportedPreview,
        ref: payload.ref,
        resolvedFromPath: payload.resolvedFromPath,
        sha: payload.sha,
        lineCount,
        theme: "github-dark",
        copyable: true,
      },
    },
  }
}

export function createRepoTextContent(
  value: string,
  options: RepoTextContentOptions,
): RepoRenderableContent {
  return toRepoRenderableContent({
    ...options,
    content: value,
  })
}
