/**
 * StateConditionEditor - Editor for state conditions and mutations
 *
 * Features:
 * - Mode: "requires" (conditions) or "sets" (mutations)
 * - Condition rows with key, operator, value
 * - Logical groups ($and/$or) for requires mode
 * - Type-aware value inputs (boolean, number, string, enum)
 * - Schema autocomplete and undefined variable warnings
 * - JSON preview mode
 */

import { useState } from "react"
import { Plus, Trash2, Code, AlertTriangle, Layers } from "lucide-react"
import type { StoryStateVariablePublic } from "@/client"
import type { ComparisonOperator, MutationOperator, StateConditions } from "@/utils/stateConditions"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface StateConditionEditorProps {
  value: Record<string, unknown> | null
  onChange: (value: Record<string, unknown> | null) => void
  label: string
  schema?: StoryStateVariablePublic[]
  mode?: "requires" | "sets"
}

type ValueType = "boolean" | "string" | "number" | "enum"
type GroupType = "$and" | "$or"

// Comparison operators for requires_state
const COMPARISON_OPERATORS: {
  value: ComparisonOperator | "eq"
  label: string
  types: ValueType[]
}[] = [
  { value: "eq", label: "equals", types: ["boolean", "string", "number", "enum"] },
  { value: "$ne", label: "not equals", types: ["boolean", "string", "number", "enum"] },
  { value: "$gt", label: ">", types: ["number"] },
  { value: "$gte", label: ">=", types: ["number"] },
  { value: "$lt", label: "<", types: ["number"] },
  { value: "$lte", label: "<=", types: ["number"] },
  { value: "$in", label: "in list", types: ["string", "number", "enum"] },
  { value: "$exists", label: "exists", types: ["boolean", "string", "number", "enum"] },
]

// Mutation operators for sets_state
const MUTATION_OPERATORS: {
  value: MutationOperator | "set"
  label: string
  types: ValueType[]
}[] = [
  { value: "set", label: "set to", types: ["boolean", "string", "number", "enum"] },
  { value: "$inc", label: "increment", types: ["number"] },
  { value: "$dec", label: "decrement", types: ["number"] },
  { value: "$toggle", label: "toggle", types: ["boolean"] },
  { value: "$unset", label: "unset", types: ["boolean", "string", "number", "enum"] },
]

interface StateEntry {
  key: string
  operator: string
  value: unknown
  type: ValueType
  enumValues?: string[]
}

interface ConditionGroup {
  type: GroupType
  conditions: StateEntry[]
}

// Parse condition value into operator and value
function parseConditionValue(condValue: unknown): { operator: string; value: unknown } {
  if (typeof condValue === "object" && condValue !== null) {
    const obj = condValue as Record<string, unknown>
    const keys = Object.keys(obj)
    if (keys.length === 1 && keys[0].startsWith("$")) {
      return { operator: keys[0], value: obj[keys[0]] }
    }
  }
  return { operator: "eq", value: condValue }
}

// Build condition value from operator and value
function buildConditionValue(operator: string, value: unknown): unknown {
  if (operator === "eq" || operator === "set") return value
  if (["$toggle", "$unset", "$exists"].includes(operator)) return { [operator]: true }
  return { [operator]: value }
}

// Parse value object into entries and groups
function parseConditions(
  value: Record<string, unknown> | null,
  getSchemaVariable: (key: string) => StoryStateVariablePublic | undefined,
  getTypeForKey: (key: string, val: unknown) => ValueType,
): { entries: StateEntry[]; groups: ConditionGroup[] } {
  if (!value) return { entries: [], groups: [] }

  const entries: StateEntry[] = []
  const groups: ConditionGroup[] = []

  for (const [key, condValue] of Object.entries(value)) {
    if (key === "$and" || key === "$or") {
      const groupConditions = condValue as StateConditions[]
      const groupEntries: StateEntry[] = []

      for (const condition of groupConditions) {
        for (const [k, v] of Object.entries(condition)) {
          if (!k.startsWith("$")) {
            const { operator, value: val } = parseConditionValue(v)
            const schemaVar = getSchemaVariable(k)
            const type = getTypeForKey(k, val)
            groupEntries.push({
              key: k,
              operator,
              value: val,
              type,
              enumValues: schemaVar?.enum_values || undefined,
            })
          }
        }
      }

      if (groupEntries.length > 0) {
        groups.push({ type: key as GroupType, conditions: groupEntries })
      }
    } else if (!key.startsWith("$")) {
      const { operator, value: val } = parseConditionValue(condValue)
      const schemaVar = getSchemaVariable(key)
      const type = getTypeForKey(key, val)
      entries.push({
        key,
        operator,
        value: val,
        type,
        enumValues: schemaVar?.enum_values || undefined,
      })
    }
  }

  return { entries, groups }
}

