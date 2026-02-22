import { expect, test } from "@playwright/test"
import type { ReactNode } from "react"
import {
  A2UIPanel,
  CanvasPanel,
  DebugPanel,
  ParticipantPanel,
  StoryEditorPanel,
  StoryPlayerPanel,
} from "@/components/Room"
import { DemoChatPanel } from "@/components/Demo/DemoChatPanel"
import { DemoStoryPanel } from "@/components/Demo/DemoStoryPanel"
import { AgentRosterBlock } from "@/components/Demo/blocks/AgentRosterBlock"
import { ContributionFeedBlock } from "@/components/Demo/blocks/ContributionFeedBlock"
import { FileExplorerBlock } from "@/components/Demo/blocks/FileExplorerBlock"
import { GitViewBlock } from "@/components/Demo/blocks/GitViewBlock"
import { OrchestratorStateBlock } from "@/components/Demo/blocks/OrchestratorStateBlock"
import { StoryMetadataBlock } from "@/components/Demo/blocks/StoryMetadataBlock"
import { ToolCapabilityBlock } from "@/components/Demo/blocks/ToolCapabilityBlock"
import {
  type DemoBlockRendererContext,
  type DemoPanelRendererContext,
  renderDemoBlock,
  renderDemoPanel,
} from "@/components/Demo/rendererRegistry"

interface ElementLike {
  type: unknown
  props: {
    children?: ReactNode
  }
}

function isElementLike(node: unknown): node is ElementLike {
  return Boolean(
    node
      && typeof node === "object"
      && "type" in (node as Record<string, unknown>)
      && "props" in (node as Record<string, unknown>),
  )
}

function toElement(node: ReactNode): ElementLike {
  expect(isElementLike(node)).toBeTruthy()
  return node as ElementLike
}

function flattenText(node: ReactNode): string {
  if (node === null || node === undefined || typeof node === "boolean") return ""
  if (typeof node === "string" || typeof node === "number") return String(node)
  if (Array.isArray(node)) return node.map(flattenText).join(" ")
  if (isElementLike(node)) return flattenText(node.props.children as ReactNode)
  return ""
}

function makePanelContext(overrides?: Partial<DemoPanelRendererContext>): DemoPanelRendererContext {
  return {
    roomId: "room-1",
    roomTitle: "Demo Room",
    roomStoryId: "story-1",
    canWrite: true,
    autoRespond: true,
    onSendMessage: () => {},
    isConnected: true,
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
    renderContentPayload: () => <div data-testid="content-panel-sentinel">content-sentinel</div>,
    ...overrides,
  }
}

function makeBlockContext(overrides?: Partial<DemoBlockRendererContext>): DemoBlockRendererContext {
  return {
    renderContentPayload: () => <div data-testid="content-block-sentinel">content-sentinel</div>,
    roomId: "room-1",
    roomTitle: "Demo Room",
    roomStoryId: "story-1",
    runtimePolicy: "auto",
    runtimeHasRuntime: true,
    autoStartError: null,
    autoRespond: true,
    isConnected: true,
    debugMessages: [],
    streamingMessage: null,
    activeUsers: [],
    roomAgentsAsAgentData: [],
    availableAgents: [],
    ...overrides,
  }
}

