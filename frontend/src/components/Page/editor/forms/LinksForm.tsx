// src/components/Page/editor/forms/LinksForm.tsx

import { zodResolver } from "@hookform/resolvers/zod"
import { Plus, Trash2 } from "lucide-react"
import { useEffect, useRef } from "react"
import { useFieldArray, useForm } from "react-hook-form"
import { z } from "zod"
import type {
  Link,
  LinksBlockConfig,
  LinksContent,
} from "@/components/Page/blocks"
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

const linkSchema = z.object({
  id: z.string(),
  type: z.enum(["website", "github", "twitter", "linkedin", "other"]),
  url: z.string().min(1, "URL is required"),
  label: z.string().optional(),
})

const schema = z.object({
  items: z.array(linkSchema),
})

type LinksFormData = z.infer<typeof schema>

const linkTypes: { value: Link["type"]; label: string }[] = [
  { value: "website", label: "Website" },
  { value: "github", label: "GitHub" },
  { value: "twitter", label: "Twitter" },
  { value: "linkedin", label: "LinkedIn" },
  { value: "other", label: "Other" },
]

interface LinksFormProps {
  content: LinksContent
  config: LinksBlockConfig
  onSave: (content: LinksContent) => void
  onCancel: () => void
}

function generateId(): string {
  return Math.random().toString(36).substring(2, 11)
}

export function LinksForm({
  content,
  config: _config,
  onSave,
  onCancel,
}: LinksFormProps) {
  const firstInputRef = useRef<HTMLInputElement>(null)
  const {
    register,
    handleSubmit,
    control,
    setValue,
    watch,
    formState: { errors },
  } = useForm<LinksFormData>({
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

  const handleAddLink = () => {
    append({
      id: generateId(),
      type: "website",
      url: "",
      label: "",
    })
  }

  const onSubmit = (data: LinksFormData) => {
    onSave({ items: data.items })
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-4">
        {fields.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">
            No links added yet. Click the button below to add one.
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
                aria-label="Remove link"
              >
                <Trash2 className="h-4 w-4" />
              </Button>

              <input type="hidden" {...register(`items.${index}.id`)} />

              <div className="space-y-2">
                <Label htmlFor={`items.${index}.type`}>Type</Label>
                <Select
                  value={watch(`items.${index}.type`)}
                  onValueChange={(value) =>
                    setValue(`items.${index}.type`, value as Link["type"])
                  }
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    {linkTypes.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor={`items.${index}.url`}>
                  URL <span className="text-destructive">*</span>
                </Label>
                <Input
                  id={`items.${index}.url`}
                  {...register(`items.${index}.url`)}
                  ref={index === 0 ? firstInputRef : undefined}
                  placeholder="https://..."
                  aria-invalid={errors.items?.[index]?.url ? "true" : undefined}
                />
                {errors.items?.[index]?.url && (
                  <p className="text-sm text-destructive">
                    {errors.items[index].url?.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor={`items.${index}.label`}>Label</Label>
                <Input
                  id={`items.${index}.label`}
                  {...register(`items.${index}.label`)}
                  placeholder="Display text (optional)"
                />
              </div>
            </div>
          ))
        )}
      </div>

      <Button
        type="button"
        variant="outline"
        onClick={handleAddLink}
        className="w-full"
      >
        <Plus className="h-4 w-4 mr-2" />
        Add Link
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
