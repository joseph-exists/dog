import { Link } from "@tanstack/react-router"
import { ArrowUpRight, TerminalSquare } from "lucide-react"

import type { WorkspaceListItemViewModel } from "@/services/workspaceService"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { WorkspaceStatusBadge } from "./WorkspaceStatusBadge"

export interface WorkspaceListPanelProps {
  workspaces: WorkspaceListItemViewModel[]
  isLoading: boolean
  error?: Error | null
}

export function WorkspaceListPanel({
  workspaces,
  isLoading,
  error,
}: WorkspaceListPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Workspace Fleet</CardTitle>
        <CardDescription>
          Track provisioning, open ready environments, and keep an eye on lifecycle state.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-20 w-full rounded-xl" />
            <Skeleton className="h-20 w-full rounded-xl" />
            <Skeleton className="h-20 w-full rounded-xl" />
          </div>
        ) : null}

        {error ? (
          <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
            {error.message}
          </div>
        ) : null}

        {!isLoading && !error && workspaces.length === 0 ? (
          <div className="rounded-xl border border-dashed p-8 text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full border bg-card">
              <TerminalSquare className="h-5 w-5 text-muted-foreground" />
            </div>
            <h3 className="text-sm font-medium">No workspaces yet</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Provision a workspace to start validating the kennel integration flow.
            </p>
          </div>
        ) : null}

        {!isLoading && !error && workspaces.length > 0 ? (
          <div className="space-y-3">
            {workspaces.map((workspace) => (
              <div
                key={workspace.id}
                className="flex flex-col gap-3 rounded-xl border bg-card/60 p-4 md:flex-row md:items-center md:justify-between"
              >
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <div className="font-medium">{workspace.name}</div>
                    <WorkspaceStatusBadge status={workspace.status} />
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {workspace.flavour} · {workspace.kind} · updated{" "}
                    {workspace.updatedAt.toLocaleString()}
                  </div>
                </div>
                <Button asChild variant="outline" size="sm" className="w-fit">
                  <Link
                    to="/workspace/$workspaceId"
                    params={{ workspaceId: workspace.id }}
                  >
                    Open
                    <ArrowUpRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
              </div>
            ))}
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
