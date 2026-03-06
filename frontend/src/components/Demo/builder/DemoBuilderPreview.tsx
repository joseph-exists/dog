import { useQuery } from "@tanstack/react-query"
import { useMemo, useState } from "react"
import { getRenderableDemoBlocks } from "@/components/Demo/blockVisibility"
import {
  getBlockCapabilityByType,
  getBlockCapabilityPreviewAdapterOverrides,
  getPanelCapabilityByKind,
  getPanelCapabilityPreviewAdapterOverrides,
} from "@/components/Demo/builder/demoBuilderCapabilityRegistry"
import {
  type EditableComposition,
  getCompositionStoryId,
} from "@/components/Demo/builder/demoBuilderSchema"
import type { PanelConfig as DemoLayoutPanelConfig } from "@/components/Demo/DemoLayout"
import { DemoPresentationFrame } from "@/components/Demo/DemoPresentationFrame"
import {
  DemoShell,
  type DemoShellBlockRenderItem,
} from "@/components/Demo/DemoShell"
import {
  buildDemoThemeIndex,
  resolveDemoPresentationFrame,
} from "@/components/Demo/demoPresentationResolver"
import {
  type DemoPanelRendererContext,
  renderDemoBlock,
  renderDemoPanel,
} from "@/components/Demo/rendererRegistry"
import {
  type Content,
  ContentRenderer,
} from "@/components/Page/primitives/ContentRenderer"
import { useCanvasRenderJobEvents } from "@/hooks/useCanvasRenderJobEvents"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { useRoomStream } from "@/hooks/useRoomStream"
import {
  DemoService,
  type TesserScript,
} from "@/services/demoService"
import type { ThemeViewModel } from "@/services/themeService"

function isRenderableContentPayload(value: unknown): value is Content {
  if (!value || typeof value !== "object") return false
  const data = value as Record<string, unknown>
  return typeof data.format === "string" && Object.hasOwn(data, "value")
}