// Convert entries and groups back to object
function buildConditionsObject(
  entries: StateEntry[],
  groups: ConditionGroup[],
): Record<string, unknown> | null {
  const obj: Record<string, unknown> = {}

  for (const entry of entries) {
    if (entry.key.trim()) {
      obj[entry.key] = buildConditionValue(entry.operator, entry.value)
    }
  }

  for (const group of groups) {
    const groupConditions: Record<string, unknown>[] = []
    for (const entry of group.conditions) {
      if (entry.key.trim()) {
        groupConditions.push({
          [entry.key]: buildConditionValue(entry.operator, entry.value),
        })
      }
    }
    if (groupConditions.length > 0) {
      obj[group.type] = groupConditions
    }
  }

  return Object.keys(obj).length > 0 ? obj : null
}

// Condition row component
interface ConditionRowProps {
  entry: StateEntry
  index: number
  schema?: StoryStateVariablePublic[]
  schemaMap: Map<string, StoryStateVariablePublic>
  isDuplicate: boolean
  isUndefined: boolean
  onKeyChange: (index: number, key: string) => void
  onOperatorChange: (index: number, op: string) => void
  onTypeChange: (index: number, type: ValueType) => void
  onValueChange: (index: number, value: unknown) => void
  onArrayValueChange: (index: number, value: string) => void
  onRemove: (index: number) => void
  availableOps: { value: string; label: string; types: ValueType[] }[]
}

