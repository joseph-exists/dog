/**
 * ChatPanel
 *  THIS IS NOT MAIN CHAT PANEL, SEE ROOMS/ChatRoomPanel INSTEAD
 *  THIS IS DEBUG ONLY DO NOT MODIFY OR SOURCE FROM THIS FILE
 */

import { Copy, Download, Search } from "lucide-react"
import * as React from "react"
import MessageInput from "@/components/Room/RoomMessages/MessageInput"
import MessageList from "@/components/Room/RoomMessages/MessageList"
import { Input } from "@/components/ui/input"
import type { MessageViewModel } from "@/services/roomService"
import { ActionBar, type ActionItem } from "../Room/primitives/ActionBar"
import { PanelContainer } from "../Room/primitives/PanelContainer"

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
  /** Include internal agent messages in message queries (dev mode). */
  includeInternalMessages?: boolean
  /** Toggle internal agent message visibility (dev mode). */
  onToggleInternalMessages?: (enabled: boolean) => void
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
  includeInternalMessages = false,
  onToggleInternalMessages,
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
        const text = messages
          .map((m) => `${m.sender_name}: ${m.content}`)
          .join("\n")
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
          m.sender_name.toLowerCase().includes(searchQuery.toLowerCase()),
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
      <div className="p-4">
        <MessageList
          roomId={roomId}
          messages={filteredMessages}
          hasMore={hasMore}
          onLoadMore={onLoadMore}
          isLoadingMore={isLoadingMore}
          isLoading={isLoading}
          streamingMessage={streamingMessage}
          isRoomOwner={isRoomOwner}
          includeInternalMessages={includeInternalMessages}
          onToggleInternalMessages={onToggleInternalMessages}
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
