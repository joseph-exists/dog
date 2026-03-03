import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import {
  AlertCircleIcon,
  ArrowLeftIcon,
  ExternalLinkIcon,
  GitBranchIcon,
  InfoIcon,
  LinkIcon,
  LockIcon,
  RefreshCwIcon,
  ShieldAlertIcon,
  UnlockIcon,
} from "lucide-react"
import { getUserRepoQueryOptions } from "@/components/Repo"
import { RepoStatusBadge } from "@/components/Repo/Display/RepoStatusBadge"
import { formatRepoDate } from "@/components/Repo/utils"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

export const Route = createFileRoute("/_layout/repo/$repoId")({
  component: RepoDetailPage,
  head: () => ({
    meta: [{ title: "Repository Details" }],
  }),
})

function RepoDetailSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-6 w-48" />
      <div className="space-y-3">
        <Skeleton className="h-9 w-64" />
        <Skeleton className="h-4 w-80" />
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Skeleton className="h-32 rounded-xl" />
        <Skeleton className="h-32 rounded-xl" />
        <Skeleton className="h-32 rounded-xl" />
        <Skeleton className="h-32 rounded-xl" />
      </div>
      <Skeleton className="h-64 rounded-xl" />
    </div>
  )
}

function RepoDetailPage() {
  const { repoId } = Route.useParams()
  const navigate = useNavigate()
  const {
    data: repo,
    isLoading,
    error,
    refetch,
    isFetching,
  } = useQuery(getUserRepoQueryOptions(repoId))

  if (isLoading) {
    return <RepoDetailSkeleton />
  }

  if (error || !repo) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="mb-4 rounded-full bg-destructive/10 p-4">
          <AlertCircleIcon className="size-8 text-destructive" />
        </div>
        <h3 className="text-lg font-semibold">Repository not found</h3>
        <p className="mb-4 text-muted-foreground">
          This repository does not exist or you do not have access to it.
        </p>
        <Button variant="outline" onClick={() => navigate({ to: "/repos" })}>
          <ArrowLeftIcon className="size-4" />
          Back to Repositories
        </Button>
      </div>
    )
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 p-6">
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link to="/repos">Repositories</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>{repo.display_name}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <div className="flex flex-col gap-4 rounded-3xl border bg-gradient-to-br from-background via-background to-muted/30 p-6 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-semibold tracking-tight">{repo.display_name}</h1>
            <RepoStatusBadge repo={repo} className="text-sm" />
          </div>
          <div className="font-mono text-sm text-muted-foreground">{repo.slug}</div>
          <p className="max-w-3xl text-sm text-muted-foreground">
            {repo.description || "Managed repository import record."}
          </p>
          <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
            <span className="inline-flex items-center gap-2">
              <GitBranchIcon className="size-4" />
              Branch {repo.source_branch || "main"}
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
        </div>

        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCwIcon className={isFetching ? "size-4 animate-spin" : "size-4"} />
            Refresh
          </Button>
          <Button asChild variant="outline">
            <Link to="/repos">
              <ArrowLeftIcon className="size-4" />
              Back
            </Link>
          </Button>
          {repo.gogs_html_url && (
            <Button asChild variant="outline">
              <a href={repo.gogs_html_url} target="_blank" rel="noreferrer">
                Internal Forge
                <ExternalLinkIcon className="size-4" />
              </a>
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Created</CardDescription>
            <CardTitle className="text-base">{formatRepoDate(repo.created_at)}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Updated</CardDescription>
            <CardTitle className="text-base">{formatRepoDate(repo.updated_at)}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Imported</CardDescription>
            <CardTitle className="text-base">{formatRepoDate(repo.imported_at)}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Owner User ID</CardDescription>
            <CardTitle className="truncate font-mono text-sm">{repo.owner_user_id}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <LinkIcon className="size-4" />
              Provenance
            </CardTitle>
            <CardDescription>
              External source and managed platform metadata for this repository.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="space-y-1">
              <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
                Source URL
              </div>
              <div className="rounded-xl border bg-muted/30 p-3 font-mono text-xs break-all">
                {repo.source_repo_url || "Not available"}
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-1">
                <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
                  Managed Repo Name
                </div>
                <div className="rounded-xl border bg-muted/30 p-3 font-mono text-xs">
                  {repo.gogs_repo_name}
                </div>
              </div>
              <div className="space-y-1">
                <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
                  Managed Repo ID
                </div>
                <div className="rounded-xl border bg-muted/30 p-3 font-mono text-xs">
                  {repo.gogs_repo_id ?? "Not available"}
                </div>
              </div>
              <div className="space-y-1 md:col-span-2">
                <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
                  Internal Full Name
                </div>
                <div className="rounded-xl border bg-muted/30 p-3 font-mono text-xs">
                  {repo.gogs_full_name || "Not available"}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <InfoIcon className="size-4" />
                Import State
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <p>
                Repository imports are asynchronous. This page polls automatically while the repo is still provisioning.
              </p>
              <p>
                Current state: <span className="font-medium text-foreground">{repo.import_status ?? "pending"}</span>
              </p>
            </CardContent>
          </Card>

          {repo.import_status === "failed" && (
            <Card className="border-destructive/40">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-destructive">
                  <ShieldAlertIcon className="size-4" />
                  Import Failure
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">
                {repo.import_error || "The platform reported a permanent import failure."}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
