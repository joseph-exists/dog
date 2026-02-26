import { CopyPlus, ChevronDown, ChevronRight, Plus, Trash2 } from "lucide-react"
import { DemoPresentationGuidedFields } from "@/components/Demo/builder/DemoPresentationGuidedFields"
import {
  BUILDER_BLOCK_CAPABILITIES,
  type BuilderBlockCapability,
  getBlockCapabilityAvailability,
  getBlockCapabilityByType,
} from "@/components/Demo/builder/demoBuilderCapabilityRegistry"
import {
  ACTIVE_BUILDER_BLOCK_TYPES,
  type ActiveBuilderBlockType,
  type BuilderBlockFieldSpec,
  type EditableBlock,
  type EditableComposition,
  getBuilderBlockTypeSchema,
} from "@/components/Demo/builder/demoBuilderSchema"
import {
  CLICK_PROMPT_DISPATCH_KIND,
  createClickPromptDispatchStarterConfig,
  parseClickPromptDispatchConfig,
} from "@/components/Demo/demoInteractionHandlers"
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

interface DemoBlockEditorProps {
  composition: EditableComposition
  blocks: EditableBlock[]
  fieldErrors: Record<string, string>
  onAddBlock: (type: ActiveBuilderBlockType) => void
  onOpenCloneDialog?: () => void
  onRemoveBlock: (index: number) => void
  onUpdateBlock: (index: number, patch: Record<string, unknown>) => void
  onCommitBlockJsonField: (index: number, fieldKey: string, raw: string) => void
  availableThemeOptions: Array<{
    id: string
    name: string
    category: "page" | "card"
  }>
}

function renderBlockScalarField(params: {
  block: EditableBlock
  index: number
  rootPath: string
  field: BuilderBlockFieldSpec
  onUpdateBlock: (index: number, patch: Record<string, unknown>) => void
  availableThemeOptions: Array<{
    id: string
    name: string
    category: "page" | "card"
  }>
}) {
  const { block, index, rootPath, field, onUpdateBlock, availableThemeOptions } =
    params
  const value = (block as Record<string, unknown>)[field.key]
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
            onUpdateBlock(index, {
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
            onUpdateBlock(index, { [field.key]: normalized || null })
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
            onUpdateBlock(index, { [field.key]: nextValue })
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
            onUpdateBlock(index, {
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
            onUpdateBlock(index, { [field.key]: normalized || null })
            return
          }
          onUpdateBlock(index, { [field.key]: rawValue })
        }}
      />
    </div>
  )
}

function getCapabilityRequirementText(
  capability: BuilderBlockCapability,
  composition: EditableComposition,
): string | null {
  const availability = getBlockCapabilityAvailability(capability, composition)
  if (availability.available) return null
  return `Requires ${availability.unmetRequirements.join(" + ")}`
}

