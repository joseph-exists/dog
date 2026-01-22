// src/components/Page/editor/forms/IdentityForm.tsx

import { zodResolver } from "@hookform/resolvers/zod"
import { useEffect, useRef } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import type {
  IdentityBlockConfig,
  IdentityContent,
} from "@/components/Page/blocks"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  tagline: z.string().optional(),
})

interface IdentityFormProps {
  content: IdentityContent
  config: IdentityBlockConfig
  onSave: (content: IdentityContent) => void
  onCancel: () => void
}

export function IdentityForm({
  content,
  config: _config,
  onSave,
  onCancel,
}: IdentityFormProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<IdentityContent>({
    resolver: zodResolver(schema),
    defaultValues: content,
  })

  // Auto-focus first field on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const { ref: nameRef, ...nameRegister } = register("name")

  return (
    <form onSubmit={handleSubmit(onSave)} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">
          Name <span className="text-destructive">*</span>
        </Label>
        <Input
          id="name"
          ref={(e) => {
            nameRef(e)
            ;(
              inputRef as React.MutableRefObject<HTMLInputElement | null>
            ).current = e
          }}
          {...nameRegister}
          placeholder="Enter name"
          aria-invalid={errors.name ? "true" : undefined}
        />
        {errors.name && (
          <p className="text-sm text-destructive">{errors.name.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="tagline">Tagline</Label>
        <Input
          id="tagline"
          {...register("tagline")}
          placeholder="A brief tagline or title"
          aria-invalid={errors.tagline ? "true" : undefined}
        />
        {errors.tagline && (
          <p className="text-sm text-destructive">{errors.tagline.message}</p>
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
