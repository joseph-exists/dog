import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  CheckIcon,
  ChevronLeft,
  FileText,
  FolderOpen,
  GitBranch,
  GitCommitHorizontal,
  GitPullRequest,
  Loader2,
  SaveIcon,
  PlusIcon,
} from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import {
  type UserRepoFileMutationInput,
  type ShadowRepoTreeEntry,
  type UserRepoViewResponse,
} from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import { UserReposService } from "@/client/sdk.gen"
import type { ResolvedGitViewConfig } from "@/components/Demo/gitViewConfig"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { cn } from "@/lib/utils"

export interface GitViewRoomContextState {
  included: boolean
  pending: boolean
  canToggle: boolean
  disabledReason?: string | null
}

export type GetGitViewRoomContextState = (payload: {
  panelId: string
  repoId: string
  path: string
  ref: string
  isBinary: boolean
  hasContent: boolean
}) => GitViewRoomContextState

export type ToggleGitViewRoomContext = (payload: {
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
}) => Promise<void>

interface RepoHeaderProps {
  title?: string | null
  subtitle: string
}

function RepoHeader({ title, subtitle }: RepoHeaderProps) {
  return (
    <div className="space-y-1">
      <div className="text-sm font-medium">{title ?? "Git View"}</div>
      <div className="text-xs text-muted-foreground">{subtitle}</div>
    </div>
  )
}

export function GitViewInvalidConfig({
  title,
  subtitle,
  expectedConfig,
}: {
  title?: string | null
  subtitle: string
  expectedConfig: Record<string, unknown>
}) {
  return (
    <div className="p-4 space-y-3">
      <RepoHeader title={title} subtitle={subtitle} />
      <div className="rounded-md border border-dashed p-3 text-xs text-muted-foreground">
        Expected config:
        <pre className="mt-2 overflow-auto rounded border bg-muted/40 p-3 text-xs">
          {JSON.stringify(expectedConfig, null, 2)}
        </pre>
      </div>
    </div>
  )
}

function TreeEntryRow({
  entry,
  isSelected,
  onSelect,
}: {
  entry: ShadowRepoTreeEntry
  isSelected: boolean
  onSelect: (entry: ShadowRepoTreeEntry) => void
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(entry)}
      className={cn(
        "flex w-full items-center justify-between gap-2 rounded px-2 py-1.5 text-left text-xs transition-colors hover:bg-background/70",
        isSelected && "bg-background shadow-sm",
      )}
    >
      <div className="min-w-0 flex items-center gap-2">
        {entry.entry_type === "directory" ? (
          <FolderOpen className="h-3.5 w-3.5 text-amber-600" />
        ) : (
          <FileText className="h-3.5 w-3.5 text-muted-foreground" />
        )}
        <span className="truncate">{entry.name}</span>
      </div>
      {typeof entry.size_bytes === "number" && entry.entry_type === "file" && (
        <span className="shrink-0 text-[10px] text-muted-foreground">
          {entry.size_bytes}b
        </span>
      )}
    </button>
  )
}

