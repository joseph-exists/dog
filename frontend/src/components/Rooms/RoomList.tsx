/**
 * RoomList Component
 *
 * Displays a list of rooms with:
 * - Grid layout (responsive)
 * - Empty state handling
 * - Room selection via click
 *
 * Phase 3 Alpha - Task 6
 */

import { EmptyState, SimpleGrid, VStack } from "@chakra-ui/react";
import { FiMessageSquare } from "react-icons/fi";

import type { RoomViewModel } from "@/services/roomService";
import RoomCard from "./RoomCard";

interface RoomListProps {
  rooms: RoomViewModel[];
  onRoomSelect: (roomId: string) => void;
  isLoading?: boolean;
  activeRoomId?: string;
}

const RoomList = ({
  rooms,
  onRoomSelect,
  isLoading = false,
  activeRoomId,
}: RoomListProps) => {
  // Empty state
  if (!isLoading && (!rooms || rooms.length === 0)) {
    return (
      <EmptyState.Root>
        <EmptyState.Content>
          <EmptyState.Indicator>
            <FiMessageSquare />
          </EmptyState.Indicator>
          <VStack textAlign="center">
            <EmptyState.Title>No rooms available</EmptyState.Title>
            <EmptyState.Description>
              You don't have access to any rooms yet.
            </EmptyState.Description>
          </VStack>
        </EmptyState.Content>
      </EmptyState.Root>
    );
  }

  // Room grid
  return (
    <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={4}>
      {rooms.map((room) => (
        <RoomCard
          key={room.room_id}
          room={room}
          onClick={() => onRoomSelect(room.room_id)}
          isActive={activeRoomId === room.room_id}
        />
      ))}
    </SimpleGrid>
  );
};

export default RoomList;
