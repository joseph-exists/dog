// /**
//  * MessageList Component
//  *
//  * Displays chronological message history with:
//  * - Messages in chronological order (oldest to newest)
//  * - Auto-scroll to bottom on new messages
//  * - "Load More" button for pagination
//  * - Empty state handling
//  * - Real-time streaming message display
//  * - Message filtering (active/inactive, pinned, sender type)
//  * - Pinned messages section at top
//  */

// import { Loader2, MessageSquare } from "lucide-react"
// import { useCallback, useEffect, useRef, useState } from "react"
// import { Button } from "@/components/ui/button"
// import type { MessageViewModel } from "@/services/roomService"
// import Message from "./Message"
// import MessageFilters, {
//   type MessageFilters as FilterState,
// } from "./MessageFilters"
// import PinnedMessagesSection from "./PinnedMessagesSection"

// interface MessageListProps {
//   roomId: string
//   messages: MessageViewModel[]
//   hasMore: boolean
//   onLoadMore: () => Promise<void>
//   isLoadingMore: boolean
//   isLoading?: boolean
//   streamingMessage: { agent_name: string; content: string } | null
//   /** Whether current user is the room owner (grants full message permissions) */
//   isRoomOwner?: boolean
//   /** Include internal agent messages in message queries (dev mode). */
//   includeInternalMessages?: boolean
//   /** Toggle internal agent message visibility (dev mode). */
//   onToggleInternalMessages?: (enabled: boolean) => void
//   onEditMessage?: (message: MessageViewModel) => void
//   onPinMessage?: (messageId: string) => void
//   onUnpinMessage?: (messageId: string) => void
//   onToggleContext?: (messageId: string, active: boolean) => void
//   onDeleteMessage?: (messageId: string) => void
//   onUiAction?: (action: string, message: MessageViewModel) => void
// }

// export default function MessageList({
//   roomId,
//   messages,
//   hasMore,
//   onLoadMore,
//   isLoadingMore,
//   isLoading = false,
//   streamingMessage,
//   isRoomOwner = false,
//   includeInternalMessages = false,
//   onToggleInternalMessages,
//   onEditMessage,
//   onPinMessage,
//   onUnpinMessage,
//   onToggleContext,
//   onDeleteMessage,
//   onUiAction,
// }: MessageListProps) {
//   const messagesEndRef = useRef<HTMLDivElement>(null)

//   // Filter state
//   const [filters, setFilters] = useState<FilterState>({
//     activeForContext: null,
//     isPinned: null,
//     senderType: "all",
//   })

//   const updateFilter = useCallback(
//     <K extends keyof FilterState>(key: K, value: FilterState[K]) => {
//       setFilters((prev) => ({ ...prev, [key]: value }))
//     },
//     [],
//   )

//   const clearFilters = useCallback(() => {
//     setFilters({
//       activeForContext: null,
//       isPinned: null,
//       senderType: "all",
//     })
//   }, [])

//   // Apply filters to messages (client-side)
//   const filteredMessages = useCallback(() => {
//     return messages.filter((msg) => {
//       // Filter by active/inactive status
//       if (filters.activeForContext !== null) {
//         if (msg.active_for_context !== filters.activeForContext) {
//           return false
//         }
//       }

//       // Filter by pinned status
//       if (filters.isPinned !== null) {
//         if (msg.is_pinned !== filters.isPinned) {
//           return false
//         }
//       }

//       // Filter by sender type
//       if (filters.senderType !== "all") {
//         const isAgentMessage =
//           msg.sender_type === "agent" || msg.sender_type === "agent_internal"
//         if (
//           (filters.senderType === "agent" && !isAgentMessage) ||
//           (filters.senderType === "user" && msg.sender_type !== "user")
//         ) {
//           return false
//         }
//       }

//       return true
//     })
//   }, [messages, filters])

//   // Get pinned messages for top section
//   const pinnedMessages = useCallback(() => {
//     return filteredMessages().filter((msg) => msg.is_pinned)
//   }, [filteredMessages])

//   // Auto-scroll to bottom when new messages arrive
//   useEffect(() => {
//     messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
//   }, [])

//   // Loading state
//   if (isLoading) {
//     return (
//       <div className="flex items-center justify-center h-full">
//         <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
//       </div>
//     )
//   }

//   const displayMessages = filteredMessages()
//   const pinned = pinnedMessages()

//   // Empty state (no messages at all)
//   if (messages.length === 0 && !streamingMessage) {
//     return (
//       <div className="flex flex-col items-center justify-center py-12 text-center">
//         <MessageSquare className="h-12 w-12 text-muted-foreground mb-4" />
//         <h3 className="text-lg font-medium">No messages yet</h3>
//         <p className="text-sm text-muted-foreground">
//           Start the conversation by sending a message below.
//         </p>
//       </div>
//     )
//   }

//   return (
//     <div className="flex flex-col gap-3 w-full">
//       {/* Filter controls */}
//       <MessageFilters
//         filters={filters}
//         includeInternalMessages={includeInternalMessages}
//         onIncludeInternalChange={onToggleInternalMessages}
//         onFilterChange={updateFilter}
//         onClearFilters={clearFilters}
//       />

//       {/* Pinned messages section */}
//       {pinned.length > 0 && <PinnedMessagesSection messages={pinned} />}

//       {/* Load More button at top */}
//       {hasMore && (
//         <div className="text-center">
//           <Button
//             size="sm"
//             variant="outline"
//             onClick={onLoadMore}
//             disabled={isLoadingMore}
//           >
//             {isLoadingMore && <Loader2 className="h-4 w-4 animate-spin" />}
//             {isLoadingMore ? "Loading..." : "Load More"}
//           </Button>
//         </div>
//       )}

//       {/* Messages - reversed to show oldest first, newest last */}
//       {displayMessages.length > 0 ? (
//         displayMessages
//           .slice()
//           .reverse()
//           .map((message) => (
//             <Message
//               key={message.message_id}
//               message={message}
//               isRoomOwner={isRoomOwner}
//               onEdit={onEditMessage ? () => onEditMessage(message) : undefined}
//               onPin={
//                 onPinMessage
//                   ? () => onPinMessage(message.message_id)
//                   : undefined
//               }
//               onUnpin={
//                 onUnpinMessage
//                   ? () => onUnpinMessage(message.message_id)
//                   : undefined
//               }
//               onToggleContext={
//                 onToggleContext
//                   ? (active) => onToggleContext(message.message_id, active)
//                   : undefined
//               }
//               onDelete={
//                 onDeleteMessage
//                   ? () => onDeleteMessage(message.message_id)
//                   : undefined
//               }
//               onUiAction={onUiAction}
//             />
//           ))
//       ) : (
//         <div className="text-center p-4 text-muted-foreground">
//           No messages match the current filters
//         </div>
//       )}

//       {/* Streaming message (optimistic UI) */}
//       {streamingMessage && (
//         <Message
//           key="streaming"
//           message={{
//             message_id: "streaming",
//             room_id: roomId,
//             sender_type: "agent",
//             sender_name: streamingMessage.agent_name,
//             sender_id: null,
//             agent_name: streamingMessage.agent_name,
//             content: streamingMessage.content,
//             button_options: null,
//             ui_components: null,
//             created_at: new Date(),
//             is_own_message: false,
//             is_pinned: false,
//             active_for_context: false,
//             can_edit: false,
//             can_delete: false,
//             can_pin: false,
//           }}
//           isStreaming={true}
//         />
//       )}

//       {/* Auto-scroll anchor */}
//       <div ref={messagesEndRef} />
//     </div>
//   )
// }
