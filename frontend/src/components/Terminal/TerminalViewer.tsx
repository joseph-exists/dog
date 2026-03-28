import { Terminal } from "@xterm/xterm"
import { useEffect, useMemo, useRef } from "react"
import { ContentRenderer } from "@/components/Common/ContentRenderer"
import { cn } from "@/lib/utils"
import {
  type TerminalConnectionStatus,
  type TerminalSessionState,
  toTerminalTranscriptContent,
} from "@/services/terminalSessionService"
import "@xterm/xterm/css/xterm.css"

export interface TerminalViewerProps {
  session: TerminalSessionState
  status: TerminalConnectionStatus
  mode?: "live" | "transcript"
  autoScroll?: boolean
  className?: string
  emptyLabel?: string
}

export function TerminalViewer({
  session,
  status,
  mode = "live",
  autoScroll = true,
  className,
  emptyLabel = "Terminal output will appear here once the session is active.",
}: TerminalViewerProps) {
  const terminalHostRef = useRef<HTMLDivElement | null>(null)
  const terminalRef = useRef<Terminal | null>(null)
  const renderedChunksRef = useRef(0)
  const sessionIdRef = useRef<string | null>(null)

  useEffect(() => {
    if (mode !== "live" || !terminalHostRef.current || terminalRef.current) {
      return
    }

    const terminal = new Terminal({
      convertEol: true,
      cursorBlink: false,
      disableStdin: true,
      fontFamily:
        'ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, "Liberation Mono", monospace',
      fontSize: 13,
      lineHeight: 1.4,
      scrollback: 2000,
      theme: {
        background: "#0a0a0a",
        foreground: "#f5f5f5",
        cursor: "#f5f5f5",
      },
    })

    terminal.open(terminalHostRef.current)
    terminalRef.current = terminal

    return () => {
      terminal.dispose()
      terminalRef.current = null
      renderedChunksRef.current = 0
      sessionIdRef.current = null
    }
  }, [mode])

  useEffect(() => {
    if (mode !== "live") return

    const terminal = terminalRef.current
    if (!terminal) return

    const isNewSession = sessionIdRef.current !== session.id

    if (isNewSession) {
      terminal.reset()
      renderedChunksRef.current = 0
      sessionIdRef.current = session.id
    }

    if (session.ansiChunks.length < renderedChunksRef.current) {
      terminal.reset()
      renderedChunksRef.current = 0
    }

    const nextChunks = session.ansiChunks.slice(renderedChunksRef.current)
    for (const chunk of nextChunks) {
      terminal.write(chunk)
    }
    renderedChunksRef.current = session.ansiChunks.length

    if (autoScroll) {
      terminal.scrollToBottom()
    }
  }, [autoScroll, mode, session.ansiChunks, session.id])

  const transcriptContent = useMemo(
    () => toTerminalTranscriptContent(session),
    [session],
  )

  if (mode === "transcript") {
    return (
      <div className={cn("h-full min-h-[20rem]", className)}>
        <ContentRenderer content={transcriptContent} variant="card" safeMode />
      </div>
    )
  }

  return (
    <div
      className={cn(
        "relative h-full min-h-[20rem] overflow-hidden bg-neutral-950 text-neutral-100",
        className,
      )}
    >
      <div ref={terminalHostRef} className="h-full min-h-[20rem] p-4" />
      {session.ansiChunks.length === 0 ? (
        <div className="pointer-events-none absolute inset-0 flex items-start p-4">
          <pre className="whitespace-pre-wrap break-words font-mono text-sm leading-6 text-neutral-400">
            {buildEmptyStateLabel(status, emptyLabel)}
          </pre>
        </div>
      ) : null}
    </div>
  )
}

function buildEmptyStateLabel(
  status: TerminalConnectionStatus,
  emptyLabel: string,
) {
  if (status === "connecting") {
    return "Connecting to terminal session..."
  }
  return emptyLabel
}
