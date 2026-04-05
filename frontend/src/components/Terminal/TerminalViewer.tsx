import { Terminal } from "@xterm/xterm"
import { useEffect, useMemo, useRef, useState } from "react"
import { ContentRenderer } from "@/components/Common/ContentRenderer"
import type {
  TerminalCapabilities,
  TerminalInputMode,
} from "@/hooks/useTerminalSession"
import { cn } from "@/lib/utils"
import {
  type TerminalConnectionStatus,
  type TerminalSessionState,
  toTerminalTranscriptContent,
} from "@/services/terminalSessionService"
import "@xterm/xterm/css/xterm.css"

export type TerminalViewerThemePreset = "graphite" | "midnight" | "amber"
export type TerminalViewerWrapMode = "wrap" | "nowrap"

export interface TerminalViewerPreferences {
  fontSize: number
  lineHeight: number
  wrapMode: TerminalViewerWrapMode
  autoScroll: boolean
  scrollback: number
  themePreset: TerminalViewerThemePreset
  statusBarVisible: boolean
}

export const DEFAULT_TERMINAL_VIEWER_PREFERENCES: TerminalViewerPreferences = {
  fontSize: 13,
  lineHeight: 1.4,
  wrapMode: "wrap",
  autoScroll: true,
  scrollback: 2_000,
  themePreset: "graphite",
  statusBarVisible: true,
}

export interface TerminalViewerProps {
  session: TerminalSessionState
  status: TerminalConnectionStatus
  capabilities?: Pick<
    TerminalCapabilities,
    "directInput" | "sendInput" | "paste" | "sendResize" | "inputMode"
  >
  mode?: "live" | "transcript"
  autoScroll?: boolean
  preferences?: Partial<TerminalViewerPreferences>
  className?: string
  emptyLabel?: string
  onSendInput?: (data: string) => boolean
  onPasteInput?: (data: string) => boolean | Promise<boolean>
  onCopyVisibleBuffer?: (data: string) => void | Promise<void>
  onViewportChange?: (cols: number, rows: number) => void
}

