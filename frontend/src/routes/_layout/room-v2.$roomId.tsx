/**
 * Room V2 Route (Enhanced Layout)
 *
 * Enhanced room with integrated agent management panel.
 * Features:
 * - Tabbed sidebar (Participants | Agents)
 * - Sprint 2 agent components integration
 * - AgentQuickAdd and AgentPartyPicker for adding agents
 * - RoomAgentList for managing room agents
 */

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { AlertCircle, ArrowLeftRight, Loader2, UsersIcon } from "lucide-react"
import { useEffect, useState } from "react"
import {
  type AgentData,
  AgentPartyPicker,
  AgentQuickAdd,
  type ParticipationMode,
  RoomAgentList,
} from "@/components/Agents"
import EditDrawer from "@/components/Common/EditDrawer"
import MessageInput from "@/components/Rooms/MessageInput"
import MessageList from "@/components/Rooms/MessageList"
import RoomDebugPanel from "@/components/Rooms/RoomDebugPanel"
import RoomHeader from "@/components/Rooms/RoomHeader"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import useCustomToast from "@/hooks/useCustomToast"
import { useRoom } from "@/hooks/useRoom"
import { useRoomStream } from "@/hooks/useRoomStream"
import { AgentService, type AgentViewModel } from "@/services/agentService"
import type {
  MessageViewModel,
  ParticipantViewModel,
} from "@/services/roomService"

export const Route = createFileRoute("/_layout/room-v2/$roomId")({
  component: RoomViewV2,
})

/**
 * Convert ParticipantViewModel to AgentData for Sprint 2 components
 */
function participantToAgentData(p: ParticipantViewModel): AgentData {
  return {
    id: p.participant_id,
    name: p.display_name,
    description: null,
    participationMode: "on_mention" as ParticipationMode,
    isEnabled: p.is_active,
  }
}

/**
 * Convert AgentViewModel to AgentData
 * Maps agent configuration from the registry to the component's expected format
 */
function availableAgentToAgentData(a: AgentViewModel): AgentData {
  return {
    id: a.id,
    name: a.name,
    description: a.description,
  }
}

/**
 * Agent Sidebar Panel Component
 */
function AgentSidebarPanel({
  roomAgents,
  availableAgents,
  existingAgentIds,
  onAddAgent,
  onAddMultipleAgents,
  onRemoveAgent,
  canManage,
  isLoading,
}: {
  roomAgents: AgentData[]
  availableAgents: AgentData[]
  existingAgentIds: string[]
  onAddAgent: (agent: AgentData) => Promise<void>
  onAddMultipleAgents: (agents: AgentData[]) => Promise<void>
  onRemoveAgent: (agent: AgentData) => Promise<void>
  canManage: boolean
  isLoading: boolean
}) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-4">
        <Loader2 className="size-4 animate-spin" />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header with actions */}
      {canManage && (
        <div className="flex items-center gap-2 p-3 border-b">
          <AgentQuickAdd
            availableAgents={availableAgents}
            existingAgentIds={existingAgentIds}
            onAdd={onAddAgent}
            buttonSize="sm"
            className="flex-1"
          />
          <AgentPartyPicker
            availableAgents={availableAgents}
            existingAgentIds={existingAgentIds}
            onConfirm={onAddMultipleAgents}
            title="Add Agents to Room"
            description="Select multiple agents to add at once"
            trigger={
              <Button variant="outline" size="sm">
                <UsersIcon className="size-4" />
              </Button>
            }
          />
        </div>
      )}

      {/* Agent list */}
      <div className="flex-1 overflow-y-auto p-3">
        <RoomAgentList
          agents={roomAgents}
          onRemove={canManage ? onRemoveAgent : undefined}
          canRemove={canManage}
          variant="list"
        />
      </div>
    </div>
  )
}

/**
 * User Sidebar Panel Component
 */
