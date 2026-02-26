import {
  GitBranch,
  GitCommitHorizontal,
  GitPullRequest,
  Plus,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"

interface GitViewBlockProps {
  title?: string | null
  config: unknown
}

interface GitCommitItem {
  sha: string
  message: string
  author?: string
}

interface GitFileItem {
  path: string
  status?: string
}

interface GitViewConfig {
  repo_name: string
  active_branch: string
  branches: string[]
  staged_files: GitFileItem[]
  recent_commits: GitCommitItem[]
  show_config_json: boolean
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return []
  return value.filter(
    (item): item is string => typeof item === "string" && item.length > 0,
  )
}

function asGitFiles(value: unknown): GitFileItem[] {
  if (!Array.isArray(value)) return []
  const files: GitFileItem[] = []
  for (const item of value) {
    if (!item || typeof item !== "object") continue
    const raw = item as Record<string, unknown>
    const path = typeof raw.path === "string" ? raw.path : ""
    if (!path) continue

    files.push({
      path,
      status: typeof raw.status === "string" ? raw.status : undefined,
    })
  }
  return files
}

function asGitCommits(value: unknown): GitCommitItem[] {
  if (!Array.isArray(value)) return []
  const commits: GitCommitItem[] = []
  for (const item of value) {
    if (!item || typeof item !== "object") continue
    const raw = item as Record<string, unknown>
    const sha = typeof raw.sha === "string" ? raw.sha : ""
    const message = typeof raw.message === "string" ? raw.message : ""
    if (!sha || !message) continue

    commits.push({
      sha,
      message,
      author: typeof raw.author === "string" ? raw.author : undefined,
    })
  }
  return commits
}

function toConfig(value: unknown): GitViewConfig {
  const raw =
    value && typeof value === "object" ? (value as Record<string, unknown>) : {}

  const repoName =
    typeof raw.repo_name === "string" && raw.repo_name.length > 0
      ? raw.repo_name
      : "demo-repo"
  const activeBranch =
    typeof raw.active_branch === "string" && raw.active_branch.length > 0
      ? raw.active_branch
      : "main"

  return {
    repo_name: repoName,
    active_branch: activeBranch,
    branches: asStringArray(raw.branches),
    staged_files: asGitFiles(raw.staged_files),
    recent_commits: asGitCommits(raw.recent_commits),
    show_config_json: raw.show_config_json === true,
  }
}

export function GitViewBlock({ title, config }: GitViewBlockProps) {
  const parsedConfig = toConfig(config)

  return (
    <div className="p-4 space-y-4">
      <div className="space-y-1">
        <div className="text-sm font-medium">{title ?? "Git View"}</div>
        <div className="text-xs text-muted-foreground">
          Repository state snapshot for this demo context.
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <Badge variant="outline" className="gap-1">
          <GitBranch className="h-3 w-3" />
          {parsedConfig.repo_name}
        </Badge>
        <Badge variant="default" className="gap-1">
          <GitPullRequest className="h-3 w-3" />
          {parsedConfig.active_branch}
        </Badge>
        <Badge variant="secondary">
          Branches: {parsedConfig.branches.length || 1}
        </Badge>
        <Badge variant="secondary">
          Staged: {parsedConfig.staged_files.length}
        </Badge>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-md border bg-muted/20 p-3">
          <div className="mb-2 text-xs text-muted-foreground">Branches</div>
          <div className="space-y-1">
            {[
              parsedConfig.active_branch,
              ...parsedConfig.branches.filter(
                (b) => b !== parsedConfig.active_branch,
              ),
            ].map((branch) => (
              <div key={branch} className="flex items-center gap-2 text-xs">
                {branch === parsedConfig.active_branch ? (
                  <Plus className="h-3 w-3 text-emerald-600" />
                ) : (
                  <GitBranch className="h-3 w-3 text-muted-foreground" />
                )}
                <span>{branch}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-md border bg-muted/20 p-3">
          <div className="mb-2 text-xs text-muted-foreground">Staged files</div>
          {parsedConfig.staged_files.length === 0 ? (
            <div className="text-xs text-muted-foreground">
              No staged changes.
            </div>
          ) : (
            <div className="space-y-1">
              {parsedConfig.staged_files.map((file) => (
                <div
                  key={file.path}
                  className="flex items-center justify-between gap-2 text-xs"
                >
                  <span className="truncate">{file.path}</span>
                  {file.status && (
                    <Badge variant="outline" className="text-[10px]">
                      {file.status}
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="rounded-md border bg-muted/20 p-3">
        <div className="mb-2 text-xs text-muted-foreground">Recent commits</div>
        {parsedConfig.recent_commits.length === 0 ? (
          <div className="text-xs text-muted-foreground">
            No commits supplied in config.
          </div>
        ) : (
          <div className="space-y-2">
            {parsedConfig.recent_commits.map((commit) => (
              <div key={commit.sha} className="flex items-start gap-2 text-xs">
                <GitCommitHorizontal className="h-3.5 w-3.5 mt-0.5 text-muted-foreground" />
                <div className="min-w-0">
                  <div className="font-medium truncate">{commit.message}</div>
                  <div className="text-muted-foreground">
                    {commit.sha.slice(0, 8)}
                    {commit.author ? ` • ${commit.author}` : ""}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {parsedConfig.show_config_json && (
        <pre className="max-h-64 overflow-auto rounded border bg-muted/40 p-3 text-xs">
          {JSON.stringify(config ?? {}, null, 2)}
        </pre>
      )}
    </div>
  )
}
