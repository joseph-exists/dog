import { CopyPlus, ChevronDown, ChevronRight, Plus, Trash2 } from "lucide-react"
import { DemoPresentationGuidedFields } from "@/components/Demo/builder/DemoPresentationGuidedFields"
import {
  BUILDER_PANEL_CAPABILITIES,
  type BuilderPanelCapability,
  getPanelCapabilityAvailability,
  getPanelCapabilityByKind,
} from "@/components/Demo/builder/demoBuilderCapabilityRegistry"
import {
  ACTIVE_BUILDER_PANEL_KINDS,
  type ActiveBuilderPanelKind,
  type BuilderPanelFieldSpec,
  type EditableComposition,
  type EditablePanel,
  getBuilderPanelKindSchema,
} from "@/components/Demo/builder/demoBuilderSchema"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
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

function toPrettyJson(value: unknown): string {
  return JSON.stringify(value ?? {}, null, 2)
}

function parseInteger(value: string): number | undefined {
  const trimmed = value.trim()
  if (!trimmed) return undefined
  const parsed = Number.parseInt(trimmed, 10)
  return Number.isFinite(parsed) ? parsed : undefined
}

interface DemoPanelEditorProps {
  composition: EditableComposition
  panels: EditablePanel[]
  fieldErrors: Record<string, string>
  onAddPanel: (kind: ActiveBuilderPanelKind) => void
  onOpenCloneDialog?: () => void
  onRemovePanel: (index: number) => void
  onUpdatePanel: (index: number, patch: Record<string, unknown>) => void
  onCommitPanelJsonField: (index: number, fieldKey: string, raw: string) => void
  availableThemeOptions: Array<{
    id: string
    name: string
    category: "page" | "card"
  }>
}

