import MessageInput from "@/components/Room/RoomMessages/MessageInput"
import MessageList from "@/components/Room/RoomMessages/MessageList"
import { useRoomMessages } from "@/hooks/useRoomMessages"

interface DemoChatPanelProps {
  roomId: string
  isConnected: boolean
  sendViaWebSocket: (content: string) => void
  streamingMessage: { agent_name: string; content: string } | null
}

export function DemoChatPanel({
  roomId,
  isConnected,
  sendViaWebSocket,
  streamingMessage,
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
      <div className="flex-1 overflow-y-auto p-4">
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