const ConditionRow = ({
  entry,
  index,
  schemaMap,
  isDuplicate,
  isUndefined,
  onKeyChange,
  onOperatorChange,
  onTypeChange,
  onValueChange,
  onArrayValueChange,
  onRemove,
  availableOps,
}: ConditionRowProps) => {
  const schemaVar = schemaMap.get(entry.key)
  const isNoValueOp = ["$exists", "$toggle", "$unset"].includes(entry.operator)
  const filteredOps = availableOps.filter((op) => op.types.includes(entry.type))

  return (
    <div className="flex flex-wrap items-start gap-2">
      {/* Key input */}
      <div className="flex-1 min-w-[100px]">
        <Input
          value={entry.key}
          onChange={(e) => onKeyChange(index, e.target.value)}
          placeholder="variable"
          className={cn(
            "h-8",
            isDuplicate && "border-red-500",
            isUndefined && !isDuplicate && "border-orange-500"
          )}
        />
        {isDuplicate && (
          <p className="text-[10px] text-red-500 mt-0.5">Duplicate key</p>
        )}
        {isUndefined && !isDuplicate && (
          <div className="flex items-center gap-1 text-[10px] text-orange-500 mt-0.5">
            <AlertTriangle className="h-2.5 w-2.5" />
            <span>Not in schema</span>
          </div>
        )}
      </div>

      {/* Operator selector */}
      <Select value={entry.operator} onValueChange={(val) => onOperatorChange(index, val)}>
        <SelectTrigger className="w-[90px] h-8">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {filteredOps.map((op) => (
            <SelectItem key={op.value} value={op.value}>
              {op.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Type selector (only if no schema) */}
      {!schemaVar && (
        <Select value={entry.type} onValueChange={(val) => onTypeChange(index, val as ValueType)}>
          <SelectTrigger className="w-[70px] h-8">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="string">text</SelectItem>
            <SelectItem value="number">num</SelectItem>
            <SelectItem value="boolean">bool</SelectItem>
          </SelectContent>
        </Select>
      )}

      {/* Type badge (if schema) */}
      {schemaVar && (
        <Badge
          variant="outline"
          className={cn(
            "h-8 px-2",
            entry.type === "boolean" && "border-purple-500 text-purple-500",
            entry.type === "number" && "border-blue-500 text-blue-500",
            entry.type === "enum" && "border-orange-500 text-orange-500",
            entry.type === "string" && "border-green-500 text-green-500"
          )}
        >
          {entry.type}
        </Badge>
      )}

      {/* Value input */}
      {!isNoValueOp && (
        <>
          {entry.operator === "$in" ? (
            <Input
              value={Array.isArray(entry.value) ? entry.value.join(", ") : ""}
              onChange={(e) => onArrayValueChange(index, e.target.value)}
              placeholder="val1, val2"
              className="flex-1 min-w-[80px] h-8"
            />
          ) : entry.type === "enum" && entry.enumValues ? (
            <Select
              value={String(entry.value)}
              onValueChange={(val) => onValueChange(index, val)}
            >
              <SelectTrigger className="flex-1 min-w-[80px] h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {entry.enumValues.map((opt) => (
                  <SelectItem key={opt} value={opt}>
                    {opt}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : entry.type === "boolean" ? (
            <Select
              value={entry.value ? "true" : "false"}
              onValueChange={(val) => onValueChange(index, val === "true")}
            >
              <SelectTrigger className="flex-1 min-w-[70px] h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="true">true</SelectItem>
                <SelectItem value="false">false</SelectItem>
              </SelectContent>
            </Select>
          ) : (
            <Input
              type={entry.type === "number" ? "number" : "text"}
              value={String(entry.value ?? "")}
              onChange={(e) => onValueChange(index, e.target.value)}
              placeholder="value"
              className="flex-1 min-w-[70px] h-8"
            />
          )}
        </>
      )}

      {/* No value indicator */}
      {isNoValueOp && (
        <span className="text-xs text-muted-foreground self-center flex-1">
          {entry.operator === "$exists" && "(check if set)"}
          {entry.operator === "$toggle" && "(flip value)"}
          {entry.operator === "$unset" && "(remove)"}
        </span>
      )}

      {/* Delete button */}
      <Button
        type="button"
        size="icon"
        variant="ghost"
        className="h-8 w-8 text-destructive hover:text-destructive"
        onClick={() => onRemove(index)}
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  )
}

const StateConditionEditor = ({
  value,
  onChange,
  label,
  schema,
  mode = "requires",
}: StateConditionEditorProps) => {
  const [showJsonPreview, setShowJsonPreview] = useState(false)

  const operators = mode === "requires" ? COMPARISON_OPERATORS : MUTATION_OPERATORS
  const schemaMap = new Map(schema?.map((v) => [v.key, v]) || [])
  const schemaKeys = schema?.map((v) => v.key) || []

  const getSchemaVariable = (key: string) => schemaMap.get(key)

  const getTypeForKey = (key: string, val: unknown): ValueType => {
    const schemaVar = getSchemaVariable(key)
    if (schemaVar) {
      if (schemaVar.value_type === "enum") return "enum"
      return schemaVar.value_type as ValueType
    }
    if (typeof val === "boolean") return "boolean"
    if (typeof val === "number") return "number"
    return "string"
  }

  const { entries, groups } = parseConditions(value, getSchemaVariable, getTypeForKey)

  const update = (newEntries: StateEntry[], newGroups: ConditionGroup[]) => {
    onChange(buildConditionsObject(newEntries, newGroups))
  }

  // Entry handlers
  const handleAddEntry = () => {
    const defaultOp = mode === "requires" ? "eq" : "set"
    update([...entries, { key: "", operator: defaultOp, value: "", type: "string" }], groups)
  }

  const handleRemoveEntry = (index: number) => {
    update(entries.filter((_, i) => i !== index), groups)
  }

  const handleKeyChange = (index: number, newKey: string) => {
    const newEntries = [...entries]
    const schemaVar = getSchemaVariable(newKey)

    if (schemaVar) {
      let newType: ValueType = schemaVar.value_type as ValueType
      let newValue: unknown = newEntries[index].value
      let enumValues: string[] | undefined
      let newOp = newEntries[index].operator

      if (schemaVar.value_type === "enum") {
        newType = "enum"
        enumValues = schemaVar.enum_values || []
        if (!enumValues.includes(String(newValue))) newValue = enumValues[0] || ""
        if (!["eq", "$ne", "$in", "set"].includes(newOp)) newOp = mode === "requires" ? "eq" : "set"
      } else if (schemaVar.value_type === "boolean") {
        newValue = Boolean(newValue)
        if (!["eq", "$ne", "$exists", "set", "$toggle"].includes(newOp)) {
          newOp = mode === "requires" ? "eq" : "set"
        }
      } else if (schemaVar.value_type === "number") {
        newValue = Number(newValue) || 0
      } else {
        newValue = String(newValue || "")
      }

      newEntries[index] = { key: newKey, operator: newOp, value: newValue, type: newType, enumValues }
    } else {
      newEntries[index] = { ...newEntries[index], key: newKey }
    }

    update(newEntries, groups)
  }

  const handleOperatorChange = (index: number, newOp: string) => {
    const newEntries = [...entries]
    const entry = newEntries[index]
    let newValue = entry.value

    if (["$exists", "$toggle", "$unset"].includes(newOp)) {
      newValue = true
    } else if (newOp === "$in") {
      newValue = Array.isArray(entry.value) ? entry.value : [entry.value]
    } else if (Array.isArray(entry.value)) {
      newValue = entry.value[0] || ""
    }

    newEntries[index] = { ...entry, operator: newOp, value: newValue }
    update(newEntries, groups)
  }

  const handleTypeChange = (index: number, newType: ValueType) => {
    const newEntries = [...entries]
    let newValue: unknown = ""
    const defaultOp = mode === "requires" ? "eq" : "set"

    if (newType === "boolean") newValue = false
    else if (newType === "number") newValue = 0

    newEntries[index] = {
      ...newEntries[index],
      type: newType,
      value: newValue,
      operator: defaultOp,
      enumValues: undefined,
    }
    update(newEntries, groups)
  }

  const handleValueChange = (index: number, newValue: unknown) => {
    const newEntries = [...entries]
    const entry = newEntries[index]
    let converted: unknown = newValue

    if (entry.type === "boolean" && entry.operator !== "$exists") {
      converted = newValue === "true" || newValue === true
    } else if (entry.type === "number") {
      converted = Number(newValue)
    }

    newEntries[index] = { ...entry, value: converted }
    update(newEntries, groups)
  }

  const handleArrayValueChange = (index: number, inputValue: string) => {
    const newEntries = [...entries]
    const values = inputValue.split(",").map((v) => v.trim()).filter(Boolean)
    newEntries[index] = { ...newEntries[index], value: values }
    update(newEntries, groups)
  }

  // Group handlers
  const handleAddGroup = () => {
    update(entries, [
      ...groups,
      { type: "$or", conditions: [{ key: "", operator: "eq", value: "", type: "string" }] },
    ])
  }

  const handleRemoveGroup = (groupIndex: number) => {
    update(entries, groups.filter((_, i) => i !== groupIndex))
  }

  const handleGroupTypeChange = (groupIndex: number, newType: GroupType) => {
    const newGroups = [...groups]
    newGroups[groupIndex] = { ...newGroups[groupIndex], type: newType }
    update(entries, newGroups)
  }

  const handleGroupAddEntry = (groupIndex: number) => {
    const newGroups = [...groups]
    newGroups[groupIndex] = {
      ...newGroups[groupIndex],
      conditions: [
        ...newGroups[groupIndex].conditions,
        { key: "", operator: mode === "requires" ? "eq" : "set", value: "", type: "string" },
      ],
    }
    update(entries, newGroups)
  }

  const handleGroupRemoveEntry = (groupIndex: number, entryIndex: number) => {
    const newGroups = [...groups]
    newGroups[groupIndex] = {
      ...newGroups[groupIndex],
      conditions: newGroups[groupIndex].conditions.filter((_, i) => i !== entryIndex),
    }
    if (newGroups[groupIndex].conditions.length === 0) {
      newGroups.splice(groupIndex, 1)
    }
    update(entries, newGroups)
  }

  // Group entry change handlers (simplified - reuse similar logic as main entries)
  const handleGroupEntryChange = (
    groupIndex: number,
    entryIndex: number,
    field: "key" | "operator" | "type" | "value" | "arrayValue",
    newValue: unknown
  ) => {
    const newGroups = [...groups]
    const entry = newGroups[groupIndex].conditions[entryIndex]

    if (field === "key") {
      const schemaVar = getSchemaVariable(newValue as string)
      if (schemaVar) {
        let type: ValueType = schemaVar.value_type as ValueType
        let value: unknown = entry.value
        let enumValues: string[] | undefined

        if (schemaVar.value_type === "enum") {
          type = "enum"
          enumValues = schemaVar.enum_values || []
          if (!enumValues.includes(String(value))) value = enumValues[0] || ""
        } else if (schemaVar.value_type === "boolean") {
          value = Boolean(value)
        } else if (schemaVar.value_type === "number") {
          value = Number(value) || 0
        }

        newGroups[groupIndex].conditions[entryIndex] = {
          key: newValue as string,
          operator: entry.operator,
          value,
          type,
          enumValues,
        }
      } else {
        newGroups[groupIndex].conditions[entryIndex] = { ...entry, key: newValue as string }
      }
    } else if (field === "operator") {
      let value = entry.value
      if (["$exists", "$toggle", "$unset"].includes(newValue as string)) {
        value = true
      } else if (newValue === "$in") {
        value = Array.isArray(entry.value) ? entry.value : [entry.value]
      }
      newGroups[groupIndex].conditions[entryIndex] = { ...entry, operator: newValue as string, value }
    } else if (field === "type") {
      let value: unknown = ""
      if (newValue === "boolean") value = false
      else if (newValue === "number") value = 0
      newGroups[groupIndex].conditions[entryIndex] = {
        ...entry,
        type: newValue as ValueType,
        value,
        operator: mode === "requires" ? "eq" : "set",
      }
    } else if (field === "value") {
      let converted: unknown = newValue
      if (entry.type === "boolean") converted = newValue === "true" || newValue === true
      else if (entry.type === "number") converted = Number(newValue)
      newGroups[groupIndex].conditions[entryIndex] = { ...entry, value: converted }
    } else if (field === "arrayValue") {
      const values = (newValue as string).split(",").map((v) => v.trim()).filter(Boolean)
      newGroups[groupIndex].conditions[entryIndex] = { ...entry, value: values }
    }

    update(entries, newGroups)
  }

  // Get all keys for duplicate detection
  const getAllKeys = (): string[] => {
    const keys = entries.map((e) => e.key).filter((k) => k.trim())
    for (const group of groups) {
      keys.push(...group.conditions.map((e) => e.key).filter((k) => k.trim()))
    }
    return keys
  }

  const getDuplicateKeys = (): string[] => {
    const keys = getAllKeys()
    return [...new Set(keys.filter((key, index) => keys.indexOf(key) !== index))]
  }

  const getUndefinedKeys = (): string[] => {
    if (!schema || schema.length === 0) return []
    return getAllKeys().filter((k) => !schemaKeys.includes(k))
  }

  const duplicateKeys = getDuplicateKeys()
  const undefinedKeys = getUndefinedKeys()
  const hasContent = entries.length > 0 || groups.length > 0

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Label className="text-muted-foreground">{label}</Label>
        <Button
          type="button"
          size="icon"
          variant="ghost"
          className="h-6 w-6"
          onClick={() => setShowJsonPreview(!showJsonPreview)}
        >
          <Code className="h-3 w-3" />
        </Button>
      </div>

      {showJsonPreview ? (
        <pre className="p-3 bg-zinc-900 text-green-400 rounded-md font-mono text-xs overflow-x-auto">
          {JSON.stringify(value, null, 2) || "{}"}
        </pre>
      ) : (
        <div className="space-y-3">
          {!hasContent && (
            <p className="text-sm text-muted-foreground italic">
              No {mode === "requires" ? "conditions" : "mutations"} set
            </p>
          )}

          {/* Top-level entries */}
          {entries.length > 0 && (
            <div className="space-y-2">
              {entries.map((entry, index) => (
                <ConditionRow
                  key={index}
                  entry={entry}
                  index={index}
                  schema={schema}
                  schemaMap={schemaMap}
                  isDuplicate={duplicateKeys.includes(entry.key)}
                  isUndefined={undefinedKeys.includes(entry.key)}
                  onKeyChange={handleKeyChange}
                  onOperatorChange={handleOperatorChange}
                  onTypeChange={handleTypeChange}
                  onValueChange={handleValueChange}
                  onArrayValueChange={handleArrayValueChange}
                  onRemove={handleRemoveEntry}
                  availableOps={operators}
                />
              ))}
            </div>
          )}

          {/* Logical Groups (requires mode only) */}
          {mode === "requires" &&
            groups.map((group, groupIndex) => (
              <Card key={groupIndex}>
                <CardContent className="p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Layers className="h-3 w-3" />
                      <Select
                        value={group.type}
                        onValueChange={(val) => handleGroupTypeChange(groupIndex, val as GroupType)}
                      >
                        <SelectTrigger className="w-[80px] h-7">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="$or">Any of</SelectItem>
                          <SelectItem value="$and">All of</SelectItem>
                        </SelectContent>
                      </Select>
                      <span className="text-xs text-muted-foreground">
                        {group.type === "$or" ? "(OR)" : "(AND)"}
                      </span>
                    </div>
                    <Button
                      type="button"
                      size="icon"
                      variant="ghost"
                      className="h-6 w-6 text-destructive"
                      onClick={() => handleRemoveGroup(groupIndex)}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>

                  {group.conditions.map((entry, entryIndex) => (
                    <ConditionRow
                      key={entryIndex}
                      entry={entry}
                      index={entryIndex}
                      schema={schema}
                      schemaMap={schemaMap}
                      isDuplicate={duplicateKeys.includes(entry.key)}
                      isUndefined={undefinedKeys.includes(entry.key)}
                      onKeyChange={(_, key) =>
                        handleGroupEntryChange(groupIndex, entryIndex, "key", key)
                      }
                      onOperatorChange={(_, op) =>
                        handleGroupEntryChange(groupIndex, entryIndex, "operator", op)
                      }
                      onTypeChange={(_, type) =>
                        handleGroupEntryChange(groupIndex, entryIndex, "type", type)
                      }
                      onValueChange={(_, val) =>
                        handleGroupEntryChange(groupIndex, entryIndex, "value", val)
                      }
                      onArrayValueChange={(_, val) =>
                        handleGroupEntryChange(groupIndex, entryIndex, "arrayValue", val)
                      }
                      onRemove={() => handleGroupRemoveEntry(groupIndex, entryIndex)}
                      availableOps={operators}
                    />
                  ))}

                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    className="h-7 text-xs"
                    onClick={() => handleGroupAddEntry(groupIndex)}
                  >
                    <Plus className="h-3 w-3 mr-1" />
                    Add to group
                  </Button>
                </CardContent>
              </Card>
            ))}

          {/* Action buttons */}
          <div className="flex gap-2">
            <Button type="button" size="sm" variant="outline" onClick={handleAddEntry}>
              <Plus className="h-3 w-3 mr-1" />
              Add {mode === "requires" ? "Condition" : "Change"}
            </Button>

            {mode === "requires" && (
              <Button
                type="button"
                size="sm"
                variant="ghost"
                onClick={handleAddGroup}
              >
                <Layers className="h-3 w-3 mr-1" />
                Add OR Group
              </Button>
            )}
          </div>

          {schema && schema.length > 0 && !hasContent && (
            <p className="text-xs text-muted-foreground">
              {schema.length} variable{schema.length !== 1 ? "s" : ""} available
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export default StateConditionEditor
