import { useCallback, useState } from "react"
import MessageInput from "@/components/Room/RoomMessages/MessageInput"
import MessageList from "@/components/Room/RoomMessages/MessageList"
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"
import { useRoomMessages } from "@/hooks/useRoomMessages"
import { useRoomStream } from "@/hooks/useRoomStream"
import type {
  DemoConfigViewModel,
  DemoSessionViewModel,
} from "@/services/demoService"
import { DemoHeader } from "./DemoHeader"
import { DemoStoryPanel } from "./DemoStoryPanel"

interface DemoPageProps {
  demoConfig: DemoConfigViewModel
  demoSession: DemoSessionViewModel
}

export function DemoPage({ demoConfig, demoSession }: DemoPageProps) {
  const [autoRespond, setAutoRespond] = useState(demoSession.autoRespond)
  const roomId = demoSession.roomId

  // WebSocket connection for real-time messages
  const {
    isConnected,
    sendMessage: sendViaWebSocket,
    streamingMessage,
  } = useRoomStream(roomId)

  // Room messages
  const {
    messages,
    sendMessage,
    isSending,
    hasMore,
    loadMore,
    isLoadingMore,
    isLoading,
  } = useRoomMessages(roomId)

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
    <div
      className="flex flex-col h-full"
    >
      <DemoHeader
        title={demoConfig.title}
        description={demoConfig.description ?? ""}
        autoRespond={autoRespond}
        onAutoRespondChange={setAutoRespond}
        isConnected={isConnected}
        pageTheme={null}
        cardsTheme={null}
        availablePageThemes={[]}
        availableCardThemes={[]}
        onPageThemeChange={() => {}}
        onCardsThemeChange={() => {}}
      />
      <ResizablePanelGroup direction="horizontal" className="flex-1">
        {/* Left: Story Panel */}
        <ResizablePanel defaultSize={60} minSize={30}>
          <DemoStoryPanel
            roomId={roomId}
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
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  )
}
