import { zodResolver } from "@hookform/resolvers/zod"
import { Plus, Trash2 } from "lucide-react"
import { useFieldArray, useForm } from "react-hook-form"
import { z } from "zod"

import type { WorkFeedBlockContent } from "@/components/UserPage/types"
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

const workItemSchema = z.object({
  id: z.string(),
  title: z.string().min(1, "Title is required"),
  workType: z.enum(["demo", "prompt", "story", "page", "artifact", "other"]),
  summary: z.string().optional(),
  status: z.enum(["draft", "published"]),
  tagsCsv: z.string().optional(),
  associatedPersonaIdsCsv: z.string().optional(),
  intendedAudienceScopesCsv: z.string().optional(),
  timestampLabel: z.string().optional(),
  href: z.string().optional(),
  isRepresentative: z.boolean(),
})

const schema = z.object({
  title: z.string().optional(),
  emptyMessage: z.string().optional(),
  items: z.array(workItemSchema),
})

type WorkFeedFormData = z.infer<typeof schema>

interface WorkFeedFormProps {
  content: WorkFeedBlockContent
  onSave: (content: WorkFeedBlockContent) => void
  onCancel: () => void
}

function csvToList(value?: string) {
  return (value ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
}

export function WorkFeedForm({ content, onSave, onCancel }: WorkFeedFormProps) {
  const { register, handleSubmit, control, setValue, watch } =
    useForm<WorkFeedFormData>({
      resolver: zodResolver(schema),
      defaultValues: {
        title: content.title ?? "",
        emptyMessage: content.emptyMessage ?? "",
        items: (content.items ?? []).map((item) => ({
          id: item.id,
          title: item.title,
          workType: item.workType,
          summary: item.summary ?? "",
          status: item.status,
          tagsCsv: item.tags.join(", "),
          associatedPersonaIdsCsv: item.associatedPersonaIds.join(", "),
          intendedAudienceScopesCsv: item.intendedAudienceScopes.join(", "),
          timestampLabel: item.timestampLabel,
          href: item.href ?? "",
          isRepresentative: item.isRepresentative,
        })),
      },
    })

  const { fields, append, remove } = useFieldArray({
    control,
    name: "items",
  })

  return (
    <form
      onSubmit={handleSubmit((data) =>
        onSave({
          title: data.title?.trim() || undefined,
          emptyMessage: data.emptyMessage?.trim() || undefined,
          items: data.items.map((item) => ({
            id: item.id,
            title: item.title.trim(),
            workType: item.workType,
            summary: item.summary?.trim() || null,
            status: item.status,
            tags: csvToList(item.tagsCsv),
            associatedPersonaIds: csvToList(item.associatedPersonaIdsCsv),
            intendedAudienceScopes: csvToList(
              item.intendedAudienceScopesCsv,
            ) as Array<"public" | "trusted" | "collaborators" | "custom">,
            timestampLabel: item.timestampLabel?.trim() || "Recently updated",
            href: item.href?.trim() || null,
            isRepresentative: item.isRepresentative,
          })),
        }),
      )}
      className="space-y-4"
    >
      <div className="space-y-2">
        <Label htmlFor="work-feed-title">Block Title</Label>
        <Input id="work-feed-title" {...register("title")} />
      </div>

      <div className="space-y-2">
        <Label htmlFor="work-feed-empty">Empty Message</Label>
        <Textarea id="work-feed-empty" {...register("emptyMessage")} />
      </div>

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

            <input type="hidden" {...register(`items.${index}.id`)} />

            <div className="space-y-2">
              <Label htmlFor={`items.${index}.title`}>Title</Label>
              <Input
                id={`items.${index}.title`}
                {...register(`items.${index}.title`)}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Work Type</Label>
                <Select
                  value={watch(`items.${index}.workType`)}
                  onValueChange={(value) =>
                    setValue(
                      `items.${index}.workType`,
                      value as WorkFeedFormData["items"][number]["workType"],
                    )
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="demo">Demo</SelectItem>
                    <SelectItem value="prompt">Prompt</SelectItem>
                    <SelectItem value="story">Story</SelectItem>
                    <SelectItem value="page">Page</SelectItem>
                    <SelectItem value="artifact">Artifact</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Status</Label>
                <Select
                  value={watch(`items.${index}.status`)}
                  onValueChange={(value) =>
                    setValue(
                      `items.${index}.status`,
                      value as WorkFeedFormData["items"][number]["status"],
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
              <Label htmlFor={`items.${index}.summary`}>Summary</Label>
              <Textarea
                id={`items.${index}.summary`}
                {...register(`items.${index}.summary`)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor={`items.${index}.tagsCsv`}>Tags</Label>
              <Input
                id={`items.${index}.tagsCsv`}
                {...register(`items.${index}.tagsCsv`)}
                placeholder="builder, narrative, systems"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor={`items.${index}.associatedPersonaIdsCsv`}>
                Persona Ids
              </Label>
              <Input
                id={`items.${index}.associatedPersonaIdsCsv`}
                {...register(`items.${index}.associatedPersonaIdsCsv`)}
                placeholder="persona-a, persona-b"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor={`items.${index}.intendedAudienceScopesCsv`}>
                Audience Scopes
              </Label>
              <Input
                id={`items.${index}.intendedAudienceScopesCsv`}
                {...register(`items.${index}.intendedAudienceScopesCsv`)}
                placeholder="public, trusted"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor={`items.${index}.timestampLabel`}>
                  Timestamp Label
                </Label>
                <Input
                  id={`items.${index}.timestampLabel`}
                  {...register(`items.${index}.timestampLabel`)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor={`items.${index}.href`}>Href</Label>
                <Input
                  id={`items.${index}.href`}
                  {...register(`items.${index}.href`)}
                />
              </div>
            </div>

            <div className="flex items-center justify-between rounded-md border p-3">
              <div>
                <p className="text-sm font-medium">Representative</p>
                <p className="text-xs text-muted-foreground">
                  Shows in the owner-facing work flow.
                </p>
              </div>
              <Switch
                checked={watch(`items.${index}.isRepresentative`)}
                onCheckedChange={(checked) =>
                  setValue(`items.${index}.isRepresentative`, checked)
                }
              />
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
            title: "",
            workType: "artifact",
            summary: "",
            status: "draft",
            tagsCsv: "",
            associatedPersonaIdsCsv: "",
            intendedAudienceScopesCsv: "public",
            timestampLabel: "Recently updated",
            href: "",
            isRepresentative: true,
          })
        }
      >
        <Plus className="mr-2 h-4 w-4" />
        Add Work Item
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
