import {
  Button,
  DialogActionTrigger,
  HStack,
  IconButton,
  Input,
  NativeSelectField,
  NativeSelectRoot,
  Tag,
  Text,
  Textarea,
  VStack,
} from "@chakra-ui/react"
import { useEffect, useState } from "react"
import { Controller, type SubmitHandler, useForm } from "react-hook-form"
import { FaPlus, FaTimes } from "react-icons/fa"

import type {
  StateValueType,
  StoryStateVariableBase,
  StoryStateVariablePublic,
} from "@/client"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
} from "@/components/ui/dialog"
import { Field } from "@/components/ui/field"
import {
  useCreateStateVariable,
  useUpdateStateVariable,
} from "@/hooks/stories/useStateSchema"

interface StateVariableModalProps {
  storyId: string
  version: number
  variable?: StoryStateVariablePublic
  isOpen: boolean
  onClose: () => void
}

interface FormData {
  key: string
  value_type: StateValueType
  default_value_boolean: boolean
  default_value_number: number | null
  default_value_string: string
  default_value_enum: string
  enum_values: string[]
  category: string
  description: string
}

const StateVariableModal = ({
  storyId,
  version,
  variable,
  isOpen,
  onClose,
}: StateVariableModalProps) => {
  const isEditMode = !!variable
  const [enumInput, setEnumInput] = useState("")

  const createMutation = useCreateStateVariable(storyId, version)
  const updateMutation = useUpdateStateVariable(storyId, version)

  const {
    control,
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors, isValid, isSubmitting },
  } = useForm<FormData>({
    mode: "onBlur",
    defaultValues: {
      key: "",
      value_type: "string",
      default_value_boolean: false,
      default_value_number: null,
      default_value_string: "",
      default_value_enum: "",
      enum_values: [],
      category: "",
      description: "",
    },
  })

  const valueType = watch("value_type")
  const enumValues = watch("enum_values")

  // Reset form when variable changes or modal opens
  useEffect(() => {
    if (isOpen) {
      if (variable) {
        const defaultVal = variable.default_value
        reset({
          key: variable.key,
          value_type: variable.value_type || "string",
          default_value_boolean:
            variable.value_type === "boolean" ? Boolean(defaultVal) : false,
          default_value_number:
            variable.value_type === "number" ? (defaultVal as number) : null,
          default_value_string:
            variable.value_type === "string" ? String(defaultVal || "") : "",
          default_value_enum:
            variable.value_type === "enum" ? String(defaultVal || "") : "",
          enum_values: variable.enum_values || [],
          category: variable.category || "",
          description: variable.description || "",
        })
      } else {
        reset({
          key: "",
          value_type: "string",
          default_value_boolean: false,
          default_value_number: null,
          default_value_string: "",
          default_value_enum: "",
          enum_values: [],
          category: "",
          description: "",
        })
      }
      setEnumInput("")
    }
  }, [isOpen, variable, reset])

  const handleAddEnumValue = () => {
    const trimmed = enumInput.trim()
    if (trimmed && !enumValues.includes(trimmed)) {
      setValue("enum_values", [...enumValues, trimmed])
      setEnumInput("")
    }
  }

  const handleRemoveEnumValue = (value: string) => {
    setValue(
      "enum_values",
      enumValues.filter((v) => v !== value),
    )
  }

  const handleEnumKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault()
      handleAddEnumValue()
    }
  }

  const onSubmit: SubmitHandler<FormData> = (data) => {
    // Build default_value based on type
    let defaultValue: unknown = null
    switch (data.value_type) {
      case "boolean":
        defaultValue = data.default_value_boolean
        break
      case "number":
        defaultValue = data.default_value_number
        break
      case "string":
        defaultValue = data.default_value_string || null
        break
      case "enum":
        defaultValue = data.default_value_enum || null
        break
    }

    const payload: StoryStateVariableBase = {
      key: data.key,
      value_type: data.value_type,
      default_value: defaultValue,
      enum_values: data.value_type === "enum" ? data.enum_values : null,
      category: data.category || null,
      description: data.description || null,
    }

    if (isEditMode) {
      updateMutation.mutate(
        { variableId: variable.id, data: payload },
        {
          onSuccess: () => {
            onClose()
          },
        },
      )
    } else {
      createMutation.mutate(payload, {
        onSuccess: () => {
          onClose()
        },
      })
    }
  }

  const isEnumValid = valueType !== "enum" || enumValues.length > 0

  return (
    <DialogRoot
      size={{ base: "sm", md: "lg" }}
      placement="center"
      open={isOpen}
      onOpenChange={({ open }) => {
        if (!open) onClose()
      }}
    >
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>
              {isEditMode ? "Edit State Variable" : "Add State Variable"}
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4} fontSize="sm" color="fg.muted">
              Define a variable that can be used in choice conditions throughout
              your story.
            </Text>
            <VStack gap={4} align="stretch">
              <Field
                required
                invalid={!!errors.key}
                errorText={errors.key?.message}
                label="Variable Key"
                helperText="Unique identifier (no spaces)"
              >
                <Input
                  {...register("key", {
                    required: "Variable key is required",
                    maxLength: {
                      value: 100,
                      message: "Key must be 100 characters or less",
                    },
                    pattern: {
                      value: /^[a-zA-Z_][a-zA-Z0-9_]*$/,
                      message:
                        "Key must start with letter/underscore, contain only letters, numbers, underscores",
                    },
                  })}
                  placeholder="has_key"
                  type="text"
                />
              </Field>

              <Field required label="Value Type">
                <NativeSelectRoot>
                  <NativeSelectField
                    {...register("value_type")}
                    placeholder="Select type"
                  >
                    <option value="boolean">Boolean (true/false)</option>
                    <option value="number">Number</option>
                    <option value="string">String (text)</option>
                    <option value="enum">Enum (predefined options)</option>
                  </NativeSelectField>
                </NativeSelectRoot>
              </Field>

              {/* Enum Values - only shown for enum type */}
              {valueType === "enum" && (
                <Field
                  required
                  label="Enum Values"
                  helperText="Add at least one option"
                  invalid={!isEnumValid}
                  errorText={
                    !isEnumValid ? "At least one enum value is required" : ""
                  }
                >
                  <VStack align="stretch" gap={2}>
                    <HStack>
                      <Input
                        value={enumInput}
                        onChange={(e) => setEnumInput(e.target.value)}
                        onKeyDown={handleEnumKeyDown}
                        placeholder="Add option..."
                        size="sm"
                      />
                      <IconButton
                        aria-label="Add enum value"
                        size="sm"
                        onClick={handleAddEnumValue}
                        disabled={!enumInput.trim()}
                      >
                        <FaPlus />
                      </IconButton>
                    </HStack>
                    {enumValues.length > 0 && (
                      <HStack flexWrap="wrap" gap={1}>
                        {enumValues.map((val) => (
                          <Tag.Root key={val} size="sm" colorPalette="blue">
                            <Tag.Label>{val}</Tag.Label>
                            <Tag.CloseTrigger
                              onClick={() => handleRemoveEnumValue(val)}
                            >
                              <FaTimes />
                            </Tag.CloseTrigger>
                          </Tag.Root>
                        ))}
                      </HStack>
                    )}
                  </VStack>
                </Field>
              )}

              {/* Default Value - changes based on type */}
              <Field label="Default Value">
                {valueType === "boolean" && (
                  <Controller
                    control={control}
                    name="default_value_boolean"
                    render={({ field }) => (
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={({ checked }) =>
                          field.onChange(checked)
                        }
                      >
                        <Text fontSize="sm">Default to true</Text>
                      </Checkbox>
                    )}
                  />
                )}
                {valueType === "number" && (
                  <Input
                    {...register("default_value_number", {
                      valueAsNumber: true,
                    })}
                    type="number"
                    placeholder="0"
                  />
                )}
                {valueType === "string" && (
                  <Input
                    {...register("default_value_string")}
                    type="text"
                    placeholder="Default text..."
                  />
                )}
                {valueType === "enum" && enumValues.length > 0 && (
                  <NativeSelectRoot>
                    <NativeSelectField
                      {...register("default_value_enum")}
                      placeholder="Select default"
                    >
                      <option value="">No default</option>
                      {enumValues.map((val) => (
                        <option key={val} value={val}>
                          {val}
                        </option>
                      ))}
                    </NativeSelectField>
                  </NativeSelectRoot>
                )}
              </Field>

              <Field
                label="Category"
                helperText="Optional grouping for organization"
              >
                <Input
                  {...register("category", {
                    maxLength: {
                      value: 100,
                      message: "Category must be 100 characters or less",
                    },
                  })}
                  placeholder="inventory"
                  type="text"
                />
              </Field>

              <Field
                label="Description"
                helperText="Explain what this variable tracks"
              >
                <Textarea
                  {...register("description", {
                    maxLength: {
                      value: 500,
                      message: "Description must be 500 characters or less",
                    },
                  })}
                  placeholder="Whether the player has picked up the golden key..."
                  rows={2}
                />
              </Field>
            </VStack>
          </DialogBody>

          <DialogFooter gap={2}>
            <DialogActionTrigger asChild>
              <Button
                variant="subtle"
                colorPalette="gray"
                disabled={isSubmitting}
              >
                Cancel
              </Button>
            </DialogActionTrigger>
            <Button
              variant="solid"
              colorPalette="blue"
              type="submit"
              disabled={!isValid || !isEnumValid}
              loading={
                isSubmitting ||
                createMutation.isPending ||
                updateMutation.isPending
              }
            >
              {isEditMode ? "Update Variable" : "Create Variable"}
            </Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  )
}

export default StateVariableModal
