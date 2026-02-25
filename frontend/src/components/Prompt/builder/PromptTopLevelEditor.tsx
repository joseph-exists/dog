import { useMemo, useState, type ReactNode } from "react"
import {
  PROMPT_CAPABILITIES,
  normalizePromptCapabilityValue,
  type PromptCapability,
} from "@/components/Prompt/builder/promptBuilderCapabilityRegistry"
import {
  normalizePromptDraft,
  type PromptConfigDraft,
} from "@/components/Prompt/builder/promptBuilderSchema"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function getValueAtPath(source: Record<string, unknown>, path: string): unknown {
  const segments = path.split(".").filter((segment) => segment.length > 0)
  let current: unknown = source
  for (const segment of segments) {
    if (!isObjectRecord(current)) return undefined
    current = current[segment]
  }
  return current
}

function setValueAtPath(
  source: Record<string, unknown>,
  path: string,
  value: unknown,
): Record<string, unknown> {
  const segments = path.split(".").filter((segment) => segment.length > 0)
  if (segments.length === 0) return source
  const next = { ...source }
  let cursor: Record<string, unknown> = next

  for (let index = 0; index < segments.length - 1; index += 1) {
    const segment = segments[index]!
    const existing = cursor[segment]
    const branch = isObjectRecord(existing) ? { ...existing } : {}
    cursor[segment] = branch
    cursor = branch
  }

  const leaf = segments[segments.length - 1]!
  cursor[leaf] = value
  return next
}

function toPrettyJson(value: unknown): string {
  if (typeof value === "undefined") return "{}"
  return JSON.stringify(value, null, 2)
}

const CATEGORY_ORDER = [
  "provider",
  "model",
  "input",
  "params",
  "tools",
  "advanced",
] as const

type PromptCategory = (typeof CATEGORY_ORDER)[number]
type PromptEditorMode = "guided" | "full"

const CATEGORY_LABELS: Record<PromptCategory, string> = {
  provider: "Provider",
  model: "Model",
  input: "Input",
  params: "Parameters",
  tools: "Tools",
  advanced: "Advanced",
}

interface GuidedSectionSpec {
  id: string
  title: string
  why: string
  when: string
  avoid: string
  keys: string[]
}

const GUIDED_SECTION_SPECS: GuidedSectionSpec[] = [
  {
    id: "runtime",
    title: "1. Choose Runtime",
    why: "Provider and model determine capability coverage, quality profile, latency, and cost.",
    when: "Set this first for new configs or when moving prompts between accounts/providers.",
    avoid: "Avoid changing this mid-tuning unless you are intentionally re-baselining behavior.",
    keys: [
      "provider.user_access_provider_id",
      "provider.provider_kind",
      "model.model_id",
    ],
  },
  {
    id: "behavior",
    title: "2. Define Behavior",
    why: "Input structure tells the model what role to take and what task to perform.",
    when: "Use simple text for straightforward tasks, or messages when conversation structure matters.",
    avoid: "Avoid mixing input styles accidentally; keep one clear authoring pattern per config.",
    keys: [
      "input.kind",
      "input.text",
      "input.messages",
    ],
  },
  {
    id: "output",
    title: "3. Tune Output",
    why: "Parameters control creativity, response length, and sampling behavior.",
    when: "Adjust after baseline quality is acceptable and you need consistency or exploration.",
    avoid: "Avoid heavy parameter changes before prompt intent is stable.",
    keys: [
      "params.temperature",
      "params.top_p",
      "params.max_output_tokens",
    ],
  },
  {
    id: "tools",
    title: "4. Configure Tool Use",
    why: "Tool settings control whether the model can call external functions and how strict that requirement is.",
    when: "Enable when tasks require retrieval, actions, or structured operations beyond plain text generation.",
    avoid: "Avoid required tool mode unless your tool list and orchestration path are ready.",
    keys: [
      "tools",
    ],
  },
]

