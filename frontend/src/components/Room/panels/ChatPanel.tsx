/**
 * ChatPanel
 *
 * Primary panel for chat messages.
 * Wraps existing MessageList and MessageInput components.
 */

import * as React from "react"
import { Search, Download, Copy } from "lucide-react"
import { PanelContainer } from "../primitives/PanelContainer"
import { ActionBar, type ActionItem } from "../primitives/ActionBar"
import MessageList from "@/components/Rooms/MessageList"
import MessageInput from "@/components/Rooms/MessageInput"
import { Input } from "@/components/ui/input"
import type { MessageViewModel } from "@/services/roomService"

interface ChatPanelProps {
  /** Room ID */
  roomId: string
  /** Messages to display */
  messages: MessageViewModel[]
  /** Whether more messages can be loaded */
  hasMore: boolean
  /** Load more messages callback */
  onLoadMore: () => Promise<void>
  /** Whether loading more messages */
  isLoadingMore: boolean
  /** Whether initial load is happening */
  isLoading: boolean
  /** Streaming message from WebSocket */
  streamingMessage: { agent_name: string; content: string } | null
  /** Whether current user is room owner */
  isRoomOwner: boolean
  /** Send message callback */
  onSendMessage: (content: string) => Promise<void>
  /** Whether sending message */
  isSending: boolean
  /** Whether WebSocket is connected */
  isConnected: boolean
  /** Send via WebSocket callback */
  sendViaWebSocket: (content: string) => void
  /** Edit message callback */
  onEditMessage?: (message: MessageViewModel) => void
  /** Pin message callback */
  onPinMessage?: (messageId: string) => void
  /** Unpin message callback */
  onUnpinMessage?: (messageId: string) => void
  /** Toggle context callback */
  onToggleContext?: (messageId: string, active: boolean) => void
  /** Delete message callback */
  onDeleteMessage?: (messageId: string) => void
}

export function ChatPanel({
  roomId,
  messages,
  hasMore,
  onLoadMore,
  isLoadingMore,
  isLoading,
  streamingMessage,
  isRoomOwner,
  onSendMessage,
  isSending,
  isConnected,
  sendViaWebSocket,
  onEditMessage,
  onPinMessage,
  onUnpinMessage,
  onToggleContext,
  onDeleteMessage,
}: ChatPanelProps) {
  const [searchQuery, setSearchQuery] = React.useState("")
  const [showSearch, setShowSearch] = React.useState(false)

  const headerActions: ActionItem[] = [
    {
      id: "search",
      icon: Search,
      label: "Search messages",
      onClick: () => setShowSearch(!showSearch),
    },
    {
      id: "copy",
      icon: Copy,
      label: "Copy conversation",
      onClick: () => {
        const text = messages.map((m) => `${m.sender_name}: ${m.content}`).join("\n")
        navigator.clipboard.writeText(text)
      },
    },
    {
      id: "export",
      icon: Download,
      label: "Export conversation",
      onClick: () => {
        // TODO: Implement export
        console.log("Export not implemented")
      },
    },
  ]

  // Filter messages by search query
  const filteredMessages = searchQuery
    ? messages.filter(
        (m) =>
          m.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
          m.sender_name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : messages

  return (
    <PanelContainer
      title="Chat"
      headerActions={<ActionBar actions={headerActions} />}
      footer={
        <MessageInput
          roomId={roomId}
          onSendMessage={onSendMessage}
          isSending={isSending}
          isConnected={isConnected}
          sendViaWebSocket={sendViaWebSocket}
        />
      }
    >
      {showSearch && (
        <div className="p-2 border-b">
          <Input
            placeholder="Search messages..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-8"
          />
        </div>
      )}
      <div className="flex-1 overflow-y-auto p-4">
        <MessageList
          roomId={roomId}
          messages={filteredMessages}
          hasMore={hasMore}
          onLoadMore={onLoadMore}
          isLoadingMore={isLoadingMore}
          isLoading={isLoading}
          streamingMessage={streamingMessage}
          isRoomOwner={isRoomOwner}
          onEditMessage={onEditMessage}
          onPinMessage={onPinMessage}
          onUnpinMessage={onUnpinMessage}
          onToggleContext={onToggleContext}
          onDeleteMessage={onDeleteMessage}
        />
      </div>
    </PanelContainer>
  )
}
