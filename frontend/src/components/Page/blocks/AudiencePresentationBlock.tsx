import { useQueryClient } from "@tanstack/react-query"
import { Eye, Pencil, Plus } from "lucide-react"
import { useMemo, useState } from "react"

import type { ApiError } from "@/client"
import { UserPersonasService } from "@/client"
import { AudiencePresentationSheet } from "@/components/UserPage/AudiencePresentationSheet"
import type {
  AudiencePresentationBlockContent,
  AudiencePresentationSummary,
  UserPageViewModel,
} from "@/components/UserPage/types"
import { getActiveAudiencePresentation } from "@/hooks/useUserPageViewModel"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { handleError } from "@/utils"
import { BlockContainer } from "../primitives"

export interface AudiencePresentationBlockConfig {
  allowAudienceSwitching?: boolean
  showPreviewCards?: boolean
}

export interface AudiencePresentationBlockProps {
  config: AudiencePresentationBlockConfig
  content?: AudiencePresentationBlockContent
  viewModel?: UserPageViewModel
  isEditing?: boolean
  entityId: string
  onContentChange?: (content: AudiencePresentationBlockContent) => void
  className?: string
}

function toContentSnapshot(
  presentations: AudiencePresentationSummary[],
): AudiencePresentationBlockContent {
  return {
    presentations: presentations.map((presentation) => ({
      ...presentation,
      userPersonaId: presentation.userPersonaId ?? null,
    })),
  }
}

export function AudiencePresentationBlock({
  config,
  content,
  viewModel,
  isEditing = false,
  entityId,
  onContentChange,
  className,
}: AudiencePresentationBlockProps) {
  const queryClient = useQueryClient()
  const [isSheetOpen, setIsSheetOpen] = useState(false)
  const [editingPresentation, setEditingPresentation] =
    useState<AudiencePresentationSummary | null>(null)

  const presentations =
    viewModel?.audiencePresentations ?? content?.presentations ?? []
  const activePresentation = useMemo(
    () =>
      getActiveAudiencePresentation(
        presentations,
        viewModel?.selectedAudienceScope ?? "public",
      ),
    [presentations, viewModel?.selectedAudienceScope],
  )

  const renderCards = viewModel?.isOwner
    ? presentations
    : activePresentation
      ? [activePresentation]
      : []

  const upsertPresentation = async (
    draft: Omit<AudiencePresentationSummary, "id"> & { id?: string },
  ) => {
    const selectedPersona = viewModel?.personas.find(
      (persona) => persona.id === draft.personaId,
    )
    const userPersonaId =
      draft.userPersonaId ?? selectedPersona?.userPersonaId ?? null

    if (!userPersonaId) {
      showErrorToast("Select a saved persona before creating an audience view")
      return
    }

    try {
      const persistedPresentation = draft.id
        ? await UserPersonasService.updateUserPersonaPresentation({
            id: userPersonaId,
            presentationId: draft.id,
            requestBody: {
              audience_scope: draft.audienceScope,
              audience_label: draft.audienceLabel,
              headline: draft.headline,
              framing_text: draft.framingText,
              visible_work_ids_json: draft.visibleWorkIds,
              relation_call_to_action: draft.relationCallToAction,
            },
          })
        : await UserPersonasService.createUserPersonaPresentation({
            id: userPersonaId,
            requestBody: {
              audience_scope: draft.audienceScope,
              audience_label: draft.audienceLabel,
              headline: draft.headline,
              framing_text: draft.framingText,
              visible_work_ids_json: draft.visibleWorkIds,
              relation_call_to_action: draft.relationCallToAction,
            },
          })

      const nextPresentation: AudiencePresentationSummary = {
        id: persistedPresentation.id,
        userPersonaId,
        personaId: draft.personaId,
        audienceScope: persistedPresentation.audience_scope ?? draft.audienceScope,
        audienceLabel: persistedPresentation.audience_label,
        headline: persistedPresentation.headline,
        framingText: persistedPresentation.framing_text ?? null,
        visibleWorkIds: persistedPresentation.visible_work_ids_json ?? [],
        relationCallToAction:
          persistedPresentation.relation_call_to_action === "request_contact" ||
          persistedPresentation.relation_call_to_action ===
            "invite_collaboration" ||
          persistedPresentation.relation_call_to_action === "follow_work"
            ? persistedPresentation.relation_call_to_action
            : "none",
      }

      const existingPresentations = presentations
      const hasExisting = existingPresentations.some(
        (presentation) => presentation.id === nextPresentation.id,
      )
      const nextPresentations = hasExisting
        ? existingPresentations.map((presentation) =>
            presentation.id === nextPresentation.id
              ? nextPresentation
              : presentation,
          )
        : [nextPresentation, ...existingPresentations]

      onContentChange?.(toContentSnapshot(nextPresentations))

      await queryClient.invalidateQueries({
        queryKey: ["user-persona-page-data", entityId],
      })

      showSuccessToast(
        hasExisting
          ? `Updated audience view "${nextPresentation.headline}"`
          : `Created audience view "${nextPresentation.headline}"`,
      )
    } catch (error) {
      handleError.call(showErrorToast, error as ApiError)
    }
  }

  return (
    <>
      <BlockContainer
        title="Audience Views"
        className={className}
        headerActions={
          viewModel?.isOwner && isEditing ? (
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setEditingPresentation(null)
                setIsSheetOpen(true)
              }}
              disabled={!isEditing}
            >
              <Plus className="mr-1 h-4 w-4" />
              Add View
            </Button>
          ) : undefined
        }
      >
        <div className="space-y-3 p-4">
          {renderCards.length === 0 ? (
            <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
              No presentation configured for this audience yet.
            </div>
          ) : (
            renderCards.map((presentation) => {
              const persona = viewModel?.personas.find(
                (candidate) => candidate.id === presentation.personaId,
              )
              return (
                <div key={presentation.id} className="rounded-lg border p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Eye className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{presentation.headline}</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Badge variant="outline">
                          {presentation.audienceLabel}
                        </Badge>
                        {persona && (
                          <Badge>{persona.nickname || persona.name}</Badge>
                        )}
                        {presentation.relationCallToAction !== "none" && (
                          <Badge variant="secondary">
                            {presentation.relationCallToAction}
                          </Badge>
                        )}
                      </div>
                    </div>

                    {viewModel?.isOwner &&
                      isEditing &&
                      config.showPreviewCards !== false && (
                      <Button
                        size="icon"
                        variant="ghost"
                        disabled={!isEditing}
                        onClick={() => {
                          setEditingPresentation(presentation)
                          setIsSheetOpen(true)
                        }}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                    )}
                  </div>

                  {presentation.framingText && (
                    <p className="mt-3 text-sm text-muted-foreground">
                      {presentation.framingText}
                    </p>
                  )}
                </div>
              )
            })
          )}
        </div>
      </BlockContainer>

      <AudiencePresentationSheet
        open={isSheetOpen}
        onOpenChange={setIsSheetOpen}
        presentation={editingPresentation}
        ownerUserId={entityId}
        workFeed={viewModel?.workFeed ?? []}
        onSave={upsertPresentation}
      />
    </>
  )
}
