import { useCallback, useState } from "react"
import MessageInput from "@/components/Rooms/MessageInput"
import MessageList from "@/components/Rooms/MessageList"
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"
import type { DemoConfig } from "@/config/demos"
import { useRoomMessages } from "@/hooks/useRoomMessages"
import { useRoomStream } from "@/hooks/useRoomStream"
import { DemoHeader } from "./DemoHeader"
import { DemoStoryPanel } from "./DemoStoryPanel"

interface DemoPageProps {
  config: DemoConfig
}

export function DemoPage({ config }: DemoPageProps) {
  const [autoRespond, setAutoRespond] = useState(config.autoRespond)

  // WebSocket connection for real-time messages
  const {
    isConnected,
    sendMessage: sendViaWebSocket,
    streamingMessage,
  } = useRoomStream(config.roomId)

  // Room messages
  const {
    messages,
    sendMessage,
    isSending,
    hasMore,
    loadMore,
    isLoadingMore,
    isLoading,
  } = useRoomMessages(config.roomId)

  // Callback for DemoStoryPanel to send synthetic messages
  const handleAutoRespondMessage = useCallback(
    (message: string) => {
      if (isConnected) {
        sendViaWebSocket(message)
      } else {
        sendMessage(message)
      }
    },
    [isConnected, sendViaWebSocket, sendMessage],
  )

  return (
    <div className="flex flex-col h-full">
      <DemoHeader
        title={config.title}
        description={config.description}
        autoRespond={autoRespond}
        onAutoRespondChange={setAutoRespond}
        isConnected={isConnected}
      />
      <ResizablePanelGroup direction="horizontal" className="flex-1">
        {/* Left: Story Panel */}
        <ResizablePanel defaultSize={60} minSize={30}>
          <DemoStoryPanel
            roomId={config.roomId}
            roomStoryId={null}
            autoRespond={autoRespond}
            onSendMessage={handleAutoRespondMessage}
          />
        </ResizablePanel>
        <ResizableHandle withHandle />
        {/* Right: Chat */}
        <ResizablePanel defaultSize={40} minSize={25}>
          <div className="flex flex-col h-full">
            <div className="flex-1 overflow-y-auto p-4">
              <MessageList
                roomId={config.roomId}
                messages={messages}
                hasMore={hasMore}
                onLoadMore={loadMore}
                isLoadingMore={isLoadingMore}
                isLoading={isLoading}
                streamingMessage={streamingMessage}
              />
            </div>
            <MessageInput
              roomId={config.roomId}
              onSendMessage={sendMessage}
              isSending={isSending}
              isConnected={isConnected}
              sendViaWebSocket={sendViaWebSocket}
            />
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  )
}
