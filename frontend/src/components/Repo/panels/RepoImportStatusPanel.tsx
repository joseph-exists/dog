import type { UserRepoPublic } from "@/client/types.gen"
import { PanelContainer } from "@/components/Page/primitives"
import {
  RepoFailureDiagnosticsBlock,
  RepoImportRecordBlock,
  RepoImportSummaryBlock,
} from "@/components/Repo/blocks"

export function RepoImportStatusPanel({ repo }: { repo: UserRepoPublic }) {
  return (
    <PanelContainer title="Import Status" scrollable>
      <div className="space-y-4 p-4">
        <RepoImportSummaryBlock repo={repo} />
        <RepoFailureDiagnosticsBlock repo={repo} />
        <RepoImportRecordBlock repo={repo} />
      </div>
    </PanelContainer>
  )
}
