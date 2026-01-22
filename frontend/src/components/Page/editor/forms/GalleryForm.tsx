// src/components/Page/editor/forms/GalleryForm.tsx
import { useEffect, useRef } from "react"
import { useForm, useFieldArray } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Plus, Trash2 } from "lucide-react"
import type {
  GalleryContent,
  GalleryBlockConfig,
} from "@/components/Page/blocks"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

const imageSchema = z.object({
  id: z.string(),
  url: z.string().min(1, "URL is required"),
  alt: z.string().optional(),
  caption: z.string().optional(),
})

const schema = z.object({
  images: z.array(imageSchema),
})

type GalleryFormData = z.infer<typeof schema>

interface GalleryFormProps {
  content: GalleryContent
  config: GalleryBlockConfig
  onSave: (content: GalleryContent) => void
  onCancel: () => void
}

function generateId(): string {
  return Math.random().toString(36).substring(2, 11)
}

export function GalleryForm({
  content,
  config: _config,
  onSave,
  onCancel,
}: GalleryFormProps) {
  const firstInputRef = useRef<HTMLInputElement>(null)
  const {
    register,
    handleSubmit,
    control,
    watch,
    formState: { errors },
  } = useForm<GalleryFormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      images: content.images || [],
    },
  })

  const { fields, append, remove } = useFieldArray({
    control,
    name: "images",
  })

  // Auto-focus first field on mount
  useEffect(() => {
    firstInputRef.current?.focus()
  }, [])

  const handleAddImage = () => {
    append({
      id: generateId(),
      url: "",
      alt: "",
      caption: "",
    })
  }

  const onSubmit = (data: GalleryFormData) => {
    onSave({ images: data.images })
  }

  // Watch URLs to show thumbnails
  const images = watch("images")

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-4">
        {fields.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">
            No images added yet. Click the button below to add one.
          </p>
        ) : (
          fields.map((field, index) => {
            const imageUrl = images[index]?.url

            return (
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
                  aria-label="Remove image"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>

                <input type="hidden" {...register(`images.${index}.id`)} />

                {/* Thumbnail preview */}
                {imageUrl && (
                  <div className="flex justify-center">
                    <img
                      src={imageUrl}
                      alt=""
                      className="w-20 h-20 rounded-md object-cover"
                    />
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor={`images.${index}.url`}>
                    URL <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id={`images.${index}.url`}
                    {...register(`images.${index}.url`)}
                    ref={index === 0 ? firstInputRef : undefined}
                    placeholder="https://..."
                    aria-invalid={
                      errors.images?.[index]?.url ? "true" : undefined
                    }
                  />
                  {errors.images?.[index]?.url && (
                    <p className="text-sm text-destructive">
                      {errors.images[index].url?.message}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor={`images.${index}.alt`}>Alt Text</Label>
                  <Input
                    id={`images.${index}.alt`}
                    {...register(`images.${index}.alt`)}
                    placeholder="Describe the image"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor={`images.${index}.caption`}>Caption</Label>
                  <Input
                    id={`images.${index}.caption`}
                    {...register(`images.${index}.caption`)}
                    placeholder="Optional caption"
                  />
                </div>
              </div>
            )
          })
        )}
      </div>

      <Button
        type="button"
        variant="outline"
        onClick={handleAddImage}
        className="w-full"
      >
        <Plus className="h-4 w-4 mr-2" />
        Add Image
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
