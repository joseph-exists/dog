import type { UserRepoPublic } from "@/client/types.gen"
import { BlockContainer } from "@/components/Page/primitives/BlockContainer"
import { RepoStatusBadge } from "@/components/Repo/Display/RepoStatusBadge"
import { formatRepoDate } from "@/components/Repo/utils"

export function RepoImportSummaryBlock({ repo }: { repo: UserRepoPublic }) {
  return (
    <BlockContainer
      title="Import Summary"
      subtitle="One-time import into the platform workspace. Upstream is treated as disconnected after intake."
      headerActions={<RepoStatusBadge repo={repo} />}
      density="compact"
      variant="card"
    >
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-1">
          <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
            Status
          </div>
          <div className="text-sm font-medium capitalize">
            {repo.import_status ?? "pending"}
          </div>
        </div>
        <div className="space-y-1">
          <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
            Branch Intent
          </div>
          <div className="text-sm">{repo.source_branch || "main"}</div>
        </div>
        <div className="space-y-1">
          <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
            Created
          </div>
          <div className="text-sm">{formatRepoDate(repo.created_at)}</div>
        </div>
        <div className="space-y-1">
          <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
            Updated
          </div>
          <div className="text-sm">{formatRepoDate(repo.updated_at)}</div>
        </div>
      </div>
    </BlockContainer>
  )
}
