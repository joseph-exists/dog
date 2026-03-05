import type { UserRepoPublic } from "@/client/types.gen"
import { BlockContainer } from "@/components/Page/primitives/BlockContainer"
import { Badge } from "@/components/ui/badge"

export function RepoImportRecordBlock({ repo }: { repo: UserRepoPublic }) {
  return (
    <BlockContainer
      title="Import Record"
      subtitle="Original import request metadata retained for audit and user reference, not active synchronization."
      metadata={<Badge variant="outline">Severed from upstream after intake</Badge>}
      density="compact"
      variant="card"
    >
      <div className="space-y-4">
        <div className="space-y-1">
          <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
            Original Source URL
          </div>
          <div className="rounded-xl border bg-muted/30 p-3 font-mono text-xs break-all">
            {repo.source_repo_url || "Not recorded"}
          </div>
        </div>
        <div className="space-y-1">
          <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
            Managed Full Name
          </div>
          <div className="rounded-xl border bg-muted/30 p-3 font-mono text-xs">
            {repo.gogs_full_name || "Not available"}
          </div>
        </div>
      </div>
    </BlockContainer>
  )
}
