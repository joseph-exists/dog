/**
 * MessageList Component
 *
 * Displays chronological message history with:
 * - Messages in chronological order (oldest to newest)
 * - Auto-scroll to bottom on new messages
 * - "Load More" button for pagination
 * - Empty state handling
 *
 * Phase 3 Alpha - Task 10
 */

import { useEffect, useRef } from "react";
import { Box, Button, EmptyState, Spinner, VStack } from "@chakra-ui/react";

import type { MessageViewModel } from "@/services/roomService";
import Message from "./Message";

interface MessageListProps {
  messages: MessageViewModel[];
  hasMore: boolean;
  onLoadMore: () => Promise<void>;
  isLoadingMore: boolean;
  isLoading?: boolean;
}

const MessageList = ({
  messages,
  hasMore,
  onLoadMore,
  isLoadingMore,
  isLoading = false,
}: MessageListProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  // Loading state
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" h="full">
        <Spinner size="lg" />
      </Box>
    );
  }

  // Empty state
  if (messages.length === 0) {
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

  // Message list
  return (
    <VStack align="stretch" gap={3} w="full">
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
      {messages.slice().reverse().map((message) => (
        <Message key={message.message_id} message={message} />
      ))}

      {/* Auto-scroll anchor */}
      <div ref={messagesEndRef} />
    </VStack>
  );
};

export default MessageList;
