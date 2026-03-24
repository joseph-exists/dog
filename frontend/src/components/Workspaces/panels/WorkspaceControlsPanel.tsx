import { useNavigate } from "@tanstack/react-router"

import type { WorkspaceDetailViewModel } from "@/services/workspaceService"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

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

  return (
    <Card>
      <CardHeader>
        <CardTitle>Controls</CardTitle>
        <CardDescription>
          Use the current backend control surface to manage this environment.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
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
