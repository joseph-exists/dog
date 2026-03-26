import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  ChevronLeft,
  FileText,
  FolderOpen,
  GitCommitHorizontal,
  Loader2,
  SaveIcon,
} from "lucide-react"
import { useEffect, useState } from "react"
import type { ApiError } from "@/client/core/ApiError"
import { UserReposService } from "@/client/sdk.gen"
import type {
  ShadowRepoTreeEntry,
  UserRepoFileMutationInput,
  UserRepoPublic,
} from "@/client/types.gen"
import { PanelContainer } from "@/components/Page/primitives"
import { getUserRepoHeadQueryOptions } from "@/components/Repo/hooks"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { parseRepoExplorerPanelConfig } from "./config"
import { RepoCapabilityPlaceholderPanel } from "./RepoCapabilityPlaceholderPanel"

function TreeEntryRow({
  entry,
  showSizes,
  onSelect,
}: {
  entry: ShadowRepoTreeEntry
  showSizes: boolean
  onSelect: (entry: ShadowRepoTreeEntry) => void
}) {
  const isDirectory = entry.entry_type === "directory"

  return (
    <button
      type="button"
      onClick={() => onSelect(entry)}
      className="flex w-full items-center justify-between gap-2 rounded-md px-2 py-1.5 text-left text-xs hover:bg-background/70"
    >
      <div className="min-w-0 flex items-center gap-2">
        {isDirectory ? (
          <FolderOpen className="h-3.5 w-3.5 text-amber-600" />
        ) : (
          <FileText className="h-3.5 w-3.5 text-muted-foreground" />
        )}
        <span className="truncate">{entry.name}</span>
      </div>
      {showSizes && typeof entry.size_bytes === "number" && !isDirectory && (
        <span className="shrink-0 text-[10px] text-muted-foreground">
          {entry.size_bytes}b
        </span>
      )}
    </button>
  )
}