interface PromptTopLevelEditorProps {
  draft: PromptConfigDraft
  fieldErrors: Record<string, string>
  onFieldErrorsChange: (next: Record<string, string>) => void
  onDraftChange: (next: PromptConfigDraft) => void
  capabilityOptions?: Record<
    string,
    Array<{ value: string; label: string; disabled?: boolean }>
  >
  loadingCapabilityOptions?: Record<string, boolean>
}

export function PromptTopLevelEditor({
  draft,
  fieldErrors,
  onFieldErrorsChange,
  onDraftChange,
  capabilityOptions = {},
  loadingCapabilityOptions = {},
}: PromptTopLevelEditorProps) {
  const [editorMode, setEditorMode] = useState<PromptEditorMode>("guided")
  const draftRecord = draft as unknown as Record<string, unknown>
  const capabilityByKey = useMemo(
    () => new Map(PROMPT_CAPABILITIES.map((capability) => [capability.key, capability])),
    [],
  )

  function clearFieldError(key: string) {
    if (!fieldErrors[key]) return
    const next = { ...fieldErrors }
    delete next[key]
    onFieldErrorsChange(next)
  }

  function applyCapabilityValue(capability: PromptCapability, rawValue: unknown) {
    const normalizedValue = normalizePromptCapabilityValue(capability, rawValue, draft)
    const nextDraftRecord = setValueAtPath(draftRecord, capability.key, normalizedValue)
    onDraftChange(normalizePromptDraft(nextDraftRecord as Partial<PromptConfigDraft>))
    clearFieldError(capability.key)
  }

  function onJsonBlur(capability: PromptCapability, raw: string) {
    try {
      const parsed = JSON.parse(raw)
      applyCapabilityValue(capability, parsed)
    } catch {
      onFieldErrorsChange({
        ...fieldErrors,
        [capability.key]: "Invalid JSON.",
      })
    }
  }

  function renderCapabilityField(capability: PromptCapability): ReactNode {
    return (
      <div key={capability.key} className="space-y-1">
        <label className="text-xs text-muted-foreground">{capability.label}</label>
        {renderCapability(capability)}
        {fieldErrors[capability.key] && (
          <p className="text-xs text-destructive">{fieldErrors[capability.key]}</p>
        )}
      </div>
    )
  }

  function renderGuidedSection(section: GuidedSectionSpec): ReactNode {
    const sectionCapabilities = section.keys
      .map((key) => capabilityByKey.get(key))
      .filter((capability): capability is PromptCapability => Boolean(capability))
    if (sectionCapabilities.length === 0) return null
    return (
      <div key={section.id} className="space-y-3 rounded-md border bg-muted/30 p-3">
        <div className="space-y-1">
          <h3 className="text-sm font-medium">{section.title}</h3>
          <p className="text-xs text-muted-foreground">{section.why}</p>
          <p className="text-xs text-muted-foreground">
            <strong>When to use:</strong> {section.when}
          </p>
          <p className="text-xs text-muted-foreground">
            <strong>Avoid when:</strong> {section.avoid}
          </p>
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          {sectionCapabilities.map((capability) => renderCapabilityField(capability))}
        </div>
      </div>
    )
  }

  function renderCapability(capability: PromptCapability): ReactNode {
    const currentValue = getValueAtPath(draftRecord, capability.key)
    const keyedOptions = capabilityOptions[capability.key] ?? []
    const hasDynamicOptions = keyedOptions.length > 0

    if (
      hasDynamicOptions
      && (capability.control === "text" || capability.control === "id")
    ) {
      const currentString =
        typeof currentValue === "string" && currentValue.length > 0
          ? currentValue
          : "__none"
      const normalizedOptions = [...keyedOptions]
      if (
        currentString !== "__none"
        && !normalizedOptions.some((option) => option.value === currentString)
      ) {
        normalizedOptions.unshift({
          value: currentString,
          label: `${currentString} (unlisted)`,
        })
      }
      return (
        <Select
          value={currentString}
          onValueChange={(value) =>
            applyCapabilityValue(capability, value === "__none" ? null : value)}
        >
          <SelectTrigger>
            <SelectValue
              placeholder={
                loadingCapabilityOptions[capability.key]
                  ? "Loading options..."
                  : capability.label
              }
            />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__none">None</SelectItem>
            {normalizedOptions.map((option) => (
              <SelectItem
                key={option.value}
                value={option.value}
                disabled={option.disabled === true}
              >
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )
    }

    if (capability.control === "boolean") {
      return (
        <div className="h-9 flex items-center">
          <Switch
            checked={currentValue === true}
            onCheckedChange={(checked) => applyCapabilityValue(capability, checked)}
          />
        </div>
      )
    }
    if (capability.control === "enum") {
      return (
        <Select
          value={typeof currentValue === "string" && currentValue.length > 0 ? currentValue : "__none"}
          onValueChange={(value) => applyCapabilityValue(capability, value === "__none" ? null : value)}
        >
          <SelectTrigger>
            <SelectValue placeholder={capability.label} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__none">None</SelectItem>
            {(capability.enumValues ?? []).map((option) => (
              <SelectItem key={option} value={option}>
                {option}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )
    }
    if (capability.control === "number") {
      return (
        <Input
          value={typeof currentValue === "number" ? String(currentValue) : ""}
          placeholder={capability.placeholder ?? capability.label}
          onChange={(event) => {
            const raw = event.target.value.trim()
            if (raw.length === 0) {
              applyCapabilityValue(capability, null)
              return
            }
            const parsed = Number(raw)
            applyCapabilityValue(capability, Number.isFinite(parsed) ? parsed : null)
          }}
        />
      )
    }
    if (capability.control === "json") {
      return (
        <Textarea
          rows={5}
          defaultValue={toPrettyJson(currentValue)}
          onBlur={(event) => onJsonBlur(capability, event.target.value)}
        />
      )
    }
    return (
      <Input
        value={typeof currentValue === "string" ? currentValue : ""}
        placeholder={capability.placeholder ?? capability.label}
        onChange={(event) => applyCapabilityValue(capability, event.target.value)}
      />
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Prompt Composition</CardTitle>
        <CardDescription>
          Build prompts in Guided mode for step-by-step authoring, or use Full Editor for complete registry-driven controls.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <Tabs
          value={editorMode}
          onValueChange={(next) => setEditorMode(next as PromptEditorMode)}
        >
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="guided">Guided</TabsTrigger>
            <TabsTrigger value="full">Full Editor</TabsTrigger>
          </TabsList>
          <TabsContent value="guided" className="mt-4 space-y-4">
            <div className="rounded-md border bg-muted/40 p-3 text-xs text-muted-foreground">
              Guided mode prioritizes the highest-impact settings in authoring order. Use it to build and tune quickly,
              then switch to Full Editor when you need low-level fields such as stop sequences or metadata.
            </div>
            {GUIDED_SECTION_SPECS.map((section) => renderGuidedSection(section))}
          </TabsContent>
          <TabsContent value="full" className="mt-4 space-y-4">
            <div className="rounded-md border bg-muted/40 p-3 text-xs text-muted-foreground">
              Full Editor exposes all registered fields mapped to the underlying JSON draft. Use this mode for
              provider-specific or advanced tuning workflows.
            </div>
            {CATEGORY_ORDER.map((category) => {
              const capabilities = PROMPT_CAPABILITIES.filter((capability) => capability.category === category)
              if (capabilities.length === 0) return null
              return (
                <div key={category} className="space-y-3">
                  <h3 className="text-sm font-medium">{CATEGORY_LABELS[category]}</h3>
                  <div className="grid gap-3 md:grid-cols-2">
                    {capabilities.map((capability) => renderCapabilityField(capability))}
                  </div>
                </div>
              )
            })}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
