import { Handshake, Pencil, Plus } from "lucide-react"
import { useState } from "react"

import { PersonaRelationSheet } from "@/components/UserPage/PersonaRelationSheet"
import type {
  PersonaRelationSummary,
  RelationshipManagerBlockContent,
  UserPageViewModel,
} from "@/components/UserPage/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { BlockContainer } from "../primitives"

export interface RelationshipManagerBlockConfig {
  allowCreate?: boolean
  allowEditing?: boolean
  audienceScoped?: boolean
}

export interface RelationshipManagerBlockProps {
  config: RelationshipManagerBlockConfig
  content?: RelationshipManagerBlockContent
  viewModel?: UserPageViewModel
  isEditing?: boolean
  entityId: string
  onContentChange?: (content: RelationshipManagerBlockContent) => void
  className?: string
}

export function RelationshipManagerBlock({
  config,
  content,
  viewModel,
  isEditing = false,
  entityId,
  onContentChange,
  className,
}: RelationshipManagerBlockProps) {
  const [isSheetOpen, setIsSheetOpen] = useState(false)
  const [editingRelation, setEditingRelation] =
    useState<PersonaRelationSummary | null>(null)

  const relations = content?.relations ?? viewModel?.relations ?? []

  const upsertRelation = (
    draft: Omit<PersonaRelationSummary, "id"> & { id?: string },
  ) => {
    const nextRelation: PersonaRelationSummary = {
      id: draft.id ?? crypto.randomUUID(),
      sourcePersonaId: draft.sourcePersonaId,
      targetLabel: draft.targetLabel,
      targetType: draft.targetType,
      relationKind: draft.relationKind,
      audienceScope: draft.audienceScope,
      note: draft.note,
      status: draft.status,
    }

    const existingRelations = content?.relations ?? relations
    const hasExisting = existingRelations.some(
      (relation) => relation.id === nextRelation.id,
    )
    const nextRelations = hasExisting
      ? existingRelations.map((relation) =>
          relation.id === nextRelation.id ? nextRelation : relation,
        )
      : [nextRelation, ...existingRelations]

    onContentChange?.({
      relations: nextRelations,
    })
  }

  return (
    <>
      <BlockContainer
        title="Relations"
        className={className}
        headerActions={
          viewModel?.isOwner && isEditing && config.allowCreate !== false ? (
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setEditingRelation(null)
                setIsSheetOpen(true)
              }}
              disabled={!isEditing || viewModel.personas.length === 0}
            >
              <Plus className="mr-1 h-4 w-4" />
              Add Relation
            </Button>
          ) : undefined
        }
      >
        <div className="space-y-3 p-4">
          {relations.length === 0 ? (
            <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
              Relations are managed only through personas. Add a persona
              relation to make this surface visible.
            </div>
          ) : (
            relations.map((relation) => {
              const sourcePersona = viewModel?.personas.find(
                (persona) => persona.id === relation.sourcePersonaId,
              )
              return (
                <div key={relation.id} className="rounded-lg border p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Handshake className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">
                          {relation.targetLabel}
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Badge>{relation.relationKind}</Badge>
                        {config.audienceScoped !== false && (
                          <Badge variant="outline">
                            {relation.audienceScope}
                          </Badge>
                        )}
                        {sourcePersona && (
                          <Badge variant="secondary">
                            {sourcePersona.nickname || sourcePersona.name}
                          </Badge>
                        )}
                      </div>
                      {relation.note && (
                        <p className="text-sm text-muted-foreground">
                          {relation.note}
                        </p>
                      )}
                    </div>

                    {viewModel?.isOwner &&
                      isEditing &&
                      config.allowEditing !== false && (
                        <Button
                          size="icon"
                          variant="ghost"
                          disabled={!isEditing}
                          onClick={() => {
                            setEditingRelation(relation)
                            setIsSheetOpen(true)
                          }}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                      )}
                  </div>
                </div>
              )
            })
          )}
        </div>
      </BlockContainer>

      <PersonaRelationSheet
        open={isSheetOpen}
        onOpenChange={setIsSheetOpen}
        relation={editingRelation}
        ownerUserId={entityId}
        onSave={upsertRelation}
      />
    </>
  )
}
