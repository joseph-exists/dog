/**
 * Unified Room Route
 *
 * New room implementation with multi-panel support.
 * Panels are dynamically configured via useRoomPanels hook.
 */

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { AlertCircle, Loader2 } from "lucide-react"
import type React from "react"
import { useEffect, useState } from "react"

import EditDrawer from "@/components/Common/EditDrawer"
import {
  A2UIPanel,
  AgentPanel,
  CanvasPanel,
  ChatPanel,
  DebugPanel,
  type PanelConfig,
  ParticipantPanel,
  RoomShell,
  StoryEditorPanel,
  StoryPanel,
} from "@/components/Room"
import type { Participant } from "@/components/Room/primitives/ParticipantStack"
import RoomDebugPanel from "@/components/Rooms/RoomDebugPanel"
import useCustomToast from "@/hooks/useCustomToast"
import { useRoom } from "@/hooks/useRoom"
import { useRoomPanels } from "@/hooks/useRoomPanels"
import { useRoomStream } from "@/hooks/useRoomStream"
import { AgentService, type AgentViewModel } from "@/services/agentService"
import { getPanelDisplayName } from "@/services/panelService"
import type {
  MessageViewModel,
  ParticipantViewModel,
} from "@/services/roomService"

export const Route = createFileRoute("/_layout/r/$roomId")({
  component: RoomView,
})

/**
 * Convert ParticipantViewModel to Participant for Room components
 */
function toParticipant(p: ParticipantViewModel): Participant {
  return {
    id: p.participant_id,
    name: p.display_name,
    type: p.participant_type,
    role: p.role,
    isActive: p.is_active,
  }
}

/**
 * Convert AgentViewModel to AgentData format
 */
function toAgentData(a: AgentViewModel) {
  return {
    id: a.id,
    name: a.name,
    description: a.description,
  }
}

