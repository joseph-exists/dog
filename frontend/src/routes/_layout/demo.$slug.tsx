import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import type { ReactNode } from "react"
import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import type { ApiError } from "@/client"
import {
  PersonasService,
  RoomRuntimeService,
  UserPersonasService,
} from "@/client"
import { AgentsService } from "@/client/sdk.gen"
import type { UserAgentConfigPublic } from "@/client/types.gen"
import { getRenderableDemoBlocks } from "@/components/Demo/blockVisibility"
import { DemoCollapsibleSurface } from "@/components/Demo/DemoCollapsibleSurface"
import {
  DemoInteractiveBlock,
  type DemoInteractiveDispatchRequest,
} from "@/components/Demo/DemoInteractiveBlock"
import { DemoPanelLayoutDialog } from "@/components/Demo/DemoPanelLayoutDialog"
import type { PanelConfig as DemoLayoutPanelConfig } from "@/components/Demo/DemoLayout"
import {
  applyDemoPanelLayoutItems,
  buildDemoCollapseStorageKey,
  buildDemoPanelLayoutStorageKey,
  createDemoPanelLayoutItems,
  demoPanelLayoutItemsEqual,
  readDemoCollapsedIds,
  readDemoPanelLayoutItems,
  reconcileDemoCollapsedIds,
  reconcileDemoPanelLayoutItems,
  writeDemoCollapsedIds,
  writeDemoPanelLayoutItems,
  type DemoPanelLayoutItem,
} from "@/components/Demo/demoPanelLayoutCustomization"
import { DemoPresentationFrame } from "@/components/Demo/DemoPresentationFrame"
import {
  DemoShell,
  type DemoShellBlockRenderItem,
} from "@/components/Demo/DemoShell"
import { resolveInteractionReceiverRegistration } from "@/components/Demo/demoInteractionHandlers"
import {
  buildDemoThemeIndex,
  resolveDemoPresentationFrame,
} from "@/components/Demo/demoPresentationResolver"
import {
  renderDemoBlock,
  renderDemoPanel,
} from "@/components/Demo/rendererRegistry"
import {
  type Content,
  ContentRenderer,
} from "@/components/Page/primitives/ContentRenderer"
import useAuth from "@/hooks/useAuth"
import { useCanvasRenderJobEvents } from "@/hooks/useCanvasRenderJobEvents"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { useRoomMessages } from "@/hooks/useRoomMessages"
import { useRoomStream } from "@/hooks/useRoomStream"
import { usePageThemes } from "@/hooks/useThemeBinding"
import {
  useAvailableThemes,
  useUserThemeBindings,
} from "@/hooks/useThemeRegistry"
import {
  DemoService,
  type ResolvedDemoSessionViewModel,
  type TesserScript,
} from "@/services/demoService"
import { RoomService } from "@/services/roomService"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/demo/$slug")({
  component: DemoRoute,
})

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

  return <ResolvedDemoRoute slug={slug} resolved={resolved} />
}

function isRenderableContentPayload(value: unknown): value is Content {
  if (!value || typeof value !== "object") return false
  const data = value as Record<string, unknown>
  return typeof data.format === "string" && Object.hasOwn(data, "value")
}

function renderContentPayload(
  value: unknown,
  fallbackLabel: string,
): ReactNode {
  if (!isRenderableContentPayload(value)) {
    return (
      <div className="p-4 text-sm text-muted-foreground">{fallbackLabel}</div>
    )
  }
  return (
    <div className="p-4 overflow-auto h-full">
      <ContentRenderer content={value} safeMode />
    </div>
  )
}

