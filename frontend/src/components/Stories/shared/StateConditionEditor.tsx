import { useState } from "react"
import {
  Box,
  Button,
  Heading,
  HStack,
  IconButton,
  Input,
  NativeSelectRoot,
  NativeSelectField,
  Text,
  VStack,
} from "@chakra-ui/react"
import { FaPlus, FaTrash, FaCode } from "react-icons/fa"

interface StateConditionEditorProps {
  value: Record<string, unknown> | null
  onChange: (value: Record<string, unknown> | null) => void
  label: string
}

type ValueType = "boolean" | "string" | "number"

interface StateEntry {
  key: string
  value: unknown
  type: ValueType
}

const StateConditionEditor = ({ value, onChange, label }: StateConditionEditorProps) => {
  const [showJsonPreview, setShowJsonPreview] = useState(false)

  // Convert value object to array of entries for editing
  const entries: StateEntry[] = value
    ? Object.entries(value).map(([key, val]) => ({
        key,
        value: val,
        type: typeof val as ValueType,
      }))
    : []

  // Convert entries array back to object
  const entriesToObject = (entries: StateEntry[]): Record<string, unknown> | null => {
    if (entries.length === 0) return null
    const obj: Record<string, unknown> = {}
    entries.forEach((entry) => {
      if (entry.key.trim()) {
        obj[entry.key] = entry.value
      }
    })
    return Object.keys(obj).length > 0 ? obj : null
  }

  const handleAddEntry = () => {
    const newEntries: StateEntry[] = [...entries, { key: "", value: "", type: "string" }]
    onChange(entriesToObject(newEntries))
  }

  const handleRemoveEntry = (index: number) => {
    const newEntries = entries.filter((_, i) => i !== index)
    onChange(entriesToObject(newEntries))
  }

  const handleKeyChange = (index: number, newKey: string) => {
    const newEntries = [...entries]
    newEntries[index] = { ...newEntries[index], key: newKey }
    onChange(entriesToObject(newEntries))
  }

  const handleTypeChange = (index: number, newType: ValueType) => {
    const newEntries = [...entries]
    let newValue: unknown = ""

    // Convert value to new type
    if (newType === "boolean") {
      newValue = newEntries[index].value === "true" || newEntries[index].value === true
    } else if (newType === "number") {
      newValue = Number(newEntries[index].value) || 0
    } else {
      newValue = String(newEntries[index].value)
    }

    newEntries[index] = { ...newEntries[index], type: newType, value: newValue }
    onChange(entriesToObject(newEntries))
  }

  const handleValueChange = (index: number, newValue: string | boolean) => {
    const newEntries = [...entries]
    const entry = newEntries[index]

    let convertedValue: unknown = newValue

    if (entry.type === "boolean") {
      convertedValue = newValue === "true" || newValue === true
    } else if (entry.type === "number") {
      convertedValue = Number(newValue)
    } else {
      convertedValue = String(newValue)
    }

    newEntries[index] = { ...newEntries[index], value: convertedValue }
    onChange(entriesToObject(newEntries))
  }

  // Check for duplicate keys
  const getDuplicateKeys = (): string[] => {
    const keys = entries.map((e) => e.key).filter((k) => k.trim())
    const duplicates = keys.filter((key, index) => keys.indexOf(key) !== index)
    return [...new Set(duplicates)]
  }

  const duplicateKeys = getDuplicateKeys()

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
        <VStack align="stretch" gap={2}>
          {entries.length === 0 ? (
            <Text fontSize="sm" color="fg.subtle" fontStyle="italic">
              No conditions set
            </Text>
          ) : (
            entries.map((entry, index) => {
              const isDuplicate = duplicateKeys.includes(entry.key)
              return (
                <HStack key={index} gap={2} align="start">
                  <Box flex={1}>
                    <Input
                      size="sm"
                      value={entry.key}
                      onChange={(e) => handleKeyChange(index, e.target.value)}
                      placeholder="key"
                      borderColor={isDuplicate ? "red.500" : undefined}
                    />
                    {isDuplicate && (
                      <Text fontSize="2xs" color="red.500" mt={1}>
                        Duplicate key
                      </Text>
                    )}
                  </Box>

                  <NativeSelectRoot size="sm" w="100px">
                    <NativeSelectField
                      value={entry.type}
                      onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                        handleTypeChange(index, e.target.value as ValueType)
                      }
                    >
                      <option value="string">String</option>
                      <option value="number">Number</option>
                      <option value="boolean">Boolean</option>
                    </NativeSelectField>
                  </NativeSelectRoot>

                  {entry.type === "boolean" ? (
                    <NativeSelectRoot size="sm" flex={1}>
                      <NativeSelectField
                        value={entry.value ? "true" : "false"}
                        onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                          handleValueChange(index, e.target.value === "true")
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
                      value={String(entry.value)}
                      onChange={(e) => handleValueChange(index, e.target.value)}
                      placeholder="value"
                      flex={1}
                    />
                  )}

                  <IconButton
                    size="sm"
                    colorPalette="red"
                    variant="ghost"
                    aria-label="Remove condition"
                    onClick={() => handleRemoveEntry(index)}
                  >
                    <FaTrash />
                  </IconButton>
                </HStack>
              )
            })
          )}

          <Button
            size="sm"
            variant="outline"
            colorPalette="blue"
            onClick={handleAddEntry}
            alignSelf="start"
          >
            <FaPlus fontSize="10px" />
            Add Condition
          </Button>
        </VStack>
      )}
    </Box>
  )
}

export default StateConditionEditor
