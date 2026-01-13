/**
 * PinnedMessagesSection Component
 *
 * Dedicated section displaying pinned messages at top of message list.
 * Visually distinct with yellow theme and pin icon.
 *
 * Features:
 * - Shows count of pinned messages
 * - Returns null if no pinned messages (conditionally rendered)
 * - Dark mode support
 * - Reuses Message component for consistent styling
 *
 * Phase 5 - Message Management Features
 */

import type { MessageViewModel } from "@/services/roomService"
import { Box, HStack, Icon, Text, VStack } from "@chakra-ui/react"
import { FaThumbtack } from "react-icons/fa"
import Message from "./Message"

interface PinnedMessagesSectionProps {
  /** Pinned messages to display */
  messages: MessageViewModel[]
}

/**
 * PinnedMessagesSection - Display area for pinned messages
 *
 * Shows pinned messages in a highlighted section at top of list.
 * Returns null if no messages are pinned.
 *
 * @param messages - Array of pinned messages
 *
 * @example
 * ```tsx
 * const pinnedMessages = messages.filter(m => m.is_pinned)
 *
 * {pinnedMessages.length > 0 && (
 *   <PinnedMessagesSection messages={pinnedMessages} />
 * )}
 * ```
 */
const PinnedMessagesSection = ({ messages }: PinnedMessagesSectionProps) => {
  // Don't render if no pinned messages
  if (messages.length === 0) {
    return null
  }

  return (
    <Box
      bg="yellow.50"
      borderLeft="4px solid"
      borderColor="yellow.400"
      p={4}
      borderRadius="md"
      _dark={{
        bg: "yellow.900",
        borderColor: "yellow.600",
      }}
    >
      {/* Header with pin icon and count */}
      <HStack mb={3}>
        <Icon as={FaThumbtack} color="yellow.600" />
        <Text
          fontWeight="bold"
          color="yellow.800"
          _dark={{ color: "yellow.200" }}
        >
          Pinned Messages ({messages.length})
        </Text>
      </HStack>

      {/* Pinned message list */}
      <VStack align="stretch" gap={2}>
        {messages.map((message) => (
          <Message key={message.message_id} message={message} />
        ))}
      </VStack>
    </Box>
  )
}

export default PinnedMessagesSection
