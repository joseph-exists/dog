import { useQueryClient } from "@tanstack/react-query"
import { Pencil, Plus } from "lucide-react"
import { useMemo, useState } from "react"

import type { ApiError, PersonaCreate } from "@/client"
import { PersonasService, UserPersonasService } from "@/client"
import type {
  PersonaManagerBlockContent,
  PrimaryPersonaBlockContent,
  UserPageViewModel,
  UserPersonaSummary,
} from "@/components/UserPage/types"
import { UserPersonaEditorSheet } from "@/components/UserPage/UserPersonaEditorSheet"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
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

function toContentSnapshot(
  personas: UserPersonaSummary[],
): PersonaManagerBlockContent {
  return {
    personas: personas.map((persona) => ({
      ...persona,
      userPersonaId: persona.userPersonaId ?? null,
      personaVisibility: persona.personaVisibility ?? null,
    })),
  }
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
  const [editingPersona, setEditingPersona] =
    useState<UserPersonaSummary | null>(null)

  const personas = useMemo(
    () => viewModel?.personas ?? content?.personas ?? [],
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
    const existingPersona = draft.id
      ? personas.find((persona) => persona.id === draft.id)
      : null
    let personaId = draft.id
    let userPersonaId = existingPersona?.userPersonaId ?? null
    let persistedName = draft.name.trim()
    let personaVisibility = existingPersona?.personaVisibility ?? "private"

    try {
      if (!personaId) {
        const payload: PersonaCreate = {
          name: persistedName,
          description: draft.shortBio,
          long_description: draft.longBio,
          general_domain: draft.tags[0]?.label ?? null,
          specific_domain: draft.tags[1]?.label ?? null,
          visibility: "private",
          owner_user_id: entityId,
        }
        const createdPersona = await PersonasService.createPersona({
          requestBody: payload,
        })
        const createdUserPersona = await UserPersonasService.createUserPersona({
          requestBody: {
            persona_id: createdPersona.id,
            nickname: draft.nickname,
            description: draft.shortBio,
            short_bio: draft.shortBio,
            long_bio: draft.longBio,
            tags_json: draft.tags as unknown as Array<Record<string, unknown>>,
            publication_state: draft.publicationState,
            is_primary: draft.setAsPrimary,
            is_active: true,
          },
        })

        personaId = createdPersona.id
        userPersonaId = createdUserPersona.id
        persistedName = createdPersona.name
        personaVisibility = createdPersona.visibility ?? "private"
      } else {
        if (!userPersonaId) {
          showErrorToast("This persona is missing its backend reference")
          return
        }

        if (
          existingPersona &&
          persistedName !== existingPersona.name &&
          existingPersona.personaVisibility === "system"
        ) {
          showErrorToast("System-derived personas cannot be renamed here")
          persistedName = existingPersona.name
        } else if (existingPersona && persistedName !== existingPersona.name) {
          await PersonasService.updatePersona({
            id: personaId,
            requestBody: { name: persistedName },
          })
        }

        await UserPersonasService.updateUserPersona({
          id: userPersonaId,
          requestBody: {
            nickname: draft.nickname,
            description: draft.shortBio,
            short_bio: draft.shortBio,
            long_bio: draft.longBio,
            tags_json: draft.tags as unknown as Array<Record<string, unknown>>,
            publication_state: draft.publicationState,
            is_primary: draft.setAsPrimary,
            is_active: true,
          },
        })
      }
    } catch (error) {
      handleError.call(showErrorToast, error as ApiError)
      return
    }

    const nextPersona: UserPersonaSummary = {
      id: personaId,
      userPersonaId,
      personaVisibility,
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

    const existingPersonas = personas
    const hasExisting = existingPersonas.some(
      (persona) => persona.id === personaId,
    )
    const basePersonas = hasExisting
      ? existingPersonas.map((persona) =>
          persona.id === personaId ? nextPersona : persona,
        )
      : [nextPersona, ...existingPersonas]
    const nextPersonas = draft.setAsPrimary
      ? basePersonas.map((persona) => ({
          ...persona,
          isPrimary: persona.id === personaId,
        }))
      : basePersonas

    onContentChange?.(toContentSnapshot(nextPersonas))

    if (config.allowPrimarySelection !== false && draft.setAsPrimary) {
      onPrimaryPersonaChange?.({
        primaryPersonaId: personaId,
        explanation:
          "A primary persona can orient the page while remaining an explicit, reversible choice.",
      })
    } else if (
      config.allowPrimarySelection !== false &&
      existingPersona?.isPrimary
    ) {
      onPrimaryPersonaChange?.({
        primaryPersonaId: null,
        explanation:
          "A primary persona can orient the page while remaining an explicit, reversible choice.",
      })
    }

    await queryClient.invalidateQueries({
      queryKey: ["persona-library", "user", entityId],
    })
    await queryClient.invalidateQueries({
      queryKey: ["user-persona-page-data", entityId],
    })
    await queryClient.invalidateQueries({
      queryKey: ["user-persona-authoring-bundle", entityId],
    })

    showSuccessToast(
      hasExisting
        ? `Updated persona "${persistedName}"`
        : `Created persona "${persistedName}"`,
    )
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
                      <Badge variant="outline">
                        {persona.publicationState}
                      </Badge>
                      <Badge variant="secondary">
                        {persona.publicationState === "published"
                          ? "Included in visitor snapshot"
                          : "Draft only"}
                      </Badge>
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
