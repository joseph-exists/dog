import { useNavigate } from "@tanstack/react-router"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import type { WorkspaceDetailViewModel } from "@/services/workspaceService"

export interface WorkspaceControlsPanelProps {
  workspace: WorkspaceDetailViewModel
  isStarting: boolean
  isStopping: boolean
  isDestroying: boolean
  onStart: () => Promise<void>
  onStop: () => Promise<void>
  onDestroy: () => Promise<void>
}

export function WorkspaceControlsPanel({
  workspace,
  isStarting,
  isStopping,
  isDestroying,
  onStart,
  onStop,
  onDestroy,
}: WorkspaceControlsPanelProps) {
  const navigate = useNavigate()

  const destroy = async () => {
    await onDestroy()
    navigate({ to: "/workspaces" })
  }

  const description = workspace.canManageRuntime
    ? "Use the current backend control surface to manage this environment."
    : "This workspace is visible in your current access scope, but runtime management remains unavailable from this account."

  return (
    <Card>
      <CardHeader>
        <CardTitle>Controls</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {!workspace.canManageRuntime ? (
          <div className="rounded-lg border bg-muted/20 p-3 text-sm text-muted-foreground">
            This workspace is visible in your current access scope, but runtime
            management is not available from this account.
          </div>
        ) : null}
        <Button
          variant="outline"
          className="w-full"
          disabled={!workspace.canStart || isStarting}
          onClick={() => void onStart()}
        >
          {isStarting ? "Starting..." : "Start Workspace"}
        </Button>
        <Button
          variant="outline"
          className="w-full"
          disabled={!workspace.canStop || isStopping}
          onClick={() => void onStop()}
        >
          {isStopping ? "Stopping..." : "Stop Workspace"}
        </Button>
        <Button
          variant="destructive"
          className="w-full"
          disabled={!workspace.canDestroy || isDestroying}
          onClick={() => void destroy()}
        >
          {isDestroying ? "Destroying..." : "Destroy Workspace"}
        </Button>
      </CardContent>
    </Card>
  )
}
