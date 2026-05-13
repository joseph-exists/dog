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
import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { AgentsService, StoriesService } from "@/client/sdk.gen"
import type { UserAgentConfigPublic } from "@/client/types.gen"
import EditDrawer from "@/components/Common/EditDrawer"
import type { PanelKind } from "@/components/Page/registry/panelTypes"
import { getUserRepoQueryOptions, renderRepoPanel } from "@/components/Repo"
import {
  createRepoPanelAdapter,
  createRoomArtifactRepoIdentity,
  type RepoPanelTarget,
} from "@/components/Repo/panels/dataSource"
import {
  A2UIPanel,
  CanvasPanel,
  ChatPanel,
  DebugPanel,
  type PanelConfig,
  ParticipantPanel,
  RoomShell,
  SoloStoryPlayerPanel,
  StoryEditorPanel,
  StoryPanel,
  WorkspaceConnectionsPanel,
} from "@/components/Room"
import { RoomPromptSettingsDialog } from "@/components/Room/Dialogs/RoomPromptSettingsDialog"
import RoomDebugPanel from "@/components/Room/panels/RoomDebugPanel"
import { PanelContainer } from "@/components/Room/primitives"
import type { Participant } from "@/components/Room/primitives/ParticipantStack"
import { showSuccessToast } from "@/hooks/useCustomToast"
import { useRoom } from "@/hooks/useRoom"
import { useRoomPanels } from "@/hooks/useRoomPanels"
import { useRoomRepoContext } from "@/hooks/useRoomRepoContext"
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
function asAgentParticipationMode(
  mode: string | null | undefined,
): "always" | "on_mention" | "manual" | undefined {
  return mode === "always" || mode === "on_mention" || mode === "manual"
    ? mode
    : undefined
}

function findAgentConfigForParticipant(
  participant: ParticipantViewModel,
  availableAgents: UserAgentConfigPublic[],
): UserAgentConfigPublic | undefined {
  if (participant.participant_type !== "agent") return undefined
  return availableAgents.find(
    (agent) =>
      agent.id === participant.participant_id ||
      agent.name === participant.participant_id ||
      agent.slug === participant.participant_id,
  )
}

function toParticipant(
  p: ParticipantViewModel,
  agentConfig?: UserAgentConfigPublic,
): Participant {
  const isAgent = p.participant_type === "agent"
  const agentName = agentConfig?.name ?? p.display_name
  return {
    id: p.participant_id,
    name: agentName,
    type: p.participant_type,
    role: p.role,
    isActive: p.is_active,
    agentProfileId: agentConfig?.id,
    agentCard: isAgent
      ? {
          id: p.participant_id,
          name: agentName,
          description: agentConfig?.description ?? null,
          model_name: agentConfig?.model_name ?? null,
          participation_mode: asAgentParticipationMode(
            agentConfig?.participation_mode,
          ),
          is_enabled: p.is_active,
          capabilities: agentConfig?.capabilities ?? undefined,
        }
      : undefined,
  }
}

function toRecord(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null
  return value as Record<string, unknown>
}

function getString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0
    ? value.trim()
    : null
}

function findRepoTargetInBindingSource(
  source: unknown,
  roomId: string,
): RepoPanelTarget | null {
  const record = toRecord(source)
  if (!record) return null

  const repoModel = getString(record.repo_model)
  const sourceModel = getString(record.source)
  const entityType = getString(record.entity_type)
  const entityIdSource = getString(record.entity_id_source)
  const repoId = getString(record.repo_id)
  if (
    repoModel === "shadow_repo" ||
    sourceModel === "shadow_repo" ||
    repoId === "room" ||
    (entityType === "room" && entityIdSource === "current_room")
  ) {
    return {
      model: "room_shadow_repo",
      roomId,
      repoId: "room",
    }
  }

  const direct =
    repoId ||
    getString(record.user_repo_id) ||
    getString(record.default_repo_id) ||
    getString(record.entity_id)
  if (direct) return { model: "user_repo", repoId: direct }

  const metadata = toRecord(record.metadata_json)
  if (metadata) {
    const metadataRepoId =
      getString(metadata.repo_id) ||
      getString(metadata.user_repo_id) ||
      getString(metadata.default_repo_id)
    if (metadataRepoId) return { model: "user_repo", repoId: metadataRepoId }
  }

  const presentation = toRecord(record.presentation)
  if (presentation) {
    const presentationRepoId =
      getString(presentation.repo_id) ||
      getString(presentation.user_repo_id) ||
      getString(presentation.default_repo_id)
    if (presentationRepoId) {
      return { model: "user_repo", repoId: presentationRepoId }
    }
  }

  return null
}

