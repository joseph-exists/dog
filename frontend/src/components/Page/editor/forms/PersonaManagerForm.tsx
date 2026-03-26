import { zodResolver } from "@hookform/resolvers/zod"
import { Plus, Trash2 } from "lucide-react"
import { useFieldArray, useForm } from "react-hook-form"
import { z } from "zod"

import type { PersonaManagerBlockContent } from "@/components/UserPage/types"
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
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"

const personaSchema = z.object({
  id: z.string(),
  name: z.string().min(1, "Name is required"),
  nickname: z.string().optional(),
  shortBio: z.string().optional(),
  longBio: z.string().optional(),
  tagsCsv: z.string().optional(),
  publicationState: z.enum(["draft", "published"]),
  associatedWorkCount: z.number().int().min(0),
  isPrimary: z.boolean(),
  isVisibleInCurrentAudience: z.boolean(),
})

const schema = z.object({
  personas: z.array(personaSchema),
})

type PersonaManagerFormData = z.infer<typeof schema>

function csvToTags(csv?: string) {
  return (csv ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
    .map((label, index) => ({
      id: `${label.toLowerCase().replace(/\s+/g, "-")}-${index}`,
      label,
      weight: 0.6,
      source: "user" as const,
    }))
}

interface PersonaManagerFormProps {
  content: PersonaManagerBlockContent
  onSave: (content: PersonaManagerBlockContent) => void
  onCancel: () => void
}

export function PersonaManagerForm({
  content,
  onSave,
  onCancel,
}: PersonaManagerFormProps) {
  const { register, handleSubmit, control, setValue, watch } =
    useForm<PersonaManagerFormData>({
      resolver: zodResolver(schema),
      defaultValues: {
        personas: (content.personas ?? []).map((persona) => ({
          id: persona.id,
          name: persona.name,
          nickname: persona.nickname ?? "",
          shortBio: persona.shortBio ?? "",
          longBio: persona.longBio ?? "",
          tagsCsv: persona.tags.map((tag) => tag.label).join(", "),
          publicationState: persona.publicationState,
          associatedWorkCount: persona.associatedWorkCount,
          isPrimary: persona.isPrimary,
          isVisibleInCurrentAudience: persona.isVisibleInCurrentAudience,
        })),
      },
    })

  const { fields, append, remove } = useFieldArray({
    control,
    name: "personas",
  })

  return (
    <form
      onSubmit={handleSubmit((data) =>
        onSave({
          personas: data.personas.map((persona) => ({
            id: persona.id,
            name: persona.name.trim(),
            nickname: persona.nickname?.trim() || null,
            shortBio: persona.shortBio?.trim() || null,
            longBio: persona.longBio?.trim() || null,
            tags: csvToTags(persona.tagsCsv),
            publicationState: persona.publicationState,
            associatedWorkCount: persona.associatedWorkCount,
            isPrimary: persona.isPrimary,
            isVisibleInCurrentAudience: persona.isVisibleInCurrentAudience,
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

            <input type="hidden" {...register(`personas.${index}.id`)} />

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor={`personas.${index}.name`}>Name</Label>
                <Input
                  id={`personas.${index}.name`}
                  {...register(`personas.${index}.name`)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor={`personas.${index}.nickname`}>Nickname</Label>
                <Input
                  id={`personas.${index}.nickname`}
                  {...register(`personas.${index}.nickname`)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor={`personas.${index}.shortBio`}>Short Bio</Label>
              <Textarea
                id={`personas.${index}.shortBio`}
                {...register(`personas.${index}.shortBio`)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor={`personas.${index}.longBio`}>Long Bio</Label>
              <Textarea
                id={`personas.${index}.longBio`}
                {...register(`personas.${index}.longBio`)}
                className="min-h-24"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor={`personas.${index}.tagsCsv`}>Tags</Label>
                <Input
                  id={`personas.${index}.tagsCsv`}
                  {...register(`personas.${index}.tagsCsv`)}
                />
              </div>
              <div className="space-y-2">
                <Label>Publication State</Label>
                <Select
                  value={watch(`personas.${index}.publicationState`)}
                  onValueChange={(value) =>
                    setValue(
                      `personas.${index}.publicationState`,
                      value as PersonaManagerFormData["personas"][number]["publicationState"],
                    )
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="draft">Draft</SelectItem>
                    <SelectItem value="published">Published</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor={`personas.${index}.associatedWorkCount`}>
                Associated Work Count
              </Label>
              <Input
                id={`personas.${index}.associatedWorkCount`}
                type="number"
                {...register(`personas.${index}.associatedWorkCount`, {
                  valueAsNumber: true,
                })}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="flex items-center justify-between rounded-md border p-3">
                <div>
                  <p className="text-sm font-medium">Primary</p>
                </div>
                <Switch
                  checked={watch(`personas.${index}.isPrimary`)}
                  onCheckedChange={(checked) =>
                    setValue(`personas.${index}.isPrimary`, checked)
                  }
                />
              </div>

              <div className="flex items-center justify-between rounded-md border p-3">
                <div>
                  <p className="text-sm font-medium">Visible In Audience</p>
                </div>
                <Switch
                  checked={watch(
                    `personas.${index}.isVisibleInCurrentAudience`,
                  )}
                  onCheckedChange={(checked) =>
                    setValue(
                      `personas.${index}.isVisibleInCurrentAudience`,
                      checked,
                    )
                  }
                />
              </div>
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
            name: "",
            nickname: "",
            shortBio: "",
            longBio: "",
            tagsCsv: "",
            publicationState: "draft",
            associatedWorkCount: 0,
            isPrimary: false,
            isVisibleInCurrentAudience: true,
          })
        }
      >
        <Plus className="mr-2 h-4 w-4" />
        Add Persona
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