function RoomView() {
  const { roomId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccessToast } = useCustomToast()

  // Edit drawer state
  const [isEditDrawerOpen, setIsEditDrawerOpen] = useState(false)
  const [editingMessage, setEditingMessage] = useState<MessageViewModel | null>(
    null,
  )

  // Debug panel overlay state (separate from panel config)
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
    isConnected,
    sendMessage: sendViaWebSocket,
    streamingMessage,
  } = useRoomStream(roomId)

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
    hasMoreMessages,
    loadMoreMessages,
    isLoadingMoreMessages,
    sendMessage,
    isSending,
    addParticipant,
    removeParticipant,
    deleteRoom,
    editMessage,
    isEditing,
    pinMessage,
    unpinMessage,
    toggleContext,
    deleteMessage,
  } = useRoom(roomId, {
    includeInternalMessages: showInternalMessages,
    onDeleteSuccess: () => {
      navigate({ to: "/rooms" })
    },
  })

  // Panel configuration from backend
  const {
    panels: panelConfigs,
    // panelSource can be used to display where config came from: "user_override" | "room_defaults" | "type_defaults"
    isLoading: isLoadingPanels,
  } = useRoomPanels(roomId, {
    enabled: !isLoadingRoom,
  })

  // Handle authorization errors
  useEffect(() => {
    if (
      roomError &&
      "status" in roomError &&
      (roomError as { status: number }).status === 403
    ) {
      navigate({ to: "/rooms" })
    }
  }, [roomError, navigate])

  // Convert data for components
  const roomParticipants: Participant[] = participants.map(toParticipant)
  const activeUsers = participants.filter((p) => p.participant_type === "user")
  const roomAgentsAsAgentData = activeAgents.map((p) => ({
    id: p.participant_id,
    name: p.display_name,
    description: null,
    participationMode: "on_mention" as const,
    isEnabled: p.is_active,
  }))
  const availableAgentsAsAgentData = (availableAgentsData?.agents || []).map(
    toAgentData,
  )
  const existingAgentIds = activeAgents.map((a) => a.participant_id)

  // Handlers
  const handleAddAgent = async (agent: { id: string; name: string }) => {
    await addParticipant(agent.id, "agent")
    showSuccessToast(`Added ${agent.name} to the room`)
  }

  const handleAddMultipleAgents = async (
    agents: { id: string; name: string }[],
  ) => {
    for (const agent of agents) {
      await addParticipant(agent.id, "agent")
    }
    showSuccessToast(`Added ${agents.length} agent(s) to the room`)
  }

  const handleRemoveAgent = async (agent: { id: string; name: string }) => {
    await removeParticipant(agent.id)
    showSuccessToast(`Removed ${agent.name} from the room`)
  }

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

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href)
    showSuccessToast("Link copied to clipboard")
  }

  const handleDeleteRoom = async () => {
    if (window.confirm("Are you sure you want to delete this room?")) {
      await deleteRoom()
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

  const canManage = currentUserRole === "owner"

  // ==========================================================================
  // Panel component registry - maps panel kinds to render functions
  // ==========================================================================
  const panelComponents: Record<string, () => React.ReactNode> = {
    chat: () => (
      <ChatPanel
        roomId={roomId}
        messages={messages}
        hasMore={hasMoreMessages}
        onLoadMore={loadMoreMessages}
        isLoadingMore={isLoadingMoreMessages}
        isLoading={isLoadingMessages}
        streamingMessage={streamingMessage}
        isRoomOwner={canManage}
        includeInternalMessages={showInternalMessages}
        onToggleInternalMessages={setShowInternalMessages}
        onSendMessage={sendMessage}
        isSending={isSending}
        isConnected={isConnected}
        sendViaWebSocket={sendViaWebSocket}
        onEditMessage={handleEditMessage}
        onPinMessage={handlePinMessage}
        onUnpinMessage={handleUnpinMessage}
        onToggleContext={handleToggleContext}
        onDeleteMessage={handleDeleteMessage}
      />
    ),
    agentPanel: () => (
      <AgentPanel
        roomAgents={roomAgentsAsAgentData}
        availableAgents={availableAgentsAsAgentData}
        existingAgentIds={existingAgentIds}
        onAddAgent={handleAddAgent}
        onAddMultipleAgents={handleAddMultipleAgents}
        onRemoveAgent={handleRemoveAgent}
        canManage={canManage}
        isLoading={isLoadingParticipants || isLoadingAvailable}
      />
    ),
    debug: () => (
      <DebugPanel
        messages={messages}
        streamingMessage={streamingMessage}
        isConnected={isConnected}
        activeAgents={activeAgents}
        showInternalMessages={showInternalMessages}
        onToggleInternalMessages={setShowInternalMessages}
      />
    ),
    storyEditor: () => (
      <StoryEditorPanel
        storyId={room?.story_id || ""}
        onNavigateToStories={() => navigate({ to: "/stories" })}
      />
    ),
    storyRuntime: () => (
      <StoryPanel
        roomId={roomId}
        roomTitle={room?.title ?? null}
        roomStoryId={room?.story_id ?? null}
        canWrite={canManage}
      />
    ),
    canvas: () => <CanvasPanel />,
    a2ui: () => <A2UIPanel roomId={roomId} />,
    participantPanel: () => (
      <ParticipantPanel
        activeUsers={activeUsers}
        activeAgents={activeAgents}
        isLoading={isLoadingParticipants}
        currentUserRole={currentUserRole}
        onRemoveParticipant={removeParticipant}
        onToggleAgent={async (agentId, activate) => {
          if (activate) {
            await addParticipant(agentId, "agent")
          } else {
            await removeParticipant(agentId)
          }
        }}
      />
    ),
  }

  // Build panels from configuration
  const panels: PanelConfig[] = panelConfigs.map((config) => ({
    id: config.id,
    kind: config.kind,
    prominence: config.prominence,
    title: getPanelDisplayName(
      config.kind as
        | "chat"
        | "storyEditor"
        | "storyRuntime"
        | "agentPanel"
        | "debug"
        | "canvas"
        | "a2ui"
        | "participantPanel",
    ),
    render: panelComponents[config.kind] || (() => null),
  }))

  // Fallback if no panels configured (shouldn't happen with type_defaults)
  if (panels.length === 0 && !isLoadingPanels) {
    panels.push(
      {
        id: "chat",
        kind: "chat",
        prominence: "primary",
        title: "Chat",
        render: panelComponents.chat,
      },
      {
        id: "agents",
        kind: "agentPanel",
        prominence: "auxiliary",
        title: "Agents",
        render: panelComponents.agentPanel,
      },
    )
  }

  return (
    <div className="h-[calc(100vh-8rem)] flex">
      <div className="flex-1 min-w-0">
        <RoomShell
          roomId={roomId}
          title={room?.title || "Untitled Room"}
          type="chat"
          participants={roomParticipants}
          panels={panels}
          canEdit={canManage}
          onCopyLink={handleCopyLink}
          onDelete={canManage ? handleDeleteRoom : undefined}
          showDebugPanel={showDebugPanel}
          onToggleDebugPanel={() => setShowDebugPanel(!showDebugPanel)}
          devModeEnabled={showInternalMessages}
        />
      </div>

      {/* Debug Panel Overlay (legacy, kept for quick access) */}
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
