/**
 * Message Component
 *
 * Displays individual message with:
 * - Sender name
 * - Message content
 * - Timestamp (relative format)
 * - Visual distinction for user/agent/own messages
 *
 * Phase 3 Alpha - Task 9
 */

import { Box, Text } from "@chakra-ui/react";

import type { MessageViewModel } from "@/services/roomService";

interface MessageProps {
  message: MessageViewModel;
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

const Message = ({ message }: MessageProps) => {
  return (
    <Box
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
    >
      {/* Sender name */}
      <Text fontSize="xs" opacity={0.8} mb={1} fontWeight="medium">
        {message.sender_name}
      </Text>

      {/* Message content */}
      <Text whiteSpace="pre-wrap">{message.content}</Text>

      {/* Timestamp */}
      <Text fontSize="xs" opacity={0.6} mt={1}>
        {formatTimestamp(message.created_at)}
      </Text>
    </Box>
  );
};

export default Message;
