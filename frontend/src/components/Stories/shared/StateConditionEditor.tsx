import {
  Badge,
  Box,
  Button,
  Card,
  HStack,
  Heading,
  IconButton,
  Input,
  NativeSelectField,
  NativeSelectRoot,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useState } from "react"
import {
  FaCode,
  FaExclamationTriangle,
  FaLayerGroup,
  FaPlus,
  FaTrash,
} from "react-icons/fa"

import type { StoryStateVariablePublic } from "@/client"
import type {
  ComparisonOperator,
  MutationOperator,
  StateConditions,
} from "@/utils/stateConditions"

interface StateConditionEditorProps {
  value: Record<string, unknown> | null
  onChange: (value: Record<string, unknown> | null) => void
  label: string
  schema?: StoryStateVariablePublic[]
  mode?: "requires" | "sets" // Different operators for conditions vs mutations
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
  { value: "$inc", label: "increment by", types: ["number"] },
  { value: "$dec", label: "decrement by", types: ["number"] },
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

// Parse a condition value into operator and value
function parseConditionValue(
  condValue: unknown,
): { operator: string; value: unknown } {
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
  if (operator === "eq" || operator === "set") {
    return value
  }
  if (operator === "$toggle" || operator === "$unset") {
    return { [operator]: true }
  }
  return { [operator]: value }
}

// Parse value object into entries and groups
function parseConditions(
  value: Record<string, unknown> | null,
  getSchemaVariable: (key: string) => StoryStateVariablePublic | undefined,
  getTypeForKey: (key: string, val: unknown) => ValueType,
): { entries: StateEntry[]; groups: ConditionGroup[] } {
  if (!value) {
    return { entries: [], groups: [] }
  }

  const entries: StateEntry[] = []
  const groups: ConditionGroup[] = []

  for (const [key, condValue] of Object.entries(value)) {
    if (key === "$and" || key === "$or") {
      // This is a logical group
      const groupConditions = condValue as StateConditions[]
      const groupEntries: StateEntry[] = []

      for (const condition of groupConditions) {
        // Each condition in the group should be a single-key object
        for (const [k, v] of Object.entries(condition)) {
          if (!k.startsWith("$")) {
            const { operator, value: val } = parseConditionValue(v)
            const schemaVar = getSchemaVariable(k)
            const type = getTypeForKey(k, val)
            const enumValues = schemaVar?.enum_values || undefined

            groupEntries.push({ key: k, operator, value: val, type, enumValues })
          }
        }
      }

      if (groupEntries.length > 0) {
        groups.push({ type: key as GroupType, conditions: groupEntries })
      }
    } else if (!key.startsWith("$")) {
      // Regular condition
      const { operator, value: val } = parseConditionValue(condValue)
      const schemaVar = getSchemaVariable(key)
      const type = getTypeForKey(key, val)
      const enumValues = schemaVar?.enum_values || undefined

      entries.push({ key, operator, value: val, type, enumValues })
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

  // Add regular entries
  for (const entry of entries) {
    if (entry.key.trim()) {
      obj[entry.key] = buildConditionValue(entry.operator, entry.value)
    }
  }

  // Add groups
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

// Operator entry type for flexibility
type OperatorEntry = {
  value: string
  label: string
  types: ValueType[]
}

// Condition entry row component
interface ConditionRowProps {
  entry: StateEntry
  index: number
  schema?: StoryStateVariablePublic[]
  schemaMap: Map<string, StoryStateVariablePublic>
  datalistId: string
  duplicateKeys: string[]
  undefinedKeys: string[]
  onKeyChange: (index: number, key: string) => void
  onOperatorChange: (index: number, op: string) => void
  onTypeChange: (index: number, type: ValueType) => void
  onValueChange: (index: number, value: unknown) => void
  onArrayValueChange: (index: number, value: string) => void
  onRemove: (index: number) => void
  getOperatorsForType: (type: ValueType) => OperatorEntry[]
}

const ConditionRow = ({
  entry,
  index,
  schema,
  schemaMap,
  datalistId,
  duplicateKeys,
  undefinedKeys,
  onKeyChange,
  onOperatorChange,
  onTypeChange,
  onValueChange,
  onArrayValueChange,
  onRemove,
  getOperatorsForType,
}: ConditionRowProps) => {
  const schemaVar = schemaMap.get(entry.key)
  const isDuplicate = duplicateKeys.includes(entry.key)
  const isUndefined = undefinedKeys.includes(entry.key)
  const availableOps = getOperatorsForType(entry.type)
  const isNoValueOp = ["$exists", "$toggle", "$unset"].includes(entry.operator)

  return (
    <HStack gap={2} align="start" flexWrap="wrap">
      {/* Key input */}
      <Box flex={1} minW="100px">
        <Input
          size="sm"
          value={entry.key}
          onChange={(e) => onKeyChange(index, e.target.value)}
          placeholder="variable"
          list={schema ? datalistId : undefined}
          borderColor={
            isDuplicate ? "red.500" : isUndefined ? "orange.500" : undefined
          }
        />
        {isDuplicate && (
          <Text fontSize="2xs" color="red.500" mt={1}>
            Duplicate key
          </Text>
        )}
        {isUndefined && !isDuplicate && (
          <HStack fontSize="2xs" color="orange.500" mt={1} gap={1}>
            <FaExclamationTriangle size={10} />
            <Text>Not in schema</Text>
          </HStack>
        )}
      </Box>

      {/* Operator selector */}
      <NativeSelectRoot size="sm" w="100px">
        <NativeSelectField
          value={entry.operator}
          onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
            onOperatorChange(index, e.target.value)
          }
        >
          {availableOps.map((op) => (
            <option key={op.value} value={op.value}>
              {op.label}
            </option>
          ))}
        </NativeSelectField>
      </NativeSelectRoot>

      {/* Type selector (only if no schema) */}
      {!schemaVar && (
        <NativeSelectRoot size="sm" w="80px">
          <NativeSelectField
            value={entry.type}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
              onTypeChange(index, e.target.value as ValueType)
            }
          >
            <option value="string">text</option>
            <option value="number">num</option>
            <option value="boolean">bool</option>
          </NativeSelectField>
        </NativeSelectRoot>
      )}

      {/* Type badge (if schema) */}
      {schemaVar && (
        <Badge
          size="sm"
          colorPalette={
            entry.type === "boolean"
              ? "purple"
              : entry.type === "number"
                ? "blue"
                : entry.type === "enum"
                  ? "orange"
                  : "green"
          }
          alignSelf="center"
        >
          {entry.type}
        </Badge>
      )}

      {/* Value input - varies by operator and type */}
      {!isNoValueOp && (
        <>
          {entry.operator === "$in" ? (
            <Input
              size="sm"
              value={Array.isArray(entry.value) ? entry.value.join(", ") : ""}
              onChange={(e) => onArrayValueChange(index, e.target.value)}
              placeholder="val1, val2"
              flex={1}
              minW="80px"
            />
          ) : entry.type === "enum" && entry.enumValues ? (
            <NativeSelectRoot size="sm" flex={1} minW="80px">
              <NativeSelectField
                value={String(entry.value)}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                  onValueChange(index, e.target.value)
                }
              >
                {entry.enumValues.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </NativeSelectField>
            </NativeSelectRoot>
          ) : entry.type === "boolean" ? (
            <NativeSelectRoot size="sm" flex={1} minW="70px">
              <NativeSelectField
                value={entry.value ? "true" : "false"}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                  onValueChange(index, e.target.value === "true")
                }
              >
                <option value="true">true</option>
                <option value="false">false</option>
              </NativeSelectField>
            </NativeSelectRoot>
          ) : (
            <Input
              size="sm"
              type={entry.type === "number" ? "number" : "text"}
              value={String(entry.value ?? "")}
              onChange={(e) => onValueChange(index, e.target.value)}
              placeholder="value"
              flex={1}
              minW="70px"
            />
          )}
        </>
      )}

      {/* No value indicator for special operators */}
      {isNoValueOp && (
        <Text fontSize="xs" color="fg.muted" alignSelf="center" flex={1}>
          {entry.operator === "$exists" && "(check if set)"}
          {entry.operator === "$toggle" && "(flip value)"}
          {entry.operator === "$unset" && "(remove)"}
        </Text>
      )}

      {/* Delete button */}
      <IconButton
        size="sm"
        colorPalette="red"
        variant="ghost"
        aria-label="Remove"
        onClick={() => onRemove(index)}
      >
        <FaTrash />
      </IconButton>
    </HStack>
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

  // Create a lookup map for schema variables
  const schemaMap = new Map(schema?.map((v) => [v.key, v]) || [])
  const schemaKeys = schema?.map((v) => v.key) || []

  // Get schema variable info for a key
  const getSchemaVariable = (key: string) => schemaMap.get(key)

  // Determine type from schema or infer from value
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

  // Parse current value into entries and groups
  const { entries, groups } = parseConditions(value, getSchemaVariable, getTypeForKey)

  // Update helper
  const update = (newEntries: StateEntry[], newGroups: ConditionGroup[]) => {
    onChange(buildConditionsObject(newEntries, newGroups))
  }

  // --- Entry handlers ---
  const handleAddEntry = () => {
    const defaultOp = mode === "requires" ? "eq" : "set"
    const newEntries: StateEntry[] = [
      ...entries,
      { key: "", operator: defaultOp, value: "", type: "string" },
    ]
    update(newEntries, groups)
  }

  const handleRemoveEntry = (index: number) => {
    const newEntries = entries.filter((_, i) => i !== index)
    update(newEntries, groups)
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
        if (!enumValues.includes(String(newValue))) {
          newValue = enumValues[0] || ""
        }
        if (!["eq", "$ne", "$in", "set"].includes(newOp)) {
          newOp = mode === "requires" ? "eq" : "set"
        }
      } else if (schemaVar.value_type === "boolean") {
        newValue = Boolean(newValue)
        if (!["eq", "$ne", "$exists", "set", "$toggle"].includes(newOp)) {
          newOp = mode === "requires" ? "eq" : "set"
        }
      } else if (schemaVar.value_type === "number") {
        newValue = Number(newValue) || 0
      } else {
        newValue = String(newValue || "")
        if (!["eq", "$ne", "$in", "$exists", "set"].includes(newOp)) {
          newOp = mode === "requires" ? "eq" : "set"
        }
      }

      newEntries[index] = {
        key: newKey,
        operator: newOp,
        value: newValue,
        type: newType,
        enumValues,
      }
    } else {
      newEntries[index] = { ...newEntries[index], key: newKey }
    }

    update(newEntries, groups)
  }

