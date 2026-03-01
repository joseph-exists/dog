import { useEffect, useMemo, useState } from "react"

import type {
  PersonaPublicationState,
  UserPersonaSummary,
  WeightedTag,
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
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"

export interface UserPersonaEditorDraft {
  id?: string
  name: string
  nickname: string | null
  shortBio: string | null
  longBio: string | null
  publicationState: PersonaPublicationState
  tags: WeightedTag[]
  setAsPrimary: boolean
}

interface UserPersonaEditorSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  persona?: UserPersonaSummary | null
  onSave: (draft: UserPersonaEditorDraft) => Promise<void> | void
}

function tagsToCsv(tags: WeightedTag[]) {
  return tags.map((tag) => tag.label).join(", ")
}

function csvToTags(csv: string): WeightedTag[] {
  return csv
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean)
    .map((label, index) => ({
      id: `${label.toLowerCase().replace(/\s+/g, "-")}-${index}`,
      label,
      weight: 0.6,
      source: "user" as const,
    }))
}

export function UserPersonaEditorSheet({
  open,
  onOpenChange,
  persona,
  onSave,
}: UserPersonaEditorSheetProps) {
  const [name, setName] = useState("")
  const [nickname, setNickname] = useState("")
  const [shortBio, setShortBio] = useState("")
  const [longBio, setLongBio] = useState("")
  const [publicationState, setPublicationState] =
    useState<PersonaPublicationState>("draft")
  const [tagsInput, setTagsInput] = useState("")
  const [setAsPrimary, setSetAsPrimary] = useState(false)

  const title = useMemo(
    () => (persona ? `Edit ${persona.name}` : "Create Persona"),
    [persona],
  )

  useEffect(() => {
    if (!open) return
    setName(persona?.name ?? "")
    setNickname(persona?.nickname ?? "")
    setShortBio(persona?.shortBio ?? "")
    setLongBio(persona?.longBio ?? "")
    setPublicationState(persona?.publicationState ?? "draft")
    setTagsInput(tagsToCsv(persona?.tags ?? []))
    setSetAsPrimary(persona?.isPrimary ?? false)
  }, [open, persona])

  const handleSave = async () => {
    await onSave({
      id: persona?.id,
      name: name.trim(),
      nickname: nickname.trim() || null,
      shortBio: shortBio.trim() || null,
      longBio: longBio.trim() || null,
      publicationState,
      tags: csvToTags(tagsInput),
      setAsPrimary,
    })
    onOpenChange(false)
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[420px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{title}</SheetTitle>
        </SheetHeader>

        <div className="mt-6 space-y-4">
          <div className="space-y-2">
            <Label htmlFor="user-persona-name">Name</Label>
            <Input
              id="user-persona-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Persona name"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="user-persona-nickname">Nickname</Label>
            <Input
              id="user-persona-nickname"
              value={nickname}
              onChange={(event) => setNickname(event.target.value)}
              placeholder="Optional nickname"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="user-persona-short-bio">Short Bio</Label>
            <Textarea
              id="user-persona-short-bio"
              value={shortBio}
              onChange={(event) => setShortBio(event.target.value)}
              placeholder="A short framing sentence for this persona"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="user-persona-long-bio">Long Bio</Label>
            <Textarea
              id="user-persona-long-bio"
              value={longBio}
              onChange={(event) => setLongBio(event.target.value)}
              placeholder="Longer description, motivations, and context"
              className="min-h-28"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="user-persona-tags">Tags</Label>
            <Input
              id="user-persona-tags"
              value={tagsInput}
              onChange={(event) => setTagsInput(event.target.value)}
              placeholder="writer, systems, pedagogy"
            />
          </div>

          <div className="space-y-2">
            <Label>Publication State</Label>
            <Select
              value={publicationState}
              onValueChange={(value) =>
                setPublicationState(value as PersonaPublicationState)
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

          <div className="flex items-center justify-between rounded-lg border p-3">
            <div className="space-y-1">
              <div className="text-sm font-medium">Set As Primary Persona</div>
              <p className="text-xs text-muted-foreground">
                This is optional and can be changed later.
              </p>
            </div>
            <Switch checked={setAsPrimary} onCheckedChange={setSetAsPrimary} />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={name.trim().length === 0}>
              Save Persona
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}
