/**
 * ChatPanel
 *
 * Primary panel for chat messages.
 * Wraps existing MessageList and MessageInput components.
 */

import { Copy, Download, Search, Users } from "lucide-react"
import * as React from "react"
import type { UserAgentConfigData as AgentData} from "@/components/Agents/types"
import AgentPartyPicker  from "@/components/Agents/RoomManagers/AgentPartyPicker"
import MessageInput from "@/components/Room/RoomMessages/MessageInput"
import MessageList from "@/components/Room/RoomMessages/MessageList"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import type { MessageViewModel } from "@/services/roomService"
import { ActionBar, type ActionItem } from "../primitives/ActionBar"
import { PanelContainer } from "../primitives/PanelContainer"

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
  /** AG-UI action button click callback — fires when user clicks an action button
   *  rendered in an agent message. The action string identifies what was clicked
   *  (e.g. "expand_details", "regenerate") and the message provides context about
   *  which agent emitted it. */
  onUiAction?: (action: string, message: MessageViewModel) => void
  /** Available agents for the party picker */
  availableAgents?: AgentData[]
  /** IDs of agents already in the room */
  existingAgentIds?: string[]
  /** Add multiple agents callback */
  onAddMultipleAgents?: (agents: AgentData[]) => Promise<void>
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
  onUiAction,
  availableAgents = [],
  existingAgentIds = [],
  onAddMultipleAgents,
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
      headerActions={
        <div className="flex items-center gap-1">
          {isRoomOwner && onAddMultipleAgents && (
            <AgentPartyPicker
              availableAgents={availableAgents}
              existingAgentIds={existingAgentIds}
              onConfirm={onAddMultipleAgents}
              title="Add Agents to Room"
              description="Select multiple agents to add at once"
              trigger={
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <Users className="h-4 w-4" />
                </Button>
              }
            />
          )}
          <ActionBar actions={headerActions} />
        </div>
      }
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
          onUiAction={onUiAction}
        />
      </div>
    </PanelContainer>
  )
}
