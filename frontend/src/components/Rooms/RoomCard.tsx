/**
 * RoomCard Component
 *
 * Displays individual room summary with:
 * - Room title
 * - Last activity timestamp (relative)
 * - Hover and click interactions
 *
 * Phase 3 Alpha - Task 5
 */

import { Flex, Text } from "@chakra-ui/react";
import { FiMessageSquare } from "react-icons/fi";

import type { RoomViewModel } from "@/services/roomService";

interface RoomCardProps {
  room: RoomViewModel;
  onClick: () => void;
  isActive?: boolean;
}

/**
 * Format a date as relative time
 * Returns: "Just now", "5 minutes ago", "2 hours ago", "3 days ago"
 */
const formatRelativeTime = (date: Date): string => {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? "s" : ""} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
  return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
};

const RoomCard = ({ room, onClick, isActive = false }: RoomCardProps) => {
  return (
    <Flex
      direction="column"
      p={4}
      borderWidth={1}
      borderRadius="md"
      cursor="pointer"
      onClick={onClick}
      borderColor={isActive ? "blue.500" : "gray.200"}
      bg={isActive ? "blue.50" : "transparent"}
      _hover={{
        bg: isActive ? "blue.50" : "gray.50",
        borderColor: "blue.500",
        _dark: {
          bg: isActive ? "blue.900" : "gray.800",
        },
      }}
      _dark={{
        borderColor: isActive ? "blue.500" : "gray.700",
        bg: isActive ? "blue.900" : "transparent",
      }}
      transition="all 0.2s"
    >
      <Flex align="center" gap={2} mb={2}>
        <FiMessageSquare />
        <Text fontWeight="bold" fontSize="lg">
          {room.title || "Untitled Room"}
        </Text>
      </Flex>

      <Text fontSize="sm" color="gray.600" _dark={{ color: "gray.400" }}>
        Last activity: {formatRelativeTime(room.last_activity)}
      </Text>
    </Flex>
  );
};

export default RoomCard;
