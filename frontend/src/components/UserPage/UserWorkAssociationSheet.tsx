import { useEffect, useState } from "react"

import { PersonaPicker } from "@/components/Persona"
import type {
  AudienceScope,
  UserWorkFeedItem,
  UserWorkType,
} from "@/components/UserPage/types"
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
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"

export interface UserWorkAssociationDraft {
  id?: string
  title: string
  summary: string | null
  workType: UserWorkType
  tags: string[]
  associatedPersonaIds: string[]
  intendedAudienceScopes: AudienceScope[]
  href: string | null
  isRepresentative: boolean
}

interface UserWorkAssociationSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  item?: UserWorkFeedItem | null
  ownerUserId: string
  onSave: (draft: UserWorkAssociationDraft) => Promise<void> | void
}

export function UserWorkAssociationSheet({
  open,
  onOpenChange,
  item,
  ownerUserId,
  onSave,
}: UserWorkAssociationSheetProps) {
  const [title, setTitle] = useState("")
  const [summary, setSummary] = useState("")
  const [workType, setWorkType] = useState<UserWorkType>("artifact")
  const [tagsInput, setTagsInput] = useState("")
  const [selectedPersonaIds, setSelectedPersonaIds] = useState<string[]>([])
  const [audienceScope, setAudienceScope] = useState<AudienceScope>("public")
  const [href, setHref] = useState("")
  const [isRepresentative, setIsRepresentative] = useState(true)

  useEffect(() => {
    if (!open) return
    setTitle(item?.title ?? "")
    setSummary(item?.summary ?? "")
    setWorkType(item?.workType ?? "artifact")
    setTagsInput(item?.tags.join(", ") ?? "")
    setSelectedPersonaIds(item?.associatedPersonaIds ?? [])
    setAudienceScope(item?.intendedAudienceScopes[0] ?? "public")
    setHref(item?.href ?? "")
    setIsRepresentative(item?.isRepresentative ?? true)
  }, [open, item])

  const handleSave = async () => {
    await onSave({
      id: item?.id,
      title: title.trim(),
      summary: summary.trim() || null,
      workType,
      tags: tagsInput
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean),
      associatedPersonaIds: selectedPersonaIds,
      intendedAudienceScopes: [audienceScope],
      href: href.trim() || null,
      isRepresentative,
    })
    onOpenChange(false)
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[460px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{item ? "Edit Work Item" : "Add Work Item"}</SheetTitle>
        </SheetHeader>

        <div className="mt-6 space-y-4">
          <div className="space-y-2">
            <Label htmlFor="work-title">Title</Label>
            <Input
              id="work-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Title"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="work-summary">Summary</Label>
            <Textarea
              id="work-summary"
              value={summary}
              onChange={(event) => setSummary(event.target.value)}
              placeholder="A short explanation of the work"
            />
          </div>

          <div className="space-y-2">
            <Label>Work Type</Label>
            <Select
              value={workType}
              onValueChange={(value) => setWorkType(value as UserWorkType)}
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
            <Label>Associate Personas</Label>
            <div className="rounded-lg border p-3">
              <PersonaPicker
                owner={{ type: "user", id: ownerUserId, name: "User" }}
                mode="select-multiple"
                variant="inline"
                layout="list"
                selected={selectedPersonaIds}
                onSelect={(selected) =>
                  setSelectedPersonaIds(
                    Array.isArray(selected)
                      ? selected.filter(
                          (item): item is string => typeof item === "string",
                        )
                      : [],
                  )
                }
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Audience Scope</Label>
            <Select
              value={audienceScope}
              onValueChange={(value) =>
                setAudienceScope(value as AudienceScope)
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
            <Label htmlFor="work-tags">Tags</Label>
            <Input
              id="work-tags"
              value={tagsInput}
              onChange={(event) => setTagsInput(event.target.value)}
              placeholder="frontend, demo, narrative"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="work-href">Link</Label>
            <Input
              id="work-href"
              value={href}
              onChange={(event) => setHref(event.target.value)}
              placeholder="/demo/some-demo"
            />
          </div>

          <div className="flex items-center justify-between rounded-lg border p-3">
            <div className="space-y-1">
              <div className="text-sm font-medium">Representative Work</div>
              <p className="text-xs text-muted-foreground">
                Controls whether the item appears in the owner-facing work flow.
              </p>
            </div>
            <Switch
              checked={isRepresentative}
              onCheckedChange={setIsRepresentative}
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={title.trim().length === 0}>
              Save Work
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}