export function RepoExplorerPanel({
  repo,
  panelId,
  config,
  enabled,
  selectedPath,
  onSelectPath,
  onRefObserved,
}: {
  repo: UserRepoPublic
  panelId: string
  config: unknown
  enabled: boolean
  selectedPath: string | null
  onSelectPath: (path: string | null) => void
  onRefObserved?: (payload: {
    panelId: string
    repoId: string
    ref: string
    path?: string | null
  }) => void
}) {
  const queryClient = useQueryClient()
  const resolvedConfig = parseRepoExplorerPanelConfig(config, panelId)
  const [currentPath, setCurrentPath] = useState(resolvedConfig.initial_path)
  const [createMode, setCreateMode] = useState<"file" | "folder" | null>(null)
  const [draftCreatePath, setDraftCreatePath] = useState("")
  const [draftCreateContent, setDraftCreateContent] = useState("")

  useEffect(() => {
    setCurrentPath(resolvedConfig.initial_path)
  }, [resolvedConfig.initial_path])

  if (!enabled) {
    return (
      <RepoCapabilityPlaceholderPanel
        title={resolvedConfig.title || "Explorer"}
        description="Repository tree browsing is configured per panel, but this repository is not currently viewer-enabled."
        unmetRequirements={["user-repo tree read capability"]}
      />
    )
  }

  const parentPath = currentPath
    .split("/")
    .filter(Boolean)
    .slice(0, -1)
    .join("/")
  const explicitRef = resolvedConfig.ref?.trim() || null
  const commitLimit = resolvedConfig.show_commit_badge ? 1 : 0

  const viewQuery = useQuery({
    queryKey: [
      "repo-explorer-view",
      panelId,
      repo.id,
      currentPath,
      explicitRef ?? "__default__",
    ],
    queryFn: () =>
      UserReposService.getUserRepoTree({
        repoId: repo.id,
        path: currentPath || undefined,
        // Only send `ref` when the panel author explicitly pins one.
        // Otherwise the backend resolves the live default branch from Gittin,
        // which avoids stale `main`/`master` assumptions in the route payload.
        ref: explicitRef || undefined,
        // Only request commits when the panel is configured to render commit
        // metadata. Tree browsing does not require commit history payloads.
        commitLimit,
      }),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  })
  const headQuery = useQuery({
    ...getUserRepoHeadQueryOptions(repo.id, viewQuery.data?.ref || explicitRef),
    enabled,
  })
  const createMutation = useMutation({
    mutationFn: (payload: {
      branch: string
      expectedHeadSha: string
      commitMessage: string
      mutations: Array<UserRepoFileMutationInput>
    }) =>
      UserReposService.commitUserRepoChanges({
        repoId: repo.id,
        requestBody: {
          branch: payload.branch,
          expected_head_sha: payload.expectedHeadSha,
          commit_message: payload.commitMessage,
          mutations: payload.mutations,
        },
      }),
    onSuccess: async (_response, payload) => {
      const upsertedPath = payload.mutations.find(
        (mutation) =>
          mutation.operation === "upsert" &&
          !mutation.path.endsWith("/.gitkeep"),
      )?.path
      if (upsertedPath) onSelectPath(upsertedPath)
      setCreateMode(null)
      setDraftCreatePath("")
      setDraftCreateContent("")
      showSuccessToast("Repository changes committed.")
      await Promise.all([
        viewQuery.refetch(),
        headQuery.refetch(),
        queryClient.invalidateQueries({
          predicate: (query) =>
            Array.isArray(query.queryKey) &&
            query.queryKey[0] === "repo-file-view" &&
            query.queryKey.includes(repo.id),
        }),
      ])
    },
    onError: async (error: ApiError) => {
      const body = error?.body as
        | { error_code?: string; detail?: { error_code?: string } }
        | undefined
      const errorCode = body?.error_code || body?.detail?.error_code
      if (errorCode === "HEAD_CONFLICT") {
        showErrorToast(
          "This repo has moved. Reloading latest head before retry.",
        )
        await Promise.all([viewQuery.refetch(), headQuery.refetch()])
        return
      }
      if (errorCode === "REPO_NOT_READY") {
        showErrorToast("Repository is not writable yet.")
        return
      }
      if (errorCode === "INVALID_WRITE_REQUEST") {
        showErrorToast("Write request was rejected. Check file path/content.")
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
    if (!viewQuery.data?.ref || !onRefObserved) return
    onRefObserved({
      panelId,
      repoId: repo.id,
      ref: viewQuery.data.ref,
      path: currentPath || null,
    })
  }, [currentPath, onRefObserved, panelId, repo.id, viewQuery.data?.ref])

  return (
    <PanelContainer
      title={resolvedConfig.title || "Explorer"}
      headerActions={
        <div className="flex items-center gap-2">
          <Badge variant="outline">{currentPath || "/"}</Badge>
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
      }
      scrollable
    >
      <div className="space-y-3 p-4">
        {createMode ? (
          <div className="space-y-2 rounded-md border bg-background/80 p-2">
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
                  const rawPath = draftCreatePath.trim().replaceAll("\\", "/")
                  const normalizedPath = rawPath.includes("/")
                    ? rawPath
                    : [currentPath, rawPath].filter(Boolean).join("/")
                  const targetPath = normalizedPath
                    .replace(/^\/+/, "")
                    .replace(/\/+/g, "/")
                    .replace(/\/+$/, "")
                  if (!targetPath || !headQuery.data?.expectedHeadSha) return

                  void createMutation.mutateAsync({
                    branch:
                      viewQuery.data?.ref ||
                      headQuery.data.ref ||
                      repo.default_branch ||
                      "main",
                    expectedHeadSha: headQuery.data.expectedHeadSha,
                    commitMessage:
                      createMode === "folder"
                        ? `Create folder ${targetPath}`
                        : `Create ${targetPath}`,
                    mutations: [
                      {
                        path:
                          createMode === "folder"
                            ? `${targetPath}/.gitkeep`
                            : targetPath,
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

        {resolvedConfig.show_commit_badge && (
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary" className="gap-1">
              <GitCommitHorizontal className="h-3 w-3" />
              {viewQuery.data?.summary.latest_commit_sha?.slice(0, 8) ||
                "No commit"}
            </Badge>
            <Badge variant="outline">
              {viewQuery.data?.ref || "default branch"}
            </Badge>
          </div>
        )}

        {viewQuery.isLoading ? (
          <div className="text-sm text-muted-foreground">
            Loading repository tree...
          </div>
        ) : viewQuery.isError ? (
          <div className="text-sm text-muted-foreground">
            Could not load the repository tree for this panel instance.
          </div>
        ) : (viewQuery.data?.tree?.length ?? 0) === 0 ? (
          <div className="text-sm text-muted-foreground">
            {resolvedConfig.empty_label || "No files or folders at this path."}
          </div>
        ) : (
          <div className="space-y-1">
            {viewQuery.data?.tree?.map((entry) => (
              <TreeEntryRow
                key={`${entry.entry_type}:${entry.path}`}
                entry={entry}
                showSizes={resolvedConfig.show_sizes}
                onSelect={(nextEntry) => {
                  if (nextEntry.entry_type === "directory") {
                    setCurrentPath(nextEntry.path)
                    return
                  }
                  onSelectPath(nextEntry.path)
                }}
              />
            ))}
          </div>
        )}

        {selectedPath && (
          <div className="text-xs text-muted-foreground">
            Selected file: <span className="font-mono">{selectedPath}</span>
          </div>
        )}
      </div>
    </PanelContainer>
  )
}
