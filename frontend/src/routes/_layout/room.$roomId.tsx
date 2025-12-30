/**
 * Individual Room Route
 *
 * Displays a single room with:
 * - Room title and metadata (RoomHeader)
 * - Message history (MessageList)
 * - Message input (MessageInput)
 * - Participant list (ParticipantList)
 *
 * Phase 3 Alpha - Tasks 3, 12, 15, 19
 */

import {
  Box,
  Container,
  EmptyState,
  Flex,
  Spinner,
  VStack,
} from "@chakra-ui/react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";

import MessageInput from "@/components/Rooms/MessageInput";
import MessageList from "@/components/Rooms/MessageList";
import ParticipantList from "@/components/Rooms/ParticipantList";
import RoomHeader from "@/components/Rooms/RoomHeader";
import { useRoom } from "@/hooks/useRoom";

export const Route = createFileRoute("/_layout/room/$roomId")({
  component: RoomView,
});

function RoomView() {
  const { roomId } = Route.useParams();
  const navigate = useNavigate();

  // Use the aggregate room hook with polling enabled
  const {
    room,
    messages,
    participants,
    isLoadingRoom,
    isLoadingMessages,
    isLoadingParticipants,
    roomError,
    currentUserRole,
    activeAgents,
    activeUsers,
    hasMoreMessages,
    loadMoreMessages,
    isLoadingMoreMessages,
    sendMessage,
    isSending,
    addParticipant,
    removeParticipant,
    updateRoom,
    deleteRoom,
  } = useRoom(roomId, {
    enablePolling: true,
    onDeleteSuccess: () => {
      // Navigate to rooms list after successful deletion
      navigate({ to: '/rooms' });
    },
  });

  // Handle authorization errors (403 - not a participant)
  useEffect(() => {
    if (roomError && "status" in roomError && roomError.status === 403) {
      navigate({ to: "/rooms" });
    }
  }, [roomError, navigate]);

  // Handle agent toggle
  const handleToggleAgent = async (agentId: string, activate: boolean) => {
    if (activate) {
      await addParticipant(agentId, 'agent');
    } else {
      await removeParticipant(agentId);
    }
  };

  // Loading state - show spinner while initial data loads
  if (isLoadingRoom || isLoadingMessages) {
    return (
      <Container maxW="full">
        <Flex justify="center" align="center" minH="50vh">
          <Spinner size="xl" />
        </Flex>
      </Container>
    );
  }

  // Error state - room not found or other errors
  if (roomError) {
    return (
      <Container maxW="full">
        <EmptyState.Root>
          <EmptyState.Content>
            <VStack textAlign="center">
              <EmptyState.Title>Room not found</EmptyState.Title>
              <EmptyState.Description>
                This room doesn't exist or you don't have access to it.
              </EmptyState.Description>
            </VStack>
          </EmptyState.Content>
        </EmptyState.Root>
      </Container>
    );
  }

  // Main room view
  return (
    <Container maxW="full" h="calc(100vh - 100px)">
      <VStack h="full" gap={0} align="stretch">
        {/* Room Header */}
        <RoomHeader
          room={room}
          participants={participants}
          activeAgents={activeAgents}
          currentUserRole={currentUserRole}
          onAddParticipant={addParticipant}
          onUpdateRoom={updateRoom}
          onDeleteRoom={deleteRoom}
        />

        {/* Message Area */}
        <Flex flex={1} direction="column" overflow="hidden">
          <Box flex={1} overflowY="auto" p={4}>
            <MessageList
              messages={messages}
              hasMore={hasMoreMessages}
              onLoadMore={loadMoreMessages}
              isLoadingMore={isLoadingMoreMessages}
              isLoading={isLoadingMessages}
            />
          </Box>

          {/* Message Input */}
          <MessageInput
            onSendMessage={sendMessage}
            isSending={isSending}
          />
        </Flex>

        {/* Participant List */}
        <ParticipantList
          activeUsers={activeUsers}
          activeAgents={activeAgents}
          isLoading={isLoadingParticipants}
          currentUserRole={currentUserRole}
          onRemoveParticipant={removeParticipant}
          onToggleAgent={handleToggleAgent}
        />
      </VStack>
    </Container>
  );
}
