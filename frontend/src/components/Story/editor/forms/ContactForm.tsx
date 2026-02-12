// src/components/Page/editor/forms/ContactForm.tsx

import { zodResolver } from "@hookform/resolvers/zod"
import { useEffect, useRef } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import type {
  ContactBlockConfig,
  ContactContent,
} from "@/components/Page/blocks"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

const schema = z.object({
  email: z
    .string()
    .optional()
    .refine(
      (val) => !val || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val),
      "Invalid email format",
    ),
  phone: z.string().optional(),
})

interface ContactFormProps {
  content: ContactContent
  config: ContactBlockConfig
  onSave: (content: ContactContent) => void
  onCancel: () => void
}

export function ContactForm({
  content,
  config: _config,
  onSave,
  onCancel,
}: ContactFormProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ContactContent>({
    resolver: zodResolver(schema),
    defaultValues: content,
  })

  // Auto-focus first field on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const { ref: emailRef, ...emailRegister } = register("email")

  return (
    <form onSubmit={handleSubmit(onSave)} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          ref={(e) => {
            emailRef(e)
            ;(
              inputRef as React.MutableRefObject<HTMLInputElement | null>
            ).current = e
          }}
          {...emailRegister}
          placeholder="email@example.com"
          aria-invalid={errors.email ? "true" : undefined}
        />
        {errors.email && (
          <p className="text-sm text-destructive">{errors.email.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="phone">Phone</Label>
        <Input
          id="phone"
          type="tel"
          {...register("phone")}
          placeholder="+1 (555) 000-0000"
          aria-invalid={errors.phone ? "true" : undefined}
        />
        {errors.phone && (
          <p className="text-sm text-destructive">{errors.phone.message}</p>
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
