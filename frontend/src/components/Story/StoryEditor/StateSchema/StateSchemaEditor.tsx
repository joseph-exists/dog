/**
 * StateSchemaEditor - Table of state variables grouped by category
 *
 * Features:
 * - Table display with key, type, default value, description columns
 * - Grouped by category with collapsible sections
 * - Add, edit, delete actions
 * - Read-only mode for published stories
 */

import {
  ChevronDown,
  ChevronRight,
  Pencil,
  Plus,
  Trash2,
  Variable,
} from "lucide-react"
import { useMemo, useState } from "react"
import type { StateValueType, StoryStateVariablePublic } from "@/client"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  useCreateStateVariable,
  useDeleteStateVariable,
  useStateSchema,
  useUpdateStateVariable,
} from "@/hooks/stories/useStateSchema"
import StateVariableDialog from "./StateVariableDialog"

const TYPE_COLORS: Record<StateValueType, string> = {
  string: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
  number: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
  boolean:
    "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300",
  enum: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300",
}

interface StateSchemaEditorProps {
  storyId: string
  version: number
  readOnly?: boolean
}

const StateSchemaEditor = ({
  storyId,
  version,
  readOnly = false,
}: StateSchemaEditorProps) => {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingVariable, setEditingVariable] = useState<
    StoryStateVariablePublic | undefined
  >()
  const [deleteVariable, setDeleteVariable] =
    useState<StoryStateVariablePublic | null>(null)
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(["uncategorized"]),
  )

  // Fetch state schema
  const { data: schemaData, isLoading } = useStateSchema(storyId, version)
  const variables = schemaData?.data || []

  // Mutations
  const createVariable = useCreateStateVariable(storyId, version)
  const updateVariable = useUpdateStateVariable(storyId, version)
  const deleteVariableMutation = useDeleteStateVariable(storyId, version)

  // Group variables by category
  const groupedVariables = useMemo(() => {
    const groups: Record<string, StoryStateVariablePublic[]> = {}

    variables.forEach((v) => {
      const category = v.category || "uncategorized"
      if (!groups[category]) {
        groups[category] = []
      }
      groups[category].push(v)
    })

    // Sort categories alphabetically but keep "uncategorized" last
    const sortedKeys = Object.keys(groups).sort((a, b) => {
      if (a === "uncategorized") return 1
      if (b === "uncategorized") return -1
      return a.localeCompare(b)
    })

    return sortedKeys.map((key) => ({
      category: key,
      variables: groups[key].sort((a, b) => a.key.localeCompare(b.key)),
    }))
  }, [variables])

  // Existing keys for validation
  const existingKeys = useMemo(() => variables.map((v) => v.key), [variables])

  // Toggle category expansion
  const toggleCategory = (category: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev)
      if (next.has(category)) {
        next.delete(category)
      } else {
        next.add(category)
      }
      return next
    })
  }

  // Handle save (create or update)
  const handleSave = async (data: {
    key: string
    description?: string | null
    value_type: StateValueType
    default_value?: unknown
    enum_values?: string[] | null
    category?: string | null
  }) => {
    if (editingVariable) {
      await updateVariable.mutateAsync({
        variableId: editingVariable.id,
        data: {
          description: data.description,
          value_type: data.value_type,
          default_value: data.default_value,
          enum_values: data.enum_values,
          category: data.category,
        },
      })
    } else {
      await createVariable.mutateAsync({
        key: data.key,
        description: data.description,
        value_type: data.value_type,
        default_value: data.default_value,
        enum_values: data.enum_values,
        category: data.category,
      })
    }
    setEditingVariable(undefined)
  }

  // Handle delete
  const handleDelete = async () => {
    if (deleteVariable) {
      await deleteVariableMutation.mutateAsync(deleteVariable.id)
      setDeleteVariable(null)
    }
  }

  // Open dialog for new variable
  const handleAddNew = () => {
    setEditingVariable(undefined)
    setDialogOpen(true)
  }

  // Open dialog for editing
  const handleEdit = (variable: StoryStateVariablePublic) => {
    setEditingVariable(variable)
    setDialogOpen(true)
  }

  // Format default value for display
  const formatDefaultValue = (variable: StoryStateVariablePublic) => {
    if (
      variable.default_value === null ||
      variable.default_value === undefined
    ) {
      return <span className="text-muted-foreground italic">null</span>
    }
    if (variable.value_type === "boolean") {
      return variable.default_value ? "true" : "false"
    }
    if (variable.value_type === "string") {
      return `"${variable.default_value}"`
    }
    return String(variable.default_value)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <p className="text-muted-foreground">Loading state schema...</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Variable className="h-5 w-5 text-muted-foreground" />
          <h3 className="font-semibold">State Variables</h3>
          <Badge variant="secondary">{variables.length}</Badge>
        </div>
        {!readOnly && (
          <Button size="sm" onClick={handleAddNew}>
            <Plus className="h-4 w-4 mr-2" />
            Add Variable
          </Button>
        )}
      </div>

      {/* Empty state */}
      {variables.length === 0 ? (
        <div className="border border-dashed rounded-lg p-8 text-center">
          <Variable className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground mb-4">
            No state variables defined yet
          </p>
          {!readOnly && (
            <Button variant="outline" onClick={handleAddNew}>
              <Plus className="h-4 w-4 mr-2" />
              Add Your First Variable
            </Button>
          )}
        </div>
      ) : (
        /* Grouped variables */
        <div className="space-y-4">
          {groupedVariables.map(({ category, variables: categoryVars }) => (
            <Collapsible
              key={category}
              open={expandedCategories.has(category)}
              onOpenChange={() => toggleCategory(category)}
            >
              <CollapsibleTrigger asChild>
                <Button
                  variant="ghost"
                  className="w-full justify-start gap-2 font-medium"
                >
                  {expandedCategories.has(category) ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                  <span className="capitalize">
                    {category === "uncategorized" ? "Uncategorized" : category}
                  </span>
                  <Badge variant="outline" className="ml-auto">
                    {categoryVars.length}
                  </Badge>
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div className="border rounded-md mt-2">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-[200px]">Key</TableHead>
                        <TableHead className="w-[100px]">Type</TableHead>
                        <TableHead className="w-[150px]">Default</TableHead>
                        <TableHead>Description</TableHead>
                        {!readOnly && (
                          <TableHead className="w-[100px] text-right">
                            Actions
                          </TableHead>
                        )}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {categoryVars.map((variable) => (
                        <TableRow key={variable.id}>
                          <TableCell className="font-mono text-sm">
                            {variable.key}
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant="secondary"
                              className={
                                TYPE_COLORS[variable.value_type || "string"]
                              }
                            >
                              {variable.value_type || "string"}
                            </Badge>
                            {variable.value_type === "enum" &&
                              variable.enum_values && (
                                <span className="text-xs text-muted-foreground ml-2">
                                  ({variable.enum_values.length} values)
                                </span>
                              )}
                          </TableCell>
                          <TableCell className="font-mono text-sm">
                            {formatDefaultValue(variable)}
                          </TableCell>
                          <TableCell className="text-muted-foreground text-sm max-w-[200px] truncate">
                            {variable.description || "—"}
                          </TableCell>
                          {!readOnly && (
                            <TableCell className="text-right">
                              <div className="flex justify-end gap-1">
                                <Button
                                  size="icon"
                                  variant="ghost"
                                  onClick={() => handleEdit(variable)}
                                >
                                  <Pencil className="h-4 w-4" />
                                </Button>
                                <Button
                                  size="icon"
                                  variant="ghost"
                                  onClick={() => setDeleteVariable(variable)}
                                >
                                  <Trash2 className="h-4 w-4 text-destructive" />
                                </Button>
                              </div>
                            </TableCell>
                          )}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CollapsibleContent>
            </Collapsible>
          ))}
        </div>
      )}

      {/* Add/Edit Dialog */}
      <StateVariableDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        variable={editingVariable}
        onSave={handleSave}
        existingKeys={
          editingVariable
            ? existingKeys.filter((k) => k !== editingVariable.key)
            : existingKeys
        }
      />

      {/* Delete Confirmation */}
      <AlertDialog
        open={!!deleteVariable}
        onOpenChange={(open) => !open && setDeleteVariable(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete State Variable</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the variable "
              {deleteVariable?.key}"?
              <br />
              <span className="text-amber-600">
                This may break choices that reference this variable.
              </span>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete}>Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

export default StateSchemaEditor
