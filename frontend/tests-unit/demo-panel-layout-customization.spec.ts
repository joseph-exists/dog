import { expect, test } from "@playwright/test"
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
} from "@/components/Demo/demoPanelLayoutCustomization"

test.describe("demoPanelLayoutCustomization helpers", () => {
  test("creates local-storage keys per demo scope", async () => {
    expect(buildDemoPanelLayoutStorageKey("demo-123")).toBe(
      "demo-panel-layout:demo-123",
    )
    expect(buildDemoCollapseStorageKey("demo-123")).toBe(
      "demo-view-collapsed:demo-123",
    )
  })

  test("reconciles stored layout against authored panels", async () => {
    const authored = createDemoPanelLayoutItems([
      { id: "runtime", kind: "storyRuntime", title: "Story Runtime" },
      { id: "chat", kind: "chat", title: "Chat", prominence: "auxiliary" },
      { id: "participants", kind: "participantPanel", title: "Participants" },
    ])
    const stored = [
      {
        id: "participants",
        kind: "participantPanel",
        title: "Participants",
        prominence: "auxiliary" as const,
        hidden: true,
      },
      {
        id: "runtime",
        kind: "storyRuntime",
        title: "Story Runtime",
        prominence: "primary" as const,
        hidden: false,
      },
      {
        id: "missing",
        kind: "debug",
        title: "Missing",
        prominence: "auxiliary" as const,
        hidden: false,
      },
    ]

    expect(reconcileDemoPanelLayoutItems(authored, stored)).toEqual([
      {
        id: "participants",
        kind: "participantPanel",
        title: "Participants",
        prominence: "auxiliary",
        hidden: true,
      },
      {
        id: "runtime",
        kind: "storyRuntime",
        title: "Story Runtime",
        prominence: "primary",
        hidden: false,
      },
      {
        id: "chat",
        kind: "chat",
        title: "Chat",
        prominence: "auxiliary",
        hidden: false,
      },
    ])
  })

  test("applies visibility and prominence overrides without mutating authored records", async () => {
    const authoredPanels = [
      { id: "runtime", prominence: "primary" as const, value: "runtime" },
      { id: "chat", prominence: "primary" as const, value: "chat" },
      { id: "participants", prominence: "auxiliary" as const, value: "people" },
    ]
    const items = [
      {
        id: "participants",
        kind: "participantPanel",
        title: "Participants",
        prominence: "primary" as const,
        hidden: false,
      },
      {
        id: "runtime",
        kind: "storyRuntime",
        title: "Story Runtime",
        prominence: "auxiliary" as const,
        hidden: false,
      },
      {
        id: "chat",
        kind: "chat",
        title: "Chat",
        prominence: "primary" as const,
        hidden: true,
      },
    ]

    expect(applyDemoPanelLayoutItems(authoredPanels, items)).toEqual([
      { id: "participants", prominence: "primary", value: "people" },
      { id: "runtime", prominence: "auxiliary", value: "runtime" },
    ])
    expect(authoredPanels[0]?.prominence).toBe("primary")
    expect(authoredPanels[1]?.prominence).toBe("primary")
  })

  test("reads only valid stored payloads", async () => {
    const validStorage = {
      getItem: () =>
        JSON.stringify({
          version: 1,
          items: [
            {
              id: "chat",
              kind: "chat",
              title: "Chat",
              prominence: "primary",
              hidden: false,
            },
          ],
        }),
    }
    const invalidStorage = {
      getItem: () =>
        JSON.stringify({
          version: 1,
          items: [{ id: "chat", hidden: false }],
        }),
    }

    expect(
      readDemoPanelLayoutItems(validStorage, "demo-panel-layout:demo"),
    ).toEqual([
      {
        id: "chat",
        kind: "chat",
        title: "Chat",
        prominence: "primary",
        hidden: false,
      },
    ])
    expect(
      readDemoPanelLayoutItems(invalidStorage, "demo-panel-layout:demo"),
    ).toBeNull()
  })

  test("compares layout arrays structurally", async () => {
    const left = createDemoPanelLayoutItems([
      { id: "chat", kind: "chat", title: "Chat" },
    ])
    const right = createDemoPanelLayoutItems([
      { id: "chat", kind: "chat", title: "Chat" },
    ])
    const changed = createDemoPanelLayoutItems([
      { id: "chat", kind: "chat", title: "Chat", prominence: "auxiliary" },
    ])

    expect(demoPanelLayoutItemsEqual(left, right)).toBeTruthy()
    expect(demoPanelLayoutItemsEqual(left, changed)).toBeFalsy()
  })

  test("reads and reconciles collapsed ids against current demo content", async () => {
    const storage = {
      getItem: () => JSON.stringify(["panel:chat", "block:briefing", 12, null]),
    }

    expect(readDemoCollapsedIds(storage, "demo-view-collapsed:demo")).toEqual([
      "panel:chat",
      "block:briefing",
    ])
    expect(
      reconcileDemoCollapsedIds(
        ["panel:chat", "block:briefing", "panel:missing"],
        ["panel:chat", "block:briefing"],
      ),
    ).toEqual(["panel:chat", "block:briefing"])
  })
})