test.describe("Demo renderer registry panel mapping", () => {
  const supportedCases: Array<{ kind: string; expectedType: unknown }> = [
    { kind: "storyRuntime", expectedType: DemoStoryPanel },
    { kind: "chat", expectedType: DemoChatPanel },
    { kind: "participantPanel", expectedType: ParticipantPanel },
    { kind: "canvas", expectedType: CanvasPanel },
    { kind: "a2ui", expectedType: A2UIPanel },
    { kind: "storyEditor", expectedType: StoryEditorPanel },
    { kind: "storyPlayer", expectedType: StoryPlayerPanel },
    { kind: "debug", expectedType: DebugPanel },
  ]

  for (const { kind, expectedType } of supportedCases) {
    test(`maps panel kind "${kind}" to expected component`, async () => {
      const panel = { id: `panel-${kind}`, kind } as const
      const element = toElement(renderDemoPanel(panel as never, makePanelContext()))
      expect(element.type).toBe(expectedType)
    })
  }

  test("content panel delegates to renderContentPayload callback", async () => {
    const calls: Array<{ payload: unknown; label: string }> = []
    const panel = {
      id: "panel-content",
      kind: "content",
      options: { content_json: { format: "markdown", value: "hello" } },
    }
    const ctx = makePanelContext({
      renderContentPayload: (payload, label) => {
        calls.push({ payload, label })
        return <div>content-hit</div>
      },
    })

    const element = toElement(renderDemoPanel(panel as never, ctx))
    expect(flattenText(element.props.children as ReactNode)).toContain("content-hit")
    expect(calls).toHaveLength(1)
    expect(calls[0]?.payload).toEqual({ format: "markdown", value: "hello" })
    expect(calls[0]?.label).toContain("Content panel is configured")
  })

  test("storyEditor returns fallback messaging when no story is attached", async () => {
    const panel = { id: "panel-story-editor", kind: "storyEditor" }
    const element = toElement(
      renderDemoPanel(panel as never, makePanelContext({ roomStoryId: null })),
    )
    expect(element.type).toBe("div")
    expect(flattenText(element.props.children as ReactNode)).toContain(
      "Story editor panel requires a story attached to this room.",
    )
  })

  test("unsupported panel kind returns non-fatal fallback", async () => {
    const panel = { id: "panel-unknown", kind: "futurePanelKind" }
    const element = toElement(renderDemoPanel(panel as never, makePanelContext()))
    expect(element.type).toBe("div")
    expect(flattenText(element.props.children as ReactNode)).toContain(
      "Unsupported panel kind",
    )
    expect(flattenText(element.props.children as ReactNode)).toContain(
      "futurePanelKind",
    )
  })
})

test.describe("Demo renderer registry block mapping", () => {
  const dedicatedCases: Array<{ type: string; expectedType: unknown }> = [
    { type: "storyMetadata", expectedType: StoryMetadataBlock },
    { type: "agentRoster", expectedType: AgentRosterBlock },
    { type: "orchestratorState", expectedType: OrchestratorStateBlock },
    { type: "toolCapability", expectedType: ToolCapabilityBlock },
    { type: "contributionFeed", expectedType: ContributionFeedBlock },
    { type: "gitView", expectedType: GitViewBlock },
    { type: "fileExplorer", expectedType: FileExplorerBlock },
  ]

  for (const { type, expectedType } of dedicatedCases) {
    test(`maps block type "${type}" to dedicated component`, async () => {
      const block = { id: `block-${type}`, type, config_json: {} }
      const element = toElement(renderDemoBlock(block as never, makeBlockContext()))
      expect(element.type).toBe(expectedType)
    })
  }

  const contentCases: Array<{ type: "context" | "content"; payload: unknown }> = [
    { type: "context", payload: { format: "text", value: "ctx payload" } },
    { type: "content", payload: { format: "markdown", value: "# header" } },
  ]

  for (const { type, payload } of contentCases) {
    test(`block type "${type}" delegates payload to renderContentPayload callback`, async () => {
      const calls: Array<{ inPayload: unknown; inLabel: string }> = []
      const block = { id: `block-${type}`, type, content_json: payload }

      const element = toElement(
        renderDemoBlock(
          block as never,
          makeBlockContext({
            renderContentPayload: (inPayload, inLabel) => {
              calls.push({ inPayload, inLabel })
              return <div>content-path</div>
            },
          }),
        ),
      )

      expect(flattenText(element.props.children as ReactNode)).toContain("content-path")
      expect(calls).toHaveLength(1)
      expect(calls[0]?.inPayload).toEqual(payload)
      expect(calls[0]?.inLabel).toContain(block.id)
    })
  }

  test("story block uses structured fallback renderer path", async () => {
    const block = { id: "block-story", type: "story", config_json: { theme: "dense" } }
    const element = toElement(renderDemoBlock(block as never, makeBlockContext()))
    expect(element.type).toBe("div")
    expect(flattenText(element.props.children as ReactNode)).toContain("Story Block")
    expect(flattenText(element.props.children as ReactNode)).toContain(
      "awaiting dedicated presentation",
    )
  })

  test("unsupported block type returns non-fatal fallback", async () => {
    const block = { id: "block-unknown", type: "futureBlockType" }
    const element = toElement(renderDemoBlock(block as never, makeBlockContext()))
    expect(element.type).toBe("div")
    expect(flattenText(element.props.children as ReactNode)).toContain(
      "is not mapped yet",
    )
    expect(flattenText(element.props.children as ReactNode)).toContain(
      "futureBlockType",
    )
  })
})
