// src/components/Page/editor/forms/DomainsForm.tsx

import { zodResolver } from "@hookform/resolvers/zod"
import { useEffect, useRef } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import type {
  DomainsBlockConfig,
  DomainsContent,
} from "@/components/Page/blocks"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

const schema = z.object({
  generalDomain: z.string().optional(),
  specificDomain: z.string().optional(),
  generalDomainHigh: z.string().optional(),
  specificDomainHigh: z.string().optional(),
})

interface DomainsFormProps {
  content: DomainsContent
  config: DomainsBlockConfig
  onSave: (content: DomainsContent) => void
  onCancel: () => void
}

export function DomainsForm({
  content,
  config: _config,
  onSave,
  onCancel,
}: DomainsFormProps) {
  const firstInputRef = useRef<HTMLInputElement>(null)
  const { register, handleSubmit } = useForm<DomainsContent>({
    resolver: zodResolver(schema),
    defaultValues: content,
  })

  useEffect(() => {
    firstInputRef.current?.focus()
  }, [])

  const { ref: firstRef, ...firstRegister } = register("generalDomainHigh")

  return (
    <form onSubmit={handleSubmit(onSave)} className="space-y-4">
      <div className="space-y-4">
        <p className="text-xs text-muted-foreground">
          High-level domains represent broad expertise areas. Specific domains
          are narrower specializations.
        </p>

        <div className="space-y-2">
          <Label htmlFor="generalDomainHigh">General Domain (High)</Label>
          <Input
            id="generalDomainHigh"
            ref={(e) => {
              firstRef(e)
              ;(
                firstInputRef as React.MutableRefObject<HTMLInputElement | null>
              ).current = e
            }}
            {...firstRegister}
            placeholder="e.g. Technology"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="specificDomainHigh">Specific Domain (High)</Label>
          <Input
            id="specificDomainHigh"
            {...register("specificDomainHigh")}
            placeholder="e.g. Machine Learning"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="generalDomain">General Domain</Label>
          <Input
            id="generalDomain"
            {...register("generalDomain")}
            placeholder="e.g. Software Engineering"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="specificDomain">Specific Domain</Label>
          <Input
            id="specificDomain"
            {...register("specificDomain")}
            placeholder="e.g. Frontend Development"
          />
        </div>
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
