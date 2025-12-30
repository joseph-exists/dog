/**
 * Room List Route
 *
 * Displays all rooms accessible to the current user.
 * Allows navigation to individual room views.
 *
 * Phase 3 Alpha - Tasks 2, 7
 */

import {
  Container,
  EmptyState,
  Flex,
  Heading,
  Spinner,
  VStack,
} from "@chakra-ui/react";
import { useQuery } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";

import RoomList from "@/components/Rooms/RoomList";
import AddRoom from "@/components/Rooms/AddRoom";
import { RoomService } from "@/services/roomService";

export const Route = createFileRoute("/_layout/rooms")({
  component: Rooms,
});

function Rooms() {
  const navigate = useNavigate();

  // Fetch rooms using RoomService
  const { data: rooms, isLoading, error } = useQuery({
    queryKey: ["rooms"],
    queryFn: () => RoomService.listRooms(),
  });

  // Handle room selection
  const handleRoomSelect = (roomId: string) => {
    navigate({ to: `/room/${roomId}` });
  };

  // Loading state
  if (isLoading) {
    return (
      <Container maxW="full">
        <Flex justify="center" align="center" minH="50vh">
          <Spinner size="xl" />
        </Flex>
      </Container>
    );
  }

  // Error state
  if (error) {
    return (
      <Container maxW="full">
        <EmptyState.Root>
          <EmptyState.Content>
            <VStack textAlign="center">
              <EmptyState.Title>Error loading rooms</EmptyState.Title>
              <EmptyState.Description>
                {error instanceof Error ? error.message : "Unknown error occurred"}
              </EmptyState.Description>
            </VStack>
          </EmptyState.Content>
        </EmptyState.Root>
      </Container>
    );
  }

  // Room list display
  return (
    <Container maxW="full">
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg">Rooms</Heading>
        <AddRoom />
      </Flex>

      <RoomList
        rooms={rooms || []}
        onRoomSelect={handleRoomSelect}
        isLoading={isLoading}
      />
    </Container>
  );
}
