import { UserRoundCheck } from "lucide-react"
import { useMemo, useState } from "react"

import { PersonaPicker } from "@/components/Persona"
import type {
  PrimaryPersonaBlockContent,
  UserPageViewModel,
} from "@/components/UserPage/types"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { BlockContainer } from "../primitives"

export interface PrimaryPersonaBlockConfig {
  allowUnset?: boolean
  emphasizeOptionality?: boolean
}

export interface PrimaryPersonaBlockProps {
  config: PrimaryPersonaBlockConfig
  content?: PrimaryPersonaBlockContent
  viewModel?: UserPageViewModel
  entityId: string
  isOwner?: boolean
  isEditing?: boolean
  onContentChange?: (content: PrimaryPersonaBlockContent) => void
  className?: string
}

export function PrimaryPersonaBlock({
  config,
  content,
  viewModel,
  entityId,
  isOwner = false,
  isEditing = false,
  onContentChange,
  className,
}: PrimaryPersonaBlockProps) {
  const [isOpen, setIsOpen] = useState(false)

  const primaryPersonaId =
    content?.primaryPersonaId ?? viewModel?.primaryPersonaId ?? null
  const primaryPersona = useMemo(
    () => viewModel?.personas.find((persona) => persona.id === primaryPersonaId),
    [viewModel?.personas, primaryPersonaId],
  )

  const visiblePrimaryPersona =
    !isOwner && primaryPersona?.publicationState !== "published"
      ? null
      : primaryPersona

  return (
    <>
      <BlockContainer
        title="Primary Persona"
        className={className}
        headerActions={
          isOwner && isEditing ? (
            <Button
              size="sm"
              variant="outline"
              onClick={() => setIsOpen(true)}
              disabled={!isEditing}
            >
              Choose Persona
            </Button>
          ) : undefined
        }
      >
        <div className="space-y-3 p-4">
          {visiblePrimaryPersona ? (
            <div className="rounded-lg border bg-muted/30 p-4">
              <div className="flex items-center gap-2 text-sm font-medium">
                <UserRoundCheck className="h-4 w-4 text-primary" />
                {visiblePrimaryPersona.nickname || visiblePrimaryPersona.name}
              </div>
              {visiblePrimaryPersona.shortBio && (
                <p className="mt-2 text-sm text-muted-foreground">
                  {visiblePrimaryPersona.shortBio}
                </p>
              )}
            </div>
          ) : (
            <div className="rounded-lg border border-dashed p-4">
              <p className="text-sm text-muted-foreground">
                No primary persona is set. This remains an explicit, optional
                choice.
              </p>
            </div>
          )}

          {config.emphasizeOptionality !== false && (
            <p className="text-xs text-muted-foreground">
              {content?.explanation ||
                "A primary persona helps orient this page, but it is never inferred automatically."}
            </p>
          )}
        </div>
      </BlockContainer>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>Select Primary Persona</DialogTitle>
            <DialogDescription>
              Choose one persona or leave it unset.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="rounded-lg border p-3">
              <PersonaPicker
                owner={{ type: "user", id: entityId, name: "User" }}
                mode="select-single"
                variant="inline"
                layout="list"
                selected={primaryPersonaId}
                onSelect={(selected) => {
                  onContentChange?.({
                    ...content,
                    primaryPersonaId:
                      typeof selected === "string" ? selected : null,
                  })
                }}
              />
            </div>

            {config.allowUnset !== false && (
              <div className="flex justify-end">
                <Button
                  variant="outline"
                  onClick={() => {
                    onContentChange?.({
                      ...content,
                      primaryPersonaId: null,
                    })
                    setIsOpen(false)
                  }}
                >
                  Unset Primary Persona
                </Button>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
