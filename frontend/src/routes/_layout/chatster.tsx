/**
 * Chatster — Minimal debug chat route
 *
 * Purpose: Test WebSocket connectivity and room messaging
 * without the overhead of agent integration, pinning, editing, etc.
 *
 * Uses the same hooks as ChatPanel (useRoomStream + useRoomMessages)
 * so we can isolate WebSocket issues from UI complexity.
 */

import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Circle, Loader2, Wifi, WifiOff } from "lucide-react"
import { useEffect, useRef, useState } from "react"

import MessageInput from "@/components/TESTCHATONLY-NOChat/MessageInput"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useRoomMessages } from "@/hooks/useRoomMessages"
import { useRoomStream } from "@/hooks/useRoomStream"
import type { MessageViewModel } from "@/services/roomService"
import { RoomService } from "@/services/roomService"

export const Route = createFileRoute("/_layout/chatster")({
  component: ChatsterView,
})

function ChatsterView() {
  const [selectedRoomId, setSelectedRoomId] = useState<string>("")

  // Fetch available rooms
  const { data: rooms, isLoading: isLoadingRooms } = useQuery({
    queryKey: ["rooms"],
    queryFn: () => RoomService.listRooms(),
  })

  // WebSocket stream (only when room selected)
  const {
    isConnected,
    sendMessage: sendViaWebSocket,
    streamingMessage,
    lastSequence,
  } = useRoomStream(selectedRoomId || undefined)

  // Messages via REST (same query key that useRoomStream invalidates)
  // When selectedRoomId is "", the query will simply not find anything — acceptable for debug tool
  const {
    messages,
    isLoading: isLoadingMessages,
    hasMore,
    loadMore,
    isLoadingMore,
    sendMessage,
    isSending,
  } = useRoomMessages(selectedRoomId)

  return (
    <div className="flex flex-col h-full">
      {/* Header: Room selector + connection status */}
      <div className="flex items-center gap-3 p-3 border-b bg-muted/30">
        <span className="text-sm font-medium text-muted-foreground">
          Chatster
        </span>

        <Select value={selectedRoomId} onValueChange={setSelectedRoomId}>
          <SelectTrigger className="w-[240px] h-8">
            <SelectValue placeholder="Select a room..." />
          </SelectTrigger>
          <SelectContent>
            {isLoadingRooms ? (
              <SelectItem value="_loading" disabled>
                Loading...
              </SelectItem>
            ) : rooms?.length ? (
              rooms.map((room) => (
                <SelectItem key={room.room_id} value={room.room_id}>
                  {room.title || room.room_id.slice(0, 8)}
                </SelectItem>
              ))
            ) : (
              <SelectItem value="_empty" disabled>
                No rooms found
              </SelectItem>
            )}
          </SelectContent>
        </Select>

        {/* Connection indicator */}
        {selectedRoomId && (
          <div className="flex items-center gap-2 ml-auto">
            {isConnected ? (
              <Badge variant="outline" className="gap-1 text-green-600">
                <Wifi className="h-3 w-3" />
                Connected
              </Badge>
            ) : (
              <Badge variant="outline" className="gap-1 text-red-500">
                <WifiOff className="h-3 w-3" />
                Disconnected
              </Badge>
            )}
            <span className="text-xs text-muted-foreground">
              seq: {lastSequence}
            </span>
          </div>
        )}
      </div>

      {/* Message area */}
      {!selectedRoomId ? (
        <div className="flex-1 flex items-center justify-center text-muted-foreground">
          Select a room to start debugging
        </div>
      ) : isLoadingMessages ? (
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <MessageArea
          messages={messages}
          streamingMessage={streamingMessage}
          hasMore={hasMore}
          isLoadingMore={isLoadingMore}
          onLoadMore={loadMore}
        />
      )}

      {/* Input (only when room selected) */}
      {selectedRoomId && (
        <MessageInput
          roomId={selectedRoomId}
          onSendMessage={sendMessage}
          isSending={isSending}
          isConnected={isConnected}
          sendViaWebSocket={sendViaWebSocket}
        />
      )}
    </div>
  )
}

/**
 * Minimal message list — just sender name, content, and timestamp.
 * No action menus, no pinning, no editing, no context toggles.
 */
function MessageArea({
  messages,
  streamingMessage,
  hasMore,
  isLoadingMore,
  onLoadMore,
}: {
  messages: MessageViewModel[]
  streamingMessage: { agent_name: string; content: string } | null
  hasMore: boolean
  isLoadingMore: boolean
  onLoadMore: () => Promise<void>
}) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const prevCountRef = useRef(messages.length)

  // Auto-scroll on new messages
  useEffect(() => {
    if (messages.length > prevCountRef.current) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" })
    }
    prevCountRef.current = messages.length
  }, [messages.length])

  // Messages are returned newest-first from the API; reverse for display
  const displayMessages = [...messages].reverse()

  return (
    <div className="flex-1 overflow-y-auto p-3 space-y-2">
      {/* Load more button */}
      {hasMore && (
        <button
          type="button"
          onClick={onLoadMore}
          disabled={isLoadingMore}
          className="w-full text-xs text-muted-foreground hover:text-foreground py-1"
        >
          {isLoadingMore ? "Loading..." : "↑ Load older messages"}
        </button>
      )}

      {/* Messages */}
      {displayMessages.map((msg) => (
        <MessageBubble key={msg.message_id} message={msg} />
      ))}

      {/* Streaming message (agent typing) */}
      {streamingMessage && (
        <div className="flex items-start gap-2 opacity-70">
          <Circle className="h-2 w-2 mt-2 fill-purple-500 text-purple-500 animate-pulse" />
          <div>
            <span className="text-xs font-medium text-purple-600">
              {streamingMessage.agent_name}
            </span>
            <p className="text-sm whitespace-pre-wrap">
              {streamingMessage.content}
            </p>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}

/** Single message display — minimal, just the facts */
function MessageBubble({ message }: { message: MessageViewModel }) {
  const isAgent = message.sender_type === "agent"
  const isInternal = message.sender_type === "agent_internal"

  return (
    <div className={`flex items-start gap-2 ${isInternal ? "opacity-50" : ""}`}>
      <div
        className={`h-2 w-2 mt-2 rounded-full shrink-0 ${
          isAgent ? "bg-purple-500" : isInternal ? "bg-gray-400" : "bg-blue-500"
        }`}
      />
      <div className="min-w-0">
        <div className="flex items-baseline gap-2">
          <span
            className={`text-xs font-medium ${
              isAgent ? "text-purple-600" : "text-blue-600"
            }`}
          >
            {message.sender_name}
          </span>
          <span className="text-[10px] text-muted-foreground">
            {formatTime(message.created_at)}
          </span>
          {isInternal && (
            <Badge variant="outline" className="text-[9px] h-4 px-1">
              internal
            </Badge>
          )}
        </div>
        <p className="text-sm whitespace-pre-wrap break-words">
          {message.content}
        </p>
      </div>
    </div>
  )
}

function formatTime(date: Date): string {
  return new Date(date).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  })
}
