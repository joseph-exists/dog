import { createFileRoute } from "@tanstack/react-router"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import type { ReactNode } from "react"
import type { ApiError } from "@/client"
import { AgentsService } from "@/client/sdk.gen"
import type { UserAgentConfigPublic } from "@/client/types.gen"
import { PersonasService, RoomRuntimeService, UserPersonasService } from "@/client"
import {
  ContentRenderer,
  type Content,
} from "@/components/Page/primitives/ContentRenderer"
import type { PanelConfig as DemoLayoutPanelConfig } from "@/components/Demo/DemoLayout"
import { DemoShell, type DemoShellBlockRenderItem } from "@/components/Demo/DemoShell"
import { DemoStoryPanel } from "@/components/Demo/DemoStoryPanel"
import { CanvasPanel, ParticipantPanel } from "@/components/Room"
import MessageInput from "@/components/Room/RoomMessages/MessageInput"
import MessageList from "@/components/Room/RoomMessages/MessageList"
import useAuth from "@/hooks/useAuth"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { useRoomMessages } from "@/hooks/useRoomMessages"
import { useRoomStream } from "@/hooks/useRoomStream"
import { usePageThemes } from "@/hooks/useThemeBinding"
import { useAvailableThemes, useUserThemeBindings } from "@/hooks/useThemeRegistry"
import { DemoService, type ResolvedDemoSessionViewModel } from "@/services/demoService"
import { RoomService } from "@/services/roomService"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/demo/$slug")({
  component: DemoRoute,
})

function DemoChatPanel({
  roomId,
  isConnected,
  sendViaWebSocket,
  streamingMessage,
}: {
  roomId: string
  isConnected: boolean
  sendViaWebSocket: (content: string) => void
  streamingMessage: { agent_name: string; content: string } | null
}) {
  const {
    messages,
    sendMessage,
    isSending,
    hasMore,
    loadMore,
    isLoadingMore,
    isLoading,
  } = useRoomMessages(roomId)

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4">
        <MessageList
          roomId={roomId}
          messages={messages}
          hasMore={hasMore}
          onLoadMore={loadMore}
          isLoadingMore={isLoadingMore}
          isLoading={isLoading}
          streamingMessage={streamingMessage}
        />
      </div>
      <MessageInput
        roomId={roomId}
        onSendMessage={sendMessage}
        isSending={isSending}
        isConnected={isConnected}
        sendViaWebSocket={sendViaWebSocket}
      />
    </div>
  )
}

function DemoRoute() {
  const { slug } = Route.useParams()

  const {
    data: resolved,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["demo", "resolve-session", slug],
    queryFn: () => DemoService.resolveSessionForSlug(slug),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">Loading demo...</p>
      </div>
    )
  }

  if (isError || !resolved) {
    const status = (error as { status?: number } | null)?.status
    const isNotFound = status === 404
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">
          {isNotFound
            ? `Demo "${slug}" not found.`
            : "Unable to load demo right now."}
        </p>
      </div>
    )
  }

  return <ResolvedDemoRoute resolved={resolved} />
}

function isRenderableContentPayload(value: unknown): value is Content {
  if (!value || typeof value !== "object") return false
  const data = value as Record<string, unknown>
  return typeof data.format === "string" && Object.prototype.hasOwnProperty.call(data, "value")
}

function renderContentPayload(
  value: unknown,
  fallbackLabel: string,
): ReactNode {
  if (!isRenderableContentPayload(value)) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        {fallbackLabel}
      </div>
    )
  }
  return (
    <div className="p-4 overflow-auto h-full">
      <ContentRenderer content={value} safeMode />
    </div>
  )
}

function getPanelContentPayload(panel: { options?: unknown }): unknown {
  if (!panel.options || typeof panel.options !== "object") return undefined
  const options = panel.options as Record<string, unknown>
  return options.content_json
}

