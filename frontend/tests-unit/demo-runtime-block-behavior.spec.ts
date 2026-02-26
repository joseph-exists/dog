import { expect, test } from "@playwright/test"
import {
  formatContributionSenderType,
  parseContributionFeedConfig,
  selectContributionFeedMessages,
} from "@/components/Demo/blocks/ContributionFeedBlock"
import {
  parseOrchestratorStateConfig,
  summarizeOrchestratorState,
} from "@/components/Demo/blocks/OrchestratorStateBlock"
import {
  deriveStoryMetadataRuntimeState,
  shouldShowRawStoryMetadataConfig,
} from "@/components/Demo/blocks/StoryMetadataBlock"
import type { DemoRoomAgentData } from "@/components/Demo/rendererRegistry"
import type { RoomRuntimeViewModel } from "@/services/roomRuntimeService"
import type { MessageViewModel } from "@/services/roomService"

function makeRuntime(
  overrides?: Partial<RoomRuntimeViewModel>,
): RoomRuntimeViewModel {
  return {
    roomId: "room-1",
    storyId: "story-1",
    storyVersion: 1,
    revision: 0,
    headChoiceId: null,
    currentNode: null,
    nodeChain: [],
    availableChoices: [],
    storyState: null,
    rewindTargets: null,
    hasRuntime: false,
    isAtEndNode: false,
    canRewind: false,
    canReset: false,
    ...overrides,
  }
}

function makeAgent(overrides?: Partial<DemoRoomAgentData>): DemoRoomAgentData {
  return {
    id: "agent-1",
    name: "Agent One",
    description: null,
    participation_mode: "on_mention",
    scope: "system",
    is_coordinator: false,
    is_enabled: true,
    ...overrides,
  }
}

function makeMessage(overrides?: Partial<MessageViewModel>): MessageViewModel {
  return {
    message_id: "msg-1",
    room_id: "room-1",
    sender_type: "user",
    sender_name: "User A",
    sender_id: "user-1",
    agent_name: null,
    content: "hello",
    created_at: new Date("2026-02-22T10:00:00.000Z"),
    is_own_message: false,
    is_pinned: false,
    active_for_context: false,
    can_edit: false,
    can_delete: false,
    can_pin: false,
    ...overrides,
  }
}

test.describe("StoryMetadataBlock derived runtime behavior", () => {
  test("uses route runtime fallback when runtime projection is missing", async () => {
    const derived = deriveStoryMetadataRuntimeState({
      runtime: null,
      isLoading: false,
      runtimeHasRuntime: true,
    })
    expect(derived.hasRuntime).toBe(true)
    expect(derived.statusLabel).toBe("running")
    expect(derived.revisionLabel).toBe("-")
    expect(derived.currentNodeLabel).toBe("-")
    expect(derived.availableChoices).toBe(0)
  })

  test("prefers runtime projection when present", async () => {
    const derived = deriveStoryMetadataRuntimeState({
      runtime: makeRuntime({
        hasRuntime: true,
        revision: 7,
        currentNode: {
          id: "node-1",
          title: "Fork in the road",
          content: "Text",
          contentFormat: null,
          isStartNode: false,
          isEndNode: false,
        },
        availableChoices: [
          {
            id: "choice-1",
            text: "Left",
            toNodeId: "node-2",
            order: 1,
            requiresState: null,
            setsState: null,
            isAvailable: true,
            unavailableReason: null,
          },
        ],
      }),
      isLoading: false,
      runtimeHasRuntime: false,
    })

    expect(derived.hasRuntime).toBe(true)
    expect(derived.statusLabel).toBe("running")
    expect(derived.revisionLabel).toBe(7)
    expect(derived.currentNodeLabel).toBe("Fork in the road")
    expect(derived.availableChoices).toBe(1)
  })

  test("runtime.hasRuntime takes precedence over route fallback", async () => {
    const derived = deriveStoryMetadataRuntimeState({
      runtime: makeRuntime({ hasRuntime: false }),
      isLoading: false,
      runtimeHasRuntime: true,
    })
    expect(derived.hasRuntime).toBe(false)
    expect(derived.statusLabel).toBe("not started")
  })

  test("preserves loading state and config toggle detection", async () => {
    const derived = deriveStoryMetadataRuntimeState({
      runtime: null,
      isLoading: true,
      runtimeHasRuntime: false,
    })
    expect(derived.isLoading).toBe(true)
    expect(shouldShowRawStoryMetadataConfig({ show_config_json: true })).toBe(
      true,
    )
    expect(shouldShowRawStoryMetadataConfig({ show_config_json: false })).toBe(
      false,
    )
  })
})