function renderPanelScalarField(params: {
  panel: EditablePanel
  index: number
  rootPath: string
  field: BuilderPanelFieldSpec
  onUpdatePanel: (index: number, patch: Record<string, unknown>) => void
  availableThemeOptions: Array<{
    id: string
    name: string
    category: "page" | "card"
  }>
}) {
  const { panel, index, rootPath, field, onUpdatePanel, availableThemeOptions } =
    params
  const value = (panel as Record<string, unknown>)[field.key]
  if (field.key === "theme_id" && field.control === "id") {
    return (
      <div
        key={field.key}
        className="space-y-1 md:col-span-2"
        data-builder-path={`${rootPath}.${field.key}`}
      >
        <label className="text-xs text-muted-foreground">
          Theme (title picker)
        </label>
        <Select
          value={
            typeof value === "string" && value.length > 0 ? value : "__none"
          }
          onValueChange={(nextValue) =>
            onUpdatePanel(index, {
              [field.key]: nextValue === "__none" ? null : nextValue,
            })
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="Select theme" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__none">None</SelectItem>
            {availableThemeOptions.map((theme) => (
              <SelectItem
                key={`${theme.category}:${theme.id}`}
                value={theme.id}
              >
                {theme.name} ({theme.category})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Input
          value={String(value ?? "")}
          placeholder={field.label}
          onChange={(event) => {
            const normalized = event.target.value.trim()
            onUpdatePanel(index, { [field.key]: normalized || null })
          }}
        />
      </div>
    )
  }
  if (field.control === "enum") {
    return (
      <div data-builder-path={`${rootPath}.${field.key}`}>
        <Select
          key={field.key}
          value={String(value ?? field.enumValues?.[0] ?? "")}
          onValueChange={(nextValue) =>
            onUpdatePanel(index, { [field.key]: nextValue })
          }
        >
          <SelectTrigger>
            <SelectValue placeholder={field.label} />
          </SelectTrigger>
          <SelectContent>
            {(field.enumValues ?? []).map((enumValue) => (
              <SelectItem key={enumValue} value={enumValue}>
                {enumValue}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    )
  }
  if (field.control === "number") {
    return (
      <div data-builder-path={`${rootPath}.${field.key}`}>
        <Input
          key={field.key}
          value={String(value ?? "")}
          placeholder={field.label}
          onChange={(event) =>
            onUpdatePanel(index, {
              [field.key]: parseInteger(event.target.value),
            })
          }
        />
      </div>
    )
  }
  return (
    <div data-builder-path={`${rootPath}.${field.key}`}>
      <Input
        key={field.key}
        value={String(value ?? "")}
        placeholder={field.label}
        onChange={(event) => {
          const rawValue = event.target.value
          if (field.control === "id") {
            const normalized = rawValue.trim()
            onUpdatePanel(index, { [field.key]: normalized || null })
            return
          }
          onUpdatePanel(index, { [field.key]: rawValue })
        }}
      />
    </div>
  )
}

function getCapabilityRequirementText(
  capability: BuilderPanelCapability,
  composition: EditableComposition,
): string | null {
  const availability = getPanelCapabilityAvailability(capability, composition)
  if (availability.available) return null
  return `Requires ${availability.unmetRequirements.join(" + ")}`
}

function resolvePanelKind(panel: EditablePanel): ActiveBuilderPanelKind {
  const rawKind = String((panel as { kind?: unknown }).kind ?? "content")
  if (ACTIVE_BUILDER_PANEL_KINDS.includes(rawKind as ActiveBuilderPanelKind)) {
    return rawKind as ActiveBuilderPanelKind
  }
  return "content"
}

function toDisplayTitle(value: unknown): string {
  if (typeof value !== "string") return "Untitled"
  const trimmed = value.trim()
  return trimmed.length > 0 ? trimmed : "Untitled"
}

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function parseInteractionReceiverOptions(options: unknown): {
  enabled: boolean
  receiverId: string | null
  acceptsClickPromptDispatch: boolean
} {
  if (!isObjectRecord(options)) {
    return {
      enabled: false,
      receiverId: null,
      acceptsClickPromptDispatch: true,
    }
  }
  const receiver = isObjectRecord(options.interaction_receiver)
    ? options.interaction_receiver
    : {}
  const enabled = receiver.enabled === true
  const receiverId =
    typeof receiver.receiver_id === "string" &&
    receiver.receiver_id.trim().length > 0
      ? receiver.receiver_id.trim()
      : null
  const accepts = Array.isArray(receiver.accepts)
    ? receiver.accepts.filter(
        (item): item is string => typeof item === "string",
      )
    : ["click_prompt_dispatch.v1"]
  return {
    enabled,
    receiverId,
    acceptsClickPromptDispatch: accepts.includes("click_prompt_dispatch.v1"),
  }
}

function updateInteractionReceiverOptions(
  currentOptions: unknown,
  patch: {
    enabled?: boolean
    receiverId?: string | null
    acceptsClickPromptDispatch?: boolean
  },
): Record<string, unknown> {
  const base = isObjectRecord(currentOptions) ? { ...currentOptions } : {}
  const receiver = isObjectRecord(base.interaction_receiver)
    ? { ...base.interaction_receiver }
    : {}

  const current = parseInteractionReceiverOptions(base)
  const nextEnabled =
    typeof patch.enabled === "boolean" ? patch.enabled : current.enabled
  const nextReceiverId =
    "receiverId" in patch ? patch.receiverId : current.receiverId
  const nextAccepts =
    typeof patch.acceptsClickPromptDispatch === "boolean"
      ? patch.acceptsClickPromptDispatch
      : current.acceptsClickPromptDispatch

  receiver.enabled = nextEnabled
  receiver.receiver_id = nextReceiverId
  receiver.accepts = nextAccepts ? ["click_prompt_dispatch.v1"] : []
  base.interaction_receiver = receiver
  return base
}

export function DemoPanelEditor({
  composition,
  panels,
  fieldErrors,
  onAddPanel,
  onOpenCloneDialog,
  onRemovePanel,
  onUpdatePanel,
  onCommitPanelJsonField,
  availableThemeOptions,
}: DemoPanelEditorProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Panels</CardTitle>
        <CardDescription>
          Add and tune panel specs. Each panel row mirrors shared composition
          primitives.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-2">
          {onOpenCloneDialog && (
            <Button type="button" variant="secondary" size="sm" onClick={onOpenCloneDialog}>
              <CopyPlus className="h-3.5 w-3.5 mr-1" />
              Clone Existing Panel
            </Button>
          )}
          {BUILDER_PANEL_CAPABILITIES.map((capability) => {
            const requirementText = getCapabilityRequirementText(
              capability,
              composition,
            )
            return (
              <div key={capability.kind} className="space-y-1">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={Boolean(requirementText)}
                  onClick={() => onAddPanel(capability.kind)}
                >
                  <Plus className="h-3.5 w-3.5 mr-1" />
                  {capability.displayName}
                </Button>
                {requirementText && (
                  <p className="text-[11px] text-amber-700">
                    {requirementText}
                  </p>
                )}
              </div>
            )
          })}
        </div>

        {panels.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            No panels configured.
          </div>
        ) : (
          panels.map((panel, index) =>
            (() => {
              const panelKind = resolvePanelKind(panel)
              const panelSchema = getBuilderPanelKindSchema(panelKind)
              const panelCapability = getPanelCapabilityByKind(panelKind)
              const titleText = toDisplayTitle(panel.title)
              const rootPath = `panels[${index}]`
              const prominence =
                panel.prominence === "auxiliary" ? "Auxiliary" : "Primary"
              const scalarFields = panelSchema.fieldSpecs.filter(
                (field) => field.control !== "json",
              )
              const jsonFields = panelSchema.fieldSpecs.filter(
                (field) => field.control === "json",
              )
              return (
                <Card
                  id={`builder-panel-${index}`}
                  data-builder-path={rootPath}
                  key={`${String((panel as { id?: unknown }).id ?? index)}-${index}`}
                >
                  <details open className="group">
                    <summary className="list-none cursor-pointer [&::-webkit-details-marker]:hidden">
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between gap-2">
                          <div className="min-w-0">
                            <CardTitle className="text-sm truncate">
                              {panelSchema.displayName} · {titleText} ·{" "}
                              {prominence}
                            </CardTitle>
                            <p className="text-[11px] text-muted-foreground truncate">
                              panel #{index + 1} · kind: {panelKind}
                            </p>
                          </div>
                          <div className="flex items-center gap-1">
                            <ChevronRight className="h-4 w-4 group-open:hidden" />
                            <ChevronDown className="h-4 w-4 hidden group-open:block" />
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(event) => {
                                event.preventDefault()
                                event.stopPropagation()
                                onRemovePanel(index)
                              }}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </CardHeader>
                    </summary>
                    <CardContent className="grid gap-3 md:grid-cols-4">
                      {scalarFields.map((field) =>
                        renderPanelScalarField({
                          panel,
                          index,
                          rootPath,
                          field,
                          onUpdatePanel,
                          availableThemeOptions,
                        }),
                      )}

                      {jsonFields.map((field) => {
                        const currentJson =
                          (panel as Record<string, unknown>)[field.key] ?? {}
                        const showGuidedPresentation =
                          field.key === "presentation_json" &&
                          (panelCapability?.presentationFieldSpecs?.length ??
                            0) > 0
                        return (
                          <div
                            key={field.key}
                            className="md:col-span-4 space-y-2"
                            data-builder-path={`${rootPath}.${field.key}`}
                          >
                            {showGuidedPresentation && (
                              <DemoPresentationGuidedFields
                                value={currentJson}
                                fieldSpecs={
                                  panelCapability?.presentationFieldSpecs ?? []
                                }
                                onChange={(nextValue) =>
                                  onUpdatePanel(index, {
                                    [field.key]: nextValue,
                                  })
                                }
                              />
                            )}
                            <div className="space-y-1">
                              <label className="text-xs text-muted-foreground">
                                {showGuidedPresentation
                                  ? `${field.label} (Advanced JSON Fallback)`
                                  : field.label}
                              </label>
                              {field.key === "options" &&
                                panelKind === "chat" && (
                                  <div className="rounded border p-2 space-y-2">
                                    <p className="text-[11px] text-muted-foreground">
                                      Register this chat panel as a receiver for
                                      block interaction dispatch events.
                                    </p>
                                    <div className="flex items-center justify-between gap-2">
                                      <label className="text-xs text-muted-foreground">
                                        Register Receiver
                                      </label>
                                      <Switch
                                        checked={
                                          parseInteractionReceiverOptions(
                                            currentJson,
                                          ).enabled
                                        }
                                        onCheckedChange={(checked) => {
                                          onUpdatePanel(index, {
                                            options:
                                              updateInteractionReceiverOptions(
                                                currentJson,
                                                {
                                                  enabled: checked,
                                                },
                                              ),
                                          })
                                        }}
                                      />
                                    </div>
                                    <div
                                      className="space-y-1"
                                      data-builder-path={`${rootPath}.options.interaction_receiver`}
                                    >
                                      <label className="text-xs text-muted-foreground">
                                        Receiver ID (defaults to panel id)
                                      </label>
                                      <Input
                                        value={
                                          parseInteractionReceiverOptions(
                                            currentJson,
                                          ).receiverId ?? ""
                                        }
                                        placeholder={`Defaults to ${panel.id ?? "panel-id"}`}
                                        onChange={(event) => {
                                          const normalized =
                                            event.target.value.trim() || null
                                          onUpdatePanel(index, {
                                            options:
                                              updateInteractionReceiverOptions(
                                                currentJson,
                                                {
                                                  receiverId: normalized,
                                                },
                                              ),
                                          })
                                        }}
                                      />
                                    </div>
                                    <div className="flex items-center justify-between gap-2">
                                      <label className="text-xs text-muted-foreground">
                                        Accept click_prompt_dispatch.v1
                                      </label>
                                      <Switch
                                        checked={
                                          parseInteractionReceiverOptions(
                                            currentJson,
                                          ).acceptsClickPromptDispatch
                                        }
                                        onCheckedChange={(checked) => {
                                          onUpdatePanel(index, {
                                            options:
                                              updateInteractionReceiverOptions(
                                                currentJson,
                                                {
                                                  acceptsClickPromptDispatch:
                                                    checked,
                                                },
                                              ),
                                          })
                                        }}
                                      />
                                    </div>
                                  </div>
                                )}
                              <Textarea
                                key={`${field.key}-${toPrettyJson(currentJson)}`}
                                rows={4}
                                defaultValue={toPrettyJson(currentJson)}
                                onBlur={(event) =>
                                  onCommitPanelJsonField(
                                    index,
                                    field.key,
                                    event.target.value,
                                  )
                                }
                              />
                            </div>
                            {fieldErrors[`panel:${index}:${field.key}`] && (
                              <p className="text-xs text-destructive">
                                {fieldErrors[`panel:${index}:${field.key}`]}
                              </p>
                            )}
                          </div>
                        )
                      })}
                    </CardContent>
                  </details>
                </Card>
              )
            })(),
          )
        )}
      </CardContent>
    </Card>
  )
}
