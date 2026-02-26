import MessageInput from "@/components/Room/RoomMessages/MessageInput"
import MessageList from "@/components/Room/RoomMessages/MessageList"
import { useRoomMessages } from "@/hooks/useRoomMessages"

interface DemoChatPanelProps {
  roomId: string
  isConnected: boolean
  sendViaWebSocket: (content: string) => void
  streamingMessage: { agent_name: string; content: string } | null
  feedDensity?: "comfortable" | "compact"
  messageRowHighlightCss?: string
  calloutLabel?: string | null
}

export function DemoChatPanel({
  roomId,
  isConnected,
  sendViaWebSocket,
  streamingMessage,
  feedDensity = "comfortable",
  messageRowHighlightCss,
  calloutLabel,
}: DemoChatPanelProps) {
  const {
    messages,
    sendMessage,
    isSending,
    hasMore,
    loadMore,
    isLoadingMore,
    isLoading,
  } = useRoomMessages(roomId)

  return (
    <div className="flex flex-col h-full">
      {calloutLabel && (
        <div className="px-3 py-2 text-xs border-b bg-muted/30 text-muted-foreground">
          {calloutLabel}
        </div>
      )}
      <div
        className={
          feedDensity === "compact"
            ? "flex-1 overflow-y-auto p-2"
            : "flex-1 overflow-y-auto p-4"
        }
        style={
          messageRowHighlightCss
            ? { boxShadow: messageRowHighlightCss }
            : undefined
        }
      >
        <MessageList
          roomId={roomId}
          messages={messages}
          hasMore={hasMore}
          onLoadMore={loadMore}
          isLoadingMore={isLoadingMore}
          isLoading={isLoading}
          streamingMessage={streamingMessage}
        />
      </div>
      <MessageInput
        roomId={roomId}
        onSendMessage={sendMessage}
        isSending={isSending}
        isConnected={isConnected}
        sendViaWebSocket={sendViaWebSocket}
      />
    </div>
  )
}
