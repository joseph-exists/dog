import { RotateCcw, Trash2, Unplug, Wifi } from "lucide-react"
import { Button } from "@/components/ui/button"

export interface TerminalToolbarProps {
  canConnect: boolean
  isConnected: boolean
  onConnect: () => void
  onDisconnect: () => void
  onClear: () => void
}

export function TerminalToolbar({
  canConnect,
  isConnected,
  onConnect,
  onDisconnect,
  onClear,
}: TerminalToolbarProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {isConnected ? (
        <Button variant="outline" size="sm" onClick={onDisconnect}>
          <Unplug className="mr-2 h-4 w-4" />
          Disconnect
        </Button>
      ) : (
        <Button variant="outline" size="sm" disabled={!canConnect} onClick={onConnect}>
          <Wifi className="mr-2 h-4 w-4" />
          Connect
        </Button>
      )}
      <Button variant="ghost" size="sm" onClick={onConnect} disabled={!canConnect}>
        <RotateCcw className="mr-2 h-4 w-4" />
        Reconnect
      </Button>
      <Button variant="ghost" size="sm" onClick={onClear}>
        <Trash2 className="mr-2 h-4 w-4" />
        Clear
      </Button>
    </div>
  )
}
