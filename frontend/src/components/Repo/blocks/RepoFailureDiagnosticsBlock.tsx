import { ShieldAlertIcon } from "lucide-react"
import type { UserRepoPublic } from "@/client/types.gen"
import { BlockContainer } from "@/components/Page/primitives/BlockContainer"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

export function RepoFailureDiagnosticsBlock({
  repo,
}: {
  repo: UserRepoPublic
}) {
  const hasFailure = repo.import_status === "failed"

  return (
    <BlockContainer
      title="Failure Diagnostics"
      subtitle="Permanent import failures stay inspectable on the platform record."
      density="compact"
      variant="card"
      isEmpty={!hasFailure}
      emptyState={
        <div className="py-6 text-sm text-muted-foreground">
          No failure diagnostics are present for this repository.
        </div>
      }
    >
      <Alert variant="destructive">
        <ShieldAlertIcon className="h-4 w-4" />
        <AlertTitle>Import failure</AlertTitle>
        <AlertDescription>
          {repo.import_error ||
            "The platform reported a permanent import failure."}
        </AlertDescription>
      </Alert>
    </BlockContainer>
  )
}
