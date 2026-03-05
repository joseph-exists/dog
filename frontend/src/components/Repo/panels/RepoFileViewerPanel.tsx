import { useQuery } from "@tanstack/react-query"
import { CheckIcon, CopyIcon, FileCode2, FileQuestion, Loader2, PlusIcon } from "lucide-react"
import { useEffect } from "react"
import { UserReposService } from "@/client/sdk.gen"
import type { UserRepoPublic } from "@/client/types.gen"
import { RepoContentRenderer, toRepoRenderableContent } from "@/components/Repo"
import { PanelContainer } from "@/components/Page/primitives"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { showSuccessToast } from "@/hooks/useCustomToast"
import { RepoCapabilityPlaceholderPanel } from "./RepoCapabilityPlaceholderPanel"
import { parseRepoFileViewerPanelConfig } from "./config"

export function RepoFileViewerPanel({
  repo,
  panelId,
  config,
  enabled,
  selectedPath,
  onFileOpened,
  onRefObserved,
  getRoomContextState,
  onToggleRoomContext,
}: {
  repo: UserRepoPublic
  panelId: string
  config: unknown
  enabled: boolean
  selectedPath: string | null
  onFileOpened?: (payload: {
    panelId: string
    repoId: string
    path: string
    ref: string
  }) => void
  onRefObserved?: (payload: {
    panelId: string
    repoId: string
    ref: string
    path?: string | null
  }) => void
  getRoomContextState?: (payload: {
    panelId: string
    repoId: string
    path: string
    ref: string
    isBinary: boolean
    hasContent: boolean
  }) => {
    included: boolean
    pending: boolean
    canToggle: boolean
    disabledReason?: string | null
  }
  onToggleRoomContext?: (payload: {
    panelId: string
    repoId: string
    repoSlug: string
    path: string
    ref: string
    content: string
    contentType: string | null
    encoding: string | null
    sizeBytes: number | null
    isBinary: boolean
    isTruncated: boolean
    truncationReason: string | null
  }) => Promise<void> | void
}) {
  const resolvedConfig = parseRepoFileViewerPanelConfig(config, panelId)
  const resolvedPath =
    resolvedConfig.path_mode === "fixed"
      ? resolvedConfig.fixed_path || null
      : selectedPath
  const explicitRef = resolvedConfig.ref?.trim() || null
  const isReadmeMode = resolvedConfig.path_mode === "readme"

  if (!enabled) {
    return (
      <RepoCapabilityPlaceholderPanel
        title={resolvedConfig.title || "File Viewer"}
        description="Repository file viewing is config-driven and multi-instance ready, but this repository is not currently viewer-enabled."
        unmetRequirements={["user-repo blob read capability"]}
      />
    )
  }

  const fileQuery = useQuery({
    queryKey: [
      "repo-file-view",
      panelId,
      repo.id,
      resolvedPath,
      explicitRef ?? "__default__",
      isReadmeMode ? "readme" : "file",
    ],
    queryFn: () =>
      isReadmeMode
        ? UserReposService.getUserRepoReadme({
            repoId: repo.id,
            // Only send `ref` when the panel config pins one. Default-branch
            // resolution belongs to the backend because imported repos do not
            // consistently use `main`.
            ref: explicitRef || undefined,
          })
        : UserReposService.getUserRepoFile({
            repoId: repo.id,
            path: resolvedPath!,
            ref: explicitRef || undefined,
          }),
    enabled: isReadmeMode || Boolean(resolvedPath),
  })

  useEffect(() => {
    if (!fileQuery.data?.path || !fileQuery.data?.ref) return
    onFileOpened?.({
      panelId,
      repoId: repo.id,
      path: fileQuery.data.path,
      ref: fileQuery.data.ref,
    })
    onRefObserved?.({
      panelId,
      repoId: repo.id,
      ref: fileQuery.data.ref,
      path: fileQuery.data.path,
    })
  }, [
    fileQuery.data?.path,
    fileQuery.data?.ref,
    onFileOpened,
    onRefObserved,
    panelId,
    repo.id,
  ])

  const roomContextState =
    fileQuery.data?.path && fileQuery.data?.ref && getRoomContextState
      ? getRoomContextState({
          panelId,
          repoId: repo.id,
          path: fileQuery.data.path,
          ref: fileQuery.data.ref,
          isBinary: fileQuery.data.is_binary === true,
          hasContent: typeof fileQuery.data.content === "string",
        })
      : null

  return (
    <PanelContainer
      title={resolvedConfig.title || "File Viewer"}
      headerActions={
        <>
          {resolvedConfig.show_path_badge &&
          (resolvedPath || fileQuery.data?.path) ? (
            <Badge variant="outline" className="font-mono text-[10px]">
              {resolvedPath || fileQuery.data?.path}
            </Badge>
          ) : null}
          {resolvedConfig.show_copy_control && fileQuery.data?.content ? (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-xs"
              onClick={async () => {
                if (!fileQuery.data?.content) return
                await navigator.clipboard.writeText(fileQuery.data.content)
                showSuccessToast("File content copied.")
              }}
            >
              <CopyIcon className="size-3.5" />
              Copy
            </Button>
          ) : null}
          {onToggleRoomContext &&
          fileQuery.data?.path &&
          fileQuery.data?.ref &&
          roomContextState ? (
            <Button
              type="button"
              variant={roomContextState.included ? "secondary" : "ghost"}
              size="sm"
              className="h-7 px-2 text-xs"
              disabled={roomContextState.pending || !roomContextState.canToggle}
              title={roomContextState.disabledReason ?? undefined}
              onClick={async () => {
                if (!fileQuery.data) return
                await onToggleRoomContext({
                  panelId,
                  repoId: repo.id,
                  repoSlug: repo.slug,
                  path: fileQuery.data.path,
                  ref: fileQuery.data.ref,
                  content: fileQuery.data.content ?? "",
                  contentType: fileQuery.data.content_type || null,
                  encoding: fileQuery.data.encoding || null,
                  sizeBytes: fileQuery.data.size_bytes ?? null,
                  isBinary: fileQuery.data.is_binary === true,
                  isTruncated: fileQuery.data.is_truncated === true,
                  truncationReason: fileQuery.data.truncation_reason || null,
                })
              }}
            >
              {roomContextState.pending ? (
                <Loader2 className="size-3.5 animate-spin" />
              ) : roomContextState.included ? (
                <CheckIcon className="size-3.5" />
              ) : (
                <PlusIcon className="size-3.5" />
              )}
              {roomContextState.included ? "In Context" : "Add to Context"}
            </Button>
          ) : null}
        </>
      }
      footer={
        fileQuery.data ? (
          <div className="px-4 py-2 text-xs text-muted-foreground">
            <div className="flex flex-wrap items-center gap-3">
              <div className="inline-flex items-center gap-2">
                <FileCode2 className="size-3.5" />
                Ref {fileQuery.data.ref}
              </div>
              {"resolved_from_path" in fileQuery.data &&
              typeof fileQuery.data.resolved_from_path === "string" ? (
                <div className="font-mono">
                  Resolved from {fileQuery.data.resolved_from_path}
                </div>
              ) : null}
            </div>
          </div>
        ) : null
      }
      scrollable={false}
    >
      {!resolvedPath && !isReadmeMode ? (
        <div className="flex h-full flex-col items-center justify-center gap-2 p-6 text-center text-sm text-muted-foreground">
          <FileQuestion className="size-6" />
          <div>{resolvedConfig.empty_label || "No file is selected for this viewer instance."}</div>
        </div>
      ) : fileQuery.isLoading ? (
        <div className="flex h-full items-center justify-center p-6 text-sm text-muted-foreground">
          Loading file content...
        </div>
      ) : fileQuery.isError || !fileQuery.data ? (
        <div className="flex h-full items-center justify-center p-6 text-sm text-muted-foreground">
          {isReadmeMode
            ? "No README is available for this repository."
            : "Could not load file content for this panel instance."}
        </div>
      ) : (
        <RepoContentRenderer
          chrome="default"
          title={
            resolvedConfig.title ||
            (isReadmeMode ? "README" : fileQuery.data.path)
          }
          subtitle={
            isReadmeMode
              ? "Platform-managed repository README"
              : "Platform-managed repository file view"
          }
          content={toRepoRenderableContent({
            repoId: repo.id,
            repoSlug: repo.slug,
            path:
              "resolved_from_path" in fileQuery.data &&
              typeof fileQuery.data.resolved_from_path === "string"
                ? fileQuery.data.resolved_from_path
                : fileQuery.data.path,
            content: fileQuery.data.content,
            mimeType: fileQuery.data.content_type || undefined,
            encoding: fileQuery.data.encoding,
            sizeBytes: fileQuery.data.size_bytes,
            isBinary: fileQuery.data.is_binary,
            isTruncated: fileQuery.data.is_truncated,
            truncationReason: fileQuery.data.truncation_reason || undefined,
            isUnsupportedPreview: fileQuery.data.is_unsupported_preview,
            ref: fileQuery.data.ref,
            resolvedFromPath:
              "resolved_from_path" in fileQuery.data &&
              typeof fileQuery.data.resolved_from_path === "string"
                ? fileQuery.data.resolved_from_path
                : undefined,
            sourceKind: isReadmeMode ? "readme" : "blob",
          })}
          variant="page"
          safeMode
          className="h-full rounded-none border-0 shadow-none"
        />
      )}
    </PanelContainer>
  )
}
