import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  CheckIcon,
  CopyIcon,
  FileCode2,
  FileQuestion,
  Loader2,
  PencilIcon,
  PlusIcon,
  SaveIcon,
  XIcon,
} from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import type { ApiError } from "@/client/core/ApiError"
import type { UserRepoPublic } from "@/client/types.gen"
import { PanelContainer } from "@/components/Page/primitives"
import {
  RepoContentRenderer,
  toRepoRenderableContent,
} from "@/components/Repo"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { parseRepoFileViewerPanelConfig } from "./config"
import {
  createRepoPanelAdapter,
  type RepoPanelDataSourceAdapter,
} from "./dataSource"
import { RepoCapabilityPlaceholderPanel } from "./RepoCapabilityPlaceholderPanel"

function extractCommitErrorCode(error: unknown): string | null {
  if (!error || typeof error !== "object") return null
  const body = (error as { body?: unknown }).body
  if (!body || typeof body !== "object") return null

  const errorCode = (body as { error_code?: unknown }).error_code
  if (typeof errorCode === "string" && errorCode.trim().length > 0)
    return errorCode

  const detail = (body as { detail?: unknown }).detail
  if (!detail || typeof detail !== "object") return null
  const nestedErrorCode = (detail as { error_code?: unknown }).error_code
  return typeof nestedErrorCode === "string" &&
    nestedErrorCode.trim().length > 0
    ? nestedErrorCode
    : null
}

