import {
  type BuilderPresentationFieldSpec,
} from "@/components/Demo/builder/demoBuilderCapabilityRegistry"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"

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
  if (value === null || typeof value === "undefined") {
    delete cursor[leaf]
  } else {
    cursor[leaf] = value
  }
  return next
}

interface DemoPresentationGuidedFieldsProps {
  value: unknown
  fieldSpecs: BuilderPresentationFieldSpec[]
  onChange: (nextValue: Record<string, unknown>) => void
}

export function DemoPresentationGuidedFields({
  value,
  fieldSpecs,
  onChange,
}: DemoPresentationGuidedFieldsProps) {
  const objectValue = isObjectRecord(value) ? value : {}

  function updatePath(path: string, nextValue: unknown) {
    onChange(setValueAtPath(objectValue, path, nextValue))
  }

  if (fieldSpecs.length === 0) return null

  return (
    <div className="rounded border p-3 space-y-3">
      <p className="text-xs font-medium">Presentation Controls</p>
      <div className="grid gap-3 md:grid-cols-3">
        {fieldSpecs.map((field) => {
          const currentValue = getValueAtPath(objectValue, field.path)
          return (
            <div key={field.path} className="space-y-1">
              <label className="text-xs text-muted-foreground">{field.label}</label>
              {field.control === "boolean" ? (
                <div className="h-9 flex items-center">
                  <Switch
                    checked={currentValue === true}
                    onCheckedChange={(checked) => updatePath(field.path, checked)}
                  />
                </div>
              ) : field.control === "enum" ? (
                <Select
                  value={typeof currentValue === "string" && currentValue.length > 0 ? currentValue : "__none"}
                  onValueChange={(next) => updatePath(field.path, next === "__none" ? null : next)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={field.label} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none">None</SelectItem>
                    {(field.enumValues ?? []).map((option) => (
                      <SelectItem key={option} value={option}>{option}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : field.control === "number" ? (
                <Input
                  value={typeof currentValue === "number" ? String(currentValue) : ""}
                  placeholder={field.placeholder ?? "number"}
                  onChange={(event) => {
                    const raw = event.target.value.trim()
                    if (raw.length === 0) {
                      updatePath(field.path, null)
                      return
                    }
                    const parsed = Number.parseInt(raw, 10)
                    updatePath(field.path, Number.isFinite(parsed) ? parsed : null)
                  }}
                />
              ) : (
                <Input
                  value={typeof currentValue === "string" ? currentValue : ""}
                  placeholder={field.placeholder ?? field.label}
                  onChange={(event) => {
                    const next = event.target.value
                    updatePath(field.path, next.trim().length > 0 ? next : null)
                  }}
                />
              )}
              {field.description && (
                <p className="text-[11px] text-muted-foreground">{field.description}</p>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
