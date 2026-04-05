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
  const [session, setSession] = useState<TerminalSessionState>(() =>
    createTerminalSession(url),
  )
  const [error, setError] = useState<Error | null>(null)
  const [_connectionNonce, setConnectionNonce] = useState(0)

  const wsRef = useRef<WebSocket | null>(null)
  const manualDisconnectRef = useRef(false)

  useEffect(() => {
    setSession(createTerminalSession(url))
    setError(null)
  }, [url])

  useEffect(() => {
    if (!url || !enabled) {
      return
    }

    manualDisconnectRef.current = false
    setSession((current) => setTerminalConnectionStatus(current, "connecting"))

    const ws = new WebSocket(url)
    ws.binaryType = "arraybuffer"
    wsRef.current = ws

    ws.onopen = () => {
      setError(null)
      setSession((current) => setTerminalConnectionStatus(current, "open"))
    }

    ws.onmessage = (event) => {
      void decodeTerminalEventData(event.data)
        .then((decoded) => {
          setSession((current) =>
            appendTerminalFrame(
              current,
              createTerminalFrame("output", decoded),
              {
                maxFrames,
                maxChars,
              },
            ),
          )
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
    }

    return () => {
      manualDisconnectRef.current = true
      ws.close()
      wsRef.current = null
    }
  }, [url, enabled, maxFrames, maxChars, _connectionNonce])

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

  const sendInput = useCallback(
    (data: string) => {
      if (
        !data ||
        !wsRef.current ||
        wsRef.current.readyState !== WebSocket.OPEN
      ) {
        return false
      }

      wsRef.current.send(new TextEncoder().encode(data))
      return true
    },
    [],
  )

  const sendResize = useCallback((cols: number, rows: number) => {
    if (
      !wsRef.current ||
      wsRef.current.readyState !== WebSocket.OPEN ||
      !Number.isFinite(cols) ||
      !Number.isFinite(rows) ||
      cols <= 0 ||
      rows <= 0
    ) {
      return false
    }

    wsRef.current.send(
      JSON.stringify({
        type: "terminal_control",
        control: "resize",
        cols,
        rows,
      }),
    )
    return true
  }, [])

  const setViewport = useCallback(
    (cols: number | null, rows: number | null) => {
      setSession((current) => updateTerminalViewport(current, { cols, rows }))
    },
    [],
  )

  const capabilities: TerminalCapabilities = {
    connect: Boolean(url),
    reconnect: Boolean(url),
    disconnect:
      session.status === "connecting" || session.status === "open",
    sendInput: Boolean(url),
    directInput: Boolean(url) && allowDirectInput && defaultInputMode === "direct",
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
  }
}
