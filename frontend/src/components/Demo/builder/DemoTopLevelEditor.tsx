import type {
  DemoChatMode,
  DemoLayoutMode,
  DemoPersonaPolicy,
  DemoRuntimePolicy,
} from "@/client/types.gen"
import {
  type EditableComposition,
} from "@/components/Demo/builder/demoBuilderSchema"
import {
  BUILDER_COMPOSITION_CAPABILITIES,
  type BuilderCompositionCapability,
} from "@/components/Demo/builder/demoBuilderCapabilityRegistry"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Loader2 } from "lucide-react"

function toPrettyJson(value: unknown): string {
  return JSON.stringify(value ?? {}, null, 2)
}

function renderCompositionJsonField(props: {
  capability: BuilderCompositionCapability
  value: unknown
  error?: string
  onBlur: (raw: string) => void
}) {
  const { capability, value, error, onBlur } = props
  return (
    <div className="space-y-1">
      <label className="text-xs text-muted-foreground">{capability.label}</label>
      <Textarea
        rows={6}
        defaultValue={toPrettyJson(value ?? {})}
        onBlur={(event) => onBlur(event.target.value)}
      />
      {error && (
        <p className="text-xs text-destructive">{error}</p>
      )}
    </div>
  )
}

interface DemoTopLevelEditorProps {
  selectedDemoConfigId: string
  isLoadingComposition: boolean
  composition: EditableComposition
  fieldErrors: Record<string, string>
  onLayoutModeChange: (value: DemoLayoutMode) => void
  onRuntimePolicyChange: (value: DemoRuntimePolicy) => void
  onPersonaPolicyChange: (value: DemoPersonaPolicy) => void
  onChatModeChange: (value: DemoChatMode) => void
  onFixedUserPersonaIdChange: (value: string | null) => void
  onPageThemeIdChange: (value: string | null) => void
  onCardsThemeIdChange: (value: string | null) => void
  onMetadataJsonBlur: (raw: string) => void
  onPresentationJsonBlur: (raw: string) => void
}

export function DemoTopLevelEditor({
  selectedDemoConfigId,
  isLoadingComposition,
  composition,
  fieldErrors,
  onLayoutModeChange,
  onRuntimePolicyChange,
  onPersonaPolicyChange,
  onChatModeChange,
  onFixedUserPersonaIdChange,
  onPageThemeIdChange,
  onCardsThemeIdChange,
  onMetadataJsonBlur,
  onPresentationJsonBlur,
}: DemoTopLevelEditorProps) {
  const nonJsonCapabilities = BUILDER_COMPOSITION_CAPABILITIES.filter((capability) => capability.control !== "json")
  const jsonCapabilities = BUILDER_COMPOSITION_CAPABILITIES.filter((capability) => capability.control === "json")

  function getValue(key: string): unknown {
    return (composition as Record<string, unknown>)[key]
  }

  function handleScalarChange(key: string, value: string) {
    if (key === "layout_mode") {
      onLayoutModeChange(value as DemoLayoutMode)
      return
    }
    if (key === "runtime_policy") {
      onRuntimePolicyChange(value as DemoRuntimePolicy)
      return
    }
    if (key === "persona_policy") {
      onPersonaPolicyChange(value as DemoPersonaPolicy)
      return
    }
    if (key === "chat_mode") {
      onChatModeChange(value as DemoChatMode)
      return
    }
    const normalized = value.trim()
    const nullableValue = normalized.length > 0 ? normalized : null
    if (key === "fixed_user_persona_id") {
      onFixedUserPersonaIdChange(nullableValue)
    } else if (key === "page_theme_id") {
      onPageThemeIdChange(nullableValue)
    } else if (key === "cards_theme_id") {
      onCardsThemeIdChange(nullableValue)
    }
  }

  function onJsonBlur(key: string, raw: string) {
    if (key === "metadata_json") onMetadataJsonBlur(raw)
    if (key === "presentation_json") onPresentationJsonBlur(raw)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Composition</CardTitle>
        <CardDescription>
          Edit top-level composition behavior before tuning panels and blocks.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!selectedDemoConfigId ? (
          <div className="text-sm text-muted-foreground">
            Select or create a demo config to begin editing.
          </div>
        ) : isLoadingComposition ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading composition...
          </div>
        ) : (
          <>
            <div className="grid gap-3 md:grid-cols-4">
              {nonJsonCapabilities.map((capability) => (
                capability.control === "enum" ? (
                  <Select
                    key={capability.key}
                    value={String(getValue(capability.key) ?? capability.enumValues[0] ?? "")}
                    onValueChange={(value) => handleScalarChange(capability.key, value)}
                  >
                    <SelectTrigger><SelectValue placeholder={capability.label} /></SelectTrigger>
                    <SelectContent>
                      {capability.enumValues.map((enumValue) => (
                        <SelectItem key={enumValue} value={enumValue}>{enumValue}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <Input
                    key={capability.key}
                    value={String(getValue(capability.key) ?? "")}
                    placeholder={capability.label}
                    onChange={(event) => handleScalarChange(capability.key, event.target.value)}
                  />
                )
              ))}
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              {jsonCapabilities.map((capability) => (
                <div key={capability.key}>
                  {renderCompositionJsonField({
                    capability,
                    value: getValue(capability.key),
                    error: fieldErrors[capability.key],
                    onBlur: (raw) => onJsonBlur(capability.key, raw),
                  })}
                </div>
              ))}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
