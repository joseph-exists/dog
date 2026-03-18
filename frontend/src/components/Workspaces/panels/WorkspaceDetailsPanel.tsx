import type { WorkspaceDetailViewModel } from "@/services/workspaceService"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { WorkspaceStatusBadge } from "./WorkspaceStatusBadge"

export function WorkspaceDetailsPanel({ workspace }: { workspace: WorkspaceDetailViewModel }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Workspace Details</CardTitle>
        <CardDescription>
          Current provisioning state and the backend-facing metadata we have available so far.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{workspace.name}</span>
          <WorkspaceStatusBadge status={workspace.status} />
        </div>
        <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-muted-foreground">Flavour</dt>
            <dd>{workspace.flavour}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Kind</dt>
            <dd>{workspace.kind}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Kennel Name</dt>
            <dd>{workspace.kennelName ?? "Not assigned"}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Kennel Job</dt>
            <dd>{workspace.kennelJob ?? "Not assigned"}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Created</dt>
            <dd>{workspace.createdAt.toLocaleString()}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Updated</dt>
            <dd>{workspace.updatedAt.toLocaleString()}</dd>
          </div>
        </dl>
        {Object.keys(workspace.meta).length > 0 ? (
          <div className="space-y-2">
            <div className="text-sm font-medium">Metadata</div>
            <pre className="overflow-x-auto rounded-lg border bg-muted/40 p-3 text-xs">
              {JSON.stringify(workspace.meta, null, 2)}
            </pre>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
