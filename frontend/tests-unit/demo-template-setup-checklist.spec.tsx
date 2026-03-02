import { expect, test } from "@playwright/test"
import type { ReactNode } from "react"
import { DemoTemplateSetupChecklist } from "@/components/Demo/builder/DemoTemplateSetupChecklist"
import {
  createCompositionTemplate,
  resolveTemplateChecklistStatus,
  validateCompositionSemantics,
} from "@/components/Demo/builder/demoBuilderSchema"

const VALID_STORY_ID = "11111111-1111-4111-8111-111111111111"

interface ElementLike {
  props?: {
    children?: ReactNode
    href?: string
  }
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
  if (typeof node !== "object") return out
  const element = node as ElementLike
  out.push(element)
  collectElements(element.props?.children as ReactNode, out)
  return out
}

function hasText(node: ReactNode, text: string): boolean {
  if (typeof node === "string") return node.includes(text)
  if (Array.isArray(node))
    return node.some((child) => hasText(child as ReactNode, text))
  if (!node || typeof node !== "object") return false
  return hasText((node as ElementLike).props?.children as ReactNode, text)
}

test.describe("DemoTemplateSetupChecklist", () => {
  test("shows unresolved deep links for pending checklist items", async () => {
    const composition = createCompositionTemplate("composition_a_baseline")
    composition.metadata_json = {}
    const checklistStatus = resolveTemplateChecklistStatus({
      templateId: "composition_a_baseline",
      composition,
      semanticIssues: validateCompositionSemantics(composition),
      confirmations: {},
    })

    const element = DemoTemplateSetupChecklist({
      templateId: "composition_a_baseline",
      templateLabel: "Composition A",
      checklistStatus,
      isDismissed: false,
      composition,
      confirmations: {},
      onDismiss: () => {},
      onResume: () => {},
      onStoryIdChange: () => {},
      onRuntimePolicyChange: () => {},
      onPersonaPolicyChange: () => {},
      onChatModeChange: () => {},
      onFixedUserPersonaIdChange: () => {},
      onAssumptionConfirmed: () => {},
      onOpenStoryPicker: () => {},
      onOpenPersonaPicker: () => {},
    })

    const links = collectElements(element)
      .map((candidate) => candidate.props?.href)
      .filter((href): href is string => Boolean(href))

    expect(links).toContain("#template-checklist-item-story_id")
    expect(hasText(element, "Pick Story")).toBeTruthy()
    expect(hasText(element, "unresolved setup item")).toBeTruthy()
  })

  test("shows template setup complete banner when all checklist items resolve", async () => {
    const composition = createCompositionTemplate("composition_a_baseline")
    composition.metadata_json = { story_id: VALID_STORY_ID }
    const checklistStatus = resolveTemplateChecklistStatus({
      templateId: "composition_a_baseline",
      composition,
      semanticIssues: validateCompositionSemantics(composition),
      confirmations: {
        runtime_policy: true,
        chat_mode: true,
      },
    })

    const element = DemoTemplateSetupChecklist({
      templateId: "composition_a_baseline",
      templateLabel: "Composition A",
      checklistStatus,
      isDismissed: false,
      composition,
      confirmations: {
        runtime_policy: true,
        chat_mode: true,
      },
      onDismiss: () => {},
      onResume: () => {},
      onStoryIdChange: () => {},
      onRuntimePolicyChange: () => {},
      onPersonaPolicyChange: () => {},
      onChatModeChange: () => {},
      onFixedUserPersonaIdChange: () => {},
      onAssumptionConfirmed: () => {},
      onOpenStoryPicker: () => {},
      onOpenPersonaPicker: () => {},
    })

    expect(hasText(element, "Template setup complete")).toBeTruthy()
  })

  test("shows persona quick action for persona-related assumptions", async () => {
    const composition = createCompositionTemplate(
      "composition_b_runtime_coupled",
    )
    composition.persona_policy = "fixed_user_persona"
    composition.fixed_user_persona_id = null
    const checklistStatus = resolveTemplateChecklistStatus({
      templateId: "composition_b_runtime_coupled",
      composition,
      semanticIssues: validateCompositionSemantics(composition),
      confirmations: {},
    })

    const element = DemoTemplateSetupChecklist({
      templateId: "composition_b_runtime_coupled",
      templateLabel: "Composition B",
      checklistStatus,
      isDismissed: false,
      composition,
      confirmations: {},
      onDismiss: () => {},
      onResume: () => {},
      onStoryIdChange: () => {},
      onRuntimePolicyChange: () => {},
      onPersonaPolicyChange: () => {},
      onChatModeChange: () => {},
      onFixedUserPersonaIdChange: () => {},
      onAssumptionConfirmed: () => {},
      onOpenStoryPicker: () => {},
      onOpenPersonaPicker: () => {},
    })

    expect(hasText(element, "Pick Persona")).toBeTruthy()
  })
})
