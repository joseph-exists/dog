import { useEffect, useMemo, useRef } from "react"
import { ContentRenderer } from "@/components/Common/ContentRenderer"
import { cn } from "@/lib/utils"
import {
  toTerminalTranscriptContent,
  type TerminalConnectionStatus,
  type TerminalSessionState,
} from "@/services/terminalSessionService"

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
  const viewportRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!autoScroll || mode !== "live" || !viewportRef.current) return
    viewportRef.current.scrollTop = viewportRef.current.scrollHeight
  }, [session.plainText, autoScroll, mode])

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
      ref={viewportRef}
      className={cn(
        "h-full min-h-[20rem] overflow-auto bg-neutral-950 text-neutral-100",
        className,
      )}
    >
      <div
        className="min-h-[20rem]"
      >
        <pre className="min-h-[20rem] whitespace-pre-wrap break-words p-4 font-mono text-sm leading-6">
          {session.plainText || buildEmptyStateLabel(status, emptyLabel)}
        </pre>
      </div>
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
