export const CLICK_PROMPT_DISPATCH_KIND = "click_prompt_dispatch.v1"
const LEGACY_CLICK_SOURCE_SELECTOR = "pre code, code"
const DEFAULT_CLICK_SOURCE_SELECTOR = "pre, pre code, code"

export interface ClickPromptDispatchConfig {
  kind: typeof CLICK_PROMPT_DISPATCH_KIND
  enabled: boolean
  trigger: {
    selector: string
    maxSourceChars: number
  }
  modal: {
    title: string
    helperText: string
    placeholder: string
    submitLabel: string
    cancelLabel: string
    multiline: boolean
    maxMessageChars: number
  }
  dispatch: {
    target: "hidden_chat_panel"
    targetPanelId: string | null
    format: "json" | "text"
    textPrefix: string
    enforceRegisteredReceiver: boolean
  }
}

export interface ClickPromptDispatchEnvelope {
  event: "demo_block_click_prompt_dispatch.v1"
  block: {
    id: string
    title: string | null
    type: string
  }
  selected_source: string | null
  user_message: string
  target_panel_id: string | null
}

export interface DemoInteractionSourceBlock {
  id?: unknown
  title?: unknown
  type?: unknown
}

export interface InteractionReceiverRegistration {
  receiverId: string
  panelId: string
  panelKind: string
  accepts: string[]
}

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function getNestedRecord(
  value: unknown,
  path: string[],
): Record<string, unknown> | null {
  let current: unknown = value
  for (const segment of path) {
    if (!isObjectRecord(current)) return null
    current = current[segment]
  }
  return isObjectRecord(current) ? current : null
}

function getNestedString(value: unknown, path: string[]): string | null {
  let current: unknown = value
  for (const segment of path) {
    if (!isObjectRecord(current)) return null
    current = current[segment]
  }
  if (typeof current !== "string") return null
  const trimmed = current.trim()
  return trimmed.length > 0 ? trimmed : null
}

function getNestedBoolean(value: unknown, path: string[]): boolean | null {
  let current: unknown = value
  for (const segment of path) {
    if (!isObjectRecord(current)) return null
    current = current[segment]
  }
  return typeof current === "boolean" ? current : null
}

function getNestedNumber(value: unknown, path: string[]): number | null {
  let current: unknown = value
  for (const segment of path) {
    if (!isObjectRecord(current)) return null
    current = current[segment]
  }
  if (typeof current !== "number" || !Number.isFinite(current)) return null
  return current
}

export function parseClickPromptDispatchConfig(
  configJson: unknown,
): ClickPromptDispatchConfig | null {
  const interaction = getNestedRecord(configJson, ["interaction"])
  if (!interaction) return null

  const rawKind = interaction.kind
  if (rawKind !== CLICK_PROMPT_DISPATCH_KIND) return null

  const rawEnabled = interaction.enabled
  const enabled = typeof rawEnabled === "boolean" ? rawEnabled : true
  const rawTriggerSelector = getNestedString(interaction, [
    "trigger",
    "selector",
  ])
  const triggerSelector =
    rawTriggerSelector === LEGACY_CLICK_SOURCE_SELECTOR
      ? DEFAULT_CLICK_SOURCE_SELECTOR
      : (rawTriggerSelector ?? DEFAULT_CLICK_SOURCE_SELECTOR)
  const maxSourceCharsRaw = getNestedNumber(interaction, [
    "trigger",
    "max_source_chars",
  ])
  const maxSourceChars =
    maxSourceCharsRaw && maxSourceCharsRaw > 0
      ? Math.floor(maxSourceCharsRaw)
      : 1200

  const modalTitle =
    getNestedString(interaction, ["modal", "title"]) ?? "Quick input"
  const modalHelperText =
    getNestedString(interaction, ["modal", "helper_text"]) ??
    "Provide context to send to the configured chat receiver."
  const modalPlaceholder =
    getNestedString(interaction, ["modal", "placeholder"]) ??
    "Describe what you want to ask about the selected content..."
  const submitLabel =
    getNestedString(interaction, ["modal", "submit_label"]) ?? "Send"
  const cancelLabel =
    getNestedString(interaction, ["modal", "cancel_label"]) ?? "Cancel"
  const multiline =
    getNestedBoolean(interaction, ["modal", "multiline"]) ?? false
  const maxMessageCharsRaw = getNestedNumber(interaction, [
    "modal",
    "max_message_chars",
  ])
  const maxMessageChars =
    maxMessageCharsRaw && maxMessageCharsRaw > 0
      ? Math.floor(maxMessageCharsRaw)
      : 1000

  const dispatchTargetRaw = getNestedString(interaction, ["dispatch", "target"])
  const dispatchTarget =
    dispatchTargetRaw === "hidden_chat_panel"
      ? "hidden_chat_panel"
      : "hidden_chat_panel"
  const targetPanelId =
    getNestedString(interaction, ["dispatch", "target_panel_id"]) ?? null
  const formatRaw = getNestedString(interaction, ["dispatch", "format"])
  const dispatchFormat = formatRaw === "text" ? "text" : "json"
  const textPrefix =
    getNestedString(interaction, ["dispatch", "text_prefix"]) ??
    "[demo-block-interaction]"
  const enforceRegisteredReceiver =
    getNestedBoolean(interaction, [
      "dispatch",
      "enforce_registered_receiver",
    ]) ?? false

  return {
    kind: CLICK_PROMPT_DISPATCH_KIND,
    enabled,
    trigger: {
      selector: triggerSelector,
      maxSourceChars,
    },
    modal: {
      title: modalTitle,
      helperText: modalHelperText,
      placeholder: modalPlaceholder,
      submitLabel,
      cancelLabel,
      multiline,
      maxMessageChars,
    },
    dispatch: {
      target: dispatchTarget,
      targetPanelId,
      format: dispatchFormat,
      textPrefix,
      enforceRegisteredReceiver,
    },
  }
}

