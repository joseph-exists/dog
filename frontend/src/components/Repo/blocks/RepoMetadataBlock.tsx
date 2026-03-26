import type { UserRepoPublic } from "@/client/types.gen"
import { BlockContainer } from "@/components/Page/primitives/BlockContainer"
import { formatRepoDate } from "@/components/Repo/utils"
import { Badge } from "@/components/ui/badge"

export function RepoMetadataBlock({ repo }: { repo: UserRepoPublic }) {
  return (
    <BlockContainer
      title="Repository Metadata"
      subtitle="Platform-owned repository identity and managed forge mapping."
      metadata={
        <>
          <Badge variant="secondary">
            {repo.is_private ? "Private" : "Public"}
          </Badge>
          <Badge variant="outline">{repo.source_branch || "main"}</Badge>
        </>
      }
      density="compact"
      variant="card"
    >
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-1">
          <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
            Display Name
          </div>
          <div className="text-sm font-medium">{repo.display_name}</div>
        </div>
        <div className="space-y-1">
          <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
            Slug
          </div>
          <div className="font-mono text-sm">{repo.slug}</div>
        </div>
        <div className="space-y-1">
          <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
            Managed Repo Name
          </div>
          <div className="font-mono text-sm">{repo.gogs_repo_name}</div>
        </div>
        <div className="space-y-1">
          <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
            Managed Repo ID
          </div>
          <div className="font-mono text-sm">
            {repo.gogs_repo_id ?? "Not available"}
          </div>
        </div>
        <div className="space-y-1">
          <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
            Imported
          </div>
          <div className="text-sm">{formatRepoDate(repo.imported_at)}</div>
        </div>
        <div className="space-y-1">
          <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
            Owner User ID
          </div>
          <div className="truncate font-mono text-sm">{repo.owner_user_id}</div>
        </div>
      </div>
    </BlockContainer>
  )
}
