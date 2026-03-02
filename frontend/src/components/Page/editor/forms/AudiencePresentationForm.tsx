import { zodResolver } from "@hookform/resolvers/zod"
import { Plus, Trash2 } from "lucide-react"
import { useFieldArray, useForm } from "react-hook-form"
import { z } from "zod"

import type { AudiencePresentationBlockContent } from "@/components/UserPage/types"
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
import { Textarea } from "@/components/ui/textarea"

const presentationSchema = z.object({
  id: z.string(),
  personaId: z.string().min(1, "Persona id is required"),
  audienceScope: z.enum(["public", "trusted", "collaborators", "custom"]),
  audienceLabel: z.string().min(1, "Audience label is required"),
  headline: z.string().min(1, "Headline is required"),
  framingText: z.string().optional(),
  visibleWorkIdsCsv: z.string().optional(),
  relationCallToAction: z.enum([
    "none",
    "request_contact",
    "invite_collaboration",
    "follow_work",
  ]),
})

const schema = z.object({
  presentations: z.array(presentationSchema),
})

type AudiencePresentationFormData = z.infer<typeof schema>

function csvToList(value?: string) {
  return (value ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
}

interface AudiencePresentationFormProps {
  content: AudiencePresentationBlockContent
  onSave: (content: AudiencePresentationBlockContent) => void
  onCancel: () => void
}

export function AudiencePresentationForm({
  content,
  onSave,
  onCancel,
}: AudiencePresentationFormProps) {
  const { register, handleSubmit, control, setValue, watch } =
    useForm<AudiencePresentationFormData>({
      resolver: zodResolver(schema),
      defaultValues: {
        presentations: (content.presentations ?? []).map((presentation) => ({
          id: presentation.id,
          personaId: presentation.personaId,
          audienceScope: presentation.audienceScope,
          audienceLabel: presentation.audienceLabel,
          headline: presentation.headline,
          framingText: presentation.framingText ?? "",
          visibleWorkIdsCsv: presentation.visibleWorkIds.join(", "),
          relationCallToAction: presentation.relationCallToAction,
        })),
      },
    })

  const { fields, append, remove } = useFieldArray({
    control,
    name: "presentations",
  })

  return (
    <form
      onSubmit={handleSubmit((data) =>
        onSave({
          presentations: data.presentations.map((presentation) => ({
            id: presentation.id,
            personaId: presentation.personaId.trim(),
            audienceScope: presentation.audienceScope,
            audienceLabel: presentation.audienceLabel.trim(),
            headline: presentation.headline.trim(),
            framingText: presentation.framingText?.trim() || null,
            visibleWorkIds: csvToList(presentation.visibleWorkIdsCsv),
            relationCallToAction: presentation.relationCallToAction,
          })),
        }),
      )}
      className="space-y-4"
    >
      <div className="space-y-4 max-h-[420px] overflow-y-auto">
        {fields.map((field, index) => (
          <div key={field.id} className="space-y-3 rounded-lg border p-4">
            <div className="flex justify-end">
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => remove(index)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>

            <input type="hidden" {...register(`presentations.${index}.id`)} />

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor={`presentations.${index}.personaId`}>Persona Id</Label>
                <Input
                  id={`presentations.${index}.personaId`}
                  {...register(`presentations.${index}.personaId`)}
                />
              </div>

              <div className="space-y-2">
                <Label>Audience Scope</Label>
                <Select
                  value={watch(`presentations.${index}.audienceScope`)}
                  onValueChange={(value) =>
                    setValue(
                      `presentations.${index}.audienceScope`,
                      value as AudiencePresentationFormData["presentations"][number]["audienceScope"],
                    )
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="public">Public</SelectItem>
                    <SelectItem value="trusted">Trusted</SelectItem>
                    <SelectItem value="collaborators">Collaborators</SelectItem>
                    <SelectItem value="custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor={`presentations.${index}.audienceLabel`}>
                  Audience Label
                </Label>
                <Input
                  id={`presentations.${index}.audienceLabel`}
                  {...register(`presentations.${index}.audienceLabel`)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor={`presentations.${index}.headline`}>Headline</Label>
                <Input
                  id={`presentations.${index}.headline`}
                  {...register(`presentations.${index}.headline`)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor={`presentations.${index}.framingText`}>
                Framing Text
              </Label>
              <Textarea
                id={`presentations.${index}.framingText`}
                {...register(`presentations.${index}.framingText`)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor={`presentations.${index}.visibleWorkIdsCsv`}>
                Visible Work Ids
              </Label>
              <Input
                id={`presentations.${index}.visibleWorkIdsCsv`}
                {...register(`presentations.${index}.visibleWorkIdsCsv`)}
              />
            </div>

            <div className="space-y-2">
              <Label>Relation Call To Action</Label>
              <Select
                value={watch(`presentations.${index}.relationCallToAction`)}
                onValueChange={(value) =>
                  setValue(
                    `presentations.${index}.relationCallToAction`,
                    value as AudiencePresentationFormData["presentations"][number]["relationCallToAction"],
                  )
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  <SelectItem value="request_contact">Request Contact</SelectItem>
                  <SelectItem value="invite_collaboration">
                    Invite Collaboration
                  </SelectItem>
                  <SelectItem value="follow_work">Follow Work</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        ))}
      </div>

      <Button
        type="button"
        variant="outline"
        className="w-full"
        onClick={() =>
          append({
            id: crypto.randomUUID(),
            personaId: "",
            audienceScope: "public",
            audienceLabel: "Public",
            headline: "",
            framingText: "",
            visibleWorkIdsCsv: "",
            relationCallToAction: "none",
          })
        }
      >
        <Plus className="mr-2 h-4 w-4" />
        Add Audience View
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
