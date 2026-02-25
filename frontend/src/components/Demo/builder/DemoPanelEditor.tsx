import {
  ACTIVE_BUILDER_PANEL_KINDS,
  type ActiveBuilderPanelKind,
  type BuilderPanelFieldSpec,
  type EditableComposition,
  type EditablePanel,
  getBuilderPanelKindSchema,
} from "@/components/Demo/builder/demoBuilderSchema"
import {
  BUILDER_PANEL_CAPABILITIES,
  getPanelCapabilityByKind,
  getPanelCapabilityAvailability,
  type BuilderPanelCapability,
} from "@/components/Demo/builder/demoBuilderCapabilityRegistry"
import { DemoPresentationGuidedFields } from "@/components/Demo/builder/DemoPresentationGuidedFields"
import { Button } from "@/components/ui/button"
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
import { Plus, Trash2 } from "lucide-react"

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
  onRemovePanel: (index: number) => void
  onUpdatePanel: (index: number, patch: Record<string, unknown>) => void
  onCommitPanelJsonField: (index: number, fieldKey: string, raw: string) => void
  availableThemeOptions: Array<{ id: string; name: string; category: "page" | "card" }>
}

function renderPanelScalarField(params: {
  panel: EditablePanel
  index: number
  field: BuilderPanelFieldSpec
  onUpdatePanel: (index: number, patch: Record<string, unknown>) => void
  availableThemeOptions: Array<{ id: string; name: string; category: "page" | "card" }>
}) {
  const { panel, index, field, onUpdatePanel, availableThemeOptions } = params
  const value = (panel as Record<string, unknown>)[field.key]
  if (field.key === "theme_id" && field.control === "id") {
    return (
      <div key={field.key} className="space-y-1 md:col-span-2">
        <label className="text-xs text-muted-foreground">Theme (title picker)</label>
        <Select
          value={typeof value === "string" && value.length > 0 ? value : "__none"}
          onValueChange={(nextValue) => onUpdatePanel(index, { [field.key]: nextValue === "__none" ? null : nextValue })}
        >
          <SelectTrigger><SelectValue placeholder="Select theme" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="__none">None</SelectItem>
            {availableThemeOptions.map((theme) => (
              <SelectItem key={`${theme.category}:${theme.id}`} value={theme.id}>
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
      <Select
        key={field.key}
        value={String(value ?? field.enumValues?.[0] ?? "")}
        onValueChange={(nextValue) => onUpdatePanel(index, { [field.key]: nextValue })}
      >
        <SelectTrigger><SelectValue placeholder={field.label} /></SelectTrigger>
        <SelectContent>
          {(field.enumValues ?? []).map((enumValue) => (
            <SelectItem key={enumValue} value={enumValue}>{enumValue}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    )
  }
  if (field.control === "number") {
    return (
      <Input
        key={field.key}
        value={String(value ?? "")}
        placeholder={field.label}
        onChange={(event) => onUpdatePanel(index, { [field.key]: parseInteger(event.target.value) })}
      />
    )
  }
  return (
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
  )
}

function getCapabilityRequirementText(capability: BuilderPanelCapability, composition: EditableComposition): string | null {
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

export function DemoPanelEditor({
  composition,
  panels,
  fieldErrors,
  onAddPanel,
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
          Add and tune panel specs. Each panel row mirrors shared composition primitives.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-2">
          {BUILDER_PANEL_CAPABILITIES.map((capability) => {
            const requirementText = getCapabilityRequirementText(capability, composition)
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
                  <p className="text-[11px] text-amber-700">{requirementText}</p>
                )}
              </div>
            )
          })}
        </div>

        {panels.length === 0 ? (
          <div className="text-sm text-muted-foreground">No panels configured.</div>
        ) : (
          panels.map((panel, index) => (
            (() => {
              const panelKind = resolvePanelKind(panel)
              const panelSchema = getBuilderPanelKindSchema(panelKind)
              const panelCapability = getPanelCapabilityByKind(panelKind)
              const scalarFields = panelSchema.fieldSpecs.filter((field) => field.control !== "json")
              const jsonFields = panelSchema.fieldSpecs.filter((field) => field.control === "json")
              return (
            <Card id={`builder-panel-${index}`} key={`${String((panel as { id?: unknown }).id ?? index)}-${index}`}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between gap-2">
                  <CardTitle className="text-sm">Panel {index + 1}</CardTitle>
                  <Button variant="ghost" size="sm" onClick={() => onRemovePanel(index)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="grid gap-3 md:grid-cols-4">
                {scalarFields.map((field) => renderPanelScalarField({
                  panel,
                  index,
                  field,
                  onUpdatePanel,
                  availableThemeOptions,
                }))}

                {jsonFields.map((field) => {
                  const currentJson = (panel as Record<string, unknown>)[field.key] ?? {}
                  const showGuidedPresentation = field.key === "presentation_json"
                    && (panelCapability?.presentationFieldSpecs?.length ?? 0) > 0
                  return (
                    <div key={field.key} className="md:col-span-4 space-y-2">
                      {showGuidedPresentation && (
                        <DemoPresentationGuidedFields
                          value={currentJson}
                          fieldSpecs={panelCapability?.presentationFieldSpecs ?? []}
                          onChange={(nextValue) => onUpdatePanel(index, { [field.key]: nextValue })}
                        />
                      )}
                      <div className="space-y-1">
                        <label className="text-xs text-muted-foreground">
                          {showGuidedPresentation ? `${field.label} (Advanced JSON Fallback)` : field.label}
                        </label>
                        <Textarea
                          key={`${field.key}-${toPrettyJson(currentJson)}`}
                          rows={4}
                          defaultValue={toPrettyJson(currentJson)}
                          onBlur={(event) => onCommitPanelJsonField(index, field.key, event.target.value)}
                        />
                      </div>
                      {fieldErrors[`panel:${index}:${field.key}`] && (
                        <p className="text-xs text-destructive">{fieldErrors[`panel:${index}:${field.key}`]}</p>
                      )}
                    </div>
                  )
                })}
              </CardContent>
            </Card>
              )
            })()
          ))
        )}
      </CardContent>
    </Card>
  )
}
