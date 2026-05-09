import type { Terminal as XTermTerminal } from "@xterm/xterm"
import { useEffect, useRef, useState } from "react"
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
  debugSessionId?: string | null
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
  debugSessionId,
}: TerminalViewerProps) {
  const perfIdRef = useRef<string>(
    `terminal-viewer-${Math.random().toString(36).slice(2, 10)}`,
  )
  const viewerRootRef = useRef<HTMLDivElement | null>(null)
  const terminalHostRef = useRef<HTMLDivElement | null>(null)
  const terminalRef = useRef<XTermTerminal | null>(null)
  const renderedChunksRef = useRef(0)
  const sessionIdRef = useRef<string | null>(null)
  const measurementRef = useRef<HTMLSpanElement | null>(null)
  const lastViewportRef = useRef<{ cols: number; rows: number } | null>(null)
  const [emulatorReady, setEmulatorReady] = useState(false)
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
      : (preferences?.autoScroll ??
        DEFAULT_TERMINAL_VIEWER_PREFERENCES.autoScroll)
  const scrollback =
    preferences?.scrollback ?? DEFAULT_TERMINAL_VIEWER_PREFERENCES.scrollback
  const themePreset =
    preferences?.themePreset ?? DEFAULT_TERMINAL_VIEWER_PREFERENCES.themePreset
  const canUseDirectInput = Boolean(
    capabilities?.directInput && capabilities?.sendInput,
  )
  const canHandlePaste = Boolean(capabilities?.paste && onPasteInput)
  const shouldInitializeEmulator =
    mode === "live" && Boolean(session.url || session.ansiChunks.length > 0)

  useEffect(() => {
    if (
      !shouldInitializeEmulator ||
      !terminalHostRef.current ||
      terminalRef.current
    ) {
      return
    }

    let isDisposed = false
    performanceMark(`${perfIdRef.current}:init_requested`)
    performanceLog({
      scope: "terminal_viewer",
      phase: "init_requested",
      perfId: perfIdRef.current,
      hasSessionUrl: Boolean(session.url),
      ansiChunkCount: session.ansiChunks.length,
      debugSessionId,
    })

    const mountTerminal = async () => {
      performanceMark(`${perfIdRef.current}:asset_load_start`)
      const [{ Terminal }] = await Promise.all([
        import("@xterm/xterm"),
        import("@xterm/xterm/css/xterm.css"),
      ])
      performanceMark(`${perfIdRef.current}:asset_load_end`)
      performanceMeasure(
        `${perfIdRef.current}:asset_load_ms`,
        `${perfIdRef.current}:asset_load_start`,
        `${perfIdRef.current}:asset_load_end`,
      )
      performanceLog({
        scope: "terminal_viewer",
        phase: "asset_load_complete",
        perfId: perfIdRef.current,
        debugSessionId,
      })
      if (isDisposed || !terminalHostRef.current || terminalRef.current) {
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

      performanceMark(`${perfIdRef.current}:emulator_open_start`)
      terminal.open(terminalHostRef.current)
      if (canUseDirectInput) {
        terminal.focus()
      }
      performanceMark(`${perfIdRef.current}:emulator_open_end`)
      performanceMeasure(
        `${perfIdRef.current}:emulator_open_ms`,
        `${perfIdRef.current}:emulator_open_start`,
        `${perfIdRef.current}:emulator_open_end`,
      )
      performanceMeasure(
        `${perfIdRef.current}:init_to_open_ms`,
        `${perfIdRef.current}:init_requested`,
        `${perfIdRef.current}:emulator_open_end`,
      )
      performanceLog({
        scope: "terminal_viewer",
        phase: "emulator_open_complete",
        perfId: perfIdRef.current,
        debugSessionId,
      })
      terminalRef.current = terminal
      setEmulatorReady(true)
    }

    void mountTerminal()

    return () => {
      isDisposed = true
      terminalRef.current?.dispose()
      terminalRef.current = null
      setEmulatorReady(false)
      renderedChunksRef.current = 0
      sessionIdRef.current = null
      lastViewportRef.current = null
      performanceLog({
        scope: "terminal_viewer",
        phase: "dispose",
        perfId: perfIdRef.current,
        debugSessionId,
      })
    }
  }, [
    canUseDirectInput,
    debugSessionId,
    session.ansiChunks.length,
    session.url,
    shouldInitializeEmulator,
    fontSize,
    lineHeight,
    scrollback,
    themePreset,
  ])

  useEffect(() => {
    if (!shouldInitializeEmulator) return

    const terminal = terminalRef.current
    if (!terminal || !emulatorReady) return

    terminal.options.disableStdin = !canUseDirectInput
    terminal.options.fontSize = fontSize
    terminal.options.lineHeight = lineHeight
    terminal.options.scrollback = scrollback
    terminal.options.theme = terminalThemeFromPreset(themePreset)
  }, [
    canUseDirectInput,
    emulatorReady,
    shouldInitializeEmulator,
    fontSize,
    lineHeight,
    scrollback,
    themePreset,
  ])

  useEffect(() => {
    if (!shouldInitializeEmulator) return

    const root = viewerRootRef.current
    const terminal = terminalRef.current
    const measurement = measurementRef.current
    if (!root || !terminal || !measurement || !emulatorReady) return

    const TERMINAL_PADDING_PX = 16
    const MIN_COLS = 20
    const MAX_COLS = 300
    const MIN_ROWS = 8
    const MAX_ROWS = 200

    const updateViewport = () => {
      const bounds = root.getBoundingClientRect()
      const sample = measurement.getBoundingClientRect()
      const cellWidth = sample.width / 10
      const cellHeight = sample.height
      if (
        !Number.isFinite(cellWidth) ||
        !Number.isFinite(cellHeight) ||
        cellWidth <= 0 ||
        cellHeight <= 0
      ) {
        return
      }

      const usableWidth = Math.max(0, bounds.width - TERMINAL_PADDING_PX * 2)
      const usableHeight = Math.max(0, bounds.height - TERMINAL_PADDING_PX * 2)
      const cols = clamp(
        Math.floor(usableWidth / cellWidth),
        MIN_COLS,
        MAX_COLS,
      )
      const rows = clamp(
        Math.floor(usableHeight / cellHeight),
        MIN_ROWS,
        MAX_ROWS,
      )

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
    observer.observe(root)

    return () => {
      observer.disconnect()
    }
  }, [emulatorReady, shouldInitializeEmulator, onViewportChange])

  useEffect(() => {
    if (!shouldInitializeEmulator) return

    const terminal = terminalRef.current
    if (!terminal || !emulatorReady || !canUseDirectInput) {
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
    emulatorReady,
    shouldInitializeEmulator,
    onSendInput,
    status,
  ])

  useEffect(() => {
    if (!shouldInitializeEmulator) return

    const terminal = terminalRef.current
    if (!terminal || !emulatorReady) return

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
    if (nextChunks.length > 0) {
      terminal.write(nextChunks.join(""))
    }
    renderedChunksRef.current = session.ansiChunks.length

    if (resolvedAutoScroll) {
      terminal.scrollToBottom()
    }
  }, [
    emulatorReady,
    shouldInitializeEmulator,
    resolvedAutoScroll,
    session.ansiChunks,
    session.id,
  ])

  if (mode === "transcript") {
    const transcriptContent = toTerminalTranscriptContent(session)
    return (
      <div className={cn("h-full min-h-[20rem]", className)}>
        <ContentRenderer content={transcriptContent} variant="card" safeMode />
      </div>
    )
  }

  return (
    <div
      ref={viewerRootRef}
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
      {shouldInitializeEmulator ? (
        <>
          <div
            ref={terminalHostRef}
            className={cn(
              "absolute inset-0 p-4 overflow-hidden",
              wrapMode === "nowrap" ? "overflow-x-auto" : "overflow-x-hidden",
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
        </>
      ) : (
        <div className="h-full min-h-[20rem] p-4" />
      )}
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

function terminalThemeFromPreset(preset: TerminalViewerThemePreset) {
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

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value))
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

function performanceMeasure(name: string, startMark: string, endMark: string) {
  if (typeof window === "undefined" || typeof performance === "undefined")
    return
  try {
    performance.measure(name, startMark, endMark)
  } catch {
    // Marks may be missing if initialization is interrupted.
  }
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
