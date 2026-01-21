/**
 * Individual Room Route
 *
 * Displays a single room with:
 * - Room header with metadata
 * - Message history with filters
 * - Message input
 * - Participant list sidebar
 * - Message management (edit, pin, delete, toggle context)
 */

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { AlertCircle, Loader2 } from "lucide-react"
import { useEffect, useState } from "react"
import type { ApiError } from "@/client"
import type { UIPageLayoutPreviewData } from "@/components/AgentUI/types"
import EditDrawer from "@/components/Common/EditDrawer"
import MessageInput from "@/components/Rooms/MessageInput"
import MessageList from "@/components/Rooms/MessageList"
import ParticipantList from "@/components/Rooms/ParticipantList"
import RoomDebugPanel from "@/components/Rooms/RoomDebugPanel"
import RoomHeader from "@/components/Rooms/RoomHeader"
import useCustomToast from "@/hooks/useCustomToast"
import { useRoom } from "@/hooks/useRoom"
import { useRoomStream } from "@/hooks/useRoomStream"
import { PageService } from "@/services/pageService"
import type { MessageViewModel } from "@/services/roomService"
import { handleError } from "@/utils"

/**
 * Validate agent layout preview payloads before saving.
 */
function isPageLayoutPreviewData(
  value: unknown,
): value is UIPageLayoutPreviewData {
  if (!value || typeof value !== "object") return false
  const record = value as Record<string, unknown>
  return (
    typeof record.entity_type === "string" &&
    typeof record.entity_id === "string" &&
    Array.isArray(record.layout_json)
  )
}

export const Route = createFileRoute("/_layout/room/$roomId")({
  component: RoomView,
})

function RoomView() {
  const { roomId } = Route.useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()

  // Edit drawer state
  const [isEditDrawerOpen, setIsEditDrawerOpen] = useState(false)
  const [editingMessage, setEditingMessage] = useState<MessageViewModel | null>(
    null,
  )

  // Debug panel state
  const [showDebugPanel, setShowDebugPanel] = useState(false)
  const [showInternalMessages, setShowInternalMessages] = useState(false)

  // Use the aggregate room hook
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
    editMessage,
    isEditing,
    pinMessage,
    unpinMessage,
    toggleContext,
    deleteMessage,
  } = useRoom(roomId, {
    enablePolling: true,
    includeInternalMessages: showInternalMessages,
    onDeleteSuccess: () => {
      navigate({ to: "/rooms" })
    },
  })

  // WebSocket connection for real-time updates
  const {
    isConnected,
    sendMessage: sendViaWebSocket,
    streamingMessage,
  } = useRoomStream(roomId)

  const saveLayoutMutation = useMutation({
    mutationFn: PageService.saveLayout,
    onSuccess: (layout) => {
      queryClient.invalidateQueries({
        queryKey: ["pages", layout.entityType, layout.entityId],
      })
      showSuccessToast("Page layout saved")
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err)
    },
  })

  const handleUiAction = async (action: string, message: MessageViewModel) => {
    if (action !== "page_layout.accept") return

    const preview = message.ui_components?.find(
      (component) => component.type === "page_layout_preview",
    )
    if (!preview || !isPageLayoutPreviewData(preview.data)) {
      showErrorToast("Missing or invalid layout preview")
      return
    }

    await saveLayoutMutation.mutateAsync({
      entityType: preview.data.entity_type,
      entityId: preview.data.entity_id,
      layout: preview.data.layout_json,
    })
  }

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

  // Message management handlers
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
    if (window.confirm("Are you sure you want to delete this message?")) {
      await deleteMessage(messageId)
      showSuccessToast("Message deleted")
    }
  }

  // Loading state
  if (isLoadingRoom || isLoadingMessages) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  // Error state
  if (roomError) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-destructive/10 p-4 mb-4">
          <AlertCircle className="h-8 w-8 text-destructive" />
        </div>
        <h3 className="text-lg font-semibold">Room not found</h3>
        <p className="text-muted-foreground">
          This room doesn't exist or you don't have access to it.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-100px)]">
      {/* Room Header */}
      <RoomHeader
        room={room}
        participants={participants}
        activeAgents={activeAgents}
        currentUserRole={currentUserRole}
        onAddParticipant={addParticipant}
        onUpdateRoom={updateRoom}
        onDeleteRoom={deleteRoom}
        showDebugPanel={showDebugPanel}
        onToggleDebugPanel={() => setShowDebugPanel(!showDebugPanel)}
        devModeEnabled={showInternalMessages}
      />

      {/* Main content area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Message area */}
        <div className="flex flex-col flex-1 overflow-hidden">
          <div className="flex-1 overflow-y-auto p-4">
            <MessageList
              roomId={roomId}
              messages={messages}
              hasMore={hasMoreMessages}
              onLoadMore={loadMoreMessages}
              isLoadingMore={isLoadingMoreMessages}
              isLoading={isLoadingMessages}
              streamingMessage={streamingMessage}
              isRoomOwner={currentUserRole === "owner"}
              includeInternalMessages={showInternalMessages}
              onToggleInternalMessages={setShowInternalMessages}
              onEditMessage={handleEditMessage}
              onPinMessage={handlePinMessage}
              onUnpinMessage={handleUnpinMessage}
              onToggleContext={handleToggleContext}
              onDeleteMessage={handleDeleteMessage}
              onUiAction={handleUiAction}
            />
          </div>

          {/* Message Input */}
          <MessageInput
            roomId={roomId}
            onSendMessage={sendMessage}
            isSending={isSending}
            isConnected={isConnected}
            sendViaWebSocket={sendViaWebSocket}
          />
        </div>

        {/* Participant sidebar */}
        <div className="w-64 border-l border-border">
          <ParticipantList
            activeUsers={activeUsers}
            activeAgents={activeAgents}
            isLoading={isLoadingParticipants}
            currentUserRole={currentUserRole}
            onRemoveParticipant={removeParticipant}
            onToggleAgent={handleToggleAgent}
          />
        </div>

        {/* Debug Panel */}
        {showDebugPanel && (
          <RoomDebugPanel
            messages={messages}
            streamingMessage={streamingMessage}
            isConnected={isConnected}
            activeAgents={activeAgents}
            showInternalMessages={showInternalMessages}
            onToggleInternalMessages={setShowInternalMessages}
          />
        )}
      </div>

      {/* Edit Message Drawer */}
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
    </div>
  )
}
