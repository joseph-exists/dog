import { useCallback, useEffect, useRef, useState } from "react"
import {
  appendTerminalFrame,
  clearTerminalSession,
  createTerminalFrame,
  createTerminalSession,
  decodeTerminalEventData,
  setTerminalConnectionStatus,
  updateTerminalViewport,
  type TerminalSessionState,
} from "@/services/terminalSessionService"

export interface UseTerminalSessionOptions {
  url: string | null
  enabled?: boolean
  maxFrames?: number
  maxChars?: number
}

export function useTerminalSession({
  url,
  enabled = true,
  maxFrames,
  maxChars,
}: UseTerminalSessionOptions) {
  const [session, setSession] = useState<TerminalSessionState>(() =>
    createTerminalSession(url),
  )
  const [error, setError] = useState<Error | null>(null)
  const [connectionNonce, setConnectionNonce] = useState(0)

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
            appendTerminalFrame(current, createTerminalFrame("output", decoded), {
              maxFrames,
              maxChars,
            }),
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
          manualDisconnectRef.current ? "closed" : current.status === "error" ? "error" : "closed",
        ),
      )
    }

    return () => {
      manualDisconnectRef.current = true
      ws.close()
      wsRef.current = null
    }
  }, [url, enabled, connectionNonce, maxFrames, maxChars])

  const connect = useCallback(() => {
    if (!url) return
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
      if (!data || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        return false
      }

      wsRef.current.send(new TextEncoder().encode(data))
      setSession((current) =>
        appendTerminalFrame(current, createTerminalFrame("input", data), {
          maxFrames,
          maxChars,
        }),
      )
      return true
    },
    [maxFrames, maxChars],
  )

  const setViewport = useCallback((cols: number | null, rows: number | null) => {
    setSession((current) => updateTerminalViewport(current, { cols, rows }))
  }, [])

  return {
    session,
    status: session.status,
    error,
    connect,
    disconnect,
    clear,
    sendInput,
    setViewport,
    capabilities: {
      sendInput: true,
      sendResize: false,
    },
  }
}