function UserSidebarPanel({
  users,
  isLoading,
}: {
  users: ParticipantViewModel[]
  isLoading: boolean
}) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-4">
        <Loader2 className="size-4 animate-spin" />
      </div>
    )
  }

  if (users.length === 0) {
    return (
      <div className="p-4 text-center text-muted-foreground text-sm">
        No users in this room
      </div>
    )
  }

  return (
    <div className="p-3 space-y-2">
      {users.map((user) => (
        <div
          key={user.participant_id}
          className="flex items-center gap-2 p-2 rounded-md bg-muted/50"
        >
          <div className="size-8 rounded-full bg-primary/10 flex items-center justify-center text-xs font-medium">
            {user.display_name.charAt(0).toUpperCase()}
          </div>
          <span className="text-sm font-medium truncate">
            {user.display_name}
          </span>
        </div>
      ))}
    </div>
  )
}

function RoomViewV2() {
  const { roomId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccessToast } = useCustomToast()

  // Edit drawer state
  const [isEditDrawerOpen, setIsEditDrawerOpen] = useState(false)
  const [editingMessage, setEditingMessage] = useState<MessageViewModel | null>(
    null,
  )

  // Debug panel state
  const [showDebugPanel, setShowDebugPanel] = useState(false)
  const [showInternalMessages, setShowInternalMessages] = useState(false)

  // Fetch available agents
  const { data: availableAgentsData, isLoading: isLoadingAvailable } = useQuery(
    {
      queryKey: ["agents", "available"],
      queryFn: () => AgentService.listAvailableAgents(),
    },
  )

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

  // Handle authorization errors (403 - not a participant)
  useEffect(() => {
    if (roomError && "status" in roomError && roomError.status === 403) {
      navigate({ to: "/rooms" })
    }
  }, [roomError, navigate])

  // Convert data for Sprint 2 components
  const roomAgentsAsAgentData: AgentData[] = activeAgents.map(
    participantToAgentData,
  )
  const availableAgentsAsAgentData: AgentData[] = (
    availableAgentsData?.agents || []
  ).map(availableAgentToAgentData)
  const existingAgentIds = activeAgents.map((a) => a.participant_id)

  // Agent management handlers
  const handleAddAgent = async (agent: AgentData) => {
    await addParticipant(agent.id, "agent")
    showSuccessToast(`Added ${agent.name} to the room`)
  }

  const handleAddMultipleAgents = async (agents: AgentData[]) => {
    for (const agent of agents) {
      await addParticipant(agent.id, "agent")
    }
    showSuccessToast(`Added ${agents.length} agent(s) to the room`)
  }

  const handleRemoveAgent = async (agent: AgentData) => {
    await removeParticipant(agent.id)
    showSuccessToast(`Removed ${agent.name} from the room`)
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

  const canManageAgents = currentUserRole === "owner"

  return (
    <div className="flex flex-col h-[calc(100vh-100px)]">
      {/* Room Header with View Toggle */}
      <div className="flex items-center gap-2 border-b">
        <div className="flex-1">
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
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate({ to: "/r/$roomId", params: { roomId } })}
          className="mr-4"
        >
          <ArrowLeftRight className="h-4 w-4 mr-2" />
          New View
        </Button>
      </div>

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

        {/* Enhanced Sidebar with Tabs */}
        <div className="w-72 border-l border-border flex flex-col">
          <Tabs defaultValue="agents" className="flex flex-col h-full">
            <TabsList className="w-full rounded-none border-b">
              <TabsTrigger value="agents" className="flex-1">
                Agents ({activeAgents.length})
              </TabsTrigger>
              <TabsTrigger value="users" className="flex-1">
                Users ({activeUsers.length})
              </TabsTrigger>
            </TabsList>

            <TabsContent value="agents" className="flex-1 mt-0 overflow-hidden">
              <AgentSidebarPanel
                roomAgents={roomAgentsAsAgentData}
                availableAgents={availableAgentsAsAgentData}
                existingAgentIds={existingAgentIds}
                onAddAgent={handleAddAgent}
                onAddMultipleAgents={handleAddMultipleAgents}
                onRemoveAgent={handleRemoveAgent}
                canManage={canManageAgents}
                isLoading={isLoadingParticipants || isLoadingAvailable}
              />
            </TabsContent>

            <TabsContent value="users" className="flex-1 mt-0 overflow-hidden">
              <UserSidebarPanel
                users={activeUsers}
                isLoading={isLoadingParticipants}
              />
            </TabsContent>
          </Tabs>
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
