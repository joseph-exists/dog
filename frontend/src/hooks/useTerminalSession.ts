import { useCallback, useEffect, useRef, useState } from "react"
import {
  appendTerminalFrame,
  clearTerminalSession,
  createTerminalFrame,
  createTerminalSession,
  decodeTerminalEventData,
  setTerminalConnectionStatus,
  type TerminalSessionState,
  updateTerminalViewport,
} from "@/services/terminalSessionService"

export interface UseTerminalSessionOptions {
  url: string | null
  enabled?: boolean
  maxFrames?: number
  maxChars?: number
  allowDirectInput?: boolean
  allowPaste?: boolean
  allowResize?: boolean
  defaultInputMode?: Exclude<TerminalInputMode, "none">
}

export type TerminalInputMode = "none" | "line" | "direct"

export interface TerminalCapabilities {
  connect: boolean
  reconnect: boolean
  disconnect: boolean
  sendInput: boolean
  directInput: boolean
  paste: boolean
  sendResize: boolean
  transcript: boolean
  clearBuffer: boolean
  inputMode: TerminalInputMode
}

export function useTerminalSession({
  url,
  enabled = true,
  maxFrames,
  maxChars,
  allowDirectInput = true,
  allowPaste = true,
  allowResize = true,
  defaultInputMode = "direct",
}: UseTerminalSessionOptions) {
  const debugSessionIdRef = useRef<string>(
    `termdbg-${Math.random().toString(36).slice(2, 10)}`,
  )
  const debugEnabledRef = useRef<boolean>(isTerminalDebugEnabled())
  const [session, setSession] = useState<TerminalSessionState>(() =>
    createTerminalSession(url),
  )
  const [error, setError] = useState<Error | null>(null)
  const [_connectionNonce, setConnectionNonce] = useState(0)

  const wsRef = useRef<WebSocket | null>(null)
  const manualDisconnectRef = useRef(false)
  const pendingOutputRef = useRef<string[]>([])
  const flushTimeoutRef = useRef<number | null>(null)
  const resizeTimeoutRef = useRef<number | null>(null)
  const pendingResizeRef = useRef<{ cols: number; rows: number } | null>(null)
  const lastSentResizeRef = useRef<{ cols: number; rows: number } | null>(null)

  const flushPendingFrames = useCallback(() => {
    flushTimeoutRef.current = null
    const pending = pendingOutputRef.current
    if (pending.length === 0) return

    pendingOutputRef.current = []
    setSession((current) => {
      let next = current
      for (const chunk of pending) {
        next = appendTerminalFrame(next, createTerminalFrame("output", chunk), {
          maxFrames,
          maxChars,
        })
      }
      return next
    })
  }, [maxChars, maxFrames])

  const scheduleFrameFlush = useCallback(() => {
    if (flushTimeoutRef.current !== null) return
    flushTimeoutRef.current = window.setTimeout(() => {
      flushPendingFrames()
    }, 16)
  }, [flushPendingFrames])

  useEffect(() => {
    setSession(createTerminalSession(url))
    setError(null)
    pendingOutputRef.current = []
    if (flushTimeoutRef.current !== null) {
      window.clearTimeout(flushTimeoutRef.current)
      flushTimeoutRef.current = null
    }
    pendingResizeRef.current = null
    lastSentResizeRef.current = null
    if (resizeTimeoutRef.current !== null) {
      window.clearTimeout(resizeTimeoutRef.current)
      resizeTimeoutRef.current = null
    }
  }, [url])

  useEffect(() => {
    if (!url || !enabled) {
      return
    }

    manualDisconnectRef.current = false
    setSession((current) => setTerminalConnectionStatus(current, "connecting"))

    const connectionUrl = withTerminalDebugSessionId(
      url,
      debugEnabledRef.current ? debugSessionIdRef.current : null,
    )
    const ws = new WebSocket(connectionUrl)
    ws.binaryType = "arraybuffer"
    wsRef.current = ws
    if (debugEnabledRef.current) {
      terminalDebugLog("socket_connecting", {
        debugSessionId: debugSessionIdRef.current,
        url: connectionUrl,
      })
    }

    ws.onopen = () => {
      setError(null)
      setSession((current) => setTerminalConnectionStatus(current, "open"))
      if (debugEnabledRef.current) {
        terminalDebugLog("socket_open", {
          debugSessionId: debugSessionIdRef.current,
        })
      }
    }

    ws.onmessage = (event) => {
      void decodeTerminalEventData(event.data)
        .then((decoded) => {
          pendingOutputRef.current.push(decoded)
          scheduleFrameFlush()
          if (
            debugEnabledRef.current &&
            pendingOutputRef.current.length === 1
          ) {
            terminalDebugLog("first_output_received", {
              debugSessionId: debugSessionIdRef.current,
              chunkLength: decoded.length,
            })
          }
        })
        .catch((messageError) => {
          const nextError =
            messageError instanceof Error
              ? messageError
              : new Error("Failed to decode terminal frame.")
          setError(nextError)
          setSession((current) => setTerminalConnectionStatus(current, "error"))
        })
    }

    ws.onerror = () => {
      const nextError = new Error("Terminal connection error.")
      setError(nextError)
      setSession((current) => setTerminalConnectionStatus(current, "error"))
    }

    ws.onclose = () => {
      wsRef.current = null
      setSession((current) =>
        setTerminalConnectionStatus(
          current,
          manualDisconnectRef.current
            ? "closed"
            : current.status === "error"
              ? "error"
              : "closed",
        ),
      )
      if (debugEnabledRef.current) {
        terminalDebugLog("socket_closed", {
          debugSessionId: debugSessionIdRef.current,
        })
      }
    }

    return () => {
      manualDisconnectRef.current = true
      ws.close()
      wsRef.current = null
      pendingOutputRef.current = []
      if (flushTimeoutRef.current !== null) {
        window.clearTimeout(flushTimeoutRef.current)
        flushTimeoutRef.current = null
      }
      pendingResizeRef.current = null
      if (resizeTimeoutRef.current !== null) {
        window.clearTimeout(resizeTimeoutRef.current)
        resizeTimeoutRef.current = null
      }
    }
  }, [url, enabled, scheduleFrameFlush])

  const connect = useCallback(() => {
    if (!url) return
    setError(null)
    setConnectionNonce((value) => value + 1)
  }, [url])

  const reconnect = useCallback(() => {
    if (!url) return
    manualDisconnectRef.current = false
    setError(null)
    setConnectionNonce((value) => value + 1)
  }, [url])

  const disconnect = useCallback(() => {
    manualDisconnectRef.current = true
    wsRef.current?.close()
  }, [])

  const clear = useCallback(() => {
    setSession((current) => clearTerminalSession(current))
  }, [])

  const sendInput = useCallback((data: string) => {
    if (
      !data ||
      !wsRef.current ||
      wsRef.current.readyState !== WebSocket.OPEN
    ) {
      return false
    }

    wsRef.current.send(new TextEncoder().encode(data))
    if (debugEnabledRef.current) {
      terminalDebugLog("input_sent", {
        debugSessionId: debugSessionIdRef.current,
        inputLength: data.length,
      })
    }
    return true
  }, [])

  const flushResize = useCallback(() => {
    resizeTimeoutRef.current = null
    const next = pendingResizeRef.current
    pendingResizeRef.current = null
    if (!next) return

    const cols = Math.max(1, Math.min(1000, Math.floor(next.cols)))
    const rows = Math.max(1, Math.min(1000, Math.floor(next.rows)))

    if (
      !wsRef.current ||
      wsRef.current.readyState !== WebSocket.OPEN ||
      !Number.isFinite(cols) ||
      !Number.isFinite(rows)
    ) {
      return
    }

    const last = lastSentResizeRef.current
    if (last && last.cols === cols && last.rows === rows) {
      return
    }

    wsRef.current.send(
      JSON.stringify({
        type: "terminal_control",
        control: "resize",
        cols,
        rows,
      }),
    )
    lastSentResizeRef.current = { cols, rows }
  }, [])

  const sendResize = useCallback(
    (cols: number, rows: number) => {
      if (
        !Number.isFinite(cols) ||
        !Number.isFinite(rows) ||
        cols <= 0 ||
        rows <= 0
      ) {
        return false
      }

      pendingResizeRef.current = { cols, rows }
      if (resizeTimeoutRef.current !== null) {
        return true
      }

      resizeTimeoutRef.current = window.setTimeout(() => {
        flushResize()
      }, 150)
      return true
    },
    [flushResize],
  )

  const setViewport = useCallback(
    (cols: number | null, rows: number | null) => {
      setSession((current) => updateTerminalViewport(current, { cols, rows }))
    },
    [],
  )

  const capabilities: TerminalCapabilities = {
    connect: Boolean(url),
    reconnect: Boolean(url),
    disconnect: session.status === "connecting" || session.status === "open",
    sendInput: Boolean(url),
    directInput:
      Boolean(url) && allowDirectInput && defaultInputMode === "direct",
    paste: Boolean(url) && allowPaste,
    sendResize: Boolean(url) && allowResize,
    transcript: true,
    clearBuffer: true,
    inputMode: url
      ? defaultInputMode === "line" || !allowDirectInput
        ? "line"
        : "direct"
      : "none",
  }

  return {
    session,
    status: session.status,
    error,
    connect,
    reconnect,
    disconnect,
    clear,
    sendInput,
    sendResize,
    setViewport,
    capabilities,
    debugSessionId: debugEnabledRef.current ? debugSessionIdRef.current : null,
  }
}

function isTerminalDebugEnabled(): boolean {
  if (typeof window === "undefined") return false
  const query = new URLSearchParams(window.location.search)
  if (query.get("terminalDebug") === "1") return true
  return window.localStorage.getItem("terminalDebug") === "1"
}

function withTerminalDebugSessionId(
  url: string,
  debugSessionId: string | null,
): string {
  if (!debugSessionId) return url
  try {
    const parsed = new URL(url)
    parsed.searchParams.set("debug_session_id", debugSessionId)
    return parsed.toString()
  } catch {
    return url
  }
}

function terminalDebugLog(event: string, payload: Record<string, unknown>) {
  if (typeof window === "undefined") return
  const target = window as typeof window & {
    __terminalPerfLog?: Array<Record<string, unknown>>
  }
  if (!Array.isArray(target.__terminalPerfLog)) {
    target.__terminalPerfLog = []
  }
  target.__terminalPerfLog.push({
    scope: "terminal_hook",
    phase: event,
    ...payload,
    at: Date.now(),
  })
}