export function resolveInteractionReceiverRegistration(panel: {
  id?: unknown
  kind?: unknown
  options?: unknown
}): InteractionReceiverRegistration | null {
  const panelKind = typeof panel.kind === "string" ? panel.kind : null
  const panelId = typeof panel.id === "string" ? panel.id.trim() : ""
  if (!panelKind || panelId.length === 0) return null

  const options = isObjectRecord(panel.options) ? panel.options : null
  const receiver = options
    ? getNestedRecord(options, ["interaction_receiver"])
    : null
  if (!receiver) return null

  const enabled = getNestedBoolean(receiver, ["enabled"]) ?? false
  if (!enabled) return null

  const receiverId =
    getNestedString(receiver, ["receiver_id"]) ??
    getNestedString(receiver, ["registration_id"]) ??
    panelId

  const acceptsRaw = receiver.accepts
  const accepts = Array.isArray(acceptsRaw)
    ? acceptsRaw
        .filter((item): item is string => typeof item === "string")
        .map((item) => item.trim())
        .filter((item) => item.length > 0)
    : [CLICK_PROMPT_DISPATCH_KIND]

  return {
    receiverId,
    panelId,
    panelKind,
    accepts: accepts.length > 0 ? accepts : [CLICK_PROMPT_DISPATCH_KIND],
  }
}

export function buildClickPromptDispatchMessage(params: {
  block: DemoInteractionSourceBlock
  config: ClickPromptDispatchConfig
  selectedSource: string | null
  userMessage: string
}): string {
  const { block, config, selectedSource, userMessage } = params
  const payload: ClickPromptDispatchEnvelope = {
    event: "demo_block_click_prompt_dispatch.v1",
    block: {
      id: String(block.id ?? ""),
      title: typeof block.title === "string" ? block.title : null,
      type: String(block.type ?? "content"),
    },
    selected_source: selectedSource,
    user_message: userMessage,
    target_panel_id: config.dispatch.targetPanelId,
  }

  if (config.dispatch.format === "text") {
    return `${config.dispatch.textPrefix} ${JSON.stringify(payload)}`
  }
  return JSON.stringify(payload)
}

export function extractSourceTextFromClick(params: {
  root: HTMLElement | null
  target: EventTarget | null
  selector: string
  maxChars: number
}): string | null {
  const { root, target, selector, maxChars } = params
  if (!root || !(target instanceof Element)) return null
  const sourceNode = target.closest(selector)
  if (!sourceNode || !root.contains(sourceNode)) return null
  const rawText = sourceNode.textContent
  if (typeof rawText !== "string") return null
  const trimmed = rawText.trim()
  if (!trimmed) return null
  return trimmed.slice(0, Math.max(1, maxChars))
}

export function createClickPromptDispatchStarterConfig(): Record<
  string,
  unknown
> {
  return {
    interaction: {
      kind: CLICK_PROMPT_DISPATCH_KIND,
      enabled: true,
      trigger: {
        selector: DEFAULT_CLICK_SOURCE_SELECTOR,
        max_source_chars: 1200,
      },
      modal: {
        title: "Ask about selected code",
        helper_text:
          "This sends your message plus clicked-code context to the configured chat receiver.",
        placeholder: "What should the invisible chat analyze or explain?",
        submit_label: "Send",
        cancel_label: "Cancel",
        multiline: false,
        max_message_chars: 1000,
      },
      dispatch: {
        target: "hidden_chat_panel",
        target_panel_id: null,
        format: "json",
        text_prefix: "[demo-block-interaction]",
        enforce_registered_receiver: false,
      },
    },
  }
}
