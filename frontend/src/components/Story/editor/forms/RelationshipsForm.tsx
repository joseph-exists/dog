// src/components/Page/editor/forms/RelationshipsForm.tsx

import { zodResolver } from "@hookform/resolvers/zod"
import { Plus, Trash2 } from "lucide-react"
import { useEffect, useRef } from "react"
import { useFieldArray, useForm } from "react-hook-form"
import { z } from "zod"
import type {
  RelationshipItem,
  RelationshipsBlockConfig,
  RelationshipsContent,
} from "@/components/Page/blocks"
import { entityTypes, relationshipTypes } from "@/components/Page/registry"
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

const relationshipItemSchema = z.object({
  id: z.string(),
  typeId: z.string().min(1, "Entity type is required"),
  name: z.string().min(1, "Name is required"),
  avatarUrl: z.string().optional(),
  badges: z.array(z.string()).optional(),
  relationshipTypeId: z.string().min(1, "Relationship type is required"),
})

const schema = z.object({
  items: z.array(relationshipItemSchema),
})

type RelationshipsFormData = z.infer<typeof schema>

interface RelationshipsFormProps {
  content: RelationshipsContent
  config: RelationshipsBlockConfig
  onSave: (content: RelationshipsContent) => void
  onCancel: () => void
}

function generateId(): string {
  return crypto.randomUUID()
}

export function RelationshipsForm({
  content,
  config: _config,
  onSave,
  onCancel,
}: RelationshipsFormProps) {
  const firstInputRef = useRef<HTMLInputElement>(null)
  const {
    register,
    handleSubmit,
    control,
    setValue,
    watch,
    formState: { errors },
  } = useForm<RelationshipsFormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      items: content.items || [],
    },
  })

  const { fields, append, remove } = useFieldArray({
    control,
    name: "items",
  })

  // Auto-focus first field on mount
  useEffect(() => {
    firstInputRef.current?.focus()
  }, [])

  const handleAddRelationship = () => {
    append({
      id: generateId(),
      typeId: "user",
      name: "",
      avatarUrl: "",
      relationshipTypeId: relationshipTypes[0]?.id || "member",
    })
  }

  const onSubmit = (data: RelationshipsFormData) => {
    // Clean up empty optional fields
    const cleanedItems: RelationshipItem[] = data.items.map((item) => ({
      id: item.id,
      typeId: item.typeId,
      name: item.name,
      avatarUrl: item.avatarUrl || undefined,
      badges: item.badges?.length ? item.badges : undefined,
      relationshipTypeId: item.relationshipTypeId,
    }))
    onSave({ items: cleanedItems })
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-4 max-h-[400px] overflow-y-auto">
        {fields.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">
            No relationships added yet. Click the button below to add one.
          </p>
        ) : (
          fields.map((field, index) => (
            <div
              key={field.id}
              className="space-y-3 p-4 border rounded-lg relative"
            >
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                className="absolute top-2 right-2"
                onClick={() => remove(index)}
                aria-label="Remove relationship"
              >
                <Trash2 className="h-4 w-4" />
              </Button>

              <input type="hidden" {...register(`items.${index}.id`)} />

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label htmlFor={`items.${index}.typeId`}>Entity Type</Label>
                  <Select
                    value={watch(`items.${index}.typeId`)}
                    onValueChange={(value) =>
                      setValue(`items.${index}.typeId`, value)
                    }
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                      {entityTypes.map((et) => (
                        <SelectItem key={et.id} value={et.id}>
                          {et.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.items?.[index]?.typeId && (
                    <p className="text-sm text-destructive">
                      {errors.items[index].typeId?.message}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor={`items.${index}.relationshipTypeId`}>
                    Relationship
                  </Label>
                  <Select
                    value={watch(`items.${index}.relationshipTypeId`)}
                    onValueChange={(value) =>
                      setValue(`items.${index}.relationshipTypeId`, value)
                    }
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select relationship" />
                    </SelectTrigger>
                    <SelectContent>
                      {relationshipTypes.map((rt) => (
                        <SelectItem key={rt.id} value={rt.id}>
                          {rt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.items?.[index]?.relationshipTypeId && (
                    <p className="text-sm text-destructive">
                      {errors.items[index].relationshipTypeId?.message}
                    </p>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor={`items.${index}.name`}>
                  Name <span className="text-destructive">*</span>
                </Label>
                <Input
                  id={`items.${index}.name`}
                  {...register(`items.${index}.name`)}
                  ref={index === 0 ? firstInputRef : undefined}
                  placeholder="Entity name"
                  aria-invalid={
                    errors.items?.[index]?.name ? "true" : undefined
                  }
                />
                {errors.items?.[index]?.name && (
                  <p className="text-sm text-destructive">
                    {errors.items[index].name?.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor={`items.${index}.avatarUrl`}>
                  Avatar URL (optional)
                </Label>
                <Input
                  id={`items.${index}.avatarUrl`}
                  {...register(`items.${index}.avatarUrl`)}
                  placeholder="https://..."
                />
              </div>
            </div>
          ))
        )}
      </div>

      <Button
        type="button"
        variant="outline"
        onClick={handleAddRelationship}
        className="w-full"
      >
        <Plus className="h-4 w-4 mr-2" />
        Add Relationship
      </Button>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit">Save</Button>
      </div>
    </form>
  )
}
