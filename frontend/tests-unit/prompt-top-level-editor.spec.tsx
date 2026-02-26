import { expect, test } from "@playwright/test"
import type { ReactNode } from "react"
import { PromptTopLevelEditor } from "@/components/Prompt/builder/PromptTopLevelEditor"
import { createPromptDraftForCapabilityTests } from "@/components/Prompt/builder/promptBuilderCapabilityRegistry"

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
    node &&
      typeof node === "object" &&
      "type" in (node as Record<string, unknown>) &&
      "props" in (node as Record<string, unknown>),
  )
}

function collectElements(
  node: ReactNode,
  out: ElementLike[] = [],
): ElementLike[] {
  if (node === null || node === undefined || typeof node === "boolean")
    return out
  if (Array.isArray(node)) {
    for (const child of node) collectElements(child as ReactNode, out)
    return out
  }
  if (!isElementLike(node)) return out
  out.push(node)
  collectElements(node.props.children as ReactNode, out)
  return out
}

function findInputElement(root: ReactNode, placeholder: string): ElementLike {
  const elements = collectElements(root)
  const found = elements.find(
    (element) =>
      typeof element.props.onChange === "function" &&
      element.props.placeholder === placeholder,
  )
  expect(found).toBeTruthy()
  return found as ElementLike
}

test.describe("PromptTopLevelEditor", () => {
  test("uses capability normalization hook for provider id input", async () => {
    const draft = createPromptDraftForCapabilityTests()
    const nextDrafts: Array<typeof draft> = []
    const fieldErrors: Array<Record<string, string>> = []

    const element = PromptTopLevelEditor({
      draft,
      fieldErrors: {},
      onFieldErrorsChange: (next) => fieldErrors.push(next),
      onDraftChange: (next) => nextDrafts.push(next),
    })

    const input = findInputElement(element, "Access Provider")
    input.props.onChange?.({ target: { value: "  provider-next  " } })

    expect(nextDrafts).toHaveLength(1)
    expect(nextDrafts[0]?.provider.user_access_provider_id).toBe(
      "provider-next",
    )
    expect(fieldErrors).toEqual([])
  })

  test("uses dynamic capability options for id controls when provided", async () => {
    const draft = createPromptDraftForCapabilityTests()
    const nextDrafts: Array<typeof draft> = []

    const element = PromptTopLevelEditor({
      draft,
      fieldErrors: {},
      onFieldErrorsChange: () => {},
      onDraftChange: (next) => nextDrafts.push(next),
      capabilityOptions: {
        "provider.user_access_provider_id": [
          { value: "provider-a", label: "Provider A" },
          { value: "provider-b", label: "Provider B" },
        ],
      },
    })

    const selectElement = collectElements(element).find(
      (candidate) =>
        typeof (candidate.props as any).onValueChange === "function",
    )
    expect(selectElement).toBeTruthy()
    ;(selectElement!.props as any).onValueChange("provider-b")

    expect(nextDrafts).toHaveLength(1)
    expect(nextDrafts[0]?.provider.user_access_provider_id).toBe("provider-b")
  })
})
