/**
 * RoomHeader Component
 *
 * Displays room metadata:
 * - Room title
 * - Participant count
 * - Agent count
 * - User role badge
 *
 * Phase 3 Alpha - Task 11
 */

import { Box, Flex, Text, VStack } from "@chakra-ui/react";
import AddParticipantDialog from './AddParticipantDialog';
import { RoomActionsMenu } from '@/components/Common/RoomsActionsMenu';
import type { RoomViewModel, ParticipantViewModel } from "@/services/roomService";

interface RoomHeaderProps {
  room: RoomViewModel | null | undefined;
  participants: ParticipantViewModel[];
  activeAgents: ParticipantViewModel[];
  currentUserRole: string | null;
  onAddParticipant: (participantId: string, type: 'user' | 'agent') => Promise<void>;
  onUpdateRoom?: (data: { title: string }) => Promise<void>;
  onDeleteRoom?: () => Promise<void>;
}

const RoomHeader = ({
  room,
  participants,
  activeAgents,
  currentUserRole,
  onAddParticipant,
  onUpdateRoom,
  onDeleteRoom,
}: RoomHeaderProps) => {
  return (
    <Box
      p={4}
      borderBottomWidth={1}
      borderColor="gray.200"
      bg="white"
      _dark={{ borderColor: "gray.700", bg: "gray.900" }}
    >
      <Flex justify="space-between" align="center">
        <VStack align="start" gap={1}>
          {/* Room title */}
          <Text fontSize="lg" fontWeight="bold">
            {room?.title || "Untitled Room"}
          </Text>

          {/* Participant and agent counts */}
          <Text fontSize="sm">
            {participants.length} participant{participants.length !== 1 ? "s" : ""}
            {activeAgents.length > 0 &&
              ` • ${activeAgents.length} agent${activeAgents.length !== 1 ? "s" : ""}`}
          </Text>
        </VStack>

        <Flex align="center" gap={2}>
          {/* Owner actions */}
          {currentUserRole === "owner" && room && (
            <>
              <AddParticipantDialog
                roomId={room.room_id}
                currentParticipants={participants.map(p => p.participant_id)}
                onAdd={onAddParticipant}
              />
              {onUpdateRoom && (
                <RoomActionsMenu
                  room={room}
                  onUpdate={onUpdateRoom}
                  onDelete={onDeleteRoom}
                />
              )}
            </>
          )}

          {/* User role badge */}
          {currentUserRole && (
            <Text
              fontSize="xs"
              px={2}
              py={1}
              borderRadius="md"
              bg={currentUserRole === "owner" ? "blue.100" : "gray.100"}
              color={currentUserRole === "owner" ? "blue.800" : "gray.800"}
              _dark={{
                bg: currentUserRole === "owner" ? "blue.900" : "gray.800",
                color: currentUserRole === "owner" ? "blue.100" : "gray.100",
              }}
              fontWeight="medium"
            >
              {currentUserRole.toUpperCase()}
            </Text>
          )}
        </Flex>
      </Flex>
    </Box>
  );
};

export default RoomHeader;