function renderContentPayload(value: unknown, fallbackLabel: string) {
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

interface DemoBuilderPreviewProps {
  demoConfigId?: string | null
  demoSlug?: string | null
  composition: EditableComposition
  demoTitle: string
  isDirty?: boolean
  availablePageThemes: ThemeViewModel[]
  availableCardThemes: ThemeViewModel[]
  onPageThemeChange: (themeId: string) => void
  onCardsThemeChange: (themeId: string) => void
}

export function DemoBuilderPreview({
  demoConfigId = null,
  demoSlug = null,
  composition,
  demoTitle,
  isDirty = false,
  availablePageThemes,
  availableCardThemes,
  onPageThemeChange,
  onCardsThemeChange,
}: DemoBuilderPreviewProps) {
  const { handleRoomEvent, waitForJob } = useCanvasRenderJobEvents()
  const roomTitle = "Preview Room"
  const roomStoryId = getCompositionStoryId(composition)
  const { data: previewSession } = useQuery({
    queryKey: ["demo-builder", "preview-session", demoSlug],
    queryFn: () => DemoService.resolveSessionForSlug(demoSlug ?? ""),
    enabled: Boolean(demoSlug),
  })
  const roomId = previewSession?.room.room_id ?? "preview-room"
  const { isConnected } = useRoomStream(previewSession?.room.room_id, {
    enabled: Boolean(previewSession?.room.room_id),
    onEvent: handleRoomEvent,
  })
  const pageTheme = useMemo(
    () =>
      availablePageThemes.find(
        (theme) => theme.id === composition.page_theme_id,
      ) ?? null,
    [availablePageThemes, composition.page_theme_id],
  )
  const cardsTheme = useMemo(
    () =>
      availableCardThemes.find(
        (theme) => theme.id === composition.cards_theme_id,
      ) ?? null,
    [availableCardThemes, composition.cards_theme_id],
  )
  const themeIndex = useMemo(
    () => buildDemoThemeIndex(availablePageThemes, availableCardThemes),
    [availableCardThemes, availablePageThemes],
  )
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
  const [tesserHelpByScriptName, setTesserHelpByScriptName] = useState<
    Record<string, string>
  >({})
  const [tesserExamplesIndex, setTesserExamplesIndex] = useState<string | null>(null)
  const { data: tesserScriptsPayload } = useQuery({
    queryKey: ["demo-builder", "tesser", "scripts"],
    queryFn: () => DemoService.listTesserScripts(),
  })
  const availableTesserScripts: TesserScript[] = tesserScriptsPayload?.data ?? []
  const compositionFrame = useMemo(
    () =>
      resolveDemoPresentationFrame({
        scope: "composition",
        themeId: null,
        presentationJson: composition.presentation_json,
        themeIndex,
      }),
    [composition.presentation_json, themeIndex],
  )

  const basePanelContext = useMemo(
    (): DemoPanelRendererContext => ({
      demoConfigId: demoConfigId ?? "preview-demo-config",
      metadataJson:
        composition.metadata_json &&
        typeof composition.metadata_json === "object" &&
        !Array.isArray(composition.metadata_json)
          ? (composition.metadata_json as Record<string, unknown>)
          : {},
      roomId,
      roomTitle,
      roomStoryId,
      canWrite: true,
      autoRespond: true,
      onSendMessage: () => {},
      isConnected,
      sendViaWebSocket: () => {},
      streamingMessage: null,
      activeUsers: [],
      roomAgentsAsAgentData: [],
      debugActiveAgents: [],
      availableAgents: [],
      existingAgentIds: [],
      onAddAgent: async () => {},
      onRemoveAgent: async () => {},
      onToggleAgent: async () => {},
      onRemoveUser: async () => {},
      isParticipantPanelLoading: false,
      debugMessages: [],
      showInternalMessages: false,
      onToggleInternalMessages: () => {},
      renderContentPayload,
      onRenderCanvas: async (panelId, payload) => {
        const nextScriptName = payload?.scriptName ?? "simple_svg"
        if (!demoConfigId) {
          const message = "Select and save a demo config before rendering canvas panels."
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
          return
        }
        if (!previewSession?.room.room_id) {
          const message = "Preview room is not ready for live canvas render events."
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
          return
        }
        if (isDirty) {
          const message =
            "Save the demo composition before rendering canvas preview updates."
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
          return
        }
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
            demoConfigId,
            {
              panel_id: panelId,
              script_name: nextScriptName,
              script_input: payload?.scriptInput ?? {},
              title: payload?.title ?? "Tesser Render",
              subtitle: payload?.subtitle ?? null,
              persist_to_composition: true,
              commit_to_shadow_repo: false,
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
                enqueueResponse.shadow_commit_sha ??
                previous[panelId]?.lastCommitSha ??
                null,
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
          setCanvasSvgOverrideByPanelId((previous) => ({
            ...previous,
            [panelId]: terminalResponse.svg ?? "",
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
          showSuccessToast("Canvas preview updated")
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
      canvasRenderStateByPanelId,
      canvasSvgOverrideByPanelId,
      availableTesserScripts: availableTesserScripts.map((script) => ({
        ...script,
        help_text: tesserHelpByScriptName[script.name] ?? script.help_text ?? null,
      })),
      onRequestTesserScriptHelp: async (scriptName) => {
        const cached = tesserHelpByScriptName[scriptName]
        if (cached) return cached
        const response = await DemoService.getTesserScriptHelp(scriptName)
        const help = response.help_text ?? null
        if (help) {
          setTesserHelpByScriptName((previous) => ({
            ...previous,
            [scriptName]: help,
          }))
        }
        return help
      },
      onRequestTesserExamplesIndex: async () => {
        if (tesserExamplesIndex) return tesserExamplesIndex
        const response = await DemoService.getTesserExamplesIndex()
        setTesserExamplesIndex(response.content)
        return response.content
      },
    }),
    [
      availableTesserScripts,
      canvasRenderStateByPanelId,
      canvasSvgOverrideByPanelId,
      composition.metadata_json,
      demoConfigId,
      isDirty,
      roomStoryId,
      tesserExamplesIndex,
      tesserHelpByScriptName,
      previewSession?.room.room_id,
      waitForJob,
      isConnected,
    ],
  )

  const baseBlockContext = useMemo(
    () => ({
      renderContentPayload,
      metadataJson:
        composition.metadata_json &&
        typeof composition.metadata_json === "object" &&
        !Array.isArray(composition.metadata_json)
          ? (composition.metadata_json as Record<string, unknown>)
          : {},
      roomId,
      roomTitle,
      roomStoryId,
      runtimePolicy: composition.runtime_policy ?? "auto",
      runtimeHasRuntime: true,
      autoStartError: null,
      autoRespond: true,
      isConnected: false,
      debugMessages: [],
      streamingMessage: null,
      activeUsers: [],
      roomAgentsAsAgentData: [],
      availableAgents: [],
    }),
    [composition.metadata_json, composition.runtime_policy, roomStoryId],
  )

  const panels: DemoLayoutPanelConfig[] = useMemo(
    () =>
      (composition.panels ?? []).map((panel) => ({
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
          const capability = getPanelCapabilityByKind(
            typeof panel.kind === "string" ? panel.kind : null,
          )
          const overrides = capability
            ? getPanelCapabilityPreviewAdapterOverrides(
                capability,
                panel,
                composition,
              )
            : {}
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
              {renderDemoPanel(panel, {
                ...basePanelContext,
                ...overrides,
                demoConfigId: basePanelContext.demoConfigId,
                onRenderCanvas: basePanelContext.onRenderCanvas,
                canvasRenderStateByPanelId:
                  basePanelContext.canvasRenderStateByPanelId,
                canvasSvgOverrideByPanelId:
                  basePanelContext.canvasSvgOverrideByPanelId,
              })}
            </DemoPresentationFrame>
          )
        },
      })),
    [basePanelContext, composition, composition.panels, themeIndex],
  )

  const renderedBlocksByRegion = useMemo(() => {
    const orderedBlocks = getRenderableDemoBlocks(composition.blocks ?? [])
    const regions: Record<
      "top" | "primary" | "auxiliary" | "footer",
      DemoShellBlockRenderItem[]
    > = {
      top: [],
      primary: [],
      auxiliary: [],
      footer: [],
    }
    for (const { block, region, visibilityMode } of orderedBlocks) {
      const capability = getBlockCapabilityByType(
        typeof block.type === "string" ? block.type : null,
      )
      const content = renderDemoBlock(block, {
        ...baseBlockContext,
        ...(capability
          ? getBlockCapabilityPreviewAdapterOverrides(
              capability,
              block,
              composition,
            )
          : {}),
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
            {content}
          </DemoPresentationFrame>
        ),
        visibilityMode,
      })
    }
    return regions
  }, [baseBlockContext, composition, composition.blocks, themeIndex])

  return (
    <DemoPresentationFrame
      frame={compositionFrame}
      className="h-full min-h-0 border rounded-md overflow-hidden bg-background"
      contentClassName="h-full min-h-0"
    >
      <DemoShell
        demoConfig={{
          id: "demo-builder-preview",
          slug: "demo-builder-preview",
          title: demoTitle,
          description:
            typeof composition.metadata_json?.description === "string"
              ? composition.metadata_json.description
              : "Unsaved preview from Demo Builder composition.",
          scope: "personal",
          isActive: true,
          defaultAutoRespond: true,
          defaultPanelsJson: [],
          defaultLayoutJson: [],
          metadataJson: composition.metadata_json ?? {},
          ownerId: null,
          createdAt: new Date(),
          updatedAt: new Date(),
        }}
        panels={panels}
        topBlocks={renderedBlocksByRegion.top}
        primaryBlocks={renderedBlocksByRegion.primary}
        auxiliaryBlocks={renderedBlocksByRegion.auxiliary}
        footerBlocks={renderedBlocksByRegion.footer}
        autoRespond={true}
        onAutoRespondChange={() => {}}
        isConnected={false}
        pageTheme={pageTheme}
        cardsTheme={cardsTheme}
        availablePageThemes={availablePageThemes}
        availableCardThemes={availableCardThemes}
        onPageThemeChange={onPageThemeChange}
        onCardsThemeChange={onCardsThemeChange}
      />
    </DemoPresentationFrame>
  )
}
