import { useMemo, useState } from "react"

import type { WorkspaceDetailViewModel, WorkspaceTerminalDescriptor } from "@/services/workspaceService"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

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
  const [copied, setCopied] = useState(false)

  const buttonLabel = useMemo(() => {
    if (isLoadingTerminal) return "Requesting terminal..."
    if (terminal) return "Refresh terminal endpoint"
    return "Request terminal endpoint"
  }, [isLoadingTerminal, terminal])

  const copyTerminalUrl = async () => {
    if (!terminal) return
    await navigator.clipboard.writeText(terminal.terminalUrl)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1500)
  }

  return (
    <Card className="min-h-[24rem]">
      <CardHeader>
        <CardTitle>Terminal</CardTitle>
        <CardDescription>
          This first pass treats terminal access as a connection scaffold. Once the workspace is ready, request the direct kennel websocket endpoint here.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-xl border bg-muted/30 p-4 text-sm">
          Workspace status: <span className="font-medium">{workspace.status}</span>
        </div>

        <Button
          onClick={() => void onRequestTerminal()}
          disabled={!workspace.canOpenTerminal || isLoadingTerminal}
        >
          {buttonLabel}
        </Button>

        {!workspace.canOpenTerminal ? (
          <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
            Terminal access becomes available once the workspace reaches `ready`.
          </div>
        ) : null}

        {terminalError ? (
          <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
            {terminalError.message}
          </div>
        ) : null}

        {terminal ? (
          <div className="space-y-3 rounded-xl border bg-card/60 p-4">
            <div className="text-sm font-medium">Direct websocket endpoint</div>
            <code className="block overflow-x-auto rounded-md bg-muted px-3 py-2 text-xs">
              {terminal.terminalUrl}
            </code>
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
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" onClick={() => void copyTerminalUrl()}>
                {copied ? "Copied" : "Copy endpoint"}
              </Button>
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