function CommitList({ view }: { view: UserRepoViewResponse }) {
  const commits = view.commits ?? []

  return (
    <div className="rounded-md border bg-muted/20 p-3">
      <div className="mb-2 text-xs text-muted-foreground">Recent commits</div>
      {commits.length === 0 ? (
        <div className="text-xs text-muted-foreground">No commits yet.</div>
      ) : (
        <div className="space-y-2">
          {commits.map((commit) => (
            <div key={commit.sha} className="flex items-start gap-2 text-xs">
              <GitCommitHorizontal className="mt-0.5 h-3.5 w-3.5 text-muted-foreground" />
              <div className="min-w-0">
                <div className="truncate font-medium">{commit.message}</div>
                <div className="text-muted-foreground">
                  {commit.short_sha}
                  {commit.author_name ? ` • ${commit.author_name}` : ""}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

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

function normalizeRepoPath(basePath: string, candidatePath: string): string {
  const normalizedCandidate = candidatePath.trim().replaceAll("\\", "/")
  const source = normalizedCandidate.includes("/")
    ? normalizedCandidate
    : [basePath, normalizedCandidate].filter(Boolean).join("/")
  return source.replace(/^\/+/, "").replace(/\/+/g, "/").replace(/\/+$/, "")
}

function useUserRepo(config: ResolvedGitViewConfig) {
  return useQuery({
    queryKey: ["git-view-user-repo", config.entity_type, config.entity_id],
    queryFn: () => UserReposService.getUserRepo({ repoId: config.entity_id }),
    enabled: config.entity_type === "user_repo",
  })
}

export interface GitViewCoreProps {
  title?: string | null
  selectionKey?: string
  config: ResolvedGitViewConfig
  rawConfig: unknown
  onSelectFileForDebug?: (selectionKey: string, path: string | null) => void
  getRoomContextState?: GetGitViewRoomContextState
  onToggleRoomContext?: ToggleGitViewRoomContext
}

export function GitViewCore({
  title,
  selectionKey,
  config,
  rawConfig,
  onSelectFileForDebug,
  getRoomContextState,
  onToggleRoomContext,
}: GitViewCoreProps) {
  const queryClient = useQueryClient()
  const [currentPath, setCurrentPath] = useState(config.initial_path)
  const [selectedFilePath, setSelectedFilePath] = useState<string>("")
  const [createMode, setCreateMode] = useState<"file" | "folder" | null>(null)
  const [draftCreatePath, setDraftCreatePath] = useState("")
  const [draftCreateContent, setDraftCreateContent] = useState("")
  const repoQuery = useUserRepo(config)
  const isUserRepo = config.entity_type === "user_repo"
  const repo = repoQuery.data ?? null

  const viewQuery = useQuery({
    queryKey: [
      "git-view-tree",
      config.entity_type,
      config.entity_id,
      currentPath,
      config.commit_limit,
    ],
    queryFn: () =>
      UserReposService.getUserRepoTree({
        repoId: config.entity_id,
        path: currentPath || undefined,
        commitLimit: config.commit_limit,
      }),
    enabled: isUserRepo,
  })

  const treeEntries = viewQuery.data?.tree ?? []
  const fileEntries = useMemo(
    () => treeEntries.filter((entry) => entry.entry_type === "file"),
    [treeEntries],
  )

  useEffect(() => {
    if (!config.show_file_content) return
    if (selectedFilePath) {
      const stillVisible = fileEntries.some(
        (entry) => entry.path === selectedFilePath,
      )
      if (stillVisible) return
    }
    setSelectedFilePath(fileEntries[0]?.path ?? "")
  }, [config.show_file_content, fileEntries, selectedFilePath])

  const fileQuery = useQuery({
    queryKey: [
      "git-view-file",
      config.entity_type,
      config.entity_id,
      selectedFilePath,
    ],
    queryFn: () =>
      UserReposService.getUserRepoFile({
        repoId: config.entity_id,
        path: selectedFilePath,
      }),
    enabled: isUserRepo && config.show_file_content && Boolean(selectedFilePath),
  })
  const targetRef =
    fileQuery.data?.ref ||
    viewQuery.data?.ref ||
    repo?.default_branch ||
    repo?.capabilities?.default_branch ||
    "main"
  const headQuery = useQuery({
    queryKey: ["git-view-head", config.entity_id, targetRef],
    queryFn: async () => {
      const view = await UserReposService.getUserRepoTree({
        repoId: config.entity_id,
        ref: targetRef,
        commitLimit: 1,
      })
      return {
        ref: view.ref,
        expectedHeadSha: view.summary.latest_commit_sha || null,
      }
    },
    enabled: isUserRepo,
    staleTime: 10_000,
    refetchOnWindowFocus: false,
  })
  const createMutation = useMutation({
    mutationFn: (payload: {
      branch: string
      expectedHeadSha: string
      commitMessage: string
      mutations: Array<UserRepoFileMutationInput>
    }) =>
      UserReposService.commitUserRepoChanges({
        repoId: config.entity_id,
        requestBody: {
          branch: payload.branch,
          expected_head_sha: payload.expectedHeadSha,
          commit_message: payload.commitMessage,
          mutations: payload.mutations,
        },
      }),
    onSuccess: async (response, payload) => {
      const upsertedPath = payload.mutations.find(
        (mutation) =>
          mutation.operation === "upsert" && !mutation.path.endsWith("/.gitkeep"),
      )?.path
      if (upsertedPath) {
        setSelectedFilePath(upsertedPath)
      }
      setCreateMode(null)
      setDraftCreatePath("")
      setDraftCreateContent("")
      showSuccessToast("Repository changes committed.")
      queryClient.setQueryData(["git-view-head", config.entity_id, payload.branch], {
        ref: payload.branch,
        expectedHeadSha: response.new_head_sha,
      })
      await Promise.all([viewQuery.refetch(), fileQuery.refetch(), headQuery.refetch()])
    },
    onError: async (error: ApiError) => {
      const errorCode = extractCommitErrorCode(error)
      if (errorCode === "HEAD_CONFLICT") {
        showErrorToast(
          "Repo head changed. Reloading latest branch state before retry.",
        )
        await Promise.all([viewQuery.refetch(), fileQuery.refetch(), headQuery.refetch()])
        return
      }
      if (errorCode === "REPO_NOT_READY") {
        showErrorToast("Repository is not writable yet.")
        return
      }
      if (errorCode === "INVALID_WRITE_REQUEST") {
        showErrorToast("Write request was rejected. Check the new path/content.")
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
      showErrorToast("Failed to create repo changes.")
    },
  })

  useEffect(() => {
    if (!onSelectFileForDebug || !selectionKey) return
    onSelectFileForDebug(selectionKey, selectedFilePath || null)
  }, [onSelectFileForDebug, selectedFilePath, selectionKey])

  const roomContextState =
    fileQuery.data?.path && fileQuery.data?.ref && getRoomContextState
      ? getRoomContextState({
          panelId: selectionKey ?? "gitView",
          repoId: config.entity_id,
          path: fileQuery.data.path,
          ref: fileQuery.data.ref,
          isBinary: fileQuery.data.is_binary === true,
          hasContent: typeof fileQuery.data.content === "string",
        })
      : null

  const pathSegments = currentPath
    .split("/")
    .map((segment) => segment.trim())
    .filter(Boolean)
  const parentPath = pathSegments.slice(0, -1).join("/")

  return (
    <div className="p-4 space-y-4">
      <RepoHeader
        title={title}
        subtitle="Live platform-managed repository view resolved through backend APIs."
      />

      <div className="flex flex-wrap gap-2">
        <Badge variant="outline" className="gap-1">
          <GitBranch className="h-3 w-3" />
          {config.entity_type}/{config.entity_id}
        </Badge>
        <Badge variant="default" className="gap-1">
          <GitPullRequest className="h-3 w-3" />
          {viewQuery.data?.summary.default_branch ??
            repo?.default_branch ??
            "main"}
        </Badge>
        <Badge variant="secondary">
          Tree: {viewQuery.data?.tree?.length ?? 0}
        </Badge>
        <Badge variant="secondary">
          Commits: {viewQuery.data?.commits?.length ?? 0}
        </Badge>
      </div>

      {!isUserRepo ? (
        <div className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
          Git View is now backed by the user-repo workspace manager and expects
          <span className="mx-1 font-mono">entity_type: "user_repo"</span>
          with a user repo ID.
          <div className="mt-2">
            Existing authored content can keep this block layout, but the data
            source needs to be repointed to a platform-managed repo.
          </div>
        </div>
      ) : repoQuery.isLoading || viewQuery.isLoading ? (
        <div className="flex items-center gap-2 rounded-md border bg-muted/20 p-4 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading repository view...
        </div>
      ) : repoQuery.isError || viewQuery.isError ? (
        <div className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
          Could not load repository data. This repo may be unavailable or not
          visible to the current user.
        </div>
      ) : !repo || !viewQuery.data ? (
        <div className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
          No repository data available.
        </div>
      ) : (
        <>
          <div className="grid gap-3 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
            <CommitList view={viewQuery.data} />

            <div className="rounded-md border bg-muted/20 p-3">
              <div className="mb-2 flex items-center justify-between gap-2">
                <div className="text-xs text-muted-foreground">Tree</div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="max-w-[220px] truncate">
                    {currentPath || "/"}
                  </Badge>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 px-2 text-xs"
                    onClick={() => {
                      setCreateMode("file")
                      setDraftCreatePath("")
                      setDraftCreateContent("")
                    }}
                  >
                    <PlusIcon className="h-3.5 w-3.5" />
                    New File
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 px-2 text-xs"
                    onClick={() => {
                      setCreateMode("folder")
                      setDraftCreatePath("")
                      setDraftCreateContent("")
                    }}
                  >
                    <FolderOpen className="h-3.5 w-3.5" />
                    New Folder
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 px-2 text-xs"
                    disabled={!currentPath}
                    onClick={() => setCurrentPath(parentPath)}
                  >
                    <ChevronLeft className="h-3.5 w-3.5" />
                    Up
                  </Button>
                </div>
              </div>
              {createMode ? (
                <div className="mb-3 space-y-2 rounded-md border bg-background/80 p-2">
                  <Input
                    value={draftCreatePath}
                    placeholder={
                      createMode === "file"
                        ? "path/to/new-file.ts (or filename for current folder)"
                        : "new-folder (or path/to/new-folder)"
                    }
                    onChange={(event) => setDraftCreatePath(event.target.value)}
                  />
                  {createMode === "file" ? (
                    <Textarea
                      value={draftCreateContent}
                      placeholder="Initial file content"
                      className="min-h-24 text-xs font-mono"
                      onChange={(event) => setDraftCreateContent(event.target.value)}
                    />
                  ) : null}
                  <div className="flex items-center justify-end gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2 text-xs"
                      onClick={() => {
                        setCreateMode(null)
                        setDraftCreatePath("")
                        setDraftCreateContent("")
                      }}
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      className="h-7 px-2 text-xs"
                      disabled={
                        createMutation.isPending ||
                        !draftCreatePath.trim() ||
                        !headQuery.data?.expectedHeadSha
                      }
                      title={
                        !headQuery.data?.expectedHeadSha
                          ? "Resolving latest repo head..."
                          : undefined
                      }
                      onClick={() => {
                        const normalizedPath = normalizeRepoPath(
                          currentPath,
                          draftCreatePath,
                        )
                        if (!normalizedPath) return
                        const mutationPath =
                          createMode === "folder"
                            ? `${normalizedPath}/.gitkeep`
                            : normalizedPath
                        void createMutation.mutateAsync({
                          branch: targetRef,
                          expectedHeadSha: headQuery.data?.expectedHeadSha || "",
                          commitMessage:
                            createMode === "folder"
                              ? `Create folder ${normalizedPath}`
                              : `Create ${normalizedPath}`,
                          mutations: [
                            {
                              path: mutationPath,
                              operation: "upsert",
                              content:
                                createMode === "folder" ? "" : draftCreateContent,
                              encoding: "utf-8",
                            },
                          ],
                        })
                      }}
                    >
                      {createMutation.isPending ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <SaveIcon className="h-3.5 w-3.5" />
                      )}
                      Commit
                    </Button>
                  </div>
                </div>
              ) : null}

              {treeEntries.length === 0 ? (
                <div className="text-xs text-muted-foreground">
                  No files or folders at this path.
                </div>
              ) : (
                <div className="space-y-1">
                  {treeEntries.map((entry) => (
                    <TreeEntryRow
                      key={`${entry.entry_type}:${entry.path}`}
                      entry={entry}
                      isSelected={selectedFilePath === entry.path}
                      onSelect={(nextEntry) => {
                        if (nextEntry.entry_type === "directory") {
                          setCurrentPath(nextEntry.path)
                          setSelectedFilePath("")
                          return
                        }
                        setSelectedFilePath(nextEntry.path)
                      }}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>

          {config.show_file_content && (
            <div className="rounded-md border bg-muted/20 p-3">
              <div className="mb-2 flex items-center justify-between gap-2">
                <div className="text-xs text-muted-foreground">File content</div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="max-w-[240px] truncate">
                    {selectedFilePath || "No file selected"}
                  </Badge>
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
                          panelId: selectionKey ?? "gitView",
                          repoId: config.entity_id,
                          repoSlug: repo?.slug ?? config.entity_id,
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
                </div>
              </div>

              {!selectedFilePath ? (
                <div className="text-xs text-muted-foreground">
                  Select a file to view its contents.
                </div>
              ) : fileQuery.isLoading ? (
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Loading file content...
                </div>
              ) : fileQuery.isError ? (
                <div className="text-xs text-muted-foreground">
                  Could not load the selected file.
                </div>
              ) : (
                <pre className="max-h-80 overflow-auto rounded border bg-background/80 p-3 text-xs whitespace-pre-wrap">
                  {fileQuery.data?.content ?? ""}
                </pre>
              )}
            </div>
          )}
        </>
      )}

      {config.show_config_json && (
        <pre className="max-h-64 overflow-auto rounded border bg-muted/40 p-3 text-xs">
          {JSON.stringify(rawConfig ?? {}, null, 2)}
        </pre>
      )}
    </div>
  )
}
