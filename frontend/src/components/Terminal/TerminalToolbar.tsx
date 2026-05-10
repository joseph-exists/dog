import {
  ClipboardCopy,
  ClipboardPaste,
  RotateCcw,
  Trash2,
  Unplug,
  Wifi,
} from "lucide-react"
import { Button } from "@/components/ui/button"

export interface TerminalToolbarProps {
  canConnect: boolean
  canReconnect: boolean
  canClear: boolean
  canPaste: boolean
  canCopy: boolean
  isConnected: boolean
  onConnect: () => void
  onReconnect: () => void
  onDisconnect: () => void
  onClear: () => void
  onPaste?: () => void
  onCopy?: () => void
  connectLabel?: string
  reconnectLabel?: string
  disconnectLabel?: string
}

export function TerminalToolbar({
  canConnect,
  canReconnect,
  canClear,
  canPaste,
  canCopy,
  isConnected,
  onConnect,
  onReconnect,
  onDisconnect,
  onClear,
  onPaste,
  onCopy,
  connectLabel = "Connect",
  reconnectLabel = "Reconnect socket",
  disconnectLabel = "Disconnect",
}: TerminalToolbarProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {isConnected ? (
        <Button variant="outline" size="sm" onClick={onDisconnect}>
          <Unplug className="mr-2 h-4 w-4" />
          {disconnectLabel}
        </Button>
      ) : (
        <Button
          variant="outline"
          size="sm"
          disabled={!canConnect}
          onClick={onConnect}
        >
          <Wifi className="mr-2 h-4 w-4" />
          {connectLabel}
        </Button>
      )}
      <Button
        variant="ghost"
        size="sm"
        onClick={onReconnect}
        disabled={!canReconnect}
      >
        <RotateCcw className="mr-2 h-4 w-4" />
        {reconnectLabel}
      </Button>
      <Button variant="ghost" size="sm" onClick={onClear} disabled={!canClear}>
        <Trash2 className="mr-2 h-4 w-4" />
        Clear
      </Button>
      {onPaste ? (
        <Button
          variant="ghost"
          size="sm"
          onClick={onPaste}
          disabled={!canPaste}
        >
          <ClipboardPaste className="mr-2 h-4 w-4" />
          Paste
        </Button>
      ) : null}
      {onCopy ? (
        <Button variant="ghost" size="sm" onClick={onCopy} disabled={!canCopy}>
          <ClipboardCopy className="mr-2 h-4 w-4" />
          Copy buffer
        </Button>
      ) : null}
    </div>
  )
}
