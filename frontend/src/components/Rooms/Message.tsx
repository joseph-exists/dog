/**
 * Message Component
 *
 * Displays individual message with:
 * - Sender name
 * - Message content
 * - Timestamp (relative format)
 * - Visual distinction for user/agent/own messages
 * - Phase 4: Streaming indicator for real-time agent responses
 * - Phase 5: Status badges (edited, pinned, active/inactive)
 * - Phase 5: Action menu (edit, pin, delete, toggle context)
 *
 * Phase 3 Alpha - Task 9 | Phase 5 - Message Management
 */

import { Box, Text, HStack } from "@chakra-ui/react";
import { MessageBadge } from "@/components/ui/message-badge";
import MessageActionMenu from "./MessageActionMenu";

import type { MessageViewModel, RoomViewModel } from "@/services/roomService";

interface MessageProps {
  message: MessageViewModel;
  isStreaming?: boolean;
  // Phase 5: Message management props
  room?: RoomViewModel;
  isPinned?: boolean;
  isActiveForContext?: boolean;
  editedAt?: string | null;
  onEdit?: () => void;
  onPin?: () => void;
  onUnpin?: () => void;
  onToggleContext?: (active: boolean) => void;
  onDelete?: () => void;
}

/**
 * Format timestamp as relative time
 * Returns: "Just now", "2 minutes ago", "5 hours ago"
 */
const formatTimestamp = (date: Date): string => {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins} min ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
};

const Message = ({
  message,
  isStreaming = false,
  room,
  isPinned = false,
  isActiveForContext = false,
  editedAt = null,
  onEdit,
  onPin,
  onUnpin,
  onToggleContext,
  onDelete,
}: MessageProps) => {
  return (
    <Box
      position="relative"
      alignSelf={message.sender_type === "user" ? "flex-end" : "flex-start"}
      maxW="70%"
      p={3}
      borderRadius="md"
      bg={
        message.is_own_message
          ? "blue.600"
          : message.sender_type === "agent"
            ? "gray.200"
            : "blue.500"
      }
      color={message.sender_type === "agent" ? "black" : "white"}
      _dark={{
        bg:
          message.is_own_message
            ? "blue.700"
            : message.sender_type === "agent"
              ? "gray.700"
              : "blue.600",
        color: message.sender_type === "agent" ? "white" : "white",
      }}
      wordBreak="break-word"
      // Phase 4: Add border animation for streaming messages
      borderWidth={isStreaming ? 2 : 0}
      borderColor={isStreaming ? "blue.400" : "transparent"}
      animation={isStreaming ? "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite" : undefined}
    >
      {/* Phase 5: Action menu - top right corner */}
      {room && onEdit && !isStreaming && (
        <Box position="absolute" top={2} right={2}>
          <MessageActionMenu
            message={message}
            room={room}
            onEdit={onEdit}
            onPin={onPin || (() => {})}
            onUnpin={onUnpin || (() => {})}
            onToggleContext={onToggleContext || (() => {})}
            onDelete={onDelete || (() => {})}
            isPinned={isPinned}
            isActiveForContext={isActiveForContext}
          />
        </Box>
      )}

      {/* Sender name */}
      <Text fontSize="xs" opacity={0.8} mb={1} fontWeight="medium">
        {message.sender_name}
        {isStreaming && (
          <Text as="span" ml={2} fontSize="xs" opacity={0.6}>
            typing...
          </Text>
        )}
      </Text>

      {/* Phase 5: Status badges */}
      {!isStreaming && (editedAt || isPinned || isActiveForContext !== undefined) && (
        <HStack gap={2} mb={2} flexWrap="wrap">
          {editedAt && <MessageBadge variant="edited" timestamp={editedAt} />}
          {isPinned && <MessageBadge variant="pinned" />}
          {isActiveForContext !== undefined && (
            <MessageBadge
              variant={isActiveForContext ? "active" : "inactive"}
            />
          )}
        </HStack>
      )}

      {/* Message content */}
      <Text whiteSpace="pre-wrap">{message.content}</Text>

      {/* Timestamp */}
      <Text fontSize="xs" opacity={0.6} mt={1}>
        {isStreaming ? "streaming..." : formatTimestamp(message.created_at)}
      </Text>
    </Box>
  );
};

export default Message;
