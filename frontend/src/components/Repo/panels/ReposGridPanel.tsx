import { useSuspenseQuery } from "@tanstack/react-query"
import { FolderGit2Icon } from "lucide-react"
import { Suspense } from "react"
import type { UserRepoPublic } from "@/client/types.gen"
import { repoQueryKeys } from "@/components/Repo/hooks"
import { UserReposService } from "@/client/sdk.gen"
import { PanelContainer } from "@/components/Page/primitives"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { ImportRepoDialog } from "../Dialogs/ImportRepoDialog"
import { RepoCard } from "../Display/RepoCard"

function getReposQueryOptions() {
  return {
    queryKey: repoQueryKeys.all,
    queryFn: () => UserReposService.listUserRepos(),
  }
}

function RepoCardSkeleton() {
  return (
    <Card>
      <CardHeader className="space-y-3">
        <div className="flex items-center gap-3">
          <Skeleton className="size-11 rounded-2xl" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-5 w-36" />
            <Skeleton className="h-4 w-24" />
          </div>
        </div>
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-16 w-full rounded-xl" />
      </CardContent>
    </Card>
  )
}

function PendingRepos() {
  return (
    <div className="grid gap-4 p-4 sm:grid-cols-2 xl:grid-cols-3">
      <RepoCardSkeleton />
      <RepoCardSkeleton />
      <RepoCardSkeleton />
    </div>
  )
}

function RepoSection({
  title,
  description,
  repos,
}: {
  title: string
  description: string
  repos: UserRepoPublic[]
}) {
  if (repos.length === 0) return null

  return (
    <section className="space-y-4">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold">{title}</h2>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {repos.map((repo) => (
          <RepoCard key={repo.id} repo={repo} />
        ))}
      </div>
    </section>
  )
}

function ReposGridContent() {
  const { data } = useSuspenseQuery(getReposQueryOptions())
  const repos = data.data ?? []

  const importing = repos.filter(
    (repo) =>
      repo.import_status === "pending" || repo.import_status === "importing",
  )
  const ready = repos.filter((repo) => repo.import_status === "ready")
  const failed = repos.filter((repo) => repo.import_status === "failed")

  if (repos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
        <div className="mb-4 rounded-full bg-muted p-4">
          <FolderGit2Icon className="size-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No repositories yet</h3>
        <p className="mb-5 max-w-xl text-muted-foreground">
          Import repositories you want the platform to manage. Status updates and failure details will stay visible here.
        </p>
        <ImportRepoDialog />
      </div>
    )
  }

  return (
    <div className="space-y-8 p-4">
      <RepoSection
        title="Import Queue"
        description="Repositories still provisioning into the managed workspace."
        repos={importing}
      />
      <RepoSection
        title="Ready"
        description="Managed repositories that finished importing successfully."
        repos={ready}
      />
      <RepoSection
        title="Needs Attention"
        description="Imports that failed and need user review."
        repos={failed}
      />
    </div>
  )
}

export function ReposGridPanel() {
  return (
    <PanelContainer
      title="Repositories"
      headerActions={<ImportRepoDialog />}
      scrollable
    >
      <Suspense fallback={<PendingRepos />}>
        <ReposGridContent />
      </Suspense>
    </PanelContainer>
  )
}
