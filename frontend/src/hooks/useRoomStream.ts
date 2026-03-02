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
import { showWarningToast } from "@/hooks/useCustomToast"
import type { MessageViewModel } from "@/services/roomService"
import useAuth from "./useAuth"

export interface RoomStreamEvent {
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

interface WarningMessage {
  type: "warning"
  message: string
}

type WebSocketMessage =
  | RoomStreamEvent
  | MessageDelta
  | SessionCreated
  | ErrorMessage
  | WarningMessage

interface UseRoomStreamOptions {
  enabled?: boolean
  onError?: (error: Error) => void
  onEvent?: (event: RoomStreamEvent) => void
}

const RUNTIME_EVENT_TYPES = new Set([
  "room.runtime.started",
  "room.runtime.advanced",
  "room.runtime.rewound",
  "room.runtime.reset",
  "room.runtime.cleared",
])

const ROOM_AGENT_SETTINGS_EVENT_TYPES = new Set([
  "room.agent_settings.updated",
  "room.agent_settings.deleted",
])

export function shouldInvalidateRuntime(eventType: string): boolean {
  return RUNTIME_EVENT_TYPES.has(eventType)
}

export function shouldInvalidateRoomAgentSettings(eventType: string): boolean {
  return ROOM_AGENT_SETTINGS_EVENT_TYPES.has(eventType)
}

export function useRoomStream(
  roomId: string | undefined,
  options: UseRoomStreamOptions = {},
) {
  const { enabled = true, onError, onEvent } = options

  const wsRef = useRef<WebSocket | null>(null)
  const queryClient = useQueryClient()
  const shouldLog =
    import.meta.env.DEV && localStorage.getItem("debugRoomLogs") === "1"
  const { user } = useAuth()

  const [isConnected, setIsConnected] = useState(false)
  const [lastSequence, setLastSequence] = useState(0)
  const lastSequenceRef = useRef(0)
  const [streamingMessage, setStreamingMessage] = useState<{
    agent_name: string
    content: string
  } | null>(null)
  const wsInstanceCountRef = useRef(0)

  // Buffer for accumulating tokens before UI update (prevents render spam)
  const tokenBufferRef = useRef<{
    agent_name: string
    content: string
  } | null>(null)
  const updateTimerRef = useRef<NodeJS.Timeout | null>(null)

  const appendUserMessageFromEvent = useCallback(
    (event: RoomStreamEvent) => {
      const payload = event.payload ?? {}
      if (!payload.sender_id || typeof payload.content !== "string") {
        return
      }

      const senderName =
        user && payload.sender_id === user.id
          ? user.full_name || user.email || "You"
          : payload.sender_id
      const optimisticMessage: MessageViewModel = {
        message_id: `ws-${event.sequence}`,
        room_id: roomId || "",
        sender_type: "user",
        sender_name: senderName,
        sender_id: payload.sender_id,
        agent_name: null,
        content: payload.content,
        button_options: null,
        created_at: new Date(event.created_at),
        is_own_message: false,
        is_pinned: false,
        active_for_context: false,
        can_edit: false,
        can_delete: false,
        can_pin: false,
      }

      queryClient.setQueriesData(
        { queryKey: ["rooms", roomId, "messages"] },
        (old: any) => {
          if (!old?.messages) {
            return old
          }
          if (
            old.messages.some(
              (msg: MessageViewModel) =>
                msg.message_id === optimisticMessage.message_id,
            )
          ) {
            return old
          }
          if (shouldLog) {
            console.log("[useRoomStream] messages cache updated", {
              roomId,
              message_id: optimisticMessage.message_id,
            })
          }
          return {
            ...old,
            messages: [optimisticMessage, ...old.messages],
            total_count:
              typeof old.total_count === "number"
                ? old.total_count + 1
                : old.total_count,
          }
        },
      )
    },
    [queryClient, roomId, shouldLog, user],
  )

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
            onEvent?.(message)
            // Update last sequence
            setLastSequence(message.sequence)
            lastSequenceRef.current = message.sequence

            if (message.event_type === "room_message.user") {
              if (shouldLog) {
                console.log("[useRoomStream] room_message.user received", {
                  roomId,
                  sequence: message.sequence,
                })
              }
              appendUserMessageFromEvent(message)
              break
            }

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
              message.event_type === "room_message.agent" ||
              message.event_type === "room_message.agent_internal"
            ) {
              queryClient.invalidateQueries({
                queryKey: ["rooms", roomId, "messages"],
                exact: false,
              })
            }

            if (message.event_type.startsWith("participant.")) {
              queryClient.invalidateQueries({
                queryKey: ["rooms", roomId, "participants"],
              })
            }

            if (shouldInvalidateRuntime(message.event_type)) {
              queryClient.invalidateQueries({
                queryKey: ["rooms", roomId, "runtime"],
              })
            }

            if (shouldInvalidateRoomAgentSettings(message.event_type)) {
              queryClient.invalidateQueries({
                queryKey: ["rooms", roomId, "agent-settings"],
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
                exact: false,
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
          case "warning":
            showWarningToast(message.message)
            break
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error)
      }
    },
    [queryClient, roomId, onError, onEvent, appendUserMessageFromEvent, shouldLog],
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
    wsInstanceCountRef.current += 1
    console.log(
      `[useRoomStream] WebSocket instances created for room ${roomId}: ${wsInstanceCountRef.current}`,
    )

    ws.onopen = () => {
      console.log("WebSocket connected")

      // Send handshake with last sequence
      ws.send(
        JSON.stringify({
          type: "session.create",
          // NOTE: Change: use ref to avoid reconnecting when lastSequence updates.
          // To revert: send `lastSequence` and add it back to the dependency array.
          last_sequence: lastSequenceRef.current,
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
      // NOTE: Change: always close to avoid leaving CONNECTING sockets open.
      // To revert: guard with `if (ws.readyState === WebSocket.OPEN)` again.
      ws.close()
      if (updateTimerRef.current) {
        clearTimeout(updateTimerRef.current)
      }
    }
  }, [roomId, enabled, handleMessage, onError])

  return {
    isConnected,
    sendMessage,
    streamingMessage,
    lastSequence,
  }
}
