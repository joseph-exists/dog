import { useQueryClient } from "@tanstack/react-query"
/**
 * useRoomStream: React hook for real-time room updates via WebSocket.
 *
 * Features:
 * - Automatic connection/disconnection based on room ID
 * - Sequence-based reconnection with replay
 * - Token streaming for agent responses
 * - Event handling for all AG-UI message types
 * - Optimistic UI updates
 */
import { useCallback, useEffect, useRef, useState } from "react"

interface RoomEvent {
  type: "event"
  sequence: number
  event_type: string
  payload: any
  created_at: string
}

interface MessageDelta {
  type: "message.delta"
  agent_name: string
  content: string
}

interface SessionCreated {
  type: "session.created"
  room_id: string
}

interface ErrorMessage {
  type: "error"
  message: string
}

type WebSocketMessage = RoomEvent | MessageDelta | SessionCreated | ErrorMessage

interface UseRoomStreamOptions {
  enabled?: boolean
  onError?: (error: Error) => void
}

export function useRoomStream(
  roomId: string | undefined,
  options: UseRoomStreamOptions = {},
) {
  const { enabled = true, onError } = options

  const wsRef = useRef<WebSocket | null>(null)
  const queryClient = useQueryClient()

  const [isConnected, setIsConnected] = useState(false)
  const [lastSequence, setLastSequence] = useState(0)
  const [streamingMessage, setStreamingMessage] = useState<{
    agent_name: string
    content: string
  } | null>(null)

  // Buffer for accumulating tokens before UI update (prevents render spam)
  const tokenBufferRef = useRef<{
    agent_name: string
    content: string
  } | null>(null)
  const updateTimerRef = useRef<NodeJS.Timeout | null>(null)

  // Send message to room
  const sendMessage = useCallback((content: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error("WebSocket not connected")
      return
    }

    wsRef.current.send(
      JSON.stringify({
        type: "message.send",
        content,
      }),
    )
  }, [])

  // Handle incoming WebSocket messages
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)

        switch (message.type) {
          case "session.created":
            console.log("WebSocket session created")
            setIsConnected(true)
            break

          case "event":
            // Update last sequence
            setLastSequence(message.sequence)

            // Clear streaming message BEFORE invalidating queries
            // This prevents race condition where streaming message and final message are both visible
            if (message.event_type === "room_message.agent") {
              // Clear buffer and timer
              if (updateTimerRef.current) {
                clearTimeout(updateTimerRef.current)
                updateTimerRef.current = null
              }
              tokenBufferRef.current = null
              setStreamingMessage(null)
            }

            // Invalidate queries to refresh UI
            if (
              message.event_type === "room_message.user" ||
              message.event_type === "room_message.agent"
            ) {
              queryClient.invalidateQueries({
                queryKey: ["rooms", roomId, "messages"],
              })
            }

            if (message.event_type.startsWith("participant.")) {
              queryClient.invalidateQueries({
                queryKey: ["rooms", roomId, "participants"],
              })
            }

            // Phase 5: Message management events - invalidate messages query
            if (
              message.event_type === "message.edited" ||
              message.event_type === "message.pinned" ||
              message.event_type === "message.unpinned" ||
              message.event_type === "message.context_toggled" ||
              message.event_type === "message.deleted"
            ) {
              queryClient.invalidateQueries({
                queryKey: ["rooms", roomId, "messages"],
              })
            }
            break

          case "message.delta":
            // Accumulate tokens in buffer (throttled UI updates prevent render spam)
            if (
              !tokenBufferRef.current ||
              tokenBufferRef.current.agent_name !== message.agent_name
            ) {
              // New streaming message started
              tokenBufferRef.current = {
                agent_name: message.agent_name,
                content: message.content,
              }
            } else {
              // Append token to buffer
              tokenBufferRef.current.content += message.content
            }

            // Throttle UI updates to every 50ms
            if (updateTimerRef.current) {
              clearTimeout(updateTimerRef.current)
            }
            updateTimerRef.current = setTimeout(() => {
              if (tokenBufferRef.current) {
                setStreamingMessage({ ...tokenBufferRef.current })
              }
            }, 50)
            break

          case "error":
            console.error("WebSocket error:", message.message)
            onError?.(new Error(message.message))
            break
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error)
      }
    },
    [queryClient, roomId, onError],
  )

  // Connect to WebSocket
  useEffect(() => {
    if (!roomId || !enabled) return

    const token = localStorage.getItem("access_token")
    if (!token) {
      console.error("No auth token available")
      return
    }

    // WebSocket URL - use API base URL from env
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost"
    const wsUrl = `${apiUrl
      .replace("http://", "ws://")
      .replace("https://", "wss://")}/api/v1/ws/rooms/${roomId}?token=${token}`

    console.log("Connecting to WebSocket:", wsUrl)

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log("WebSocket connected")

      // Send handshake with last sequence
      ws.send(
        JSON.stringify({
          type: "session.create",
          last_sequence: lastSequence,
        }),
      )
    }

    ws.onmessage = handleMessage

    ws.onerror = (error) => {
      console.error("WebSocket error:", error)
      setIsConnected(false)
      onError?.(new Error("WebSocket connection error"))
    }

    ws.onclose = () => {
      console.log("WebSocket disconnected")
      setIsConnected(false)
    }

    // Cleanup on unmount
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
      if (updateTimerRef.current) {
        clearTimeout(updateTimerRef.current)
      }
    }
  }, [roomId, enabled, lastSequence, handleMessage, onError])

  return {
    isConnected,
    sendMessage,
    streamingMessage,
    lastSequence,
  }
}
