// src/components/Page/editor/forms/BioForm.tsx
import { useEffect, useRef } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import type { BioContent, BioBlockConfig } from "@/components/Page/blocks"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"

const schema = z.object({
  text: z.string(),
})

interface BioFormProps {
  content: BioContent
  config: BioBlockConfig
  onSave: (content: BioContent) => void
  onCancel: () => void
}

export function BioForm({ content, config, onSave, onCancel }: BioFormProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<BioContent>({
    resolver: zodResolver(schema),
    defaultValues: content,
  })

  const textValue = watch("text")
  const { maxLength } = config

  // Auto-focus first field on mount
  useEffect(() => {
    textareaRef.current?.focus()
  }, [])

  const { ref: textRef, ...textRegister } = register("text")

  return (
    <form onSubmit={handleSubmit(onSave)} className="space-y-4">
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="text">Bio</Label>
          {maxLength && (
            <span
              className={`text-xs ${
                textValue && textValue.length > maxLength
                  ? "text-destructive"
                  : "text-muted-foreground"
              }`}
            >
              {textValue?.length || 0} / {maxLength}
            </span>
          )}
        </div>
        <Textarea
          id="text"
          ref={(e) => {
            textRef(e)
            ;(textareaRef as React.MutableRefObject<HTMLTextAreaElement | null>).current =
              e
          }}
          {...textRegister}
          placeholder="Write a bio..."
          rows={6}
          aria-invalid={errors.text ? "true" : undefined}
        />
        {errors.text && (
          <p className="text-sm text-destructive">{errors.text.message}</p>
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
