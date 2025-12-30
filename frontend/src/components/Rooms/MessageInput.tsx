/**
 * MessageInput Component
 *
 * Text input for sending messages with:
 * - Controlled input with local state
 * - Send on Enter key
 * - Clear input after send
 * - Loading state while sending
 * - Validation (no empty messages)
 *
 * Phase 3 Alpha - Task 14
 */

import { useState } from "react";
import { Box, Flex, IconButton, Input } from "@chakra-ui/react";
import { FiSend } from "react-icons/fi";

interface MessageInputProps {
  onSendMessage: (content: string) => Promise<void>;
  isSending: boolean;
  disabled?: boolean;
}

const MessageInput = ({
  onSendMessage,
  isSending,
  disabled = false,
}: MessageInputProps) => {
  const [content, setContent] = useState("");

  const handleSend = async () => {
    if (!content.trim() || isSending || disabled) return;

    try {
      await onSendMessage(content.trim());
      setContent(""); // Clear on success
    } catch (error) {
      // Error handling is done by the parent component
      console.error("Failed to send message:", error);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Box
      p={4}
      borderTopWidth={1}
      borderColor="gray.200"
      bg="white"
      _dark={{ borderColor: "gray.700", bg: "gray.900" }}
    >
      <Flex gap={2}>
        <Input
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message..."
          disabled={disabled || isSending}
          flex={1}
        />
        <IconButton
          aria-label="Send message"
          onClick={handleSend}
          disabled={!content.trim() || isSending || disabled}
          loading={isSending}
          colorPalette="blue"
        >
          <FiSend />
        </IconButton>
      </Flex>
    </Box>
  );
};

export default MessageInput;