export function TerminalViewer({
  session,
  status,
  capabilities,
  mode = "live",
  autoScroll,
  preferences,
  className,
  emptyLabel = "Terminal output will appear here once the session is active.",
  onSendInput,
  onPasteInput,
  onCopyVisibleBuffer,
  onViewportChange,
}: TerminalViewerProps) {
  const terminalHostRef = useRef<HTMLDivElement | null>(null)
  const terminalRef = useRef<Terminal | null>(null)
  const renderedChunksRef = useRef(0)
  const sessionIdRef = useRef<string | null>(null)
  const measurementRef = useRef<HTMLSpanElement | null>(null)
  const lastViewportRef = useRef<{ cols: number; rows: number } | null>(null)
  const [hasTerminalFocus, setHasTerminalFocus] = useState(false)
  const fontSize =
    preferences?.fontSize ?? DEFAULT_TERMINAL_VIEWER_PREFERENCES.fontSize
  const lineHeight =
    preferences?.lineHeight ?? DEFAULT_TERMINAL_VIEWER_PREFERENCES.lineHeight
  const wrapMode =
    preferences?.wrapMode ?? DEFAULT_TERMINAL_VIEWER_PREFERENCES.wrapMode
  const resolvedAutoScroll =
    typeof autoScroll === "boolean"
      ? autoScroll
      : (preferences?.autoScroll ?? DEFAULT_TERMINAL_VIEWER_PREFERENCES.autoScroll)
  const scrollback =
    preferences?.scrollback ?? DEFAULT_TERMINAL_VIEWER_PREFERENCES.scrollback
  const themePreset =
    preferences?.themePreset ?? DEFAULT_TERMINAL_VIEWER_PREFERENCES.themePreset
  const canUseDirectInput = Boolean(
    capabilities?.directInput && capabilities?.sendInput,
  )
  const canHandlePaste = Boolean(capabilities?.paste && onPasteInput)

  useEffect(() => {
    if (mode !== "live" || !terminalHostRef.current || terminalRef.current) {
      return
    }

    const terminal = new Terminal({
      convertEol: true,
      cursorBlink: true,
      disableStdin: !canUseDirectInput,
      fontFamily:
        'ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, "Liberation Mono", monospace',
      fontSize,
      lineHeight,
      scrollback,
      theme: terminalThemeFromPreset(themePreset),
    })

    terminal.open(terminalHostRef.current)
    if (canUseDirectInput) {
      terminal.focus()
    }
    terminalRef.current = terminal

    return () => {
      terminal.dispose()
      terminalRef.current = null
      renderedChunksRef.current = 0
      sessionIdRef.current = null
      lastViewportRef.current = null
    }
  }, [canUseDirectInput, mode])

  useEffect(() => {
    if (mode !== "live") return

    const terminal = terminalRef.current
    if (!terminal) return

    terminal.options.disableStdin = !canUseDirectInput
    terminal.options.fontSize = fontSize
    terminal.options.lineHeight = lineHeight
    terminal.options.scrollback = scrollback
    terminal.options.theme = terminalThemeFromPreset(themePreset)
  }, [canUseDirectInput, mode, fontSize, lineHeight, scrollback, themePreset])

  useEffect(() => {
    if (mode !== "live") return

    const host = terminalHostRef.current
    const terminal = terminalRef.current
    const measurement = measurementRef.current
    if (!host || !terminal || !measurement) return

    const updateViewport = () => {
      const bounds = host.getBoundingClientRect()
      const sample = measurement.getBoundingClientRect()
      const cellWidth = sample.width / 10
      const cellHeight = sample.height
      if (!Number.isFinite(cellWidth) || !Number.isFinite(cellHeight)) {
        return
      }

      const cols = Math.max(20, Math.floor(bounds.width / cellWidth))
      const rows = Math.max(8, Math.floor(bounds.height / cellHeight))

      if (terminal.cols !== cols || terminal.rows !== rows) {
        terminal.resize(cols, rows)
      }

      if (
        lastViewportRef.current?.cols !== cols ||
        lastViewportRef.current?.rows !== rows
      ) {
        lastViewportRef.current = { cols, rows }
        onViewportChange?.(cols, rows)
      }
    }

    updateViewport()
    const observer = new ResizeObserver(() => {
      updateViewport()
    })
    observer.observe(host)

    return () => {
      observer.disconnect()
    }
  }, [mode, onViewportChange, fontSize, lineHeight])

  useEffect(() => {
    if (mode !== "live") return

    const terminal = terminalRef.current
    if (!terminal || !canUseDirectInput) {
      return
    }

    const disposable = terminal.onData((data) => {
      if (status !== "open" || !onSendInput) return
      onSendInput(data)
    })

    return () => {
      disposable.dispose()
    }
  }, [
    canUseDirectInput,
    mode,
    onSendInput,
    status,
  ])

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

    if (resolvedAutoScroll) {
      terminal.scrollToBottom()
    }
  }, [mode, resolvedAutoScroll, session.ansiChunks, session.id])

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
        "relative h-full min-h-[20rem] overflow-hidden bg-neutral-950 text-neutral-100 transition-shadow",
        hasTerminalFocus
          ? "ring-1 ring-sky-400/50 ring-inset"
          : "ring-1 ring-transparent ring-inset",
        className,
      )}
      onClick={() => {
        terminalRef.current?.focus()
      }}
      onFocusCapture={() => {
        setHasTerminalFocus(true)
      }}
      onBlurCapture={() => {
        setHasTerminalFocus(false)
      }}
      onKeyDownCapture={(event) => {
        const terminal = terminalRef.current
        if (!terminal) return

        const key = event.key.toLowerCase()
        if (canHandlePaste && (event.metaKey || event.ctrlKey) && key === "v") {
          event.preventDefault()
          void navigator.clipboard
            .readText()
            .then((text) => {
              if (text) {
                return onPasteInput?.(text)
              }
            })
            .catch(() => {})
          return
        }

        if (
          onCopyVisibleBuffer &&
          (event.metaKey || event.ctrlKey) &&
          event.shiftKey &&
          key === "c"
        ) {
          event.preventDefault()
          void onCopyVisibleBuffer(session.plainText)
          return
        }

        if ((event.metaKey || event.ctrlKey) && key === "k") {
          event.preventDefault()
          terminal.clear()
        }
      }}
      onPaste={(event) => {
        if (!canHandlePaste || !onPasteInput) return
        const text = event.clipboardData.getData("text")
        if (!text) return
        event.preventDefault()
        void onPasteInput(text)
      }}
    >
      <div
        ref={terminalHostRef}
        className={cn(
          "h-full min-h-[20rem] p-4",
          wrapMode === "nowrap" ? "overflow-x-auto" : "",
        )}
      />
      <span
        ref={measurementRef}
        aria-hidden="true"
        className="pointer-events-none absolute opacity-0"
        style={{
          left: 0,
          top: 0,
          fontFamily:
            'ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, "Liberation Mono", monospace',
          fontSize: `${fontSize}px`,
          lineHeight,
          whiteSpace: "pre",
        }}
      >
        0000000000
      </span>
      {session.ansiChunks.length === 0 ? (
        <div className="pointer-events-none absolute inset-0 flex items-start p-4">
          <pre className="whitespace-pre-wrap break-words font-mono text-sm leading-6 text-neutral-400">
            {buildEmptyStateLabel(status, emptyLabel)}
          </pre>
        </div>
      ) : null}
      {canUseDirectInput ? (
        <div className="pointer-events-none absolute right-4 bottom-3 rounded-full border border-neutral-700/70 bg-neutral-900/90 px-2.5 py-1 text-[11px] text-neutral-400">
          {buildInteractionHint(
            capabilities?.inputMode,
            capabilities?.sendResize,
            hasTerminalFocus,
          )}
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

function buildInteractionHint(
  inputMode: TerminalInputMode | undefined,
  sendResize: boolean | undefined,
  hasTerminalFocus: boolean,
) {
  const inputLabel =
    inputMode === "direct"
      ? hasTerminalFocus
        ? "Terminal focused"
        : "Click terminal to focus"
      : "Terminal input unavailable"
  const resizeLabel = sendResize ? "remote resize active" : "local resize only"
  return `${inputLabel} • ${resizeLabel}`
}

function terminalThemeFromPreset(
  preset: TerminalViewerThemePreset,
) {
  if (preset === "amber") {
    return {
      background: "#110f08",
      foreground: "#f8e3a1",
      cursor: "#ffd166",
    }
  }

  if (preset === "midnight") {
    return {
      background: "#090f1a",
      foreground: "#d7e3ff",
      cursor: "#90cdf4",
    }
  }

  return {
    background: "#0a0a0a",
    foreground: "#f5f5f5",
    cursor: "#f5f5f5",
  }
}