function normalizeBlockVisibility(
  visibility: unknown,
): "visible" | "hidden_unmounted" | "hidden_mounted" {
  const rawVisibility = typeof visibility === "string" ? visibility : "visible"
  if (rawVisibility === "hidden_unmounted") return "hidden_unmounted"
  if (rawVisibility === "hidden_mounted") return "hidden_mounted"
  return "visible"
}

function ResolvedDemoRoute({
  resolved,
}: {
  resolved: ResolvedDemoSessionViewModel
}) {
  const queryClient = useQueryClient()
  const roomId = resolved.room.room_id
  const roomTitle = resolved.room.title ?? "Demo Room"
  const roomStoryId = resolved.room.story_id ?? null
  const canWrite = resolved.room.can_write ?? false
  const runtimePolicy = resolved.runtime.runtime_policy
  const [runtimeHasRuntime, setRuntimeHasRuntime] = useState(
    resolved.runtime.has_runtime ?? false,
  )
  const [autoRespond, setAutoRespond] = useState(
    typeof resolved.composition.metadata_json?.auto_respond === "boolean"
      ? resolved.composition.metadata_json.auto_respond
      : true,
  )
  const [autoStartError, setAutoStartError] = useState<string | null>(
    resolved.runtime.auto_start_error ?? null,
  )
  const autoStartAttemptedRef = useRef(false)
  const { user } = useAuth()

  const { isConnected, sendMessage: sendViaWebSocket, streamingMessage } = useRoomStream(roomId)
  const participantsQueryKey = ["room", roomId, "participants", "demo"] as const
  const {
    data: participants = [],
    isLoading: isLoadingParticipants,
  } = useQuery({
    queryKey: participantsQueryKey,
    queryFn: () => RoomService.getParticipants(roomId),
  })
  const {
    data: availableAgentsData,
    isLoading: isLoadingAvailableAgents,
  } = useQuery({
    queryKey: ["agents", "available", "demo"],
    queryFn: () => AgentsService.listAvailableAgents(),
  })
  const { mutateAsync: startRuntime, isPending: isStarting } = useMutation({
    mutationFn: async (userPersonaId: string) =>
      RoomRuntimeService.putRoomRuntime({
        roomId,
        requestBody: { user_persona_id: userPersonaId, story_version: null },
      }),
  })
  const { mutateAsync: addParticipant, isPending: isAddingParticipant } = useMutation({
    mutationFn: async ({
      participantId,
      type,
    }: {
      participantId: string
      type: "user" | "agent"
    }) =>
      RoomService.addParticipant(roomId, {
        participant_id: participantId,
        participant_type: type,
        role: "member",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: participantsQueryKey })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err)
    },
  })
  const { mutateAsync: removeParticipant, isPending: isRemovingParticipant } = useMutation({
    mutationFn: async (participantId: string) =>
      RoomService.removeParticipant(roomId, participantId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: participantsQueryKey })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err)
    },
  })

  const {
    data: userPersonasData,
    isLoading: isLoadingUserPersonas,
  } = useQuery({
    queryKey: ["user-personas", "demo-autostart"],
    queryFn: () => UserPersonasService.readUserPersonas({ limit: 100 }),
    enabled: Boolean(roomStoryId),
  })

  const { mutateAsync: createBasicUserPersona, isPending: isCreatingPersona } =
    useMutation({
      mutationFn: async () => {
        const personaName = roomTitle.trim()
          ? `${roomTitle.trim()} Persona`
          : "Default Persona"
        const persona = await PersonasService.createPersona({
          requestBody: { name: personaName },
        })
        const userPersona = await UserPersonasService.createUserPersona({
          requestBody: {
            persona_id: persona.id,
            nickname: personaName,
          },
        })
        return userPersona.id
      },
    })

  useEffect(() => {
    if (!roomStoryId) return
    if (isLoadingUserPersonas) return
    if (runtimeHasRuntime) return
    if (isStarting || isCreatingPersona) return
    if (autoStartAttemptedRef.current) return
    if (runtimePolicy === "manual") return
    if (runtimePolicy === "owner_only" && !canWrite) return

    autoStartAttemptedRef.current = true
    setAutoStartError(null)

    void (async () => {
      try {
        // Future tuneability: select persona from explicit demo/session binding
        // before falling back to first available user persona.
        let userPersonaId = userPersonasData?.data?.[0]?.id ?? null
        if (!userPersonaId) {
          userPersonaId = await createBasicUserPersona()
        }
        await startRuntime(userPersonaId)
        setRuntimeHasRuntime(true)
      } catch (error) {
        const message = error instanceof Error ? error.message : "Failed to auto-start runtime."
        setAutoStartError(message)
      }
    })()
  }, [
    createBasicUserPersona,
    isCreatingPersona,
    isLoadingUserPersonas,
    isStarting,
    canWrite,
    roomStoryId,
    runtimeHasRuntime,
    runtimePolicy,
    startRuntime,
    userPersonasData?.data,
  ])

  const handleAutoRespondMessage = useCallback(
    (message: string) => {
      sendViaWebSocket(message)
    },
    [sendViaWebSocket],
  )

  const contextKey = `page:demo:${resolved.demo_config_id}`
  const { themes } = usePageThemes([contextKey], {
    entityContext: {
      entityType: "demo",
      entityId: roomId,
      ownerId: user?.id ?? "",
    },
  })
  const { setBinding } = useUserThemeBindings(contextKey)
  const { themes: availablePageThemes } = useAvailableThemes("page")
  const { themes: availableCardThemes } = useAvailableThemes("card")

  const handlePageThemeChange = useCallback(
    (themeId: string) => {
      setBinding({ contextKey, slot: "page", themeId })
    },
    [contextKey, setBinding],
  )

  const handleCardsThemeChange = useCallback(
    (themeId: string) => {
      setBinding({ contextKey, slot: "cards", themeId })
    },
    [contextKey, setBinding],
  )

  const handleAddAgent = useCallback(
    async (agent: { id: string; name?: string | null }) => {
      await addParticipant({ participantId: agent.id, type: "agent" })
      showSuccessToast(`Added ${agent.name ?? "Agent"} to the room`)
    },
    [addParticipant],
  )

  const handleRemoveAgent = useCallback(
    async (agent: { id: string; name?: string | null }) => {
      await removeParticipant(agent.id)
      showSuccessToast(`Removed ${agent.name ?? "Agent"} from the room`)
    },
    [removeParticipant],
  )

  const handleToggleAgent = useCallback(
    async (agentId: string, activate: boolean) => {
      if (activate) {
        await addParticipant({ participantId: agentId, type: "agent" })
      } else {
        await removeParticipant(agentId)
      }
      showSuccessToast(activate ? "Agent activated" : "Agent deactivated")
    },
    [addParticipant, removeParticipant],
  )

  const handleRemoveUser = useCallback(
    async (participantId: string) => {
      await removeParticipant(participantId)
      showSuccessToast("Participant removed from the room")
    },
    [removeParticipant],
  )

  const availableAgents = (availableAgentsData?.data ??
    []) as UserAgentConfigPublic[]
  const activeUsers = participants.filter((p) => p.participant_type === "user")
  const allRoomAgents = participants.filter((p) => p.participant_type === "agent")
  const roomAgentsAsAgentData = allRoomAgents.map((p) => {
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
    const config = availableAgents.find(
      (a) => a.id === p.participant_id || a.name === p.participant_id,
    )
    return config?.id ?? p.participant_id
  })

  const panels: DemoLayoutPanelConfig[] = useMemo(
    () =>
      (resolved.composition.panels ?? []).map((panel) => ({
        id: panel.id,
        kind: panel.kind ?? "content",
        prominence: panel.prominence ?? "primary",
        title: panel.title ?? panel.kind ?? "Panel",
        defaultSize:
          panel.default_size ??
          ((panel.prominence ?? "primary") === "primary" ? 65 : 35),
        minSize:
          panel.min_size ??
          ((panel.prominence ?? "primary") === "primary" ? 30 : 20),
        maxSize: panel.max_size ?? undefined,
        viewportMode: panel.viewport_mode ?? "panel",
        render: () => {
          if (panel.kind === "storyRuntime") {
            return (
              <DemoStoryPanel
                roomId={roomId}
                roomTitle={roomTitle}
                roomStoryId={roomStoryId}
                canWrite={canWrite}
                autoRespond={autoRespond}
                onSendMessage={handleAutoRespondMessage}
              />
            )
          }
          if (panel.kind === "chat") {
            return (
              <DemoChatPanel
                roomId={roomId}
                isConnected={isConnected}
                sendViaWebSocket={sendViaWebSocket}
                streamingMessage={streamingMessage}
              />
            )
          }
          if (panel.kind === "content") {
            return renderContentPayload(
              getPanelContentPayload(panel),
              "Content panel is configured, but no valid content_json payload was provided.",
            )
          }
          if (panel.kind === "participantPanel") {
            return (
              <ParticipantPanel
                activeUsers={activeUsers}
                roomAgents={roomAgentsAsAgentData}
                availableAgents={availableAgents}
                existingAgentIds={existingAgentIds}
                onAddAgent={handleAddAgent}
                onRemoveAgent={handleRemoveAgent}
                onToggleAgent={handleToggleAgent}
                onRemoveParticipant={handleRemoveUser}
                canManage={canWrite}
                isLoading={
                  isLoadingParticipants ||
                  isLoadingAvailableAgents ||
                  isAddingParticipant ||
                  isRemovingParticipant
                }
              />
            )
          }
          if (panel.kind === "canvas") {
            return <CanvasPanel />
          }
          return (
            <div className="h-full p-4 text-sm text-muted-foreground">
              Unsupported panel kind: {panel.kind}
            </div>
          )
        },
      })),
    [
      autoRespond,
      availableAgents,
      handleAddAgent,
      handleRemoveAgent,
      handleRemoveUser,
      handleToggleAgent,
      canWrite,
      existingAgentIds,
      handleAutoRespondMessage,
      isAddingParticipant,
      isLoadingAvailableAgents,
      isConnected,
      isLoadingParticipants,
      isRemovingParticipant,
      activeUsers,
      resolved.composition.panels,
      roomAgentsAsAgentData,
      roomStoryId,
      roomTitle,
      roomId,
      sendViaWebSocket,
      streamingMessage,
    ],
  )

  useEffect(() => {
    if (process.env.NODE_ENV !== "development") return

    const rawPanels = (resolved.composition.panels ?? []).map((panel) => ({
      id: panel.id,
      kind: panel.kind,
      prominence: panel.prominence,
      order: panel.order,
      default_size: panel.default_size,
      min_size: panel.min_size,
      max_size: panel.max_size,
      viewport_mode: panel.viewport_mode,
    }))

    const mappedPanels = panels.map((panel) => ({
      id: panel.id,
      kind: panel.kind,
      prominence: panel.prominence,
      defaultSize: panel.defaultSize,
      minSize: panel.minSize,
      maxSize: panel.maxSize,
      viewportMode: panel.viewportMode,
    }))

    // Debug panel mapping to trace layout size/prominence regressions.
    console.debug("[DemoRoute] raw composition panels", rawPanels)
    console.debug("[DemoRoute] mapped layout panels", mappedPanels)
  }, [panels, resolved.composition.panels])

  const renderedBlocksByRegion = useMemo(() => {
    const orderedBlocks = (resolved.composition.blocks ?? [])
      .map((block) => ({
        block,
        visibilityMode: normalizeBlockVisibility(block.visibility),
      }))
      .filter(({ visibilityMode }) => visibilityMode !== "hidden_unmounted")
      .sort((a, b) => (a.block.order ?? 1) - (b.block.order ?? 1))

    const regions: Record<
      "top" | "primary" | "auxiliary" | "footer",
      DemoShellBlockRenderItem[]
    > = {
      top: [],
      primary: [],
      auxiliary: [],
      footer: [],
    }

    for (const { block, visibilityMode } of orderedBlocks) {
      const region = (block.region ?? "top") as "top" | "primary" | "auxiliary" | "footer"
      const fallback = `Block "${block.id}" has no supported content payload.`

      let rendered: ReactNode
      if (block.type === "content" || block.type === "context") {
        rendered = renderContentPayload(block.content_json, fallback)
      } else {
        rendered = (
          <div className="p-4 text-sm text-muted-foreground">
            Block type "{block.type}" is not mapped yet.
          </div>
        )
      }

      regions[region].push({
        id: block.id,
        content: rendered,
        visibilityMode: visibilityMode === "hidden_mounted" ? "hidden_mounted" : "visible",
      })
    }

    return regions
  }, [resolved.composition.blocks])

  const roomHasStory = Boolean(roomStoryId)
  const demoExpectsStory = (resolved.composition.panels ?? []).some((panel) =>
    panel.kind === "storyRuntime" || panel.kind === "storyPlayer" || panel.kind === "storyEditor",
  )
  const runtimeMissing = !runtimeHasRuntime
  const isAutoStartInFlight = roomHasStory && runtimeMissing && (isStarting || isCreatingPersona)
  const showRuntimeNotStartedState =
    roomHasStory && runtimeMissing && !isAutoStartInFlight && autoStartError === null

  return (
    <div className="flex flex-col h-full">
      {demoExpectsStory && !roomHasStory && (
        <div className="px-4 py-2 text-sm border-b bg-muted/40 text-muted-foreground">
          No story is attached to this demo room yet.
        </div>
      )}
      {isAutoStartInFlight && (
        <div className="px-4 py-2 text-sm border-b bg-amber-50 text-amber-900">
          Starting story runtime automatically...
        </div>
      )}
      {showRuntimeNotStartedState && (
        <div className="px-4 py-2 text-sm border-b bg-amber-50 text-amber-900">
          Story attached, but runtime is not started yet. Use the story panel to start runtime.
        </div>
      )}
      {autoStartError && (
        <div className="px-4 py-2 text-sm border-b bg-red-50 text-red-900">
          Auto-start failed. You can still start runtime manually in the story panel.
        </div>
      )}
      <div className="flex-1 min-h-0">
        <DemoShell
          demoConfig={{
            id: resolved.demo_config_id,
            slug: resolved.demo_config_id,
            title: roomTitle,
            description:
              typeof resolved.composition.metadata_json?.description === "string"
                ? resolved.composition.metadata_json.description
                : null,
            scope: "personal",
            isActive: true,
            defaultAutoRespond: autoRespond,
            defaultPanelsJson: [],
            defaultLayoutJson: [],
            metadataJson: resolved.composition.metadata_json ?? {},
            ownerId: user?.id ?? null,
            createdAt: new Date(),
            updatedAt: new Date(),
          }}
          panels={panels}
          topBlocks={renderedBlocksByRegion.top}
          primaryBlocks={renderedBlocksByRegion.primary}
          auxiliaryBlocks={renderedBlocksByRegion.auxiliary}
          footerBlocks={renderedBlocksByRegion.footer}
          autoRespond={autoRespond}
          onAutoRespondChange={setAutoRespond}
          isConnected={isConnected}
          pageTheme={themes.page?.theme ?? null}
          cardsTheme={themes.cards?.theme ?? null}
          availablePageThemes={availablePageThemes}
          availableCardThemes={availableCardThemes}
          onPageThemeChange={handlePageThemeChange}
          onCardsThemeChange={handleCardsThemeChange}
        />
      </div>
    </div>
  )
}
