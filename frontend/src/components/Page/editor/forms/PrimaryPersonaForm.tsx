import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"

import type { PrimaryPersonaBlockContent } from "@/components/UserPage/types"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

const schema = z.object({
  primaryPersonaId: z.string().optional(),
  explanation: z.string().optional(),
})

type PrimaryPersonaFormData = z.infer<typeof schema>

interface PrimaryPersonaFormProps {
  content: PrimaryPersonaBlockContent
  onSave: (content: PrimaryPersonaBlockContent) => void
  onCancel: () => void
}

export function PrimaryPersonaForm({
  content,
  onSave,
  onCancel,
}: PrimaryPersonaFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PrimaryPersonaFormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      primaryPersonaId: content.primaryPersonaId ?? "",
      explanation: content.explanation ?? "",
    },
  })

  return (
    <form
      onSubmit={handleSubmit((data) =>
        onSave({
          primaryPersonaId: data.primaryPersonaId?.trim() || null,
          explanation: data.explanation?.trim() || "",
        }),
      )}
      className="space-y-4"
    >
      <div className="space-y-2">
        <Label htmlFor="primaryPersonaId">Primary Persona Id</Label>
        <Input
          id="primaryPersonaId"
          {...register("primaryPersonaId")}
          placeholder="persona-uuid"
          aria-invalid={errors.primaryPersonaId ? "true" : undefined}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="explanation">Explanation</Label>
        <Textarea
          id="explanation"
          {...register("explanation")}
          placeholder="Explain how this primary persona should orient the page."
        />
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
