import { Badge } from "@/components/ui/badge"
import type { WorkspaceStatus } from "@/client"

const variantByStatus: Record<WorkspaceStatus, "default" | "secondary" | "destructive" | "outline"> = {
  requested: "secondary",
  provisioning: "secondary",
  starting: "secondary",
  ready: "default",
  stopping: "outline",
  stopped: "outline",
  failed: "destructive",
  destroying: "outline",
  destroyed: "destructive",
}

export function WorkspaceStatusBadge({ status }: { status: WorkspaceStatus }) {
  return <Badge variant={variantByStatus[status]}>{status}</Badge>
}
