import type { ReactNode } from "react"
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

const CATEGORY_LABELS: Record<PromptCategory, string> = {
  provider: "Provider",
  model: "Model",
  input: "Input",
  params: "Parameters",
  tools: "Tools",
  advanced: "Advanced",
}

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
  const draftRecord = draft as unknown as Record<string, unknown>

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
          Registry-driven controls for provider/model/input/parameters with normalization hooks.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        {CATEGORY_ORDER.map((category) => {
          const capabilities = PROMPT_CAPABILITIES.filter((capability) => capability.category === category)
          if (capabilities.length === 0) return null
          return (
            <div key={category} className="space-y-3">
              <h3 className="text-sm font-medium">{CATEGORY_LABELS[category]}</h3>
              <div className="grid gap-3 md:grid-cols-2">
                {capabilities.map((capability) => (
                  <div key={capability.key} className="space-y-1">
                    <label className="text-xs text-muted-foreground">{capability.label}</label>
                    {renderCapability(capability)}
                    {fieldErrors[capability.key] && (
                      <p className="text-xs text-destructive">{fieldErrors[capability.key]}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
