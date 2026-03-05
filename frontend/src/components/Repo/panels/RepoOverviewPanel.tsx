import type { UserRepoPublic } from "@/client/types.gen"
import { PanelContainer } from "@/components/Page/primitives"
import {
  RepoImportRecordBlock,
  RepoImportSummaryBlock,
  RepoMetadataBlock,
} from "@/components/Repo/blocks"

export function RepoOverviewPanel({ repo }: { repo: UserRepoPublic }) {
  return (
    <PanelContainer title="Overview" scrollable>
      <div className="grid gap-4 p-4 xl:grid-cols-2">
        <RepoMetadataBlock repo={repo} />
        <RepoImportSummaryBlock repo={repo} />
        <div className="xl:col-span-2">
          <RepoImportRecordBlock repo={repo} />
        </div>
      </div>
    </PanelContainer>
  )
}
