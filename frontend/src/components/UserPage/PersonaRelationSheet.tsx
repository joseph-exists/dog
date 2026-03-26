import { useEffect, useState } from "react"

import { PersonaPicker } from "@/components/Persona"
import type {
  AudienceScope,
  PersonaRelationSummary,
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
import { Textarea } from "@/components/ui/textarea"

export interface PersonaRelationDraft {
  id?: string
  sourcePersonaId: string
  targetLabel: string
  targetType: "persona" | "external"
  relationKind: PersonaRelationSummary["relationKind"]
  audienceScope: AudienceScope
  note: string | null
  status: PersonaRelationSummary["status"]
}

interface PersonaRelationSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  relation?: PersonaRelationSummary | null
  ownerUserId: string
  onSave: (draft: PersonaRelationDraft) => Promise<void> | void
}

export function PersonaRelationSheet({
  open,
  onOpenChange,
  relation,
  ownerUserId,
  onSave,
}: PersonaRelationSheetProps) {
  const [sourcePersonaId, setSourcePersonaId] = useState("")
  const [targetLabel, setTargetLabel] = useState("")
  const [targetType, setTargetType] = useState<"persona" | "external">(
    "external",
  )
  const [relationKind, setRelationKind] =
    useState<PersonaRelationSummary["relationKind"]>("collaborator")
  const [audienceScope, setAudienceScope] = useState<AudienceScope>("public")
  const [note, setNote] = useState("")
  const [status, setStatus] =
    useState<PersonaRelationSummary["status"]>("active")

  useEffect(() => {
    if (!open) return
    setSourcePersonaId(relation?.sourcePersonaId ?? "")
    setTargetLabel(relation?.targetLabel ?? "")
    setTargetType(relation?.targetType ?? "external")
    setRelationKind(relation?.relationKind ?? "collaborator")
    setAudienceScope(relation?.audienceScope ?? "public")
    setNote(relation?.note ?? "")
    setStatus(relation?.status ?? "active")
  }, [open, relation])

  const handleSave = async () => {
    await onSave({
      id: relation?.id,
      sourcePersonaId,
      targetLabel: targetLabel.trim(),
      targetType,
      relationKind,
      audienceScope,
      note: note.trim() || null,
      status,
    })
    onOpenChange(false)
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[460px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>
            {relation ? "Edit Persona Relation" : "Add Persona Relation"}
          </SheetTitle>
        </SheetHeader>

        <div className="mt-6 space-y-4">
          <div className="space-y-2">
            <Label>Source Persona</Label>
            <div className="rounded-lg border p-3">
              <PersonaPicker
                owner={{ type: "user", id: ownerUserId, name: "User" }}
                mode="select-single"
                variant="inline"
                layout="list"
                selected={sourcePersonaId || null}
                onSelect={(selected) =>
                  setSourcePersonaId(
                    typeof selected === "string" ? selected : "",
                  )
                }
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Target Type</Label>
              <Select
                value={targetType}
                onValueChange={(value) =>
                  setTargetType(value as "persona" | "external")
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="external">External</SelectItem>
                  <SelectItem value="persona">Persona</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Relation Kind</Label>
              <Select
                value={relationKind}
                onValueChange={(value) =>
                  setRelationKind(
                    value as PersonaRelationSummary["relationKind"],
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

          <div className="space-y-2">
            <Label htmlFor="relation-target">Target Label</Label>
            <Input
              id="relation-target"
              value={targetLabel}
              onChange={(event) => setTargetLabel(event.target.value)}
              placeholder="Name this audience will see"
            />
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
              <Label>Status</Label>
              <Select
                value={status}
                onValueChange={(value) =>
                  setStatus(value as PersonaRelationSummary["status"])
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
            <Label htmlFor="relation-note">Note</Label>
            <Textarea
              id="relation-note"
              value={note}
              onChange={(event) => setNote(event.target.value)}
              placeholder="Optional contextual note"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={
                sourcePersonaId.length === 0 || targetLabel.trim().length === 0
              }
            >
              Save Relation
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}
