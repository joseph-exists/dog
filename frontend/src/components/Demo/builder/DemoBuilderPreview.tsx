import { useMemo } from "react"
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
  renderDemoBlock,
  renderDemoPanel,
} from "@/components/Demo/rendererRegistry"
import {
  type Content,
  ContentRenderer,
} from "@/components/Page/primitives/ContentRenderer"
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
  composition: EditableComposition
  demoTitle: string
  availablePageThemes: ThemeViewModel[]
  availableCardThemes: ThemeViewModel[]
  onPageThemeChange: (themeId: string) => void
  onCardsThemeChange: (themeId: string) => void
}

export function DemoBuilderPreview({
  composition,
  demoTitle,
  availablePageThemes,
  availableCardThemes,
  onPageThemeChange,
  onCardsThemeChange,
}: DemoBuilderPreviewProps) {
  const roomId = "preview-room"
  const roomTitle = "Preview Room"
  const roomStoryId = getCompositionStoryId(composition)
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
    () => ({
      roomId,
      roomTitle,
      roomStoryId,
      canWrite: true,
      autoRespond: true,
      onSendMessage: () => {},
      isConnected: false,
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
    }),
    [roomStoryId],
  )

  const baseBlockContext = useMemo(
    () => ({
      renderContentPayload,
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
    [composition.runtime_policy, roomStoryId],
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
