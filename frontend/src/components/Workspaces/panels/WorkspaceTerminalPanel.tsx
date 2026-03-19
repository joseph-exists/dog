import type { WorkspaceDetailViewModel, WorkspaceTerminalDescriptor } from "@/services/workspaceService"
import { TerminalPanel } from "@/components/Terminal"

export interface WorkspaceTerminalPanelProps {
  workspace: WorkspaceDetailViewModel
  terminal: WorkspaceTerminalDescriptor | null
  isLoadingTerminal: boolean
  terminalError?: Error | null
  onRequestTerminal: () => Promise<unknown>
}

export function WorkspaceTerminalPanel({
  workspace,
  terminal,
  isLoadingTerminal,
  terminalError,
  onRequestTerminal,
}: WorkspaceTerminalPanelProps) {
  return (
    <TerminalPanel
      title="Terminal"
      terminalUrl={terminal?.terminalUrl ?? null}
      canRequestTerminal={workspace.canOpenTerminal}
      isRequestingTerminal={isLoadingTerminal}
      terminalError={terminalError}
      onRequestTerminal={onRequestTerminal}
      metadata={
        <div className="space-y-3">
          <div className="rounded-xl border bg-muted/30 p-4 text-sm">
            Workspace status: <span className="font-medium">{workspace.status}</span>
          </div>

          {!workspace.canOpenTerminal ? (
            <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
              Terminal access becomes available once the workspace reaches `ready`.
            </div>
          ) : null}

          {terminal ? (
            <div className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-3">
              <div>
                <div className="text-muted-foreground">Protocol</div>
                <div>{terminal.protocol}</div>
              </div>
              <div>
                <div className="text-muted-foreground">Host</div>
                <div>{terminal.host}</div>
              </div>
              <div>
                <div className="text-muted-foreground">Connection Model</div>
                <div>{terminal.isDirectConnection ? "direct" : "proxied"}</div>
              </div>
            </div>
          ) : null}
        </div>
      }
    />
  )
}