function resolveRepoTargetForRoomPanel(params: {
  roomId: string
  panelConfigJson: unknown
  panelEntityBinding: unknown
  roomData: unknown
  storyData: unknown
}): RepoPanelTarget | null {
  const panelConfigTarget = findRepoTargetInBindingSource(
    params.panelConfigJson,
    params.roomId,
  )
  if (panelConfigTarget) return panelConfigTarget

  const panelBindingTarget = findRepoTargetInBindingSource(
    params.panelEntityBinding,
    params.roomId,
  )
  if (panelBindingTarget) return panelBindingTarget

  const roomTarget = findRepoTargetInBindingSource(params.roomData, params.roomId)
  if (roomTarget) return roomTarget

  return findRepoTargetInBindingSource(params.storyData, params.roomId)
}

function RoomRepoPanel({
  roomId,
  panelId,
  panelKind,
  panelConfigJson,
  panelEntityBinding,
  roomData,
  storyData,
  panelSelections,
  setPanelSelection,
  getFileRoomContextState,
  onToggleFileRoomContext,
}: {
  roomId: string
  panelId: string
  panelKind: "repoExplorer" | "fileViewer"
  panelConfigJson: unknown
  panelEntityBinding: unknown
  roomData: unknown
  storyData: unknown
  panelSelections: Record<string, string | null>
  setPanelSelection: (selectionKey: string, path: string | null) => void
  getFileRoomContextState: (payload: {
    panelId: string
    repoId: string
    path: string
    ref: string
    isBinary: boolean
    hasContent: boolean
  }) => {
    included: boolean
    pending: boolean
    canToggle: boolean
    disabledReason?: string | null
  }
  onToggleFileRoomContext: (payload: {
    panelId: string
    repoId: string
    repoSlug: string
    path: string
    ref: string
    content: string
    contentType: string | null
    encoding: string | null
    sizeBytes: number | null
    isBinary: boolean
    isTruncated: boolean
    truncationReason: string | null
  }) => Promise<void>
}) {
  const repoTarget = resolveRepoTargetForRoomPanel({
    roomId,
    panelConfigJson,
    panelEntityBinding,
    roomData,
    storyData,
  })
  const adapter = useMemo(
    () => (repoTarget ? createRepoPanelAdapter(repoTarget) : null),
    [repoTarget],
  )
  const userRepoId = repoTarget?.model === "user_repo" ? repoTarget.repoId : null

  const {
    data: repo,
    isLoading: isLoadingRepo,
    error: repoError,
  } = useQuery({
    ...getUserRepoQueryOptions(userRepoId ?? ""),
    enabled: Boolean(userRepoId),
  })
  const resolvedRepo =
    repoTarget?.model === "room_shadow_repo"
      ? createRoomArtifactRepoIdentity({
          roomId,
          roomTitle: getString(toRecord(roomData)?.title),
        })
      : repo

  const lastSelectionEmitRef = useRef<string | null>(null)
  const lastOpenEmitRef = useRef<string | null>(null)
  const lastRefEmitRef = useRef<string | null>(null)

  const emitSelectionEvent = useCallback(
    (selectionKey: string, path: string | null) => {
      const activeRepoId = resolvedRepo?.id
      if (!activeRepoId) return
      const emitKey = `${panelId}|${activeRepoId}|${selectionKey}|${path ?? ""}`
      if (lastSelectionEmitRef.current === emitKey) return
      lastSelectionEmitRef.current = emitKey

      void RoomService.emitRepoEvent(roomId, {
        action: "selection",
        panel_id: panelId,
        selection_key: selectionKey,
        path,
        repo_id: repoTarget?.model === "user_repo" ? activeRepoId : null,
        repo_model: repoTarget?.model,
        repo_key: adapter?.targetKey ?? null,
      }).catch((error) => {
        console.error("Failed to emit repo selection event", error)
      })
    },
    [adapter?.targetKey, panelId, repoTarget?.model, resolvedRepo?.id, roomId],
  )

  const emitOpenEvent = useCallback(
    (path: string, ref: string) => {
      const activeRepoId = resolvedRepo?.id
      if (!activeRepoId) return
      const emitKey = `${panelId}|${activeRepoId}|${path}|${ref}`
      if (lastOpenEmitRef.current === emitKey) return
      lastOpenEmitRef.current = emitKey

      void RoomService.emitRepoEvent(roomId, {
        action: "open",
        panel_id: panelId,
        path,
        ref,
        repo_id: repoTarget?.model === "user_repo" ? activeRepoId : null,
        repo_model: repoTarget?.model,
        repo_key: adapter?.targetKey ?? null,
      }).catch((error) => {
        console.error("Failed to emit repo open event", error)
      })
    },
    [adapter?.targetKey, panelId, repoTarget?.model, resolvedRepo?.id, roomId],
  )

  const emitRefEvent = useCallback(
    (ref: string, path?: string | null) => {
      const activeRepoId = resolvedRepo?.id
      if (!activeRepoId) return
      const emitKey = `${panelId}|${activeRepoId}|${path ?? ""}|${ref}`
      if (lastRefEmitRef.current === emitKey) return
      lastRefEmitRef.current = emitKey

      void RoomService.emitRepoEvent(roomId, {
        action: "ref",
        panel_id: panelId,
        path,
        ref,
        repo_id: repoTarget?.model === "user_repo" ? activeRepoId : null,
        repo_model: repoTarget?.model,
        repo_key: adapter?.targetKey ?? null,
      }).catch((error) => {
        console.error("Failed to emit repo ref event", error)
      })
    },
    [adapter?.targetKey, panelId, repoTarget?.model, resolvedRepo?.id, roomId],
  )

  const handleSetPanelSelection = useCallback(
    (selectionKey: string, path: string | null) => {
      setPanelSelection(selectionKey, path)
      emitSelectionEvent(selectionKey, path)
    },
    [emitSelectionEvent, setPanelSelection],
  )

  const handleFileOpened = useCallback(
    ({ path, ref }: { path: string; ref: string }) => {
      emitOpenEvent(path, ref)
    },
    [emitOpenEvent],
  )

  const handleRefObserved = useCallback(
    ({ ref, path }: { ref: string; path?: string | null }) => {
      emitRefEvent(ref, path)
    },
    [emitRefEvent],
  )

  if (!repoTarget || !adapter) {
    return (
      <PanelContainer title="Repository Panel">
        <div className="p-4 text-sm text-destructive">
          No repository binding found for this panel. Set `repo_id` in panel
          config or provide a room/story default binding.
        </div>
      </PanelContainer>
    )
  }

  if (repoTarget.model === "user_repo" && isLoadingRepo) {
    return (
      <PanelContainer title="Repository Panel">
        <div className="p-4 text-sm text-muted-foreground">
          Loading repository...
        </div>
      </PanelContainer>
    )
  }

  if (repoTarget.model === "user_repo" && (repoError || !resolvedRepo)) {
    return (
      <PanelContainer title="Repository Panel">
        <div className="p-4 text-sm text-destructive">
          Failed to load bound repository for this panel.
        </div>
      </PanelContainer>
    )
  }

  if (!resolvedRepo) {
    return (
      <PanelContainer title="Repository Panel">
        <div className="p-4 text-sm text-destructive">
          Failed to resolve bound repository for this panel.
        </div>
      </PanelContainer>
    )
  }

  const capabilityEnvelope = resolvedRepo.capabilities
  if (
    !capabilityEnvelope ||
    typeof capabilityEnvelope.has_file_tree !== "boolean" ||
    typeof capabilityEnvelope.has_blob_content !== "boolean"
  ) {
    return (
      <PanelContainer title="Repository Panel">
        <div className="p-4 text-sm text-destructive">
          Repository capability flags are missing or invalid for this panel.
        </div>
      </PanelContainer>
    )
  }

  return renderRepoPanel(
    {
      id: panelId,
      kind: panelKind,
      config_json: toRecord(panelConfigJson) ?? null,
    },
    {
      repo: resolvedRepo,
      adapter,
      capabilities: {
        hasRepoIdentity: true,
        hasFileTree: capabilityEnvelope.has_file_tree,
        hasBlobContent: capabilityEnvelope.has_blob_content,
        hasCommitHistory: capabilityEnvelope.has_commit_history === true,
        hasSearch: capabilityEnvelope.has_search === true,
        hasManageAccess: true,
      },
      panelSelections,
      setPanelSelection: handleSetPanelSelection,
      onFileOpened: handleFileOpened,
      onRefObserved: handleRefObserved,
      getFileRoomContextState,
      onToggleFileRoomContext,
    },
  )
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
  const [isPromptSettingsOpen, setIsPromptSettingsOpen] = useState(false)
  const [panelSelections, setPanelSelections] = useState<
    Record<string, string | null>
  >({})

  const updatePanelSelection = useCallback(
    (selectionKey: string, path: string | null) => {
      setPanelSelections((current) => ({
        ...current,
        [selectionKey]: path,
      }))
    },
    [],
  )
  const selectedRepoFiles = useMemo(
    () =>
      Object.entries(panelSelections)
        .filter(([, path]) => typeof path === "string" && path.length > 0)
        .map(([selectionKey, path]) => ({
          selectionKey,
          path: path as string,
        })),
    [panelSelections],
  )

  // Fetch available agents
  const { data: availableAgentsData, isLoading: isLoadingAvailable } = useQuery(
    {
      queryKey: ["agents", "available"],
      queryFn: () => AgentsService.listAvailableAgents(),
    },
  )

  // Use the aggregate room hook
  const handleRoomStreamEvent = useCallback(
    (event: { event_type: string; payload: unknown }) => {
      if (
        event.event_type !== "room.repo.selection" &&
        event.event_type !== "room.repo.opened" &&
        event.event_type !== "room.repo.ref_changed"
      ) {
        return
      }

      const payload = toRecord(event.payload)
      if (!payload) return
      const selectionKey = getString(payload.selection_key)
      const path = getString(payload.path)
      if (!selectionKey) return
      updatePanelSelection(selectionKey, path)
    },
    [updatePanelSelection],
  )

  const {
    isConnected,
    sendMessage: sendViaWebSocket,
    streamingMessage,
  } = useRoomStream(roomId, { onEvent: handleRoomStreamEvent })

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
  const { data: storyBindingSource } = useQuery({
    queryKey: ["stories", room?.story_id, "room-repo-binding"],
    queryFn: () => StoriesService.readStory({ id: room?.story_id || "" }),
    enabled: Boolean(room?.story_id),
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

  const canManage = currentUserRole === "owner"
  const {
    repoContextFiles,
    getFileRoomContextState,
    toggleFileRoomContext,
    removeRepoContextFile,
  } = useRoomRepoContext(roomId, canManage)

  const availableAgents = (availableAgentsData?.data ||
    []) as UserAgentConfigPublic[]
  // Convert data for components
  const roomParticipants: Participant[] = participants.map((participant) =>
    toParticipant(
      participant,
      findAgentConfigForParticipant(participant, availableAgents),
    ),
  )
  const activeUsers = participants.filter((p) => p.participant_type === "user")
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
  const roomPromptAgents = allRoomAgents.map((p) => {
    const agentConfig = availableAgents.find(
      (a) => a.id === p.participant_id || a.name === p.participant_id,
    )
    return {
      id: agentConfig?.id ?? p.participant_id,
      slug: agentConfig?.slug ?? null,
      name: agentConfig?.name ?? p.display_name,
      description: agentConfig?.description ?? null,
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

  const handleAddUser = async (userId: string) => {
    await addParticipant(userId, "user")
    showSuccessToast("Added user to the room")
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
        roomId={roomId}
        messages={messages}
        streamingMessage={streamingMessage}
        isConnected={isConnected}
        activeAgents={activeAgents}
        showInternalMessages={showInternalMessages}
        onToggleInternalMessages={setShowInternalMessages}
        selectedRepoFiles={selectedRepoFiles}
        repoContextFiles={repoContextFiles}
        canManageRoomContext={canManage}
        onRemoveRepoContextFile={removeRepoContextFile}
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
      <SoloStoryPlayerPanel
        storyId={room?.story_id || ""}
        runtimeNotice="Local-only panel. Choices here do not read from or write to shared room runtime."
      />
    ),
    canvas: () => <CanvasPanel />,
    a2ui: () => <A2UIPanel roomId={roomId} />,
    workspaceConnections: () => <WorkspaceConnectionsPanel roomId={roomId} />,
    participantPanel: () => (
      <ParticipantPanel
        activeUsers={activeUsers}
        roomAgents={roomAgentsAsAgentData}
        availableAgents={availableAgents}
        existingAgentIds={existingAgentIds}
        onAddAgent={handleAddAgent}
        onAddUser={handleAddUser}
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
    title: getPanelDisplayName(config.kind as PanelKind),
    render:
      config.kind === "repoExplorer" || config.kind === "fileViewer"
        ? () => (
            <RoomRepoPanel
              roomId={roomId}
              panelId={config.id}
              panelKind={config.kind as "repoExplorer" | "fileViewer"}
              panelConfigJson={config.config_json ?? null}
              panelEntityBinding={config.entity_binding ?? null}
              roomData={room}
              storyData={storyBindingSource}
              panelSelections={panelSelections}
              setPanelSelection={updatePanelSelection}
              getFileRoomContextState={getFileRoomContextState}
              onToggleFileRoomContext={toggleFileRoomContext}
            />
          )
        : panelComponents[config.kind] || (() => null),
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
          onSettings={
            canManage ? () => setIsPromptSettingsOpen(true) : undefined
          }
          onCopyLink={handleCopyLink}
          onDelete={canManage ? handleDeleteRoom : undefined}
          onRemoveAgent={
            canManage
              ? (participant) =>
                  handleRemoveAgent({
                    id: participant.id,
                    name: participant.name,
                  })
              : undefined
          }
          onViewAgent={(participant) => {
            if (!participant.agentProfileId) return
            navigate({
              to: "/agent/$agentId",
              params: { agentId: participant.agentProfileId },
            })
          }}
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
          selectedRepoFiles={selectedRepoFiles}
          repoContextFiles={repoContextFiles}
          canManageRoomContext={canManage}
          onRemoveRepoContextFile={removeRepoContextFile}
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

      {canManage ? (
        <RoomPromptSettingsDialog
          open={isPromptSettingsOpen}
          onOpenChange={setIsPromptSettingsOpen}
          roomId={roomId}
          agents={roomPromptAgents}
        />
      ) : null}
    </div>
  )
}