function ResolvedDemoRoute({
  slug,
  resolved,
}: {
  slug: string
  resolved: ResolvedDemoSessionViewModel
}) {
  const getPanelCollapseId = useCallback((panelId: string) => `panel:${panelId}`, [])
  const getBlockCollapseId = useCallback((blockId: string) => `block:${blockId}`, [])
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
  const [showInternalMessages, setShowInternalMessages] = useState(false)
  const authoredPanelLayoutItems = useMemo(
    () => createDemoPanelLayoutItems(resolved.composition.panels ?? []),
    [resolved.composition.panels],
  )
  const panelLayoutStorageKey = useMemo(
    () =>
      buildDemoPanelLayoutStorageKey(
        resolved.demo_config_id?.trim().length
          ? resolved.demo_config_id
          : slug,
      ),
    [resolved.demo_config_id, slug],
  )
  const collapseStorageKey = useMemo(
    () =>
      buildDemoCollapseStorageKey(
        resolved.demo_config_id?.trim().length
          ? resolved.demo_config_id
          : slug,
      ),
    [resolved.demo_config_id, slug],
  )
  const [layoutDialogOpen, setLayoutDialogOpen] = useState(false)
  const [panelLayoutItems, setPanelLayoutItems] = useState<DemoPanelLayoutItem[]>(
    authoredPanelLayoutItems,
  )
  const [collapsedContentIds, setCollapsedContentIds] = useState<string[]>([])
  const [canvasSvgOverrideByPanelId, setCanvasSvgOverrideByPanelId] = useState<
    Record<string, string>
  >({})
  const [canvasRenderStateByPanelId, setCanvasRenderStateByPanelId] = useState<
    Record<
      string,
      {
        isRendering: boolean
        status: string | null
        error: string | null
        lastJobId: string | null
        lastRequestId: string | null
        lastCommitSha: string | null
        lastScriptName: string | null
      }
    >
  >({})
  const autoStartAttemptedRef = useRef(false)
  const { user } = useAuth()
  const { handleRoomEvent, waitForJob } = useCanvasRenderJobEvents()

  const {
    isConnected,
    sendMessage: sendViaWebSocket,
    streamingMessage,
  } = useRoomStream(roomId, { onEvent: handleRoomEvent })
  const { messages: debugMessages = [] } = useRoomMessages(roomId)
  const participantsQueryKey = ["room", roomId, "participants", "demo"] as const
  const { data: participants = [], isLoading: isLoadingParticipants } =
    useQuery({
      queryKey: participantsQueryKey,
      queryFn: () => RoomService.getParticipants(roomId),
    })
  const { data: availableAgentsData, isLoading: isLoadingAvailableAgents } =
    useQuery({
      queryKey: ["agents", "available", "demo"],
      queryFn: () => AgentsService.listAvailableAgents(),
    })
  const { data: tesserScriptsPayload } = useQuery({
    queryKey: ["tesser", "scripts"],
    queryFn: () => DemoService.listTesserScripts(),
  })
  const { mutateAsync: startRuntime, isPending: isStarting } = useMutation({
    mutationFn: async (userPersonaId: string) =>
      RoomRuntimeService.putRoomRuntime({
        roomId,
        requestBody: { user_persona_id: userPersonaId, story_version: null },
      }),
  })
  const { mutateAsync: addParticipant, isPending: isAddingParticipant } =
    useMutation({
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
  const { mutateAsync: removeParticipant, isPending: isRemovingParticipant } =
    useMutation({
      mutationFn: async (participantId: string) =>
        RoomService.removeParticipant(roomId, participantId),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: participantsQueryKey })
      },
      onError: (err: ApiError) => {
        handleError.call(showErrorToast, err)
      },
    })

  const { data: userPersonasData, isLoading: isLoadingUserPersonas } = useQuery(
    {
      queryKey: ["user-personas", "demo-autostart"],
      queryFn: () => UserPersonasService.readUserPersonas({ limit: 100 }),
      enabled: Boolean(roomStoryId),
    },
  )

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
        const message =
          error instanceof Error
            ? error.message
            : "Failed to auto-start runtime."
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
  const themeIndex = useMemo(
    () => buildDemoThemeIndex(availablePageThemes, availableCardThemes),
    [availableCardThemes, availablePageThemes],
  )
  const compositionFrame = useMemo(
    () =>
      resolveDemoPresentationFrame({
        scope: "composition",
        themeId: null,
        presentationJson: resolved.composition.presentation_json,
        themeIndex,
      }),
    [resolved.composition.presentation_json, themeIndex],
  )

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

  const handleRenderCanvas = useCallback(
    async (
      panelId: string,
      payload?: {
        scriptName?: string
        title?: string
        subtitle?: string | null
        scriptInput?: Record<string, unknown>
      },
    ) => {
      const nextScriptName = payload?.scriptName ?? "simple_svg"
      setCanvasRenderStateByPanelId((previous) => ({
        ...previous,
        [panelId]: {
          isRendering: true,
          status: "Queueing render...",
          error: null,
          lastJobId: previous[panelId]?.lastJobId ?? null,
          lastRequestId: previous[panelId]?.lastRequestId ?? null,
          lastCommitSha: previous[panelId]?.lastCommitSha ?? null,
          lastScriptName: nextScriptName,
        },
      }))
      try {
        const enqueueResponse = await DemoService.enqueueCanvasPanelRender(
          resolved.demo_config_id,
          {
          panel_id: panelId,
          script_name: nextScriptName,
          script_input: payload?.scriptInput ?? {},
          title: payload?.title ?? "Tesser Render",
          subtitle: payload?.subtitle ?? null,
          persist_to_composition: true,
          commit_to_shadow_repo: true,
          },
        )
        const enqueueStatus = enqueueResponse.status ?? "queued"
        setCanvasRenderStateByPanelId((previous) => ({
          ...previous,
          [panelId]: {
            isRendering: enqueueStatus === "queued" || enqueueStatus === "running",
            status:
              enqueueStatus === "queued"
                ? "Render queued..."
                : enqueueStatus === "running"
                  ? "Rendering in worker..."
                  : null,
            error: null,
            lastJobId: enqueueResponse.job_id ?? previous[panelId]?.lastJobId ?? null,
            lastRequestId:
              enqueueResponse.request_id ?? previous[panelId]?.lastRequestId ?? null,
            lastCommitSha:
              enqueueResponse.shadow_commit_sha ?? previous[panelId]?.lastCommitSha ?? null,
            lastScriptName: nextScriptName,
          },
        }))
        const terminalResponse =
          enqueueStatus === "queued" || enqueueStatus === "running"
            ? await waitForJob(enqueueResponse.job_id)
            : enqueueResponse

        if (terminalResponse.status !== "completed" || !terminalResponse.svg) {
          throw new Error(
            terminalResponse.error ||
              `Canvas render ended with status '${terminalResponse.status}'.`,
          )
        }
        const svg = terminalResponse.svg
        setCanvasSvgOverrideByPanelId((previous) => ({
          ...previous,
          [panelId]: svg,
        }))
        setCanvasRenderStateByPanelId((previous) => ({
          ...previous,
          [panelId]: {
            isRendering: false,
            status: null,
            error: null,
            lastJobId: terminalResponse.job_id ?? null,
            lastRequestId: terminalResponse.request_id ?? null,
            lastCommitSha: terminalResponse.shadow_commit_sha ?? null,
            lastScriptName: nextScriptName,
          },
        }))
        showSuccessToast("Canvas render updated")
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Canvas render failed."
        setCanvasRenderStateByPanelId((previous) => ({
          ...previous,
          [panelId]: {
            isRendering: false,
            status: null,
            error: message,
            lastJobId: previous[panelId]?.lastJobId ?? null,
            lastRequestId: previous[panelId]?.lastRequestId ?? null,
            lastCommitSha: previous[panelId]?.lastCommitSha ?? null,
            lastScriptName: nextScriptName,
          },
        }))
        showErrorToast(message)
      }
    },
    [resolved.demo_config_id, waitForJob],
  )
  const [tesserHelpByScriptName, setTesserHelpByScriptName] = useState<
    Record<string, string>
  >({})
  const [tesserExamplesIndex, setTesserExamplesIndex] = useState<string | null>(
    null,
  )

  const availableTesserScripts: TesserScript[] = tesserScriptsPayload?.data ?? []

  const handleRequestTesserScriptHelp = useCallback(async (scriptName: string) => {
    const cached = tesserHelpByScriptName[scriptName]
    if (cached) return cached
    const response = await DemoService.getTesserScriptHelp(scriptName)
    const help = response.help_text ?? ""
    if (help) {
      setTesserHelpByScriptName((previous) => ({
        ...previous,
        [scriptName]: help,
      }))
    }
    return help || null
  }, [tesserHelpByScriptName])

  const handleRequestTesserExamplesIndex = useCallback(async () => {
    if (tesserExamplesIndex) return tesserExamplesIndex
    const response = await DemoService.getTesserExamplesIndex()
    const content = response.content ?? ""
    if (content) {
      setTesserExamplesIndex(content)
    }
    return content || null
  }, [tesserExamplesIndex])

  const availableAgents = (availableAgentsData?.data ??
    []) as UserAgentConfigPublic[]
  const activeUsers = participants.filter((p) => p.participant_type === "user")
  const allRoomAgents = participants.filter(
    (p) => p.participant_type === "agent",
  )
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

  useEffect(() => {
    if (typeof window === "undefined") {
      setPanelLayoutItems(authoredPanelLayoutItems)
      return
    }
    const storedItems = readDemoPanelLayoutItems(
      window.localStorage,
      panelLayoutStorageKey,
    )
    setPanelLayoutItems(
      reconcileDemoPanelLayoutItems(authoredPanelLayoutItems, storedItems),
    )
  }, [authoredPanelLayoutItems, panelLayoutStorageKey])

  const effectiveCompositionPanels = useMemo(
    () =>
      applyDemoPanelLayoutItems(
        resolved.composition.panels ?? [],
        panelLayoutItems,
      ),
    [panelLayoutItems, resolved.composition.panels],
  )
  const renderableBlocks = useMemo(
    () => getRenderableDemoBlocks(resolved.composition.blocks ?? []),
    [resolved.composition.blocks],
  )
  const validCollapsedIds = useMemo(
    () => [
      ...effectiveCompositionPanels.map((panel) => getPanelCollapseId(panel.id)),
      ...renderableBlocks.map(({ block }) => getBlockCollapseId(block.id)),
    ],
    [effectiveCompositionPanels, getBlockCollapseId, getPanelCollapseId, renderableBlocks],
  )

  const hasCustomizedPanelLayout = useMemo(
    () =>
      !demoPanelLayoutItemsEqual(panelLayoutItems, authoredPanelLayoutItems),
    [authoredPanelLayoutItems, panelLayoutItems],
  )

  useEffect(() => {
    if (typeof window === "undefined") {
      setCollapsedContentIds([])
      return
    }
    const storedIds = readDemoCollapsedIds(
      window.localStorage,
      collapseStorageKey,
    )
    setCollapsedContentIds(reconcileDemoCollapsedIds(storedIds, validCollapsedIds))
  }, [collapseStorageKey, validCollapsedIds])

  useEffect(() => {
    setCollapsedContentIds((current) =>
      reconcileDemoCollapsedIds(current, validCollapsedIds),
    )
  }, [validCollapsedIds])

  const handleApplyPanelLayout = useCallback(
    (items: DemoPanelLayoutItem[]) => {
      setPanelLayoutItems(items)
      if (typeof window !== "undefined") {
        writeDemoPanelLayoutItems(
          window.localStorage,
          panelLayoutStorageKey,
          items,
        )
      }
      setLayoutDialogOpen(false)
      showSuccessToast("Demo layout updated for this device.")
    },
    [panelLayoutStorageKey],
  )

  const handleResetPanelLayout = useCallback(() => {
    setPanelLayoutItems(authoredPanelLayoutItems)
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(panelLayoutStorageKey)
    }
    showSuccessToast("Demo layout reset to authored default.")
  }, [authoredPanelLayoutItems, panelLayoutStorageKey])

  const persistCollapsedIds = useCallback(
    (nextIds: string[]) => {
      setCollapsedContentIds(nextIds)
      if (typeof window !== "undefined") {
        writeDemoCollapsedIds(window.localStorage, collapseStorageKey, nextIds)
      }
    },
    [collapseStorageKey],
  )

  const toggleCollapsedContent = useCallback(
    (collapseId: string) => {
      persistCollapsedIds(
        collapsedContentIds.includes(collapseId)
          ? collapsedContentIds.filter((id) => id !== collapseId)
          : [...collapsedContentIds, collapseId],
      )
    },
    [collapsedContentIds, persistCollapsedIds],
  )

  const handleCollapseAllContent = useCallback(() => {
    persistCollapsedIds(validCollapsedIds)
    showSuccessToast("Panels and blocks collapsed for this demo view.")
  }, [persistCollapsedIds, validCollapsedIds])

  const handleExpandAllContent = useCallback(() => {
    persistCollapsedIds([])
    showSuccessToast("Panels and blocks expanded for this demo view.")
  }, [persistCollapsedIds])

  const hasCollapsedContent = collapsedContentIds.length > 0
  const hasExpandableContent = validCollapsedIds.some(
    (id) => !collapsedContentIds.includes(id),
  )

  const panels: DemoLayoutPanelConfig[] = useMemo(
    () =>
      effectiveCompositionPanels.map((panel) => ({
        id: panel.id,
        kind: panel.kind ?? "content",
        prominence: panel.prominence ?? "primary",
        title: panel.title ?? panel.kind ?? "Panel",
        collapsed: collapsedContentIds.includes(getPanelCollapseId(panel.id)),
        defaultSize:
          panel.default_size ??
          ((panel.prominence ?? "primary") === "primary" ? 65 : 35),
        minSize:
          panel.min_size ??
          ((panel.prominence ?? "primary") === "primary" ? 30 : 20),
        maxSize: panel.max_size ?? undefined,
        viewportMode: panel.viewport_mode ?? "panel",
        render: () => {
          const panelFrame = resolveDemoPresentationFrame({
            scope: "panel",
            themeId: panel.theme_id,
            presentationJson: panel.presentation_json,
            themeIndex,
          })
          return (
            <DemoPresentationFrame
              frame={panelFrame}
              className="h-full min-h-0"
              contentClassName="h-full min-h-0"
            >
              <DemoCollapsibleSurface
                title={panel.title ?? panel.kind ?? "Panel"}
                isCollapsed={collapsedContentIds.includes(
                  getPanelCollapseId(panel.id),
                )}
                onToggle={() => toggleCollapsedContent(getPanelCollapseId(panel.id))}
                className="h-full min-h-0"
                contentClassName="h-full min-h-0"
              >
                {renderDemoPanel(panel, {
                  demoConfigId: resolved.demo_config_id,
                  roomId,
                  roomTitle,
                  roomStoryId,
                  canWrite,
                  autoRespond,
                  onSendMessage: handleAutoRespondMessage,
                  isConnected,
                  sendViaWebSocket,
                  streamingMessage,
                  activeUsers,
                  roomAgentsAsAgentData,
                  debugActiveAgents: allRoomAgents,
                  availableAgents,
                  existingAgentIds,
                  onAddAgent: handleAddAgent,
                  onRemoveAgent: handleRemoveAgent,
                  onToggleAgent: handleToggleAgent,
                  onRemoveUser: handleRemoveUser,
                  isParticipantPanelLoading:
                    isLoadingParticipants ||
                    isLoadingAvailableAgents ||
                    isAddingParticipant ||
                    isRemovingParticipant,
                  debugMessages,
                  showInternalMessages,
                  onToggleInternalMessages: setShowInternalMessages,
                  renderContentPayload,
                  onRenderCanvas: handleRenderCanvas,
                  canvasRenderStateByPanelId,
                  canvasSvgOverrideByPanelId,
                  availableTesserScripts: availableTesserScripts.map((script) => ({
                    ...script,
                    help_text:
                      tesserHelpByScriptName[script.name] ??
                      script.help_text ??
                      null,
                  })),
                  onRequestTesserScriptHelp: handleRequestTesserScriptHelp,
                  onRequestTesserExamplesIndex: handleRequestTesserExamplesIndex,
                })}
              </DemoCollapsibleSurface>
            </DemoPresentationFrame>
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
      handleRenderCanvas,
      handleRequestTesserExamplesIndex,
      handleRequestTesserScriptHelp,
      canWrite,
      canvasRenderStateByPanelId,
      canvasSvgOverrideByPanelId,
      availableTesserScripts,
      tesserHelpByScriptName,
      existingAgentIds,
      handleAutoRespondMessage,
      isAddingParticipant,
      isLoadingAvailableAgents,
      isConnected,
      isLoadingParticipants,
      isRemovingParticipant,
      activeUsers,
      collapsedContentIds,
      debugMessages,
      effectiveCompositionPanels,
      getPanelCollapseId,
      roomAgentsAsAgentData,
      roomStoryId,
      roomTitle,
      roomId,
      themeIndex,
      toggleCollapsedContent,
      sendViaWebSocket,
      showInternalMessages,
      streamingMessage,
      allRoomAgents,
    ],
  )

  useEffect(() => {
    if (process.env.NODE_ENV !== "development") return

    const rawPanels = effectiveCompositionPanels.map((panel) => ({
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
  }, [effectiveCompositionPanels, panels])

  const interactionReceiverRegistry = useMemo(() => {
    const registry = new Map<
      string,
      {
        panelId: string
        panelKind: string
        accepts: string[]
      }
    >()
    for (const panel of effectiveCompositionPanels) {
      const registration = resolveInteractionReceiverRegistration({
        id: panel.id,
        kind: panel.kind,
        options: panel.options,
      })
      if (!registration) continue
      registry.set(registration.receiverId, {
        panelId: registration.panelId,
        panelKind: registration.panelKind,
        accepts: registration.accepts,
      })
    }
    return registry
  }, [effectiveCompositionPanels])

  const handleDispatchInteraction = useCallback(
    (request: DemoInteractiveDispatchRequest) => {
      if (request.enforceRegisteredReceiver) {
        const targetId = request.targetPanelId?.trim() ?? ""
        if (targetId.length === 0) {
          showErrorToast(
            "Interaction dispatch blocked: target_panel_id is required when receiver enforcement is enabled.",
          )
          return
        }
        const receiver = interactionReceiverRegistry.get(targetId)
        if (!receiver) {
          showErrorToast(
            `Interaction dispatch blocked: receiver "${targetId}" is not registered.`,
          )
          return
        }
        if (receiver.panelKind !== "chat") {
          showErrorToast(
            `Interaction dispatch blocked: receiver "${targetId}" is not a chat panel.`,
          )
          return
        }
        if (!receiver.accepts.includes(request.interactionKind)) {
          showErrorToast(
            `Interaction dispatch blocked: receiver "${targetId}" does not accept ${request.interactionKind}.`,
          )
          return
        }
      }
      sendViaWebSocket(request.message)
    },
    [interactionReceiverRegistry, sendViaWebSocket],
  )

  const renderedBlocksByRegion = useMemo(() => {
    const regions: Record<
      "top" | "primary" | "auxiliary" | "footer",
      DemoShellBlockRenderItem[]
    > = {
      top: [],
      primary: [],
      auxiliary: [],
      footer: [],
    }

    for (const { block, region, visibilityMode } of renderableBlocks) {
      const rendered = renderDemoBlock(block, {
        renderContentPayload,
        roomId,
        roomTitle,
        roomStoryId,
        runtimePolicy,
        runtimeHasRuntime,
        autoStartError,
        autoRespond,
        isConnected,
        debugMessages,
        streamingMessage,
        activeUsers,
        roomAgentsAsAgentData,
        availableAgents,
      })

      const blockFrame = resolveDemoPresentationFrame({
        scope: "block",
        themeId: block.theme_id,
        presentationJson: block.presentation_json,
        themeIndex,
      })
      regions[region].push({
        id: block.id,
        content: (
          <DemoPresentationFrame frame={blockFrame}>
            <DemoCollapsibleSurface
              title={block.title ?? block.type ?? "Block"}
              isCollapsed={collapsedContentIds.includes(
                getBlockCollapseId(block.id),
              )}
              onToggle={() => toggleCollapsedContent(getBlockCollapseId(block.id))}
            >
              <DemoInteractiveBlock
                block={block}
                onDispatchInteraction={handleDispatchInteraction}
              >
                {rendered}
              </DemoInteractiveBlock>
            </DemoCollapsibleSurface>
          </DemoPresentationFrame>
        ),
        visibilityMode,
      })
    }

    return regions
  }, [
    activeUsers,
    autoRespond,
    autoStartError,
    availableAgents,
    collapsedContentIds,
    debugMessages,
    getBlockCollapseId,
    isConnected,
    roomAgentsAsAgentData,
    handleDispatchInteraction,
    roomId,
    roomStoryId,
    roomTitle,
    runtimeHasRuntime,
    runtimePolicy,
    streamingMessage,
    themeIndex,
    toggleCollapsedContent,
    renderableBlocks,
  ])

  const roomHasStory = Boolean(roomStoryId)
  const demoExpectsStory = (resolved.composition.panels ?? []).some(
    (panel) =>
      panel.kind === "storyRuntime" ||
      panel.kind === "storyPlayer" ||
      panel.kind === "storyEditor",
  )
  const runtimeMissing = !runtimeHasRuntime
  const isAutoStartInFlight =
    roomHasStory && runtimeMissing && (isStarting || isCreatingPersona)
  const showRuntimeNotStartedState =
    roomHasStory &&
    runtimeMissing &&
    !isAutoStartInFlight &&
    autoStartError === null

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
          Story attached, but runtime is not started yet. Use the story panel to
          start runtime.
        </div>
      )}
      {autoStartError && (
        <div className="px-4 py-2 text-sm border-b bg-red-50 text-red-900">
          Auto-start failed. You can still start runtime manually in the story
          panel.
        </div>
      )}
      <div className="flex-1 min-h-0">
        <DemoPresentationFrame
          frame={compositionFrame}
          className="h-full min-h-0"
          contentClassName="h-full min-h-0"
        >
      <DemoShell
            demoConfig={{
              id: resolved.demo_config_id,
              slug: resolved.demo_config_id,
              title: roomTitle,
              description:
                typeof resolved.composition.metadata_json?.description ===
                "string"
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
        onCustomizeLayout={() => setLayoutDialogOpen(true)}
        canResetLayout={hasCustomizedPanelLayout}
        onResetLayout={handleResetPanelLayout}
        onCollapseAll={hasExpandableContent ? handleCollapseAllContent : undefined}
        onExpandAll={hasCollapsedContent ? handleExpandAllContent : undefined}
      />
      <DemoPanelLayoutDialog
        open={layoutDialogOpen}
        onOpenChange={setLayoutDialogOpen}
        items={panelLayoutItems}
        onApply={handleApplyPanelLayout}
        onReset={handleResetPanelLayout}
        canReset={hasCustomizedPanelLayout}
      />
        </DemoPresentationFrame>
      </div>
    </div>
  )
}
