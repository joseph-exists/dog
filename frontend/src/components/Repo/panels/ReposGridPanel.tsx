import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query"
import { FolderGit2Icon } from "lucide-react"
import { Suspense } from "react"
import type { ApiError } from "@/client/core/ApiError"
import type { UserRepoPublic } from "@/client/types.gen"
import { repoQueryKeys } from "@/components/Repo/hooks"
import { UserReposService } from "@/client/sdk.gen"
import { PanelContainer } from "@/components/Page/primitives"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import useAuth from "@/hooks/useAuth"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { UserRepoAppService } from "@/services/userRepoService"
import { handleError } from "@/utils"
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
  canManageRepo,
  onCancelImport,
  onDeleteRepo,
  cancelingRepoId,
  deletingRepoId,
}: {
  title: string
  description: string
  repos: UserRepoPublic[]
  canManageRepo: (repo: UserRepoPublic) => boolean
  onCancelImport: (repo: UserRepoPublic) => void
  onDeleteRepo: (repo: UserRepoPublic) => void
  cancelingRepoId: string | null
  deletingRepoId: string | null
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
          <RepoCard
            key={repo.id}
            repo={repo}
            canManage={canManageRepo(repo)}
            canCancelImport={repo.import_status !== "ready"}
            onCancelImport={onCancelImport}
            onDeleteRepo={onDeleteRepo}
            isCancelPending={cancelingRepoId === repo.id}
            isDeletePending={deletingRepoId === repo.id}
          />
        ))}
      </div>
    </section>
  )
}

function ReposGridContent() {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const { data } = useSuspenseQuery(getReposQueryOptions())
  const repos = data.data ?? []
  const cancelImportMutation = useMutation({
    mutationFn: async (repo: UserRepoPublic) =>
      UserRepoAppService.cancelUserRepoImport(repo.id),
    onSuccess: async (_, repo) => {
      showSuccessToast(`Import canceled for ${repo.display_name}.`)
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: repoQueryKeys.all }),
        queryClient.invalidateQueries({ queryKey: repoQueryKeys.detail(repo.id) }),
      ])
    },
    onError: (error: ApiError) => {
      handleError.call(showErrorToast, error)
    },
  })
  const deleteRepoMutation = useMutation({
    mutationFn: async (repo: UserRepoPublic) =>
      UserRepoAppService.deleteUserRepo(repo.id),
    onSuccess: async (_, repo) => {
      showSuccessToast(`Deleted ${repo.display_name}.`)
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: repoQueryKeys.all }),
        queryClient.invalidateQueries({ queryKey: repoQueryKeys.detail(repo.id) }),
      ])
    },
    onError: (error: ApiError) => {
      handleError.call(showErrorToast, error)
    },
  })

  const importing = repos.filter(
    (repo) =>
      repo.import_status === "pending" || repo.import_status === "importing",
  )
  const ready = repos.filter((repo) => repo.import_status === "ready")
  const failed = repos.filter((repo) => repo.import_status === "failed")
  const canManageRepo = (repo: UserRepoPublic) =>
    Boolean(user && (user.is_superuser || user.id === repo.owner_user_id))
  const cancelingRepoId =
    cancelImportMutation.isPending && cancelImportMutation.variables
      ? cancelImportMutation.variables.id
      : null
  const deletingRepoId =
    deleteRepoMutation.isPending && deleteRepoMutation.variables
      ? deleteRepoMutation.variables.id
      : null

  const onCancelImport = (repo: UserRepoPublic) => {
    if (!canManageRepo(repo)) return
    if (repo.import_status === "ready") return
    if (
      !window.confirm(
        `Cancel import for "${repo.display_name}"? Any queued retries will be stopped.`,
      )
    ) {
      return
    }
    cancelImportMutation.mutate(repo)
  }

  const onDeleteRepo = (repo: UserRepoPublic) => {
    if (!canManageRepo(repo)) return
    if (
      !window.confirm(
        `Delete "${repo.display_name}"? This removes the platform repo record and attempts to delete the managed forge repository.`,
      )
    ) {
      return
    }
    deleteRepoMutation.mutate(repo)
  }

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
        canManageRepo={canManageRepo}
        onCancelImport={onCancelImport}
        onDeleteRepo={onDeleteRepo}
        cancelingRepoId={cancelingRepoId}
        deletingRepoId={deletingRepoId}
      />
      <RepoSection
        title="Ready"
        description="Managed repositories that finished importing successfully."
        repos={ready}
        canManageRepo={canManageRepo}
        onCancelImport={onCancelImport}
        onDeleteRepo={onDeleteRepo}
        cancelingRepoId={cancelingRepoId}
        deletingRepoId={deletingRepoId}
      />
      <RepoSection
        title="Needs Attention"
        description="Imports that failed and need user review."
        repos={failed}
        canManageRepo={canManageRepo}
        onCancelImport={onCancelImport}
        onDeleteRepo={onDeleteRepo}
        cancelingRepoId={cancelingRepoId}
        deletingRepoId={deletingRepoId}
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
