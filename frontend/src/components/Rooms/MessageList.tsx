/**
 * MessageList Component
 *
 * Displays chronological message history with:
 * - Messages in chronological order (oldest to newest)
 * - Auto-scroll to bottom on new messages
 * - "Load More" button for pagination
 * - Empty state handling
 * - Phase 4: Real-time streaming message display
 * - Phase 5: Message filtering (active/inactive, pinned, sender type)
 * - Phase 5: Pinned messages section at top
 *
 * Phase 3 Alpha - Task 10 | Phase 5 - Message Management
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { Box, Button, EmptyState, Spinner, VStack } from "@chakra-ui/react";
import type { MessageViewModel, RoomViewModel } from "@/services/roomService";
import Message from "./Message";
import MessageFilters, { type MessageFilters as FilterState } from "./MessageFilters";
import PinnedMessagesSection from "./PinnedMessagesSection";

interface MessageListProps {
  roomId: string;
  messages: MessageViewModel[];
  hasMore: boolean;
  onLoadMore: () => Promise<void>;
  isLoadingMore: boolean;
  isLoading?: boolean;
  // Phase 4: WebSocket streaming message (passed from parent to avoid multiple connections)
  streamingMessage: { agent_name: string; content: string } | null;
  // Phase 5: Message management callbacks
  room?: RoomViewModel;
  onEditMessage?: (message: MessageViewModel) => void;
  onPinMessage?: (messageId: string) => void;
  onUnpinMessage?: (messageId: string) => void;
  onToggleContext?: (messageId: string, active: boolean) => void;
  onDeleteMessage?: (messageId: string) => void;
}

const MessageList = ({
  roomId,
  messages,
  hasMore,
  onLoadMore,
  isLoadingMore,
  isLoading = false,
  streamingMessage,
  room,
  onEditMessage,
  onPinMessage,
  onUnpinMessage,
  onToggleContext,
  onDeleteMessage,
}: MessageListProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Phase 5: Filter state
  const [filters, setFilters] = useState<FilterState>({
    activeForContext: null,
    isPinned: null,
    senderType: "all",
  });

  // Phase 5: Filter update handler
  const updateFilter = useCallback(<K extends keyof FilterState>(
    key: K,
    value: FilterState[K]
  ) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  // Phase 5: Clear filters handler
  const clearFilters = useCallback(() => {
    setFilters({
      activeForContext: null,
      isPinned: null,
      senderType: "all",
    });
  }, []);

  // Phase 5: Apply filters to messages (client-side)
  const filteredMessages = useCallback(() => {
    return messages.filter(msg => {
      // Note: These properties will come from backend once types are updated
      // For now, we'll use any type assertions where needed

      // Filter by active/inactive status
      if (filters.activeForContext !== null) {
        const msgActive = (msg as any).active_for_context ?? false;
        if (msgActive !== filters.activeForContext) {
          return false;
        }
      }

      // Filter by pinned status
      if (filters.isPinned !== null) {
        const msgPinned = (msg as any).is_pinned ?? false;
        if (msgPinned !== filters.isPinned) {
          return false;
        }
      }

      // Filter by sender type
      if (filters.senderType !== "all") {
        if (msg.sender_type !== filters.senderType) {
          return false;
        }
      }

      return true;
    });
  }, [messages, filters]);

  // Phase 5: Get pinned messages for top section
  const pinnedMessages = useCallback(() => {
    return filteredMessages().filter(msg => (msg as any).is_pinned === true);
  }, [filteredMessages]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, streamingMessage]);

  // Loading state
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" h="full">
        <Spinner size="lg" />
      </Box>
    );
  }

  // Get filtered and pinned messages
  const displayMessages = filteredMessages();
  const pinned = pinnedMessages();

  // Empty state (no messages at all)
  if (messages.length === 0 && !streamingMessage) {
    return (
      <EmptyState.Root>
        <EmptyState.Content>
          <VStack textAlign="center">
            <EmptyState.Title>No messages yet</EmptyState.Title>
            <EmptyState.Description>
              Start the conversation by sending a message below.
            </EmptyState.Description>
          </VStack>
        </EmptyState.Content>
      </EmptyState.Root>
    );
  }

  // Message list with filters and pinned section
  return (
    <VStack align="stretch" gap={3} w="full">
      {/* Phase 5: Filter controls */}
      <MessageFilters
        filters={filters}
        onFilterChange={updateFilter}
        onClearFilters={clearFilters}
      />

      {/* Phase 5: Pinned messages section */}
      {pinned.length > 0 && (
        <PinnedMessagesSection messages={pinned} />
      )}

      {/* Load More button at top */}
      {hasMore && (
        <Box textAlign="center">
          <Button
            size="sm"
            variant="outline"
            onClick={onLoadMore}
            loading={isLoadingMore}
            loadingText="Loading..."
          >
            Load More
          </Button>
        </Box>
      )}

      {/* Messages - reversed to show oldest first, newest last */}
      {displayMessages.length > 0 ? (
        displayMessages.slice().reverse().map((message) => {
          // Cast to any to access Phase 5 properties (will be properly typed after Task 4.2)
          const msg = message as any;
          return (
            <Message
              key={message.message_id}
              message={message}
              room={room}
              isPinned={msg.is_pinned ?? false}
              isActiveForContext={msg.active_for_context ?? false}
              editedAt={msg.edited_at ?? null}
              onEdit={onEditMessage ? () => onEditMessage(message) : undefined}
              onPin={onPinMessage ? () => onPinMessage(message.message_id) : undefined}
              onUnpin={onUnpinMessage ? () => onUnpinMessage(message.message_id) : undefined}
              onToggleContext={onToggleContext ? (active) => onToggleContext(message.message_id, active) : undefined}
              onDelete={onDeleteMessage ? () => onDeleteMessage(message.message_id) : undefined}
            />
          );
        })
      ) : (
        <Box textAlign="center" p={4} color="gray.500">
          No messages match the current filters
        </Box>
      )}

      {/* Phase 4: Streaming message (optimistic UI) */}
      {streamingMessage && (
        <Message
          key="streaming"
          message={{
            message_id: "streaming",
            room_id: roomId,
            sender_type: "agent",
            sender_name: streamingMessage.agent_name,
            sender_id: null,
            agent_name: streamingMessage.agent_name,
            content: streamingMessage.content,
            button_options: null,
            created_at: new Date(),
            is_own_message: false,
            // Phase 5 fields
            is_pinned: false,
            active_for_context: false,
          }}
          isStreaming={true}
        />
      )}

      {/* Auto-scroll anchor */}
      <div ref={messagesEndRef} />
    </VStack>
  );
};

export default MessageList;