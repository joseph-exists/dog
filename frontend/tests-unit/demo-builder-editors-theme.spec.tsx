import { expect, test } from "@playwright/test"
import type { ReactNode } from "react"
import { DemoBlockEditor } from "@/components/Demo/builder/DemoBlockEditor"
import { DemoPanelEditor } from "@/components/Demo/builder/DemoPanelEditor"
import { DemoTopLevelEditor } from "@/components/Demo/builder/DemoTopLevelEditor"
import { createBlockTemplate, createEmptyComposition, createPanelTemplate } from "@/components/Demo/builder/demoBuilderSchema"

interface ElementLike {
  type: unknown
  props: {
    children?: ReactNode
    placeholder?: string
    value?: unknown
    onChange?: (event: { target: { value: string } }) => void
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

function collectElements(node: ReactNode, out: ElementLike[] = []): ElementLike[] {
  if (node === null || node === undefined || typeof node === "boolean") return out
  if (Array.isArray(node)) {
    for (const child of node) collectElements(child as ReactNode, out)
    return out
  }
  if (!isElementLike(node)) return out
  out.push(node)
  collectElements(node.props.children as ReactNode, out)
  return out
}

function findInputElement(
  root: ReactNode,
  predicate: (element: ElementLike) => boolean,
): ElementLike {
  const elements = collectElements(root)
  const found = elements.find((element) => typeof element.props.onChange === "function" && predicate(element))
  expect(found).toBeTruthy()
  return found as ElementLike
}

test.describe("Demo builder editor theme field round-trip", () => {
  test("top-level theme inputs normalize empty values to null", async () => {
    const composition = createEmptyComposition()
    composition.page_theme_id = "page-old"
    composition.cards_theme_id = "cards-old"

    const pageThemeValues: Array<string | null> = []
    const cardsThemeValues: Array<string | null> = []

    const element = DemoTopLevelEditor({
      selectedDemoConfigId: "demo-1",
      isLoadingComposition: false,
      composition,
      fieldErrors: {},
      onLayoutModeChange: () => {},
      onRuntimePolicyChange: () => {},
      onPersonaPolicyChange: () => {},
      onChatModeChange: () => {},
      onFixedUserPersonaIdChange: () => {},
      onPageThemeIdChange: (value) => pageThemeValues.push(value),
      onCardsThemeIdChange: (value) => cardsThemeValues.push(value),
      onMetadataJsonBlur: () => {},
      onPresentationJsonBlur: () => {},
    })

    const pageThemeInput = findInputElement(
      element,
      (candidate) => candidate.props.placeholder === "Page Theme ID",
    )
    pageThemeInput.props.onChange?.({ target: { value: "page-next" } })
    pageThemeInput.props.onChange?.({ target: { value: "   " } })

    const cardsThemeInput = findInputElement(
      element,
      (candidate) => candidate.props.placeholder === "Cards Theme ID",
    )
    cardsThemeInput.props.onChange?.({ target: { value: "cards-next" } })
    cardsThemeInput.props.onChange?.({ target: { value: "" } })

    expect(pageThemeValues).toEqual(["page-next", null])
    expect(cardsThemeValues).toEqual(["cards-next", null])
  })

  test("panel theme input updates patch payload with string and null values", async () => {
    const panel = createPanelTemplate("chat")
    panel.theme_id = "panel-old"
    const patches: Array<{ index: number; patch: Record<string, unknown> }> = []

    const element = DemoPanelEditor({
      composition: createEmptyComposition(),
      panels: [panel],
      fieldErrors: {},
      onAddPanel: () => {},
      onRemovePanel: () => {},
      onUpdatePanel: (index, patch) => patches.push({ index, patch }),
      onCommitPanelJsonField: () => {},
    })

    const panelThemeInput = findInputElement(
      element,
      (candidate) => candidate.props.placeholder === "Theme ID" && candidate.props.value === "panel-old",
    )
    panelThemeInput.props.onChange?.({ target: { value: "panel-next" } })
    panelThemeInput.props.onChange?.({ target: { value: "  " } })

    expect(patches).toEqual([
      { index: 0, patch: { theme_id: "panel-next" } },
      { index: 0, patch: { theme_id: null } },
    ])
  })

  test("block theme input updates patch payload with string and null values", async () => {
    const block = createBlockTemplate("content")
    block.theme_id = "block-old"
    const patches: Array<{ index: number; patch: Record<string, unknown> }> = []

    const element = DemoBlockEditor({
      composition: createEmptyComposition(),
      blocks: [block],
      fieldErrors: {},
      onAddBlock: () => {},
      onRemoveBlock: () => {},
      onUpdateBlock: (index, patch) => patches.push({ index, patch }),
      onCommitBlockJsonField: () => {},
    })

    const blockThemeInput = findInputElement(
      element,
      (candidate) => candidate.props.placeholder === "Theme ID" && candidate.props.value === "block-old",
    )
    blockThemeInput.props.onChange?.({ target: { value: "block-next" } })
    blockThemeInput.props.onChange?.({ target: { value: "" } })

    expect(patches).toEqual([
      { index: 0, patch: { theme_id: "block-next" } },
      { index: 0, patch: { theme_id: null } },
    ])
  })
})
