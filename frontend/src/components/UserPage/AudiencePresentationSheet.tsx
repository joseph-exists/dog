import { useEffect, useState } from "react"

import { PersonaPicker } from "@/components/Persona"
import type {
  AudiencePresentationPublicationState,
  AudiencePresentationSummary,
  AudienceScope,
  UserWorkFeedItem,
} from "@/components/UserPage/types"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
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
import { Textarea } from "@/components/ui/textarea"

export interface AudiencePresentationDraft {
  id?: string
  userPersonaId?: string | null
  personaId: string
  audienceScope: AudienceScope
  audienceKey?: string | null
  audienceLabel: string
  headline: string
  framingText: string | null
  visibleWorkIds: string[]
  publicationState: AudiencePresentationPublicationState
  relationCallToAction: AudiencePresentationSummary["relationCallToAction"]
}

interface AudiencePresentationSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  presentation?: AudiencePresentationSummary | null
  ownerUserId: string
  workFeed: UserWorkFeedItem[]
  onSave: (draft: AudiencePresentationDraft) => Promise<void> | void
}

export function AudiencePresentationSheet({
  open,
  onOpenChange,
  presentation,
  ownerUserId,
  workFeed,
  onSave,
}: AudiencePresentationSheetProps) {
  const [personaId, setPersonaId] = useState("")
  const [audienceScope, setAudienceScope] = useState<AudienceScope>("public")
  const [audienceKey, setAudienceKey] = useState("")
  const [audienceLabel, setAudienceLabel] = useState("Public")
  const [headline, setHeadline] = useState("")
  const [framingText, setFramingText] = useState("")
  const [visibleWorkIds, setVisibleWorkIds] = useState<string[]>([])
  const [publicationState, setPublicationState] =
    useState<AudiencePresentationPublicationState>("draft")
  const [relationCallToAction, setRelationCallToAction] =
    useState<AudiencePresentationSummary["relationCallToAction"]>("none")

  useEffect(() => {
    if (!open) return
    setPersonaId(presentation?.personaId ?? "")
    setAudienceScope(presentation?.audienceScope ?? "public")
    setAudienceKey(presentation?.audienceKey ?? "")
    setAudienceLabel(presentation?.audienceLabel ?? "Public")
    setHeadline(presentation?.headline ?? "")
    setFramingText(presentation?.framingText ?? "")
    setVisibleWorkIds(presentation?.visibleWorkIds ?? [])
    setPublicationState(presentation?.publicationState ?? "draft")
    setRelationCallToAction(presentation?.relationCallToAction ?? "none")
  }, [open, presentation])

  const toggleWorkId = (workId: string, checked: boolean) => {
    setVisibleWorkIds((current) =>
      checked ? [...current, workId] : current.filter((id) => id !== workId),
    )
  }

  const handleSave = async () => {
    await onSave({
      id: presentation?.id,
      userPersonaId: presentation?.userPersonaId ?? null,
      personaId,
      audienceScope,
      audienceKey: audienceKey.trim() || null,
      audienceLabel: audienceLabel.trim(),
      headline: headline.trim(),
      framingText: framingText.trim() || null,
      visibleWorkIds,
      publicationState,
      relationCallToAction,
    })
    onOpenChange(false)
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[480px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>
            {presentation ? "Edit Audience View" : "Create Audience View"}
          </SheetTitle>
        </SheetHeader>

        <div className="mt-6 space-y-4">
          <div className="space-y-2">
            <Label>Persona</Label>
            <div className="rounded-lg border p-3">
              <PersonaPicker
                owner={{ type: "user", id: ownerUserId, name: "User" }}
                mode="select-single"
                variant="inline"
                layout="list"
                selected={personaId || null}
                onSelect={(selected) =>
                  setPersonaId(typeof selected === "string" ? selected : "")
                }
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
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
              <Label htmlFor="audience-label">Audience Label</Label>
              <Input
                id="audience-label"
                value={audienceLabel}
                onChange={(event) => setAudienceLabel(event.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Publication State</Label>
            <Select
              value={publicationState}
              onValueChange={(value) =>
                setPublicationState(
                  value as AudiencePresentationPublicationState,
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

          <div className="space-y-2">
            <Label htmlFor="audience-key">Audience Key</Label>
            <Input
              id="audience-key"
              value={audienceKey}
              onChange={(event) => setAudienceKey(event.target.value)}
              placeholder="Optional target id for custom audience views"
            />
            <p className="text-xs text-muted-foreground">
              Use this when a custom audience view should match a specific user,
              persona, group, or persona-group id.
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="audience-headline">Headline</Label>
            <Input
              id="audience-headline"
              value={headline}
              onChange={(event) => setHeadline(event.target.value)}
              placeholder="What this audience should understand first"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="audience-framing">Framing Text</Label>
            <Textarea
              id="audience-framing"
              value={framingText}
              onChange={(event) => setFramingText(event.target.value)}
              placeholder="How this persona contextualizes the work for this audience"
            />
          </div>

          <div className="space-y-2">
            <Label>Visible Work</Label>
            <div className="space-y-2 rounded-lg border p-3">
              {workFeed.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  Add work items before you define an audience view.
                </p>
              ) : (
                workFeed.map((item) => (
                  <label
                    key={item.id}
                    className="flex items-start gap-3 rounded-md border p-2"
                  >
                    <Checkbox
                      checked={visibleWorkIds.includes(item.id)}
                      onCheckedChange={(checked) =>
                        toggleWorkId(item.id, checked === true)
                      }
                    />
                    <span className="space-y-1">
                      <span className="block text-sm font-medium">
                        {item.title}
                      </span>
                      {item.summary && (
                        <span className="block text-xs text-muted-foreground">
                          {item.summary}
                        </span>
                      )}
                    </span>
                  </label>
                ))
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label>Relation Call To Action</Label>
            <Select
              value={relationCallToAction}
              onValueChange={(value) =>
                setRelationCallToAction(
                  value as AudiencePresentationSummary["relationCallToAction"],
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

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={headline.trim().length === 0 || personaId.length === 0}
            >
              Save Audience View
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}
