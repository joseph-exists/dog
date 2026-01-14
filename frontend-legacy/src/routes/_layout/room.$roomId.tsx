/**
 * Individual Room Route
 *
 * Displays a single room with:
 * - Room title and metadata (RoomHeader)
 * - Message history (MessageList)
 * - Message input (MessageInput)
 * - Participant list (ParticipantList)
 * - Phase 5: Message management (edit, pin, delete, toggle context)
 *
 * Phase 3 Alpha - Tasks 3, 12, 15, 19 | Phase 5 - Message Management
 */

import {
  Box,
  Container,
  EmptyState,
  Flex,
  Spinner,
  VStack,
} from "@chakra-ui/react"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useEffect, useState } from "react"

import EditDrawer from "@/components/Common/EditDrawer"
import MessageInput from "@/components/Rooms/MessageInput"
import MessageList from "@/components/Rooms/MessageList"
import ParticipantList from "@/components/Rooms/ParticipantList"
import RoomHeader from "@/components/Rooms/RoomHeader"
import useCustomToast from "@/hooks/useCustomToast"
import { useRoom } from "@/hooks/useRoom"
import { useRoomStream } from "@/hooks/useRoomStream"
import type { MessageViewModel } from "@/services/roomService"

export const Route = createFileRoute("/_layout/room/$roomId")({
  component: RoomView,
})

function RoomView() {
  const { roomId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccessToast } = useCustomToast()

  // Phase 5: Edit drawer state
  const [isEditDrawerOpen, setIsEditDrawerOpen] = useState(false)
  const [editingMessage, setEditingMessage] = useState<MessageViewModel | null>(
    null,
  )

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
    // Phase 5: Message management
    editMessage,
    isEditing,
    pinMessage,
    unpinMessage,
    toggleContext,
    deleteMessage,
  } = useRoom(roomId, {
    enablePolling: true,
    onDeleteSuccess: () => {
      // Navigate to rooms list after successful deletion
      navigate({ to: "/rooms" })
    },
  })

  // Single WebSocket connection for the entire room view
  // This hook is called ONCE per room and shared across child components
  const {
    isConnected,
    sendMessage: sendViaWebSocket,
    streamingMessage,
  } = useRoomStream(roomId)

  // Handle authorization errors (403 - not a participant)
  useEffect(() => {
    if (roomError && "status" in roomError && roomError.status === 403) {
      navigate({ to: "/rooms" })
    }
  }, [roomError, navigate])

  // Handle agent toggle
  const handleToggleAgent = async (agentId: string, activate: boolean) => {
    if (activate) {
      await addParticipant(agentId, "agent")
    } else {
      await removeParticipant(agentId)
    }
  }

  // Phase 5: Message management handlers
  const handleEditMessage = (message: MessageViewModel) => {
    setEditingMessage(message)
    setIsEditDrawerOpen(true)
  }

  const handleSaveEdit = async (content: string) => {
    if (!editingMessage) return
    await editMessage(editingMessage.message_id, content)
    showSuccessToast("Message updated successfully")
    setIsEditDrawerOpen(false)
    setEditingMessage(null)
  }

  const handlePinMessage = async (messageId: string) => {
    await pinMessage(messageId)
    showSuccessToast("Message pinned")
  }

  const handleUnpinMessage = async (messageId: string) => {
    await unpinMessage(messageId)
    showSuccessToast("Message unpinned")
  }

  const handleToggleContext = async (messageId: string, active: boolean) => {
    await toggleContext(messageId, active)
    showSuccessToast(active ? "Added to context" : "Removed from context")
  }

  const handleDeleteMessage = async (messageId: string) => {
    // TODO: Add confirmation dialog
    if (window.confirm("Are you sure you want to delete this message?")) {
      await deleteMessage(messageId)
      showSuccessToast("Message deleted")
    }
  }

  // Loading state - show spinner while initial data loads
  if (isLoadingRoom || isLoadingMessages) {
    return (
      <Container maxW="full">
        <Flex justify="center" align="center" minH="50vh">
          <Spinner size="xl" />
        </Flex>
      </Container>
    )
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
    )
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
              roomId={roomId}
              messages={messages}
              hasMore={hasMoreMessages}
              onLoadMore={loadMoreMessages}
              isLoadingMore={isLoadingMoreMessages}
              isLoading={isLoadingMessages}
              streamingMessage={streamingMessage}
              room={room}
              onEditMessage={handleEditMessage}
              onPinMessage={handlePinMessage}
              onUnpinMessage={handleUnpinMessage}
              onToggleContext={handleToggleContext}
              onDeleteMessage={handleDeleteMessage}
            />
          </Box>

          {/* Message Input */}
          <MessageInput
            roomId={roomId}
            onSendMessage={sendMessage}
            isSending={isSending}
            isConnected={isConnected}
            sendViaWebSocket={sendViaWebSocket}
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

      {/* Phase 5: Edit Message Drawer */}
      {editingMessage && (
        <EditDrawer
          isOpen={isEditDrawerOpen}
          onClose={() => {
            setIsEditDrawerOpen(false)
            setEditingMessage(null)
          }}
          onSave={handleSaveEdit}
          initialContent={editingMessage.content}
          title="Edit Message"
          description="Changes will be visible to all participants."
          isSaving={isEditing}
        />
      )}
    </Container>
  )
}
