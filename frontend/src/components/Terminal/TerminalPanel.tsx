import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { PanelContainer } from "@/components/Page/primitives"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useTerminalSession } from "@/hooks/useTerminalSession"
import { cn } from "@/lib/utils"
import { TerminalStatusBar } from "./TerminalStatusBar"
import { TerminalToolbar } from "./TerminalToolbar"
import {
  DEFAULT_TERMINAL_VIEWER_PREFERENCES,
  TerminalViewer,
  type TerminalViewerPreferences,
  type TerminalViewerThemePreset,
  type TerminalViewerWrapMode,
} from "./TerminalViewer"

type TerminalAdjacentTab = {
  id: string
  label: string
  content: React.ReactNode
}

export interface TerminalPanelProps {
  title?: string
  terminalUrl?: string | null
  canRequestTerminal?: boolean
  isRequestingTerminal?: boolean
  terminalError?: Error | null
  onRequestTerminal?: () => Promise<unknown> | unknown
  metadata?: React.ReactNode
  adjacentTabs?: TerminalAdjacentTab[]
  viewerPreferences?: Partial<TerminalViewerPreferences>
  endpointState?:
    | "idle"
    | "loading"
    | "available"
    | "expired"
    | "unavailable"
    | "not_allowed"
    | "error"
  endpointStateMessage?: string | null
  endpointFetchedAt?: Date | null
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
  adjacentTabs = [],
  viewerPreferences,
  endpointState = "idle",
  endpointStateMessage,
  endpointFetchedAt,
  className,
}: TerminalPanelProps) {
  const perfIdRef = useRef<string>(
    `terminal-panel-${Math.random().toString(36).slice(2, 10)}`,
  )
  const [activeTab, setActiveTab] = useState<string>("live")
  const [draftInput, setDraftInput] = useState("")
  const [fontSize, setFontSize] = useState(
    viewerPreferences?.fontSize ?? DEFAULT_TERMINAL_VIEWER_PREFERENCES.fontSize,
  )
  const [wrapMode, setWrapMode] = useState<TerminalViewerWrapMode>(
    viewerPreferences?.wrapMode ?? DEFAULT_TERMINAL_VIEWER_PREFERENCES.wrapMode,
  )
  const [autoScroll, setAutoScroll] = useState(
    viewerPreferences?.autoScroll ??
      DEFAULT_TERMINAL_VIEWER_PREFERENCES.autoScroll,
  )
  const [themePreset, setThemePreset] = useState<TerminalViewerThemePreset>(
    viewerPreferences?.themePreset ??
      DEFAULT_TERMINAL_VIEWER_PREFERENCES.themePreset,
  )

  const {
    session,
    status,
    error,
    connect,
    reconnect,
    disconnect,
    clear,
    sendInput,
    sendResize,
    setViewport,
    capabilities,
    debugSessionId,
  } = useTerminalSession({
    url: terminalUrl ?? null,
    enabled: Boolean(terminalUrl),
  })
  const isLiveTab = activeTab === "live"
  const directInputActive =
    isLiveTab &&
    status === "open" &&
    capabilities.directInput &&
    capabilities.sendInput
  const canPaste = directInputActive && capabilities.paste
  const canCopy = session.plainText.trim().length > 0
  const resolvedViewerPreferences: TerminalViewerPreferences = {
    ...DEFAULT_TERMINAL_VIEWER_PREFERENCES,
    ...viewerPreferences,
    fontSize,
    wrapMode,
    autoScroll,
    themePreset,
  }

  const requestLabel = useMemo(() => {
    if (isRequestingTerminal) return "Requesting terminal..."
    if (terminalUrl) return "Request fresh endpoint"
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

  const pasteFromClipboard = async () => {
    if (!capabilities.paste || status !== "open") return
    try {
      const text = await navigator.clipboard.readText()
      if (text) {
        sendInput(text)
      }
    } catch {
      // Browser clipboard access is best-effort; the terminal still supports native paste events.
    }
  }

  const copyVisibleBuffer = async () => {
    if (!session.plainText) return
    try {
      await navigator.clipboard.writeText(session.plainText)
    } catch {
      // Clipboard write is best-effort.
    }
  }

  const endpointBanner =
    endpointStateMessage &&
    (endpointState === "expired" ||
      endpointState === "unavailable" ||
      endpointState === "not_allowed" ||
      endpointState === "error")
      ? endpointStateMessage
      : null
  const socketBanner =
    status === "error"
      ? "Socket transport failed. Reconnect the websocket or request a fresh endpoint."
      : status === "closed" && terminalUrl
        ? "Socket transport closed. Reconnect the websocket to continue."
        : null
  const handleViewportChange = useCallback(
    (cols: number, rows: number) => {
      setViewport(cols, rows)
      if (capabilities.sendResize) {
        sendResize(cols, rows)
      }
    },
    [capabilities.sendResize, sendResize, setViewport],
  )

  useEffect(() => {
    performanceMark(`${perfIdRef.current}:mount`)
    performanceLog({
      scope: "terminal_panel",
      phase: "mount",
      perfId: perfIdRef.current,
      hasTerminalUrl: Boolean(terminalUrl),
      debugSessionId,
    })
  }, [debugSessionId, terminalUrl])

  useEffect(() => {
    performanceLog({
      scope: "terminal_panel",
      phase: "tab_change",
      perfId: perfIdRef.current,
      activeTab,
      debugSessionId,
    })
  }, [activeTab, debugSessionId])

  const headerActions = (
    <div className="flex flex-wrap items-center gap-2">
      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value)}>
        <TabsList
          className="grid w-auto"
          style={{
            gridTemplateColumns: `repeat(${2 + adjacentTabs.length}, minmax(0, 1fr))`,
          }}
        >
          <TabsTrigger value="live">Live</TabsTrigger>
          <TabsTrigger value="transcript">Transcript</TabsTrigger>
          {adjacentTabs.map((tab) => (
            <TabsTrigger key={tab.id} value={tab.id}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>
      <TerminalToolbar
        canConnect={capabilities.connect}
        canReconnect={capabilities.reconnect}
        canClear={capabilities.clearBuffer}
        canPaste={canPaste}
        canCopy={canCopy}
        isConnected={status === "open"}
        onConnect={() => connect()}
        onReconnect={() => reconnect()}
        onDisconnect={() => disconnect()}
        onClear={() => clear()}
        onPaste={pasteFromClipboard}
        onCopy={copyVisibleBuffer}
      />
      <div className="flex items-center gap-1 rounded-md border border-border/60 p-1">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setFontSize((value) => Math.max(10, value - 1))}
          title="Decrease font size"
        >
          A-
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setFontSize((value) => Math.min(20, value + 1))}
          title="Increase font size"
        >
          A+
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() =>
            setWrapMode((value) => (value === "wrap" ? "nowrap" : "wrap"))
          }
        >
          {wrapMode === "wrap" ? "Wrap on" : "Wrap off"}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setAutoScroll((value) => !value)}
        >
          {autoScroll ? "Auto-scroll on" : "Auto-scroll off"}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() =>
            setThemePreset((value) =>
              value === "graphite"
                ? "midnight"
                : value === "midnight"
                  ? "amber"
                  : "graphite",
            )
          }
        >
          Theme: {themePreset}
        </Button>
      </div>
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
        resolvedViewerPreferences.statusBarVisible ? (
          <div className="border-t border-border/70">
            <TerminalStatusBar
              session={session}
              status={status}
              capabilities={capabilities}
              endpointLabel={
                endpointFetchedAt
                  ? `Endpoint refreshed ${endpointFetchedAt.toLocaleTimeString()}`
                  : "Endpoint state unknown"
              }
            />
          </div>
        ) : undefined
      }
    >
      <div className="flex h-full min-h-[28rem] flex-col">
        {metadata && adjacentTabs.length === 0 ? (
          <div className="border-b border-border/70 px-4 py-3 text-sm">
            {metadata}
          </div>
        ) : null}

        {endpointBanner ? (
          <div className="border-b border-amber-500/30 bg-amber-500/5 px-4 py-3 text-sm text-amber-700">
            {endpointBanner}
          </div>
        ) : null}

        {terminalError || error ? (
          <div className="border-b border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
            {(terminalError ?? error)?.message}
          </div>
        ) : null}
        {socketBanner ? (
          <div className="border-b border-border/70 bg-muted/20 px-4 py-3 text-sm text-muted-foreground">
            {socketBanner}
          </div>
        ) : null}

        <div className="min-h-0 flex-1">
          {activeTab === "transcript" ? (
            <TerminalViewer
              session={session}
              status={status}
              mode="transcript"
            />
          ) : activeTab === "live" ? (
            <TerminalViewer
              session={session}
              status={status}
              capabilities={capabilities}
              mode="live"
              preferences={resolvedViewerPreferences}
              onSendInput={sendInput}
              onPasteInput={async (value) => sendInput(value)}
              onCopyVisibleBuffer={copyVisibleBuffer}
              onViewportChange={handleViewportChange}
              debugSessionId={debugSessionId}
            />
          ) : (
            <div className="h-full overflow-y-auto p-4">
              {adjacentTabs.find((tab) => tab.id === activeTab)?.content ??
                null}
            </div>
          )}
        </div>

        {isLiveTab && capabilities.sendInput && !capabilities.directInput ? (
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
        ) : null}

        {directInputActive ? (
          <div className="border-t border-border/70 px-3 py-2 text-xs text-muted-foreground">
            Live terminal supports direct shell input. Reconnect recovers the
            websocket transport, while Request fresh endpoint asks for a new
            terminal descriptor. Runtime diagnostics are available in the
            Runtime tab.
          </div>
        ) : null}
      </div>
    </PanelContainer>
  )
}

type PerfLogPayload = {
  scope: "terminal_panel" | "terminal_viewer"
  phase: string
  perfId: string
  [key: string]: unknown
}

function performanceMark(name: string) {
  if (typeof window === "undefined" || typeof performance === "undefined")
    return
  performance.mark(name)
}

function performanceLog(payload: PerfLogPayload) {
  if (typeof window === "undefined") return
  const target = window as typeof window & {
    __terminalPerfLog?: PerfLogPayload[]
  }
  if (!Array.isArray(target.__terminalPerfLog)) {
    target.__terminalPerfLog = []
  }
  target.__terminalPerfLog.push({
    ...payload,
    at: Date.now(),
  })
}
