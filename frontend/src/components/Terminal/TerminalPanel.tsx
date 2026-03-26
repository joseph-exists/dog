import { useMemo, useState } from "react"
import { PanelContainer } from "@/components/Page/primitives"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useTerminalSession } from "@/hooks/useTerminalSession"
import { cn } from "@/lib/utils"
import { TerminalStatusBar } from "./TerminalStatusBar"
import { TerminalToolbar } from "./TerminalToolbar"
import { TerminalViewer } from "./TerminalViewer"

export interface TerminalPanelProps {
  title?: string
  terminalUrl?: string | null
  canRequestTerminal?: boolean
  isRequestingTerminal?: boolean
  terminalError?: Error | null
  onRequestTerminal?: () => Promise<unknown> | unknown
  metadata?: React.ReactNode
  className?: string
}

export function TerminalPanel({
  title = "Terminal",
  terminalUrl,
  canRequestTerminal = true,
  isRequestingTerminal = false,
  terminalError,
  onRequestTerminal,
  metadata,
  className,
}: TerminalPanelProps) {
  const [mode, setMode] = useState<"live" | "transcript">("live")
  const [draftInput, setDraftInput] = useState("")

  const { session, status, error, connect, disconnect, clear, sendInput } =
    useTerminalSession({
      url: terminalUrl ?? null,
      enabled: Boolean(terminalUrl),
    })

  const requestLabel = useMemo(() => {
    if (isRequestingTerminal) return "Requesting terminal..."
    if (terminalUrl) return "Refresh endpoint"
    return "Request terminal"
  }, [isRequestingTerminal, terminalUrl])

  const submitInput = () => {
    if (!draftInput.trim()) return
    const payload = draftInput.endsWith("\n") ? draftInput : `${draftInput}\n`
    const sent = sendInput(payload)
    if (sent) {
      setDraftInput("")
    }
  }

  const headerActions = (
    <div className="flex flex-wrap items-center gap-2">
      <Tabs
        value={mode}
        onValueChange={(value) => setMode(value as "live" | "transcript")}
      >
        <TabsList className="grid w-[11rem] grid-cols-2">
          <TabsTrigger value="live">Live</TabsTrigger>
          <TabsTrigger value="transcript">Transcript</TabsTrigger>
        </TabsList>
      </Tabs>
      <TerminalToolbar
        canConnect={Boolean(terminalUrl)}
        isConnected={status === "open"}
        onConnect={() => connect()}
        onDisconnect={() => disconnect()}
        onClear={() => clear()}
      />
      {onRequestTerminal ? (
        <Button
          variant="outline"
          size="sm"
          onClick={() => void onRequestTerminal()}
          disabled={!canRequestTerminal || isRequestingTerminal}
        >
          {requestLabel}
        </Button>
      ) : null}
    </div>
  )

  return (
    <PanelContainer
      title={title}
      className={cn("h-full rounded-xl border bg-card", className)}
      headerActions={headerActions}
      scrollable={false}
      footer={
        <div className="border-t border-border/70">
          <TerminalStatusBar session={session} status={status} />
        </div>
      }
    >
      <div className="flex h-full min-h-[28rem] flex-col">
        {metadata ? (
          <div className="border-b border-border/70 px-4 py-3 text-sm">
            {metadata}
          </div>
        ) : null}

        {terminalError || error ? (
          <div className="border-b border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
            {(terminalError ?? error)?.message}
          </div>
        ) : null}

        <div className="min-h-0 flex-1">
          <TerminalViewer session={session} status={status} mode={mode} />
        </div>

        <div className="border-t border-border/70 p-3">
          <div className="flex flex-col gap-2 md:flex-row">
            <Input
              value={draftInput}
              onChange={(event) => setDraftInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault()
                  submitInput()
                }
              }}
              placeholder="Send a line of terminal input"
              disabled={status !== "open"}
            />
            <Button
              onClick={submitInput}
              disabled={status !== "open" || !draftInput.trim()}
            >
              Send
            </Button>
          </div>
        </div>
      </div>
    </PanelContainer>
  )
}
