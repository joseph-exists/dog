import { zodResolver } from "@hookform/resolvers/zod"
import { Plus, Trash2 } from "lucide-react"
import { useFieldArray, useForm } from "react-hook-form"
import { z } from "zod"

import type { RelationshipManagerBlockContent } from "@/components/UserPage/types"
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

const relationSchema = z.object({
  id: z.string(),
  sourcePersonaId: z.string().min(1, "Source persona id is required"),
  targetLabel: z.string().min(1, "Target label is required"),
  targetType: z.enum(["persona", "external"]),
  relationKind: z.enum([
    "collaborator",
    "trusted",
    "learning_from",
    "working_with",
  ]),
  audienceScope: z.enum(["public", "trusted", "collaborators", "custom"]),
  note: z.string().optional(),
  status: z.enum(["active", "pending"]),
})

const schema = z.object({
  relations: z.array(relationSchema),
})

type RelationshipManagerFormData = z.infer<typeof schema>

interface RelationshipManagerFormProps {
  content: RelationshipManagerBlockContent
  onSave: (content: RelationshipManagerBlockContent) => void
  onCancel: () => void
}

export function RelationshipManagerForm({
  content,
  onSave,
  onCancel,
}: RelationshipManagerFormProps) {
  const { register, handleSubmit, control, setValue, watch } =
    useForm<RelationshipManagerFormData>({
      resolver: zodResolver(schema),
      defaultValues: {
        relations: (content.relations ?? []).map((relation) => ({
          id: relation.id,
          sourcePersonaId: relation.sourcePersonaId,
          targetLabel: relation.targetLabel,
          targetType: relation.targetType,
          relationKind: relation.relationKind,
          audienceScope: relation.audienceScope,
          note: relation.note ?? "",
          status: relation.status,
        })),
      },
    })

  const { fields, append, remove } = useFieldArray({
    control,
    name: "relations",
  })

  return (
    <form
      onSubmit={handleSubmit((data) =>
        onSave({
          relations: data.relations.map((relation) => ({
            id: relation.id,
            sourcePersonaId: relation.sourcePersonaId.trim(),
            targetLabel: relation.targetLabel.trim(),
            targetType: relation.targetType,
            relationKind: relation.relationKind,
            audienceScope: relation.audienceScope,
            note: relation.note?.trim() || null,
            status: relation.status,
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

            <input type="hidden" {...register(`relations.${index}.id`)} />

            <div className="space-y-2">
              <Label htmlFor={`relations.${index}.sourcePersonaId`}>
                Source Persona Id
              </Label>
              <Input
                id={`relations.${index}.sourcePersonaId`}
                {...register(`relations.${index}.sourcePersonaId`)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor={`relations.${index}.targetLabel`}>Target Label</Label>
              <Input
                id={`relations.${index}.targetLabel`}
                {...register(`relations.${index}.targetLabel`)}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Target Type</Label>
                <Select
                  value={watch(`relations.${index}.targetType`)}
                  onValueChange={(value) =>
                    setValue(
                      `relations.${index}.targetType`,
                      value as RelationshipManagerFormData["relations"][number]["targetType"],
                    )
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="persona">Persona</SelectItem>
                    <SelectItem value="external">External</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Relation Kind</Label>
                <Select
                  value={watch(`relations.${index}.relationKind`)}
                  onValueChange={(value) =>
                    setValue(
                      `relations.${index}.relationKind`,
                      value as RelationshipManagerFormData["relations"][number]["relationKind"],
                    )
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="collaborator">Collaborator</SelectItem>
                    <SelectItem value="trusted">Trusted</SelectItem>
                    <SelectItem value="learning_from">Learning From</SelectItem>
                    <SelectItem value="working_with">Working With</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Audience Scope</Label>
                <Select
                  value={watch(`relations.${index}.audienceScope`)}
                  onValueChange={(value) =>
                    setValue(
                      `relations.${index}.audienceScope`,
                      value as RelationshipManagerFormData["relations"][number]["audienceScope"],
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

              <div className="space-y-2">
                <Label>Status</Label>
                <Select
                  value={watch(`relations.${index}.status`)}
                  onValueChange={(value) =>
                    setValue(
                      `relations.${index}.status`,
                      value as RelationshipManagerFormData["relations"][number]["status"],
                    )
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor={`relations.${index}.note`}>Note</Label>
              <Textarea id={`relations.${index}.note`} {...register(`relations.${index}.note`)} />
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
            sourcePersonaId: "",
            targetLabel: "",
            targetType: "external",
            relationKind: "collaborator",
            audienceScope: "public",
            note: "",
            status: "active",
          })
        }
      >
        <Plus className="mr-2 h-4 w-4" />
        Add Relation
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