test.describe("OrchestratorStateBlock config and summary behavior", () => {
  test("applies defaults when config is empty", async () => {
    const config = parseOrchestratorStateConfig({})
    expect(config).toEqual({
      show_agent_list: true,
      only_active_agents: true,
      show_config_json: false,
    })
  })

  test("respects explicit config flags", async () => {
    const config = parseOrchestratorStateConfig({
      show_agent_list: false,
      only_active_agents: false,
      show_config_json: true,
    })
    expect(config).toEqual({
      show_agent_list: false,
      only_active_agents: false,
      show_config_json: true,
    })
  })

  test("default summary filters to active agents and active orchestrators", async () => {
    const config = parseOrchestratorStateConfig({})
    const agents = [
      makeAgent({ id: "a1", is_enabled: true, is_coordinator: false }),
      makeAgent({ id: "a2", is_enabled: true, is_coordinator: true }),
      makeAgent({ id: "a3", is_enabled: false, is_coordinator: true }),
    ]
    const summary = summarizeOrchestratorState({ config, roomAgents: agents })

    expect(summary.filteredAgents.map((agent) => agent.id)).toEqual([
      "a1",
      "a2",
    ])
    expect(summary.activeAgents.map((agent) => agent.id)).toEqual(["a1", "a2"])
    expect(summary.orchestrators.map((agent) => agent.id)).toEqual(["a2"])
  })

  test("unfiltered summary includes inactive agents and inactive orchestrators", async () => {
    const config = parseOrchestratorStateConfig({ only_active_agents: false })
    const agents = [
      makeAgent({ id: "a1", is_enabled: true, is_coordinator: false }),
      makeAgent({ id: "a2", is_enabled: false, is_coordinator: true }),
    ]
    const summary = summarizeOrchestratorState({ config, roomAgents: agents })

    expect(summary.filteredAgents.map((agent) => agent.id)).toEqual([
      "a1",
      "a2",
    ])
    expect(summary.activeAgents.map((agent) => agent.id)).toEqual(["a1"])
    expect(summary.orchestrators.map((agent) => agent.id)).toEqual(["a2"])
  })
})

test.describe("ContributionFeedBlock config and message selection behavior", () => {
  test("applies config defaults and max_items normalization", async () => {
    expect(parseContributionFeedConfig({})).toEqual({
      max_items: 12,
      include_internal: false,
      show_sender_type: false,
      show_timestamps: true,
      show_config_json: false,
    })

    expect(parseContributionFeedConfig({ max_items: 3.9 }).max_items).toBe(3)
    expect(parseContributionFeedConfig({ max_items: 0 }).max_items).toBe(12)
  })

  test("filters internal messages by default", async () => {
    const config = parseContributionFeedConfig({})
    const messages = [
      makeMessage({ message_id: "u1", sender_type: "user" }),
      makeMessage({ message_id: "a1", sender_type: "agent" }),
      makeMessage({ message_id: "i1", sender_type: "agent_internal" }),
    ]
    const selection = selectContributionFeedMessages({ config, messages })

    expect(selection.filtered.map((msg) => msg.message_id)).toEqual([
      "u1",
      "a1",
    ])
    expect(selection.recentMessages.map((msg) => msg.message_id)).toEqual([
      "u1",
      "a1",
    ])
  })

  test("include_internal=true keeps internal messages", async () => {
    const config = parseContributionFeedConfig({ include_internal: true })
    const messages = [
      makeMessage({ message_id: "u1", sender_type: "user" }),
      makeMessage({ message_id: "i1", sender_type: "agent_internal" }),
    ]
    const selection = selectContributionFeedMessages({ config, messages })
    expect(selection.filtered.map((msg) => msg.message_id)).toEqual([
      "u1",
      "i1",
    ])
  })

  test("sorts by recency descending and enforces max_items", async () => {
    const config = parseContributionFeedConfig({
      max_items: 2,
      include_internal: true,
    })
    const messages = [
      makeMessage({
        message_id: "m1",
        created_at: new Date("2026-02-22T09:00:00.000Z"),
      }),
      makeMessage({
        message_id: "m2",
        created_at: new Date("2026-02-22T11:00:00.000Z"),
      }),
      makeMessage({
        message_id: "m3",
        created_at: new Date("2026-02-22T10:00:00.000Z"),
      }),
    ]
    const selection = selectContributionFeedMessages({ config, messages })

    expect(selection.recentMessages.map((msg) => msg.message_id)).toEqual([
      "m2",
      "m3",
    ])
  })

  test("sender type formatting normalizes agent_internal label", async () => {
    expect(formatContributionSenderType("agent_internal")).toBe(
      "agent/internal",
    )
    expect(formatContributionSenderType("agent")).toBe("agent")
    expect(formatContributionSenderType("user")).toBe("user")
  })
})
