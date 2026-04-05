import type { TerminalCapabilities } from "@/hooks/useTerminalSession"
import { Badge } from "@/components/ui/badge"
import type {
  TerminalConnectionStatus,
  TerminalSessionState,
} from "@/services/terminalSessionService"

export interface TerminalStatusBarProps {
  session: TerminalSessionState
  status: TerminalConnectionStatus
  capabilities?: Pick<
    TerminalCapabilities,
    "directInput" | "sendInput" | "sendResize" | "inputMode" | "reconnect"
  >
  transportLabel?: string
  endpointLabel?: string
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

function getStatusVariant(
  status: TerminalConnectionStatus,
): "default" | "secondary" | "destructive" | "outline" {
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
  capabilities,
  transportLabel = "Direct websocket",
  endpointLabel = "Current endpoint",
}: TerminalStatusBarProps) {
  const inputLabel = getInputLabel(capabilities)
  const resizeLabel = capabilities?.sendResize
    ? "Remote resize"
    : session.viewport.cols && session.viewport.rows
      ? "Local resize only"
      : "Resize unavailable"

  return (
    <div className="flex flex-wrap items-center gap-2 border-t border-border/70 px-3 py-2 text-xs text-muted-foreground">
      <Badge variant={getStatusVariant(status)}>{getStatusLabel(status)}</Badge>
      <span>{transportLabel}</span>
      <span>{endpointLabel}</span>
      <span>{inputLabel}</span>
      <span>{resizeLabel}</span>
      <span>{capabilities?.reconnect ? "Socket reconnect ready" : "Reconnect unavailable"}</span>
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

function getInputLabel(
  capabilities: TerminalStatusBarProps["capabilities"],
): string {
  if (!capabilities?.sendInput) return "Input unavailable"
  if (capabilities.inputMode === "direct" && capabilities.directInput) {
    return "Direct shell input"
  }
  if (capabilities.inputMode === "line") {
    return "Line input"
  }
  return "Input available"
}
