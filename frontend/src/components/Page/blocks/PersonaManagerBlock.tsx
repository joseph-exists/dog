import { useQueryClient } from "@tanstack/react-query"
import { Pencil, Plus } from "lucide-react"
import { useMemo, useState } from "react"

import type { PersonaCreate } from "@/client"
import { PersonasService } from "@/client"
import { UserPersonaEditorSheet } from "@/components/UserPage/UserPersonaEditorSheet"
import type {
  PersonaManagerBlockContent,
  PrimaryPersonaBlockContent,
  UserPageViewModel,
  UserPersonaSummary,
} from "@/components/UserPage/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { PersonaLibraryService } from "@/services/personaLibraryService"
import { BlockContainer } from "../primitives"

export interface PersonaManagerBlockConfig {
  allowCreate?: boolean
  allowPrimarySelection?: boolean
  allowPublishing?: boolean
  allowTagEditing?: boolean
}

export interface PersonaManagerBlockProps {
  config: PersonaManagerBlockConfig
  content?: PersonaManagerBlockContent
  viewModel?: UserPageViewModel
  isEditing?: boolean
  entityId: string
  onContentChange?: (content: PersonaManagerBlockContent) => void
  onPrimaryPersonaChange?: (content: PrimaryPersonaBlockContent) => void
  className?: string
}

export function PersonaManagerBlock({
  config,
  content,
  viewModel,
  isEditing = false,
  entityId,
  onContentChange,
  onPrimaryPersonaChange,
  className,
}: PersonaManagerBlockProps) {
  const queryClient = useQueryClient()
  const [isSheetOpen, setIsSheetOpen] = useState(false)
  const [editingPersona, setEditingPersona] = useState<UserPersonaSummary | null>(
    null,
  )

  const personas = useMemo(
    () => content?.personas ?? viewModel?.personas ?? [],
    [content?.personas, viewModel?.personas],
  )

  const upsertPersona = async (draft: {
    id?: string
    name: string
    nickname: string | null
    shortBio: string | null
    longBio: string | null
    publicationState: "draft" | "published"
    tags: UserPersonaSummary["tags"]
    setAsPrimary: boolean
  }) => {
    let personaId = draft.id
    let persistedName = draft.name

    if (!personaId) {
      try {
        const payload: PersonaCreate = {
          name: draft.name,
          description: draft.shortBio,
          general_domain: draft.tags[0]?.label ?? null,
          specific_domain: draft.tags[1]?.label ?? null,
        }
        const createdPersona = await PersonasService.createPersona({
          requestBody: payload,
        })
        await PersonaLibraryService.addToLibrary(
          { type: "user", id: entityId, name: "User" },
          createdPersona.id,
          draft.nickname ?? undefined,
        )
        personaId = createdPersona.id
        persistedName = createdPersona.name
        await queryClient.invalidateQueries({
          queryKey: ["persona-library", "user", entityId],
        })
        showSuccessToast(`Created persona "${createdPersona.name}"`)
      } catch {
        showErrorToast("Failed to create persona")
        return
      }
    }

    const nextPersona: UserPersonaSummary = {
      id: personaId,
      name: persistedName,
      nickname: draft.nickname,
      shortBio: draft.shortBio,
      longBio: draft.longBio,
      tags: draft.tags,
      publicationState: draft.publicationState,
      associatedWorkCount:
        viewModel?.workFeed.filter((item) =>
          item.associatedPersonaIds.includes(personaId),
        ).length ?? 0,
      isPrimary: draft.setAsPrimary,
      isVisibleInCurrentAudience: true,
    }

    const existingPersonas = content?.personas ?? personas
    const hasExisting = existingPersonas.some((persona) => persona.id === personaId)
    const nextPersonas = hasExisting
      ? existingPersonas.map((persona) =>
          persona.id === personaId ? nextPersona : persona,
        )
      : [nextPersona, ...existingPersonas]

    onContentChange?.({
      personas: nextPersonas,
    })

    if (draft.setAsPrimary && config.allowPrimarySelection !== false) {
      onPrimaryPersonaChange?.({
        primaryPersonaId: personaId,
        explanation:
          "A primary persona can orient the page while remaining an explicit, reversible choice.",
      })
    }
  }

  return (
    <>
      <BlockContainer
        title="Persona Management"
        className={className}
        headerActions={
          viewModel?.isOwner && isEditing && config.allowCreate !== false ? (
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setEditingPersona(null)
                setIsSheetOpen(true)
              }}
              disabled={!isEditing}
            >
              <Plus className="mr-1 h-4 w-4" />
              Create Persona
            </Button>
          ) : undefined
        }
      >
        <div className="space-y-3 p-4">
          {personas.length === 0 ? (
            <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
              Create a persona to begin managing audience-specific identity,
              work association, and relation affordances.
            </div>
          ) : (
            personas.map((persona) => (
              <div key={persona.id} className="rounded-lg border p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">
                        {persona.nickname || persona.name}
                      </span>
                      {persona.isPrimary && <Badge>Primary</Badge>}
                      <Badge variant="outline">{persona.publicationState}</Badge>
                    </div>
                    {persona.shortBio && (
                      <p className="text-sm text-muted-foreground">
                        {persona.shortBio}
                      </p>
                    )}
                    <div className="flex flex-wrap gap-2">
                      {persona.tags.map((tag) => (
                        <Badge key={tag.id} variant="secondary">
                          {tag.label}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {isEditing && (
                    <Button
                      size="icon"
                      variant="ghost"
                      disabled={!isEditing}
                      onClick={() => {
                        setEditingPersona(persona)
                        setIsSheetOpen(true)
                      }}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </BlockContainer>

      <UserPersonaEditorSheet
        open={isSheetOpen}
        onOpenChange={setIsSheetOpen}
        persona={editingPersona}
        onSave={upsertPersona}
      />
    </>
  )
}
