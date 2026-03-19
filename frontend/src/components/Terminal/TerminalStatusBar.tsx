import { Badge } from "@/components/ui/badge"
import type {
  TerminalConnectionStatus,
  TerminalSessionState,
} from "@/services/terminalSessionService"

export interface TerminalStatusBarProps {
  session: TerminalSessionState
  status: TerminalConnectionStatus
  transportLabel?: string
}

function getStatusLabel(status: TerminalConnectionStatus) {
  switch (status) {
    case "idle":
      return "Idle"
    case "connecting":
      return "Connecting"
    case "open":
      return "Live"
    case "closed":
      return "Closed"
    case "error":
      return "Error"
  }
}

function getStatusVariant(status: TerminalConnectionStatus): "default" | "secondary" | "destructive" | "outline" {
  switch (status) {
    case "open":
      return "default"
    case "error":
      return "destructive"
    case "connecting":
      return "secondary"
    case "closed":
      return "outline"
    case "idle":
      return "outline"
  }
}

export function TerminalStatusBar({
  session,
  status,
  transportLabel = "Direct websocket",
}: TerminalStatusBarProps) {
  return (
    <div className="flex flex-wrap items-center gap-2 border-t border-border/70 px-3 py-2 text-xs text-muted-foreground">
      <Badge variant={getStatusVariant(status)}>{getStatusLabel(status)}</Badge>
      <span>{transportLabel}</span>
      <span>{session.frames.length} frames</span>
      {session.lastFrameAt ? (
        <span>Last activity {session.lastFrameAt.toLocaleTimeString()}</span>
      ) : null}
      {session.viewport.cols && session.viewport.rows ? (
        <span>
          {session.viewport.cols} x {session.viewport.rows}
        </span>
      ) : null}
    </div>
  )
}