export function RepoFileViewerPanel({
  repo,
  adapter: providedAdapter,
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
  adapter?: RepoPanelDataSourceAdapter
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
  const queryClient = useQueryClient()
  const adapter =
    providedAdapter ??
    createRepoPanelAdapter({ model: "user_repo", repoId: repo.id })
  const resolvedConfig = parseRepoFileViewerPanelConfig(config, panelId)
  const resolvedPath =
    resolvedConfig.path_mode === "fixed"
      ? resolvedConfig.fixed_path || null
      : selectedPath
  const explicitRef = resolvedConfig.ref?.trim() || null
  const isReadmeMode = resolvedConfig.path_mode === "readme"
  const [isEditing, setIsEditing] = useState(false)
  const [draftContent, setDraftContent] = useState("")
  const [draftPath, setDraftPath] = useState<string | null>(null)

  const fileQuery = useQuery({
    queryKey: [
      "repo-file-view",
      panelId,
      adapter.targetKey,
      resolvedPath,
      explicitRef ?? "__default__",
      isReadmeMode ? "readme" : "file",
    ],
    queryFn: () =>
      isReadmeMode
        ? adapter.getReadme({
            // Only send `ref` when the panel config pins one. Default-branch
            // resolution belongs to the backend because imported repos do not
            // consistently use `main`.
            ref: explicitRef || undefined,
          })
        : adapter.getFile({
            path: resolvedPath!,
            ref: explicitRef || undefined,
          }),
    enabled: enabled && (isReadmeMode || Boolean(resolvedPath)),
  })
  const headQuery = useQuery({
    queryKey: [
      "repo-panel-head",
      adapter.targetKey,
      fileQuery.data?.ref || explicitRef || "__default__",
    ],
    queryFn: () => adapter.getHead({ ref: fileQuery.data?.ref || explicitRef }),
    enabled,
    staleTime: 10_000,
    refetchOnWindowFocus: false,
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
  useEffect(() => {
    if (!fileQuery.data?.path) return
    if (draftPath !== fileQuery.data.path) {
      setDraftPath(fileQuery.data.path)
      setDraftContent(fileQuery.data.content ?? "")
      setIsEditing(false)
      return
    }
    if (!isEditing) {
      setDraftContent(fileQuery.data.content ?? "")
    }
  }, [draftPath, fileQuery.data?.content, fileQuery.data?.path, isEditing])

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
  const defaultBranch =
    repo.default_branch ||
    repo.capabilities?.default_branch ||
    repo.source_branch ||
    "main"
  const canEditText =
    isReadmeMode !== true &&
    fileQuery.data != null &&
    fileQuery.data.is_binary !== true &&
    fileQuery.data.is_unsupported_preview !== true &&
    fileQuery.data.is_truncated !== true &&
    typeof fileQuery.data.content === "string"
  const hasDraftChanges =
    canEditText && isEditing && draftContent !== (fileQuery.data?.content ?? "")
  const headSha = headQuery.data?.expectedHeadSha
  const commitMutation = useMutation({
    mutationFn: async (payload: {
      path: string
      content: string
      encoding: string
      branch: string
      expectedHeadSha: string
    }) =>
      adapter.commit({
        branch: payload.branch,
        commitMessage: `Update ${payload.path}`,
        expectedHeadSha: payload.expectedHeadSha,
        mutations: [
          {
            path: payload.path,
            operation: "upsert",
            content: payload.content,
            encoding: payload.encoding,
          },
        ],
      }),
    onSuccess: async (response, payload) => {
      setIsEditing(false)
      setDraftContent(payload.content)
      showSuccessToast(`Saved ${payload.path}.`)
      queryClient.setQueryData(
        ["repo-panel-head", adapter.targetKey, payload.branch],
        () => ({ ref: payload.branch, expectedHeadSha: response.new_head_sha }),
      )
      await Promise.all([
        fileQuery.refetch(),
        headQuery.refetch(),
        queryClient.invalidateQueries({
          predicate: (query) =>
            Array.isArray(query.queryKey) &&
            query.queryKey[0] === "repo-explorer-view" &&
            query.queryKey.includes(adapter.targetKey),
        }),
        queryClient.invalidateQueries({
          predicate: (query) =>
            Array.isArray(query.queryKey) &&
            query.queryKey[0] === "repo-panel-head" &&
            query.queryKey[1] === adapter.targetKey,
        }),
      ])
    },
    onError: async (error: ApiError) => {
      const errorCode = extractCommitErrorCode(error)
      if (errorCode === "HEAD_CONFLICT") {
        showErrorToast(
          "This repo has moved. Reloading latest head before retry.",
        )
        await Promise.all([fileQuery.refetch(), headQuery.refetch()])
        return
      }
      if (errorCode === "REPO_NOT_READY") {
        showErrorToast("Repository is not writable yet.")
        return
      }
      if (errorCode === "INVALID_WRITE_REQUEST") {
        showErrorToast(
          "Write request was rejected. Check file path and payload.",
        )
        return
      }
      if (errorCode === "BRANCH_NOT_WRITABLE") {
        showErrorToast("Only the repo default branch is writable.")
        return
      }
      if (errorCode === "WRITE_FAILED") {
        showErrorToast("Backend failed to commit and push this change.")
        return
      }
      showErrorToast("Failed to save file changes.")
    },
  })
  const saveDisabled = !hasDraftChanges || commitMutation.isPending || !headSha
  const headerTitle = useMemo(() => {
    if (!canEditText) return null
    if (headQuery.isLoading) return "Resolving latest head..."
    if (!headSha) return "No writable head available."
    return `Head ${headSha.slice(0, 8)}`
  }, [canEditText, headQuery.isLoading, headSha])

  if (!enabled) {
    return (
      <RepoCapabilityPlaceholderPanel
        title={resolvedConfig.title || "File Viewer"}
        description="Repository file viewing is config-driven and multi-instance ready, but this repository is not currently viewer-enabled."
        unmetRequirements={["user-repo blob read capability"]}
      />
    )
  }

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
          {canEditText && !isEditing ? (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-xs"
              onClick={() => {
                setDraftContent(fileQuery.data?.content ?? "")
                setIsEditing(true)
              }}
            >
              <PencilIcon className="size-3.5" />
              Edit
            </Button>
          ) : null}
          {canEditText && isEditing ? (
            <>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-xs"
                onClick={() => {
                  setDraftContent(fileQuery.data?.content ?? "")
                  setIsEditing(false)
                }}
              >
                <XIcon className="size-3.5" />
                Cancel
              </Button>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className="h-7 px-2 text-xs"
                disabled={saveDisabled}
                title={!headSha ? "Syncing latest repo head..." : undefined}
                onClick={() => {
                  if (!fileQuery.data?.path || !headSha) return
                  void commitMutation.mutateAsync({
                    path: fileQuery.data.path,
                    content: draftContent,
                    encoding: fileQuery.data.encoding || "utf-8",
                    branch: fileQuery.data.ref || explicitRef || defaultBranch,
                    expectedHeadSha: headSha,
                  })
                }}
              >
                {commitMutation.isPending ? (
                  <Loader2 className="size-3.5 animate-spin" />
                ) : (
                  <SaveIcon className="size-3.5" />
                )}
                Save
              </Button>
            </>
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
              {headerTitle ? <div>{headerTitle}</div> : null}
              {hasDraftChanges ? (
                <Badge variant="secondary">Unsaved changes</Badge>
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
          <div>
            {resolvedConfig.empty_label ||
              "No file is selected for this viewer instance."}
          </div>
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
      ) : isEditing && canEditText ? (
        <div className="flex h-full flex-col p-4">
          <textarea
            value={draftContent}
            onChange={(event) => setDraftContent(event.target.value)}
            className="min-h-0 flex-1 resize-none rounded-md border border-border bg-background p-3 font-mono text-xs leading-relaxed"
            spellCheck={false}
            aria-label={`Editing ${fileQuery.data.path}`}
          />
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
            content: fileQuery.data.content ?? "",
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
