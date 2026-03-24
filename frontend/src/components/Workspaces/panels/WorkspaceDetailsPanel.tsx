import type { WorkspaceDetailViewModel } from "@/services/workspaceService"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { WorkspaceStatusBadge } from "./WorkspaceStatusBadge"

export function WorkspaceDetailsPanel({ workspace }: { workspace: WorkspaceDetailViewModel }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Workspace Details</CardTitle>
        <CardDescription>
          Current lifecycle state, project visibility, and backend-facing operational context.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{workspace.name}</span>
          <WorkspaceStatusBadge status={workspace.status} />
        </div>
        {workspace.failureMessage ? (
          <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
            {workspace.failureMessage}
          </div>
        ) : null}
        <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-muted-foreground">Visibility</dt>
            <dd>{workspace.visibility}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Project</dt>
            <dd>{workspace.projectSummary?.name ?? "Not assigned"}</dd>
          </div>
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
          <div>
            <dt className="text-muted-foreground">Last Transition</dt>
            <dd>{workspace.lastTransitionAt?.toLocaleString() ?? "Not recorded"}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Terminal Status</dt>
            <dd>{workspace.terminalStatus}</dd>
          </div>
        </dl>
        <div className="space-y-2">
          <div className="text-sm font-medium">Current Action Surface</div>
          <div className="flex flex-wrap gap-2">
            {workspace.allowedActions.length > 0 ? (
              workspace.allowedActions.map((action) => (
                <span
                  key={action}
                  className="rounded-full border bg-muted/40 px-2.5 py-1 text-xs text-muted-foreground"
                >
                  {action}
                </span>
              ))
            ) : (
              <span className="text-sm text-muted-foreground">No actions currently available.</span>
            )}
          </div>
        </div>
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
