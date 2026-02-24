import {
  ACTIVE_BUILDER_BLOCK_TYPES,
  type ActiveBuilderBlockType,
  type BuilderBlockFieldSpec,
  type EditableComposition,
  type EditableBlock,
  getBuilderBlockTypeSchema,
} from "@/components/Demo/builder/demoBuilderSchema"
import {
  BUILDER_BLOCK_CAPABILITIES,
  getBlockCapabilityByType,
  getBlockCapabilityAvailability,
  type BuilderBlockCapability,
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

interface DemoBlockEditorProps {
  composition: EditableComposition
  blocks: EditableBlock[]
  fieldErrors: Record<string, string>
  onAddBlock: (type: ActiveBuilderBlockType) => void
  onRemoveBlock: (index: number) => void
  onUpdateBlock: (index: number, patch: Record<string, unknown>) => void
  onCommitBlockJsonField: (index: number, fieldKey: string, raw: string) => void
}

function renderBlockScalarField(params: {
  block: EditableBlock
  index: number
  field: BuilderBlockFieldSpec
  onUpdateBlock: (index: number, patch: Record<string, unknown>) => void
}) {
  const { block, index, field, onUpdateBlock } = params
  const value = (block as Record<string, unknown>)[field.key]
  if (field.control === "enum") {
    return (
      <Select
        key={field.key}
        value={String(value ?? field.enumValues?.[0] ?? "")}
        onValueChange={(nextValue) => onUpdateBlock(index, { [field.key]: nextValue })}
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
        onChange={(event) => onUpdateBlock(index, { [field.key]: parseInteger(event.target.value) })}
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
          onUpdateBlock(index, { [field.key]: normalized || null })
          return
        }
        onUpdateBlock(index, { [field.key]: rawValue })
      }}
    />
  )
}

function getCapabilityRequirementText(capability: BuilderBlockCapability, composition: EditableComposition): string | null {
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

export function DemoBlockEditor({
  composition,
  blocks,
  fieldErrors,
  onAddBlock,
  onRemoveBlock,
  onUpdateBlock,
  onCommitBlockJsonField,
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
          {BUILDER_BLOCK_CAPABILITIES.map((capability) => {
            const requirementText = getCapabilityRequirementText(capability, composition)
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
                  <p className="text-[11px] text-amber-700">{requirementText}</p>
                )}
              </div>
            )
          })}
        </div>

        {blocks.length === 0 ? (
          <div className="text-sm text-muted-foreground">No blocks configured.</div>
        ) : (
          blocks.map((block, index) => (
            (() => {
              const blockType = resolveBlockType(block)
              const blockSchema = getBuilderBlockTypeSchema(blockType)
              const blockCapability = getBlockCapabilityByType(blockType)
              const scalarFields = blockSchema.fieldSpecs.filter((field) => field.control !== "json")
              const jsonFields = blockSchema.fieldSpecs.filter((field) => field.control === "json")
              return (
            <Card key={`${String((block as { id?: unknown }).id ?? index)}-${index}`}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between gap-2">
                  <CardTitle className="text-sm">Block {index + 1}</CardTitle>
                  <Button variant="ghost" size="sm" onClick={() => onRemoveBlock(index)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="grid gap-3 md:grid-cols-4">
                {scalarFields.map((field) => renderBlockScalarField({
                  block,
                  index,
                  field,
                  onUpdateBlock,
                }))}

                <div className="md:col-span-4 space-y-3">
                  {jsonFields.map((field) => {
                    const currentJson = (block as Record<string, unknown>)[field.key] ?? {}
                    const showGuidedPresentation = field.key === "presentation_json"
                      && (blockCapability?.presentationFieldSpecs?.length ?? 0) > 0
                    return (
                      <div key={field.key} className="space-y-2">
                        {showGuidedPresentation && (
                          <DemoPresentationGuidedFields
                            value={currentJson}
                            fieldSpecs={blockCapability?.presentationFieldSpecs ?? []}
                            onChange={(nextValue) => onUpdateBlock(index, { [field.key]: nextValue })}
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
                            onBlur={(event) => onCommitBlockJsonField(index, field.key, event.target.value)}
                          />
                        </div>
                        {fieldErrors[`block:${index}:${field.key}`] && (
                          <p className="text-xs text-destructive">{fieldErrors[`block:${index}:${field.key}`]}</p>
                        )}
                      </div>
                    )
                  })}
                </div>
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
