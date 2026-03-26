import { Link } from "@tanstack/react-router"
import {
  ArrowUpRightIcon,
  GitBranchIcon,
  LockIcon,
  MoreVerticalIcon,
  Trash2Icon,
  UnlockIcon,
} from "lucide-react"
import type { UserRepoPublic } from "@/client/types.gen"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { formatRepoShortDate, getRepoInitial } from "../utils"
import { RepoStatusBadge } from "./RepoStatusBadge"

export function RepoCard({
  repo,
  canManage = false,
  canCancelImport = false,
  onCancelImport,
  onDeleteRepo,
  isCancelPending = false,
  isDeletePending = false,
}: {
  repo: UserRepoPublic
  canManage?: boolean
  canCancelImport?: boolean
  onCancelImport?: (repo: UserRepoPublic) => void
  onDeleteRepo?: (repo: UserRepoPublic) => void
  isCancelPending?: boolean
  isDeletePending?: boolean
}) {
  return (
    <Card className="group flex h-full flex-col border-border/70 transition-colors hover:border-primary/40">
      <CardHeader className="space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl border bg-muted text-sm font-semibold">
              {getRepoInitial(repo.display_name)}
            </div>
            <div className="min-w-0">
              <CardTitle className="truncate text-base">
                {repo.display_name}
              </CardTitle>
              <div className="truncate text-sm text-muted-foreground">
                {repo.slug}
              </div>
            </div>
          </div>
          <RepoStatusBadge repo={repo} />
        </div>
        <p className="line-clamp-2 text-sm text-muted-foreground">
          {repo.description || "Platform-managed repository import."}
        </p>
      </CardHeader>

      <CardContent className="flex-1 space-y-3 text-sm">
        <div className="flex items-center justify-between gap-3 text-muted-foreground">
          <span className="inline-flex items-center gap-2">
            <GitBranchIcon className="size-4" />
            {repo.source_branch || "main"}
          </span>
          <span className="inline-flex items-center gap-2">
            {repo.is_private ? (
              <LockIcon className="size-4" />
            ) : (
              <UnlockIcon className="size-4" />
            )}
            {repo.is_private ? "Private" : "Public"}
          </span>
        </div>

        <div className="rounded-xl border bg-muted/30 p-3">
          <div className="mb-1 text-xs uppercase tracking-[0.18em] text-muted-foreground">
            Source
          </div>
          <div className="truncate font-mono text-xs">
            {repo.source_repo_url || "Not provided"}
          </div>
        </div>
      </CardContent>

      <CardFooter className="flex items-center justify-between gap-3 border-t pt-4 text-xs text-muted-foreground">
        <span>Created {formatRepoShortDate(repo.created_at)}</span>
        <div className="flex items-center gap-1">
          {canManage ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label="Repository actions"
                >
                  <MoreVerticalIcon className="size-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {canCancelImport ? (
                  <DropdownMenuItem
                    disabled={isCancelPending || isDeletePending}
                    onClick={() => onCancelImport?.(repo)}
                  >
                    {isCancelPending ? "Canceling import..." : "Cancel import"}
                  </DropdownMenuItem>
                ) : null}
                <DropdownMenuItem
                  disabled={isDeletePending || isCancelPending}
                  className="text-destructive focus:text-destructive"
                  onClick={() => onDeleteRepo?.(repo)}
                >
                  <Trash2Icon className="mr-2 size-4" />
                  {isDeletePending ? "Deleting..." : "Delete repository"}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : null}
          <Button asChild variant="ghost" size="sm">
            <Link to="/repo/$repoId" params={{ repoId: repo.id }}>
              Review
              <ArrowUpRightIcon className="size-4" />
            </Link>
          </Button>
        </div>
      </CardFooter>
    </Card>
  )
}
