import { expect, test } from "@playwright/test"
import type { ReactNode } from "react"
import { DemoBlockEditor } from "@/components/Demo/builder/DemoBlockEditor"
import { DemoPresentationGuidedFields } from "@/components/Demo/builder/DemoPresentationGuidedFields"
import { getBlockCapabilityByType } from "@/components/Demo/builder/demoBuilderCapabilityRegistry"
import { createBlockTemplate, createEmptyComposition } from "@/components/Demo/builder/demoBuilderSchema"

interface ElementLike {
  type: unknown
  props: {
    children?: ReactNode
    placeholder?: string
    defaultValue?: unknown
    onChange?: (event: { target: { value: string } }) => void
    onBlur?: (event: { target: { value: string } }) => void
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

function collectText(node: ReactNode, out: string[] = []): string[] {
  if (typeof node === "string") {
    out.push(node)
    return out
  }
  if (node === null || node === undefined || typeof node === "boolean") return out
  if (Array.isArray(node)) {
    for (const child of node) collectText(child as ReactNode, out)
    return out
  }
  if (!isElementLike(node)) return out
  collectText(node.props.children as ReactNode, out)
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

function findTextareaElement(
  root: ReactNode,
  predicate: (element: ElementLike) => boolean,
): ElementLike {
  const elements = collectElements(root)
  const found = elements.find((element) => typeof element.props.onBlur === "function" && predicate(element))
  expect(found).toBeTruthy()
  return found as ElementLike
}

function expectAdvancedFallbackLabel(root: ReactNode) {
  const text = collectText(root).join(" ")
  expect(text).toContain("Advanced JSON Fallback")
}

test.describe("Demo builder guided presentation controls", () => {
  test("storyMetadata guided control updates nested presentation_json and keeps advanced fallback", async () => {
    const block = createBlockTemplate("storyMetadata")
    block.presentation_json = { tokens: { existing: "story" } }
    const guidedPatches: Array<Record<string, unknown>> = []
    const commits: Array<{ index: number; fieldKey: string; raw: string }> = []
    const capability = getBlockCapabilityByType("storyMetadata")

    const guidedElement = DemoPresentationGuidedFields({
      value: block.presentation_json ?? {},
      fieldSpecs: capability?.presentationFieldSpecs ?? [],
      onChange: (nextValue) => guidedPatches.push(nextValue),
    })

    const guidedInput = findInputElement(
      guidedElement,
      (candidate) => candidate.props.placeholder === "Card Pattern CSS",
    )
    guidedInput.props.onChange?.({ target: { value: "repeating-linear-gradient(...)" } })

    expect(guidedPatches[0]).toEqual({
      tokens: { existing: "story" },
      backgrounds: { card_pattern: { css: "repeating-linear-gradient(...)" } },
    })

    const editorElement = DemoBlockEditor({
      composition: createEmptyComposition(),
      blocks: [block],
      fieldErrors: {},
      onAddBlock: () => {},
      onRemoveBlock: () => {},
      onUpdateBlock: () => {},
      onCommitBlockJsonField: (index, fieldKey, raw) => commits.push({ index, fieldKey, raw }),
    })

    expectAdvancedFallbackLabel(editorElement)

    const fallbackTextarea = findTextareaElement(
      editorElement,
      (candidate) => String(candidate.props.defaultValue ?? "").includes("\"existing\": \"story\""),
    )
    fallbackTextarea.props.onBlur?.({ target: { value: "{\"tokens\":{\"existing\":\"story-updated\"}}" } })

    expect(commits).toContainEqual({
      index: 0,
      fieldKey: "presentation_json",
      raw: "{\"tokens\":{\"existing\":\"story-updated\"}}",
    })
  })

  test("orchestratorState guided control updates nested presentation_json and keeps advanced fallback", async () => {
    const block = createBlockTemplate("orchestratorState")
    block.presentation_json = { tokens: { existing: "orchestrator" } }
    const guidedPatches: Array<Record<string, unknown>> = []
    const commits: Array<{ index: number; fieldKey: string; raw: string }> = []
    const capability = getBlockCapabilityByType("orchestratorState")

    const guidedElement = DemoPresentationGuidedFields({
      value: block.presentation_json ?? {},
      fieldSpecs: capability?.presentationFieldSpecs ?? [],
      onChange: (nextValue) => guidedPatches.push(nextValue),
    })

    const guidedInput = findInputElement(
      guidedElement,
      (candidate) => candidate.props.placeholder === "linear-gradient(...)",
    )
    guidedInput.props.onChange?.({ target: { value: "linear-gradient(120deg, rgba(1,2,3,0.5), rgba(4,5,6,0.2))" } })

    expect(guidedPatches[0]).toEqual({
      tokens: { existing: "orchestrator" },
      overlays: {
        block_header: {
          css: "linear-gradient(120deg, rgba(1,2,3,0.5), rgba(4,5,6,0.2))",
        },
      },
    })

    const editorElement = DemoBlockEditor({
      composition: createEmptyComposition(),
      blocks: [block],
      fieldErrors: {},
      onAddBlock: () => {},
      onRemoveBlock: () => {},
      onUpdateBlock: () => {},
      onCommitBlockJsonField: (index, fieldKey, raw) => commits.push({ index, fieldKey, raw }),
    })

    expectAdvancedFallbackLabel(editorElement)

    const fallbackTextarea = findTextareaElement(
      editorElement,
      (candidate) => String(candidate.props.defaultValue ?? "").includes("\"existing\": \"orchestrator\""),
    )
    fallbackTextarea.props.onBlur?.({ target: { value: "{\"tokens\":{\"existing\":\"orchestrator-updated\"}}" } })

    expect(commits).toContainEqual({
      index: 0,
      fieldKey: "presentation_json",
      raw: "{\"tokens\":{\"existing\":\"orchestrator-updated\"}}",
    })
  })

  test("contributionFeed guided control updates nested presentation_json and keeps advanced fallback", async () => {
    const block = createBlockTemplate("contributionFeed")
    block.presentation_json = { tokens: { existing: "feed" } }
    const guidedPatches: Array<Record<string, unknown>> = []
    const commits: Array<{ index: number; fieldKey: string; raw: string }> = []
    const capability = getBlockCapabilityByType("contributionFeed")

    const guidedElement = DemoPresentationGuidedFields({
      value: block.presentation_json ?? {},
      fieldSpecs: capability?.presentationFieldSpecs ?? [],
      onChange: (nextValue) => guidedPatches.push(nextValue),
    })

    const guidedInput = findInputElement(
      guidedElement,
      (candidate) => candidate.props.placeholder === "Row Highlight CSS",
    )
    guidedInput.props.onChange?.({ target: { value: "inset 0 0 0 1px rgba(255,255,255,0.06)" } })

    expect(guidedPatches[0]).toEqual({
      tokens: { existing: "feed" },
      effects: {
        message_row_highlight: {
          css: "inset 0 0 0 1px rgba(255,255,255,0.06)",
        },
      },
    })

    const editorElement = DemoBlockEditor({
      composition: createEmptyComposition(),
      blocks: [block],
      fieldErrors: {},
      onAddBlock: () => {},
      onRemoveBlock: () => {},
      onUpdateBlock: () => {},
      onCommitBlockJsonField: (index, fieldKey, raw) => commits.push({ index, fieldKey, raw }),
    })

    expectAdvancedFallbackLabel(editorElement)

    const fallbackTextarea = findTextareaElement(
      editorElement,
      (candidate) => String(candidate.props.defaultValue ?? "").includes("\"existing\": \"feed\""),
    )
    fallbackTextarea.props.onBlur?.({ target: { value: "{\"tokens\":{\"existing\":\"feed-updated\"}}" } })

    expect(commits).toContainEqual({
      index: 0,
      fieldKey: "presentation_json",
      raw: "{\"tokens\":{\"existing\":\"feed-updated\"}}",
    })
  })
})