  const handleOperatorChange = (index: number, newOp: string) => {
    const newEntries = [...entries]
    const entry = newEntries[index]

    let newValue = entry.value

    if (newOp === "$exists" || newOp === "$toggle" || newOp === "$unset") {
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

    if (newType === "boolean") {
      newValue = false
    } else if (newType === "number") {
      newValue = 0
    }

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

    let convertedValue: unknown = newValue

    if (entry.type === "boolean" && entry.operator !== "$exists") {
      convertedValue = newValue === "true" || newValue === true
    } else if (entry.type === "number") {
      convertedValue = Number(newValue)
    }

    newEntries[index] = { ...entry, value: convertedValue }
    update(newEntries, groups)
  }

  const handleArrayValueChange = (index: number, inputValue: string) => {
    const newEntries = [...entries]
    const entry = newEntries[index]
    const values = inputValue.split(",").map((v) => v.trim()).filter(Boolean)
    newEntries[index] = { ...entry, value: values }
    update(newEntries, groups)
  }

  // --- Group handlers ---
  const handleAddGroup = () => {
    const newGroups: ConditionGroup[] = [
      ...groups,
      {
        type: "$or",
        conditions: [{ key: "", operator: "eq", value: "", type: "string" }],
      },
    ]
    update(entries, newGroups)
  }

  const handleRemoveGroup = (groupIndex: number) => {
    const newGroups = groups.filter((_, i) => i !== groupIndex)
    update(entries, newGroups)
  }

  const handleGroupTypeChange = (groupIndex: number, newType: GroupType) => {
    const newGroups = [...groups]
    newGroups[groupIndex] = { ...newGroups[groupIndex], type: newType }
    update(entries, newGroups)
  }

  const handleGroupAddEntry = (groupIndex: number) => {
    const newGroups = [...groups]
    const defaultOp = mode === "requires" ? "eq" : "set"
    newGroups[groupIndex] = {
      ...newGroups[groupIndex],
      conditions: [
        ...newGroups[groupIndex].conditions,
        { key: "", operator: defaultOp, value: "", type: "string" },
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
    // Remove empty groups
    if (newGroups[groupIndex].conditions.length === 0) {
      newGroups.splice(groupIndex, 1)
    }
    update(entries, newGroups)
  }

  const handleGroupKeyChange = (groupIndex: number, entryIndex: number, newKey: string) => {
    const newGroups = [...groups]
    const group = newGroups[groupIndex]
    const schemaVar = getSchemaVariable(newKey)

    if (schemaVar) {
      let newType: ValueType = schemaVar.value_type as ValueType
      let newValue: unknown = group.conditions[entryIndex].value
      let enumValues: string[] | undefined
      let newOp = group.conditions[entryIndex].operator

      if (schemaVar.value_type === "enum") {
        newType = "enum"
        enumValues = schemaVar.enum_values || []
        if (!enumValues.includes(String(newValue))) {
          newValue = enumValues[0] || ""
        }
        if (!["eq", "$ne", "$in", "set"].includes(newOp)) {
          newOp = mode === "requires" ? "eq" : "set"
        }
      } else if (schemaVar.value_type === "boolean") {
        newValue = Boolean(newValue)
        if (!["eq", "$ne", "$exists", "set", "$toggle"].includes(newOp)) {
          newOp = mode === "requires" ? "eq" : "set"
        }
      } else if (schemaVar.value_type === "number") {
        newValue = Number(newValue) || 0
      } else {
        newValue = String(newValue || "")
        if (!["eq", "$ne", "$in", "$exists", "set"].includes(newOp)) {
          newOp = mode === "requires" ? "eq" : "set"
        }
      }

      group.conditions[entryIndex] = {
        key: newKey,
        operator: newOp,
        value: newValue,
        type: newType,
        enumValues,
      }
    } else {
      group.conditions[entryIndex] = { ...group.conditions[entryIndex], key: newKey }
    }

    update(entries, newGroups)
  }

  const handleGroupOperatorChange = (groupIndex: number, entryIndex: number, newOp: string) => {
    const newGroups = [...groups]
    const entry = newGroups[groupIndex].conditions[entryIndex]

    let newValue = entry.value

    if (newOp === "$exists" || newOp === "$toggle" || newOp === "$unset") {
      newValue = true
    } else if (newOp === "$in") {
      newValue = Array.isArray(entry.value) ? entry.value : [entry.value]
    } else if (Array.isArray(entry.value)) {
      newValue = entry.value[0] || ""
    }

    newGroups[groupIndex].conditions[entryIndex] = { ...entry, operator: newOp, value: newValue }
    update(entries, newGroups)
  }

  const handleGroupTypeChangeEntry = (groupIndex: number, entryIndex: number, newType: ValueType) => {
    const newGroups = [...groups]
    let newValue: unknown = ""
    const defaultOp = mode === "requires" ? "eq" : "set"

    if (newType === "boolean") {
      newValue = false
    } else if (newType === "number") {
      newValue = 0
    }

    newGroups[groupIndex].conditions[entryIndex] = {
      ...newGroups[groupIndex].conditions[entryIndex],
      type: newType,
      value: newValue,
      operator: defaultOp,
      enumValues: undefined,
    }
    update(entries, newGroups)
  }

  const handleGroupValueChange = (groupIndex: number, entryIndex: number, newValue: unknown) => {
    const newGroups = [...groups]
    const entry = newGroups[groupIndex].conditions[entryIndex]

    let convertedValue: unknown = newValue

    if (entry.type === "boolean" && entry.operator !== "$exists") {
      convertedValue = newValue === "true" || newValue === true
    } else if (entry.type === "number") {
      convertedValue = Number(newValue)
    }

    newGroups[groupIndex].conditions[entryIndex] = { ...entry, value: convertedValue }
    update(entries, newGroups)
  }

  const handleGroupArrayValueChange = (groupIndex: number, entryIndex: number, inputValue: string) => {
    const newGroups = [...groups]
    const entry = newGroups[groupIndex].conditions[entryIndex]
    const values = inputValue.split(",").map((v) => v.trim()).filter(Boolean)
    newGroups[groupIndex].conditions[entryIndex] = { ...entry, value: values }
    update(entries, newGroups)
  }

  // Get available operators for a type
  const getOperatorsForType = (type: ValueType) => {
    return operators.filter((op) => op.types.includes(type))
  }

  // Check for duplicate keys (across entries and groups)
  const getAllKeys = (): string[] => {
    const keys = entries.map((e) => e.key).filter((k) => k.trim())
    for (const group of groups) {
      keys.push(...group.conditions.map((e) => e.key).filter((k) => k.trim()))
    }
    return keys
  }

  const getDuplicateKeys = (): string[] => {
    const keys = getAllKeys()
    const duplicates = keys.filter((key, index) => keys.indexOf(key) !== index)
    return [...new Set(duplicates)]
  }

  const getUndefinedKeys = (): string[] => {
    if (!schema || schema.length === 0) return []
    return getAllKeys().filter((k) => !schemaKeys.includes(k))
  }

  const duplicateKeys = getDuplicateKeys()
  const undefinedKeys = getUndefinedKeys()

  const datalistId = `schema-keys-${label.replace(/\s+/g, "-").toLowerCase()}`

  const hasContent = entries.length > 0 || groups.length > 0

  return (
    <Box>
      <HStack justify="space-between" mb={3}>
        <Heading size="xs" color="fg.muted">
          {label}
        </Heading>
        <IconButton
          size="xs"
          variant="ghost"
          aria-label="Toggle JSON preview"
          onClick={() => setShowJsonPreview(!showJsonPreview)}
        >
          <FaCode />
        </IconButton>
      </HStack>

      {schema && schema.length > 0 && (
        <datalist id={datalistId}>
          {schema.map((v) => (
            <option key={v.key} value={v.key}>
              {v.description || v.key}
            </option>
          ))}
        </datalist>
      )}

      {showJsonPreview ? (
        <Box
          p={3}
          bg="gray.900"
          color="green.300"
          borderRadius="md"
          fontFamily="mono"
          fontSize="xs"
          overflowX="auto"
        >
          <pre>{JSON.stringify(value, null, 2) || "{}"}</pre>
        </Box>
      ) : (
        <VStack align="stretch" gap={3}>
          {!hasContent && (
            <Text fontSize="sm" color="fg.subtle" fontStyle="italic">
              No {mode === "requires" ? "conditions" : "mutations"} set
            </Text>
          )}

          {/* Top-level entries (implicitly AND) */}
          {entries.length > 0 && (
            <VStack align="stretch" gap={2}>
              {entries.map((entry, index) => (
                <ConditionRow
                  key={index}
                  entry={entry}
                  index={index}
                  schema={schema}
                  schemaMap={schemaMap}
                  datalistId={datalistId}
                  duplicateKeys={duplicateKeys}
                  undefinedKeys={undefinedKeys}
                  onKeyChange={handleKeyChange}
                  onOperatorChange={handleOperatorChange}
                  onTypeChange={handleTypeChange}
                  onValueChange={handleValueChange}
                  onArrayValueChange={handleArrayValueChange}
                  onRemove={handleRemoveEntry}
                  getOperatorsForType={getOperatorsForType}
                />
              ))}
            </VStack>
          )}

          {/* Logical Groups (only for requires mode) */}
          {mode === "requires" && groups.map((group, groupIndex) => (
            <Card.Root key={groupIndex} size="sm" variant="outline">
              <Card.Body py={2} px={3}>
                <VStack align="stretch" gap={2}>
                  <HStack justify="space-between">
                    <HStack gap={2}>
                      <FaLayerGroup size={12} />
                      <NativeSelectRoot size="xs" w="80px">
                        <NativeSelectField
                          value={group.type}
                          onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                            handleGroupTypeChange(groupIndex, e.target.value as GroupType)
                          }
                        >
                          <option value="$or">Any of</option>
                          <option value="$and">All of</option>
                        </NativeSelectField>
                      </NativeSelectRoot>
                      <Text fontSize="xs" color="fg.muted">
                        {group.type === "$or" ? "(OR)" : "(AND)"}
                      </Text>
                    </HStack>
                    <IconButton
                      size="xs"
                      colorPalette="red"
                      variant="ghost"
                      aria-label="Remove group"
                      onClick={() => handleRemoveGroup(groupIndex)}
                    >
                      <FaTrash />
                    </IconButton>
                  </HStack>

                  {group.conditions.map((entry, entryIndex) => (
                    <ConditionRow
                      key={entryIndex}
                      entry={entry}
                      index={entryIndex}
                      schema={schema}
                      schemaMap={schemaMap}
                      datalistId={datalistId}
                      duplicateKeys={duplicateKeys}
                      undefinedKeys={undefinedKeys}
                      onKeyChange={(idx, key) => handleGroupKeyChange(groupIndex, idx, key)}
                      onOperatorChange={(idx, op) => handleGroupOperatorChange(groupIndex, idx, op)}
                      onTypeChange={(idx, type) => handleGroupTypeChangeEntry(groupIndex, idx, type)}
                      onValueChange={(idx, val) => handleGroupValueChange(groupIndex, idx, val)}
                      onArrayValueChange={(idx, val) => handleGroupArrayValueChange(groupIndex, idx, val)}
                      onRemove={(idx) => handleGroupRemoveEntry(groupIndex, idx)}
                      getOperatorsForType={getOperatorsForType}
                    />
                  ))}

                  <Button
                    size="xs"
                    variant="ghost"
                    colorPalette="blue"
                    onClick={() => handleGroupAddEntry(groupIndex)}
                    alignSelf="start"
                  >
                    <FaPlus fontSize="8px" />
                    Add to group
                  </Button>
                </VStack>
              </Card.Body>
            </Card.Root>
          ))}

          {/* Action buttons */}
          <HStack gap={2}>
            <Button
              size="sm"
              variant="outline"
              colorPalette="blue"
              onClick={handleAddEntry}
            >
              <FaPlus fontSize="10px" />
              Add {mode === "requires" ? "Condition" : "Change"}
            </Button>

            {mode === "requires" && (
              <Button
                size="sm"
                variant="ghost"
                colorPalette="purple"
                onClick={handleAddGroup}
              >
                <FaLayerGroup fontSize="10px" />
                Add OR Group
              </Button>
            )}
          </HStack>

          {schema && schema.length > 0 && !hasContent && (
            <Text fontSize="xs" color="fg.muted">
              {schema.length} variable{schema.length !== 1 ? "s" : ""} available
            </Text>
          )}
        </VStack>
      )}
    </Box>
  )
}

export default StateConditionEditor
