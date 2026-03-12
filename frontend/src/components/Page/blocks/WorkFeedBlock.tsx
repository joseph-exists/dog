import { BriefcaseBusiness, Pencil, Plus } from "lucide-react"
import { useMemo, useState } from "react"

import {
  UserWorkAssociationSheet,
  type UserWorkAssociationDraft,
} from "@/components/UserPage/UserWorkAssociationSheet"
import type {
  UserPageViewModel,
  UserWorkFeedItem,
  WorkFeedBlockContent,
} from "@/components/UserPage/types"
import { filterWorkFeedForAudience } from "@/hooks/useUserPageViewModel"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { BlockContainer } from "../primitives"

export interface WorkFeedBlockConfig {
  layout?: "stack"
  maxVisible?: number
  showPersonaBadges?: boolean
  showAudienceBadges?: boolean
}

export interface WorkFeedBlockProps {
  config: WorkFeedBlockConfig
  content?: WorkFeedBlockContent
  viewModel?: UserPageViewModel
  isEditing?: boolean
  entityId: string
  onContentChange?: (content: WorkFeedBlockContent) => void
  className?: string
}

export function WorkFeedBlock({
  config,
  content,
  viewModel,
  isEditing = false,
  entityId,
  onContentChange,
  className,
}: WorkFeedBlockProps) {
  const [isSheetOpen, setIsSheetOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<UserWorkFeedItem | null>(null)

  const findPersonaByReference = (personaId: string) =>
    viewModel?.personas.find(
      (candidate) =>
        candidate.id === personaId || candidate.userPersonaId === personaId,
    )

  const items = content?.items ?? viewModel?.workFeed ?? []
  const visibleItems = useMemo(() => {
    const filtered = filterWorkFeedForAudience(
      items,
      viewModel?.audiencePresentations ?? [],
      viewModel?.selectedAudienceScope ?? "public",
      viewModel?.isOwner ?? false,
      viewModel?.resolvedAudienceKeys ?? [],
    )
    const maxVisible = config.maxVisible ?? filtered.length
    return filtered.slice(0, maxVisible)
  }, [
    items,
    viewModel?.audiencePresentations,
    viewModel?.selectedAudienceScope,
    viewModel?.isOwner,
    viewModel?.resolvedAudienceKeys,
    config.maxVisible,
  ])

  const upsertItem = (draft: UserWorkAssociationDraft) => {
    const nextItem: UserWorkFeedItem = {
      id: draft.id ?? crypto.randomUUID(),
      title: draft.title,
      summary: draft.summary,
      workType: draft.workType,
      status: "published",
      tags: draft.tags,
      associatedPersonaIds: draft.associatedPersonaIds,
      intendedAudienceScopes: draft.intendedAudienceScopes,
      timestampLabel: "Recently updated",
      href: draft.href,
      isRepresentative: draft.isRepresentative,
    }

    const existingItems = content?.items ?? items
    const hasExisting = existingItems.some((item) => item.id === nextItem.id)
    const nextItems = hasExisting
      ? existingItems.map((item) => (item.id === nextItem.id ? nextItem : item))
      : [nextItem, ...existingItems]

    onContentChange?.({
      title: content?.title,
      emptyMessage: content?.emptyMessage,
      items: nextItems,
    })
  }

  return (
    <>
      <BlockContainer
        title={content?.title || "Work Flow"}
        className={className}
        headerActions={
          viewModel?.isOwner && isEditing ? (
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setEditingItem(null)
                setIsSheetOpen(true)
              }}
              disabled={!isEditing}
            >
              <Plus className="mr-1 h-4 w-4" />
              Add Work
            </Button>
          ) : undefined
        }
      >
        <div className="space-y-3 p-4">
          {visibleItems.length === 0 ? (
            <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
              {content?.emptyMessage ||
                "No representative work has been configured for this audience yet."}
            </div>
          ) : (
            visibleItems.map((item) => (
              <div key={item.id} className="rounded-lg border p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <BriefcaseBusiness className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{item.title}</span>
                      <Badge variant="outline">{item.workType}</Badge>
                    </div>
                    {item.summary && (
                      <p className="text-sm text-muted-foreground">
                        {item.summary}
                      </p>
                    )}
                  </div>

                  {viewModel?.isOwner && isEditing && (
                    <Button
                      size="icon"
                      variant="ghost"
                      disabled={!isEditing}
                      onClick={() => {
                        setEditingItem(item)
                        setIsSheetOpen(true)
                      }}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                  )}
                </div>

                <div className="mt-3 flex flex-wrap gap-2">
                  {item.tags.map((tag) => (
                    <Badge key={tag} variant="secondary">
                      {tag}
                    </Badge>
                  ))}
                  {config.showAudienceBadges !== false &&
                    item.intendedAudienceScopes.map((scope) => (
                      <Badge key={`${item.id}-${scope}`} variant="outline">
                        {scope}
                      </Badge>
                    ))}
                  {config.showPersonaBadges &&
                    item.associatedPersonaIds.map((personaId) => {
                      const persona = findPersonaByReference(personaId)
                      return persona ? (
                        <Badge key={`${item.id}-${personaId}`}>
                          {persona.nickname || persona.name}
                        </Badge>
                      ) : null
                    })}
                </div>
              </div>
            ))
          )}
        </div>
      </BlockContainer>

      <UserWorkAssociationSheet
        open={isSheetOpen}
        onOpenChange={setIsSheetOpen}
        item={editingItem}
        ownerUserId={entityId}
        onSave={upsertItem}
      />
    </>
  )
}
