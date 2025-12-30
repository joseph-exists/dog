/**
 * MessageInput Component
 *
 * Text input for sending messages with:
 * - Controlled input with local state
 * - Send on Enter key
 * - Clear input after send
 * - Loading state while sending
 * - Validation (no empty messages)
 * - Phase 4: WebSocket streaming support with REST API fallback
 *
 */

import { useState } from "react";
import { Box, Flex, IconButton, Input } from "@chakra-ui/react";
import { FiSend } from "react-icons/fi";

interface MessageInputProps {
  roomId: string;
  onSendMessage: (content: string) => Promise<void>;
  isSending: boolean;
  disabled?: boolean;
  // Phase 4: WebSocket props (passed from parent to avoid multiple connections)
  isConnected: boolean;
  sendViaWebSocket: (content: string) => void;
}

const MessageInput = ({
  // roomId,
  onSendMessage,
  isSending,
  disabled = false,
  isConnected,
  sendViaWebSocket,
}: MessageInputProps) => {
  const [content, setContent] = useState("");

  const handleSend = async () => {
    if (!content.trim() || isSending || disabled) return;

    try {
      // Phase 4: Prefer WebSocket if connected, fallback to REST API
      if (isConnected) {
        sendViaWebSocket(content.trim());
        setContent(""); // Clear immediately for WebSocket (optimistic)
      } else {
        // Fallback to REST API (Phase 1-3 behavior)
        await onSendMessage(content.trim());
        setContent(""); // Clear on success
      }
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
          placeholder={
            isConnected
              ? "Type a message..."
              : "Type a message... (offline)"
          }
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