function resolveBlockType(block: EditableBlock): ActiveBuilderBlockType {
  const rawType = String((block as { type?: unknown }).type ?? "content")
  if (ACTIVE_BUILDER_BLOCK_TYPES.includes(rawType as ActiveBuilderBlockType)) {
    return rawType as ActiveBuilderBlockType
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

function canUseClickPromptDispatch(type: ActiveBuilderBlockType): boolean {
  return type === "content" || type === "context"
}

function getConfigJsonHelpText(type: ActiveBuilderBlockType): string | null {
  if (!canUseClickPromptDispatch(type)) return null
  return "Optional interaction contract: configure click-to-input dispatch (`config_json.interaction`) so users can click code, enter text, and send both to a hidden chat receiver."
}

function mergeStarterConfig(existing: unknown): Record<string, unknown> {
  const starter = createClickPromptDispatchStarterConfig()
  if (!isObjectRecord(existing)) return starter
  return {
    ...existing,
    ...starter,
    interaction: {
      ...(isObjectRecord(existing.interaction) ? existing.interaction : {}),
      ...(isObjectRecord(starter.interaction) ? starter.interaction : {}),
    },
  }
}

function getChatPanelOptions(composition: EditableComposition): Array<{
  id: string
  label: string
}> {
  return (composition.panels ?? [])
    .filter(
      (panel) =>
        panel.kind === "chat" &&
        typeof panel.id === "string" &&
        panel.id.trim().length > 0,
    )
    .map((panel) => ({
      id: String(panel.id),
      label:
        typeof panel.title === "string" && panel.title.trim().length > 0
          ? `${panel.title} (${panel.id})`
          : String(panel.id),
    }))
}

function updateInteractionConfig(
  current: unknown,
  patch: {
    targetPanelId?: string | null
    enforceRegisteredReceiver?: boolean
  },
): Record<string, unknown> {
  const base = mergeStarterConfig(current)
  const interaction = isObjectRecord(base.interaction)
    ? { ...base.interaction }
    : {}
  const dispatch = isObjectRecord(interaction.dispatch)
    ? { ...interaction.dispatch }
    : {}
  if ("targetPanelId" in patch) {
    dispatch.target_panel_id = patch.targetPanelId
  }
  if (typeof patch.enforceRegisteredReceiver === "boolean") {
    dispatch.enforce_registered_receiver = patch.enforceRegisteredReceiver
  }
  interaction.kind = CLICK_PROMPT_DISPATCH_KIND
  interaction.dispatch = dispatch
  return {
    ...base,
    interaction,
  }
}

export function DemoBlockEditor({
  composition,
  blocks,
  fieldErrors,
  onAddBlock,
  onOpenCloneDialog,
  onRemoveBlock,
  onUpdateBlock,
  onCommitBlockJsonField,
  availableThemeOptions,
}: DemoBlockEditorProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Blocks</CardTitle>
        <CardDescription>
          Add and tune block specs, including region and visibility semantics.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-2">
          {onOpenCloneDialog && (
            <Button type="button" variant="secondary" size="sm" onClick={onOpenCloneDialog}>
              <CopyPlus className="h-3.5 w-3.5 mr-1" />
              Clone Existing Block
            </Button>
          )}
          {BUILDER_BLOCK_CAPABILITIES.map((capability) => {
            const requirementText = getCapabilityRequirementText(
              capability,
              composition,
            )
            return (
              <div key={capability.type} className="space-y-1">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={Boolean(requirementText)}
                  onClick={() => onAddBlock(capability.type)}
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

        {blocks.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            No blocks configured.
          </div>
        ) : (
          blocks.map((block, index) =>
            (() => {
              const blockType = resolveBlockType(block)
              const blockSchema = getBuilderBlockTypeSchema(blockType)
              const blockCapability = getBlockCapabilityByType(blockType)
              const rootPath = `blocks[${index}]`
              const titleText = toDisplayTitle(block.title)
              const region =
                typeof block.region === "string" ? block.region : "top"
              const visibility =
                typeof block.visibility === "string"
                  ? block.visibility
                  : "visible"
              const scalarFields = blockSchema.fieldSpecs.filter(
                (field) => field.control !== "json",
              )
              const jsonFields = blockSchema.fieldSpecs.filter(
                (field) => field.control === "json",
              )
              const chatPanelOptions = getChatPanelOptions(composition)
              return (
                <Card
                  id={`builder-block-${index}`}
                  data-builder-path={rootPath}
                  key={`${String((block as { id?: unknown }).id ?? index)}-${index}`}
                >
                  <details open className="group">
                    <summary className="list-none cursor-pointer [&::-webkit-details-marker]:hidden">
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between gap-2">
                          <div className="min-w-0">
                            <CardTitle className="text-sm truncate">
                              {blockSchema.displayName} · {titleText} · Region:{" "}
                              {region}
                            </CardTitle>
                            <p className="text-[11px] text-muted-foreground truncate">
                              block #{index + 1} · type: {blockType} ·
                              visibility: {visibility}
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
                                onRemoveBlock(index)
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
                        renderBlockScalarField({
                          block,
                          index,
                          rootPath,
                          field,
                          onUpdateBlock,
                          availableThemeOptions,
                        }),
                      )}

                      <div className="md:col-span-4 space-y-3">
                        {jsonFields.map((field) => {
                          const currentJson =
                            (block as Record<string, unknown>)[field.key] ?? {}
                          const showGuidedPresentation =
                            field.key === "presentation_json" &&
                            (blockCapability?.presentationFieldSpecs?.length ??
                              0) > 0
                          return (
                            <div
                              key={field.key}
                              className="space-y-2"
                              data-builder-path={`${rootPath}.${field.key}`}
                            >
                              {showGuidedPresentation && (
                                <DemoPresentationGuidedFields
                                  value={currentJson}
                                  fieldSpecs={
                                    blockCapability?.presentationFieldSpecs ??
                                    []
                                  }
                                  onChange={(nextValue) =>
                                    onUpdateBlock(index, {
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
                                {field.key === "config_json" &&
                                  getConfigJsonHelpText(blockType) && (
                                    <div className="space-y-2">
                                      <p className="text-[11px] text-muted-foreground">
                                        {getConfigJsonHelpText(blockType)}
                                      </p>
                                      <Button
                                        type="button"
                                        variant="outline"
                                        size="sm"
                                        onClick={() => {
                                          onUpdateBlock(index, {
                                            config_json:
                                              mergeStarterConfig(currentJson),
                                          })
                                        }}
                                      >
                                        Apply Click Input Starter
                                      </Button>
                                      {(() => {
                                        const parsedInteraction =
                                          parseClickPromptDispatchConfig(
                                            currentJson,
                                          )
                                        if (!parsedInteraction) return null
                                        return (
                                          <div
                                            className="rounded border p-2 space-y-2"
                                            data-builder-path={`${rootPath}.config_json.interaction.dispatch`}
                                          >
                                            <div className="flex items-center justify-between gap-2">
                                              <label className="text-xs text-muted-foreground">
                                                Enforce Registered Receiver
                                              </label>
                                              <Switch
                                                checked={
                                                  parsedInteraction.dispatch
                                                    .enforceRegisteredReceiver
                                                }
                                                onCheckedChange={(checked) => {
                                                  onUpdateBlock(index, {
                                                    config_json:
                                                      updateInteractionConfig(
                                                        currentJson,
                                                        {
                                                          enforceRegisteredReceiver:
                                                            checked,
                                                        },
                                                      ),
                                                  })
                                                }}
                                              />
                                            </div>
                                            <div className="space-y-1">
                                              <label className="text-xs text-muted-foreground">
                                                Target Chat Receiver (Panel ID)
                                              </label>
                                              <Select
                                                value={
                                                  parsedInteraction.dispatch
                                                    .targetPanelId ?? "__none"
                                                }
                                                onValueChange={(value) => {
                                                  onUpdateBlock(index, {
                                                    config_json:
                                                      updateInteractionConfig(
                                                        currentJson,
                                                        {
                                                          targetPanelId:
                                                            value === "__none"
                                                              ? null
                                                              : value,
                                                        },
                                                      ),
                                                  })
                                                }}
                                              >
                                                <SelectTrigger>
                                                  <SelectValue placeholder="Select chat receiver panel" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                  <SelectItem value="__none">
                                                    None
                                                  </SelectItem>
                                                  {chatPanelOptions.map(
                                                    (option) => (
                                                      <SelectItem
                                                        key={option.id}
                                                        value={option.id}
                                                      >
                                                        {option.label}
                                                      </SelectItem>
                                                    ),
                                                  )}
                                                </SelectContent>
                                              </Select>
                                              <p className="text-[11px] text-muted-foreground">
                                                If enforcement is enabled, only
                                                registered chat receivers can
                                                accept this dispatch.
                                              </p>
                                            </div>
                                          </div>
                                        )
                                      })()}
                                    </div>
                                  )}
                                <Textarea
                                  key={`${field.key}-${toPrettyJson(currentJson)}`}
                                  rows={4}
                                  defaultValue={toPrettyJson(currentJson)}
                                  onBlur={(event) =>
                                    onCommitBlockJsonField(
                                      index,
                                      field.key,
                                      event.target.value,
                                    )
                                  }
                                />
                              </div>
                              {fieldErrors[`block:${index}:${field.key}`] && (
                                <p className="text-xs text-destructive">
                                  {fieldErrors[`block:${index}:${field.key}`]}
                                </p>
                              )}
                            </div>
                          )
                        })}
                      </div>
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
