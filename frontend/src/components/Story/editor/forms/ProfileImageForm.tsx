// src/components/Page/editor/forms/ProfileImageForm.tsx

import { zodResolver } from "@hookform/resolvers/zod"
import { useEffect, useRef } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import type {
  ProfileImageBlockConfig,
  ProfileImageContent,
} from "@/components/Page/blocks"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

const schema = z.object({
  imageUrl: z.string().optional(),
  alt: z.string().optional(),
})

interface ProfileImageFormProps {
  content: ProfileImageContent
  config: ProfileImageBlockConfig
  onSave: (content: ProfileImageContent) => void
  onCancel: () => void
}

export function ProfileImageForm({
  content,
  config: _config,
  onSave,
  onCancel,
}: ProfileImageFormProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<ProfileImageContent>({
    resolver: zodResolver(schema),
    defaultValues: content,
  })

  const imageUrl = watch("imageUrl")

  // Auto-focus first field on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const { ref: imageUrlRef, ...imageUrlRegister } = register("imageUrl")

  return (
    <form onSubmit={handleSubmit(onSave)} className="space-y-4">
      {/* Image preview */}
      {imageUrl && (
        <div className="flex justify-center">
          <img
            src={imageUrl}
            alt=""
            className="w-24 h-24 rounded-lg object-cover"
          />
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="imageUrl">Image URL</Label>
        <Input
          id="imageUrl"
          ref={(e) => {
            imageUrlRef(e)
            ;(
              inputRef as React.MutableRefObject<HTMLInputElement | null>
            ).current = e
          }}
          {...imageUrlRegister}
          placeholder="https://..."
          aria-invalid={errors.imageUrl ? "true" : undefined}
        />
        {errors.imageUrl && (
          <p className="text-sm text-destructive">{errors.imageUrl.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="alt">Alt Text</Label>
        <Input
          id="alt"
          {...register("alt")}
          placeholder="Describe the image"
          aria-invalid={errors.alt ? "true" : undefined}
        />
        {errors.alt && (
          <p className="text-sm text-destructive">{errors.alt.message}</p>
        )}
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit">Save</Button>
      </div>
    </form>
  )
}
