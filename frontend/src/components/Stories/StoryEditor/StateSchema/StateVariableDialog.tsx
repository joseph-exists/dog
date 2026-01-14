/**
 * StateVariableDialog - Dialog for creating/editing state variables
 *
 * Features:
 * - Key, description, value_type, default_value, category fields
 * - Enum support with comma-separated values
 * - Dynamic default value input based on type
 * - Create and edit modes
 */

import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import type { StoryStateVariablePublic, StateValueType } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"

const VALUE_TYPES: { value: StateValueType; label: string }[] = [
  { value: "string", label: "String" },
  { value: "number", label: "Number" },
  { value: "boolean", label: "Boolean" },
  { value: "enum", label: "Enum" },
]

const variableSchema = z.object({
  key: z
    .string()
    .min(1, "Key is required")
    .regex(/^[a-zA-Z_][a-zA-Z0-9_]*$/, "Key must be a valid identifier"),
  description: z.string().optional(),
  value_type: z.enum(["string", "number", "boolean", "enum"]),
  default_value_string: z.string().optional(),
  default_value_number: z.number().optional(),
  default_value_boolean: z.boolean().optional(),
  enum_values_raw: z.string().optional(),
  category: z.string().optional(),
})

type VariableFormData = z.infer<typeof variableSchema>

interface StateVariableDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  variable?: StoryStateVariablePublic
  onSave: (data: {
    key: string
    description?: string | null
    value_type: StateValueType
    default_value?: unknown
    enum_values?: string[] | null
    category?: string | null
  }) => Promise<void>
  existingKeys?: string[]
}

const StateVariableDialog = ({
  open,
  onOpenChange,
  variable,
  onSave,
  existingKeys = [],
}: StateVariableDialogProps) => {
  const isEditing = !!variable

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<VariableFormData>({
    resolver: zodResolver(variableSchema),
    defaultValues: {
      key: "",
      description: "",
      value_type: "string",
      default_value_string: "",
      default_value_number: 0,
      default_value_boolean: false,
      enum_values_raw: "",
      category: "",
    },
  })

  const valueType = watch("value_type")

  // Initialize form when editing
  useEffect(() => {
    if (variable) {
      reset({
        key: variable.key,
        description: variable.description || "",
        value_type: variable.value_type || "string",
        default_value_string:
          variable.value_type === "string"
            ? String(variable.default_value || "")
            : "",
        default_value_number:
          variable.value_type === "number"
            ? Number(variable.default_value || 0)
            : 0,
        default_value_boolean:
          variable.value_type === "boolean"
            ? Boolean(variable.default_value)
            : false,
        enum_values_raw: variable.enum_values?.join(", ") || "",
        category: variable.category || "",
      })
    } else {
      reset({
        key: "",
        description: "",
        value_type: "string",
        default_value_string: "",
        default_value_number: 0,
        default_value_boolean: false,
        enum_values_raw: "",
        category: "",
      })
    }
  }, [variable, reset])

  const onSubmit = async (data: VariableFormData) => {
    // Check for duplicate keys (only when creating or changing key)
    if (!isEditing || data.key !== variable?.key) {
      if (existingKeys.includes(data.key)) {
        return // Validation will catch this
      }
    }

    // Determine default value based on type
    let defaultValue: unknown = null
    switch (data.value_type) {
      case "string":
        defaultValue = data.default_value_string || null
        break
      case "number":
        defaultValue = data.default_value_number ?? null
        break
      case "boolean":
        defaultValue = data.default_value_boolean ?? false
        break
      case "enum":
        defaultValue = data.default_value_string || null
        break
    }

    // Parse enum values
    const enumValues =
      data.value_type === "enum" && data.enum_values_raw
        ? data.enum_values_raw
            .split(",")
            .map((v) => v.trim())
            .filter(Boolean)
        : null

    await onSave({
      key: data.key,
      description: data.description || null,
      value_type: data.value_type,
      default_value: defaultValue,
      enum_values: enumValues,
      category: data.category || null,
    })

    onOpenChange(false)
  }

  const handleClose = () => {
    reset()
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? "Edit State Variable" : "Add State Variable"}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? "Modify the state variable properties"
              : "Define a new state variable for your story"}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Key */}
          <div className="space-y-2">
            <Label htmlFor="key">Variable Key</Label>
            <Input
              id="key"
              placeholder="e.g., hasKey, playerHealth"
              {...register("key")}
              disabled={isEditing} // Don't allow changing key when editing
            />
            {errors.key && (
              <p className="text-destructive text-sm">{errors.key.message}</p>
            )}
          </div>

          {/* Value Type */}
          <div className="space-y-2">
            <Label htmlFor="value_type">Type</Label>
            <Select
              value={valueType}
              onValueChange={(val) =>
                setValue("value_type", val as StateValueType)
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                {VALUE_TYPES.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Enum Values (only shown for enum type) */}
          {valueType === "enum" && (
            <div className="space-y-2">
              <Label htmlFor="enum_values_raw">Enum Values</Label>
              <Input
                id="enum_values_raw"
                placeholder="value1, value2, value3"
                {...register("enum_values_raw")}
              />
              <p className="text-xs text-muted-foreground">
                Comma-separated list of allowed values
              </p>
            </div>
          )}

          {/* Default Value */}
          <div className="space-y-2">
            <Label>Default Value</Label>
            {valueType === "boolean" ? (
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="default_value_boolean"
                  checked={watch("default_value_boolean")}
                  onCheckedChange={(checked) =>
                    setValue("default_value_boolean", checked === true)
                  }
                />
                <Label htmlFor="default_value_boolean" className="font-normal">
                  {watch("default_value_boolean") ? "True" : "False"}
                </Label>
              </div>
            ) : valueType === "number" ? (
              <Input
                type="number"
                {...register("default_value_number", { valueAsNumber: true })}
                placeholder="0"
              />
            ) : valueType === "enum" ? (
              <Select
                value={watch("default_value_string") || ""}
                onValueChange={(val) => setValue("default_value_string", val)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select default" />
                </SelectTrigger>
                <SelectContent>
                  {watch("enum_values_raw")
                    ?.split(",")
                    .map((v) => v.trim())
                    .filter(Boolean)
                    .map((value) => (
                      <SelectItem key={value} value={value}>
                        {value}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            ) : (
              <Input
                {...register("default_value_string")}
                placeholder="Default value"
              />
            )}
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="What this variable represents..."
              rows={2}
              {...register("description")}
            />
          </div>

          {/* Category */}
          <div className="space-y-2">
            <Label htmlFor="category">Category (Optional)</Label>
            <Input
              id="category"
              placeholder="e.g., inventory, stats, flags"
              {...register("category")}
            />
            <p className="text-xs text-muted-foreground">
              Group related variables together
            </p>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : isEditing ? "Save Changes" : "Add Variable"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default StateVariableDialog
