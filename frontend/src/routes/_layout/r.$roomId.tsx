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
import { AgentsService } from "@/client/sdk.gen"
import type { UserAgentConfigPublic } from "@/client/types.gen"
import EditDrawer from "@/components/Common/EditDrawer"
import {
  A2UIPanel,
  CanvasPanel,
  ChatPanel,
  DebugPanel,
  type PanelConfig,
  ParticipantPanel,
  RoomShell,
  StoryEditorPanel,
  StoryPanel,
  StoryPlayerPanel,
} from "@/components/Room"
import RoomDebugPanel from "@/components/Room/panels/RoomDebugPanel"
import type { Participant } from "@/components/Room/primitives/ParticipantStack"
import { showSuccessToast } from "@/hooks/useCustomToast"
import { useRoom } from "@/hooks/useRoom"
import { useRoomPanels } from "@/hooks/useRoomPanels"
import { useRoomStream } from "@/hooks/useRoomStream"
import { getPanelDisplayName } from "@/services/panelService"
import {
  type MessageViewModel,
  type ParticipantViewModel,
  RoomService,
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

function RoomView() {
  const { roomId } = Route.useParams()
  const navigate = useNavigate()

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
      queryFn: () => AgentsService.listAvailableAgents(),
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
  const availableAgents = (availableAgentsData?.data ||
    []) as UserAgentConfigPublic[]
  // All agents in the room (active + inactive) for panel display
  const allRoomAgents = participants.filter(
    (p) => p.participant_type === "agent",
  )
  const roomAgentsAsAgentData = allRoomAgents.map((p) => {
    // Cross-reference with full agent config for real metadata
    // participant_id for agents is the agent name, not UUID
    const agentConfig = availableAgents.find(
      (a) => a.id === p.participant_id || a.name === p.participant_id,
    )
    return {
      id: p.participant_id,
      name: p.display_name,
      description: agentConfig?.description ?? null,
      participation_mode: agentConfig?.participation_mode ?? "on_mention",
      scope: agentConfig?.scope ?? "system",
      is_coordinator: agentConfig?.is_coordinator ?? false,
      is_enabled: p.is_active,
    }
  })
  const existingAgentIds = allRoomAgents.map((p) => {
    // Resolve participant name to agent config UUID for downstream filtering
    const config = availableAgents.find(
      (a) => a.id === p.participant_id || a.name === p.participant_id,
    )
    return config?.id ?? p.participant_id
  })

  // Handlers - accept any object with id and name (compatible with both API types and simplified types)
  const handleAddAgent = async (agent: {
    id: string
    name?: string | null
  }) => {
    await addParticipant(agent.id, "agent")
    showSuccessToast(`Added ${agent.name ?? "Agent"} to the room`)
  }

  const handleAddMultipleAgents = async (
    agents: { id: string; name?: string | null }[],
  ) => {
    for (const agent of agents) {
      await addParticipant(agent.id, "agent")
    }
    showSuccessToast(`Added ${agents.length} agent(s) to the room`)
  }

  const handleRemoveAgent = async (agent: {
    id: string
    name?: string | null
  }) => {
    await removeParticipant(agent.id)
    showSuccessToast(`Removed ${agent.name ?? "Agent"} from the room`)
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

  /**
   * Handle AG-UI action button clicks.
   *
   * When a user clicks an action button rendered inside an agent message,
   * this sends the action to the backend which re-invokes the originating
   * agent with a trigger like "[UI Action: expand_details]". The agent's
   * response arrives as a new room message via WebSocket — no local state
   * update is needed.
   *
   * @param action - Action identifier from the clicked button
   * @param message - The MessageViewModel containing the button's source info
   */
  const handleUiAction = async (action: string, message: MessageViewModel) => {
    // message.message_id is the agent message UUID that emitted the action button.
    // The backend uses this to look up which agent originally sent it.
    await RoomService.sendUIAction(roomId, action, message.message_id)
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
        onUiAction={handleUiAction}
        availableAgents={availableAgents}
        existingAgentIds={existingAgentIds}
        onAddMultipleAgents={handleAddMultipleAgents}
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
    storyPlayer: () => (
      <StoryPlayerPanel
        storyId={room?.story_id || ""}
        onStoryEvent={(event) => {
          const text =
            event.type === "choice_made"
              ? `[Story: chose "${event.choiceText}" → ${event.nodeTitle}]`
              : event.type === "story_ended"
                ? `[Story: reached ending "${event.nodeTitle}"]`
                : event.type === "story_rewound"
                  ? `[Story: rewound to "${event.nodeTitle}"]`
                  : event.type === "story_restarted"
                    ? `[Story: restarted "${event.nodeTitle}"]`
                    : `[Story: started "${event.nodeTitle}"]`
          sendViaWebSocket(text)
        }}
      />
    ),
    canvas: () => <CanvasPanel />,
    a2ui: () => <A2UIPanel roomId={roomId} />,
    participantPanel: () => (
      <ParticipantPanel
        activeUsers={activeUsers}
        roomAgents={roomAgentsAsAgentData}
        availableAgents={availableAgents}
        existingAgentIds={existingAgentIds}
        onAddAgent={handleAddAgent}
        onRemoveAgent={handleRemoveAgent}
        onToggleAgent={async (agentId, activate) => {
          if (activate) {
            await addParticipant(agentId, "agent")
          } else {
            await removeParticipant(agentId)
          }
        }}
        onRemoveParticipant={removeParticipant}
        canManage={canManage}
        isLoading={isLoadingParticipants || isLoadingAvailable}
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
        | "storyPlayer"
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
        id: "participants",
        kind: "participantPanel",
        prominence: "auxiliary",
        title: "Participants",
        render: panelComponents.participantPanel,
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
