import { useQuery } from "@tanstack/react-query"
import {
  CheckIcon,
  ChevronLeft,
  FileText,
  FolderOpen,
  GitBranch,
  GitCommitHorizontal,
  GitPullRequest,
  Loader2,
  PlusIcon,
} from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import {
  type ShadowRepoTreeEntry,
  type UserRepoViewResponse,
} from "@/client"
import { UserReposService } from "@/client/sdk.gen"
import type { ResolvedShadowRepoGitViewConfig } from "@/components/Demo/gitViewConfig"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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

function useUserRepo(config: ResolvedShadowRepoGitViewConfig) {
  return useQuery({
    queryKey: ["git-view-user-repo", config.entity_type, config.entity_id],
    queryFn: () => UserReposService.getUserRepo({ repoId: config.entity_id }),
    enabled: config.entity_type === "user_repo",
  })
}

export interface GitViewCoreProps {
  title?: string | null
  selectionKey?: string
  config: ResolvedShadowRepoGitViewConfig
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
  const [currentPath, setCurrentPath] = useState(config.initial_path)
  const [selectedFilePath, setSelectedFilePath] = useState<string>("")
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
                    disabled={!currentPath}
                    onClick={() => setCurrentPath(parentPath)}
                  >
                    <ChevronLeft className="h-3.5 w-3.5" />
                    Up
                  </Button>
                </div>
              </div>

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
