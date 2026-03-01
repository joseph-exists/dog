import { Eye, Pencil, Plus } from "lucide-react"
import { useMemo, useState } from "react"

import { AudiencePresentationSheet } from "@/components/UserPage/AudiencePresentationSheet"
import type {
  AudiencePresentationBlockContent,
  AudiencePresentationSummary,
  UserPageViewModel,
} from "@/components/UserPage/types"
import { getActiveAudiencePresentation } from "@/hooks/useUserPageViewModel"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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

export function AudiencePresentationBlock({
  config,
  content,
  viewModel,
  isEditing = false,
  entityId,
  onContentChange,
  className,
}: AudiencePresentationBlockProps) {
  const [isSheetOpen, setIsSheetOpen] = useState(false)
  const [editingPresentation, setEditingPresentation] =
    useState<AudiencePresentationSummary | null>(null)

  const presentations = content?.presentations ?? viewModel?.audiencePresentations ?? []
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

  const upsertPresentation = (
    draft: Omit<AudiencePresentationSummary, "id"> & { id?: string },
  ) => {
    const nextPresentation: AudiencePresentationSummary = {
      id: draft.id ?? crypto.randomUUID(),
      personaId: draft.personaId,
      audienceScope: draft.audienceScope,
      audienceLabel: draft.audienceLabel,
      headline: draft.headline,
      framingText: draft.framingText,
      visibleWorkIds: draft.visibleWorkIds,
      relationCallToAction: draft.relationCallToAction,
    }

    const existingPresentations = content?.presentations ?? presentations
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

    onContentChange?.({
      presentations: nextPresentations,
    })
  }

  return (
    <>
      <BlockContainer
        title="Audience Views"
        className={className}
        headerActions={
          viewModel?.isOwner ? (
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

                    {viewModel?.isOwner && config.showPreviewCards !== false && (
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
