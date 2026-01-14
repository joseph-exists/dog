import {
  Badge,
  Box,
  Button,
  HStack,
  IconButton,
  Spinner,
  Table,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useState } from "react"
import { FaEdit, FaPlus, FaTrash } from "react-icons/fa"

import type { StoryStateVariablePublic } from "@/client"
import {
  useDeleteStateVariable,
  useStateSchema,
} from "@/hooks/stories/useStateSchema"
import StateVariableModal from "./StateVariableModal"

interface StateSchemaEditorProps {
  storyId: string
  version: number
  isReadOnly?: boolean
}

const VALUE_TYPE_COLORS: Record<string, string> = {
  boolean: "purple",
  number: "blue",
  string: "green",
  enum: "orange",
}

const StateSchemaEditor = ({
  storyId,
  version,
  isReadOnly = false,
}: StateSchemaEditorProps) => {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingVariable, setEditingVariable] =
    useState<StoryStateVariablePublic | null>(null)

  const { data, isLoading, error } = useStateSchema(storyId, version)
  const deleteMutation = useDeleteStateVariable(storyId, version)

  const handleAdd = () => {
    setEditingVariable(null)
    setIsModalOpen(true)
  }

  const handleEdit = (variable: StoryStateVariablePublic) => {
    setEditingVariable(variable)
    setIsModalOpen(true)
  }

  const handleDelete = (variable: StoryStateVariablePublic) => {
    if (
      window.confirm(
        `Delete variable "${variable.key}"? This may break choices that reference it.`,
      )
    ) {
      deleteMutation.mutate(variable.id)
    }
  }

  const handleModalClose = () => {
    setIsModalOpen(false)
    setEditingVariable(null)
  }

  // Group variables by category
  const groupedVariables = (data?.data || []).reduce(
    (acc, variable) => {
      const category = variable.category || "Uncategorized"
      if (!acc[category]) {
        acc[category] = []
      }
      acc[category].push(variable)
      return acc
    },
    {} as Record<string, StoryStateVariablePublic[]>,
  )

  const categories = Object.keys(groupedVariables).sort((a, b) => {
    if (a === "Uncategorized") return 1
    if (b === "Uncategorized") return -1
    return a.localeCompare(b)
  })

  if (isLoading) {
    return (
      <Box py={8} textAlign="center">
        <Spinner size="lg" />
      </Box>
    )
  }

  if (error) {
    return (
      <Box py={4}>
        <Text color="red.500">Error loading state variables</Text>
      </Box>
    )
  }

  const formatDefaultValue = (variable: StoryStateVariablePublic): string => {
    if (variable.default_value === null || variable.default_value === undefined)
      return "-"
    if (variable.value_type === "boolean")
      return variable.default_value ? "true" : "false"
    return String(variable.default_value)
  }

  return (
    <Box>
      {/* Header with Add button */}
      {!isReadOnly && (
        <HStack justify="space-between" mb={4}>
          <Text fontSize="sm" color="fg.muted">
            {data?.count || 0} variable{data?.count !== 1 ? "s" : ""} defined
          </Text>
          <Button size="sm" colorPalette="blue" onClick={handleAdd}>
            <FaPlus />
            Add Variable
          </Button>
        </HStack>
      )}

      {/* Empty state */}
      {(!data?.data || data.data.length === 0) && (
        <Box
          py={8}
          textAlign="center"
          borderWidth="1px"
          borderStyle="dashed"
          borderColor="border"
          borderRadius="md"
        >
          <Text color="fg.muted" mb={2}>
            No state variables defined
          </Text>
          <Text fontSize="sm" color="fg.muted">
            State variables let you track player choices and show/hide content
            conditionally.
          </Text>
          {!isReadOnly && (
            <Button
              size="sm"
              colorPalette="blue"
              variant="ghost"
              mt={4}
              onClick={handleAdd}
            >
              <FaPlus />
              Add your first variable
            </Button>
          )}
        </Box>
      )}

      {/* Variables table grouped by category */}
      {categories.length > 0 && (
        <VStack align="stretch" gap={4}>
          {categories.map((category) => (
            <Box key={category}>
              <Text
                fontSize="xs"
                fontWeight="bold"
                color="fg.muted"
                textTransform="uppercase"
                mb={2}
              >
                {category}
              </Text>
              <Table.Root size="sm">
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>Key</Table.ColumnHeader>
                    <Table.ColumnHeader w="100px">Type</Table.ColumnHeader>
                    <Table.ColumnHeader w="120px">Default</Table.ColumnHeader>
                    {!isReadOnly && (
                      <Table.ColumnHeader w="80px" textAlign="right">
                        Actions
                      </Table.ColumnHeader>
                    )}
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {groupedVariables[category].map((variable) => (
                    <Table.Row key={variable.id}>
                      <Table.Cell>
                        <VStack align="start" gap={0}>
                          <Text fontFamily="mono" fontSize="sm">
                            {variable.key}
                          </Text>
                          {variable.description && (
                            <Text fontSize="xs" color="fg.muted" truncate>
                              {variable.description}
                            </Text>
                          )}
                        </VStack>
                      </Table.Cell>
                      <Table.Cell>
                        <Badge
                          size="sm"
                          colorPalette={
                            VALUE_TYPE_COLORS[variable.value_type || "string"]
                          }
                        >
                          {variable.value_type || "string"}
                        </Badge>
                        {variable.value_type === "enum" &&
                          variable.enum_values && (
                            <Text fontSize="xs" color="fg.muted" mt={1}>
                              {variable.enum_values.length} options
                            </Text>
                          )}
                      </Table.Cell>
                      <Table.Cell>
                        <Text fontSize="sm" fontFamily="mono">
                          {formatDefaultValue(variable)}
                        </Text>
                      </Table.Cell>
                      {!isReadOnly && (
                        <Table.Cell textAlign="right">
                          <HStack gap={1} justify="flex-end">
                            <IconButton
                              aria-label="Edit variable"
                              size="xs"
                              variant="ghost"
                              onClick={() => handleEdit(variable)}
                            >
                              <FaEdit />
                            </IconButton>
                            <IconButton
                              aria-label="Delete variable"
                              size="xs"
                              variant="ghost"
                              colorPalette="red"
                              onClick={() => handleDelete(variable)}
                              loading={deleteMutation.isPending}
                            >
                              <FaTrash />
                            </IconButton>
                          </HStack>
                        </Table.Cell>
                      )}
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
          ))}
        </VStack>
      )}

      {/* Modal for add/edit */}
      <StateVariableModal
        storyId={storyId}
        version={version}
        variable={editingVariable || undefined}
        isOpen={isModalOpen}
        onClose={handleModalClose}
      />
    </Box>
  )
}

export default StateSchemaEditor
