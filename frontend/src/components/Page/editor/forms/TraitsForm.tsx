// src/components/Page/editor/forms/TraitsForm.tsx

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Check, Info, Loader2 } from "lucide-react"
import { TraitsService } from "@/client"
import type { TraitsBlockConfig } from "@/components/Page/blocks"
import { Button } from "@/components/ui/button"
import { EntityTraitsService } from "@/services/entityTraitsService"

interface TraitsFormProps {
  config: TraitsBlockConfig
  entityType: string
  entityId: string
  onClose: () => void
}

/**
 * TraitsForm - Entity-type-aware traits editor
 *
 * For editable entity types (e.g. archetype): shows toggle UI to add/remove traits.
 * For read-only entity types (e.g. persona): shows inherited traits with info note.
 * Dispatches via EntityTraitsService based on entityType.
 */
export function TraitsForm({
  config: _config,
  entityType,
  entityId,
  onClose,
}: TraitsFormProps) {
  const queryClient = useQueryClient()
  const editable = EntityTraitsService.isEditable(entityType)

  /** Traits currently assigned to this entity */
  const { data: assignedTraits, isLoading: loadingAssigned } = useQuery({
    queryKey: EntityTraitsService.queryKey(entityType, entityId),
    queryFn: () => EntityTraitsService.getTraits(entityType, entityId),
  })

  /** All available traits (only fetched when editable) */
  const { data: allTraits, isLoading: loadingAll } = useQuery({
    queryKey: ["traits"],
    queryFn: () => TraitsService.readTraits({ limit: 100 }),
    enabled: editable,
  })

  const addMutation = useMutation({
    mutationFn: (traitId: string) =>
      EntityTraitsService.addTrait(entityType, entityId, traitId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: EntityTraitsService.queryKey(entityType, entityId),
      })
    },
  })

  const removeMutation = useMutation({
    mutationFn: (traitId: string) =>
      EntityTraitsService.removeTrait(entityType, entityId, traitId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: EntityTraitsService.queryKey(entityType, entityId),
      })
    },
  })

  const isLoading = loadingAssigned || (editable && loadingAll)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    )
  }

  const traitList = assignedTraits ?? []
  const assignedIds = new Set(traitList.map((t) => t.id))

  // Editable mode: toggle UI (used for archetypes)
  if (editable) {
    const traits = allTraits?.data ?? []

    /** Toggle a trait on or off for this entity */
    const handleToggle = (trait: { id: string }) => {
      if (assignedIds.has(trait.id)) {
        removeMutation.mutate(trait.id)
      } else {
        addMutation.mutate(trait.id)
      }
    }

    if (traits.length === 0) {
      return (
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground text-center py-4">
            No traits available. Create traits first via the Traits management
            page.
          </p>
          <div className="flex justify-end">
            <Button type="button" variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      )
    }

    return (
      <div className="space-y-4">
        <p className="text-xs text-muted-foreground">
          Toggle traits on or off for this {entityType}. Changes are saved
          immediately.
        </p>

        <div className="space-y-1 max-h-[400px] overflow-y-auto">
          {traits.map((trait) => {
            const isAssigned = assignedIds.has(trait.id)
            const isPending = addMutation.isPending || removeMutation.isPending

            return (
              <button
                key={trait.id}
                type="button"
                onClick={() => handleToggle(trait)}
                disabled={isPending}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-left hover:bg-accent transition-colors disabled:opacity-50"
              >
                <div
                  className={`flex h-5 w-5 shrink-0 items-center justify-center rounded border ${
                    isAssigned
                      ? "bg-pink-600 border-pink-600 text-white"
                      : "border-muted-foreground/30"
                  }`}
                >
                  {isAssigned && <Check className="h-3 w-3" />}
                </div>
                <div className="min-w-0 flex-1">
                  <span className="text-sm font-medium">{trait.name}</span>
                  {trait.description && (
                    <p className="text-xs text-muted-foreground truncate">
                      {trait.description}
                    </p>
                  )}
                </div>
              </button>
            )
          })}
        </div>

        <div className="flex justify-end pt-4">
          <Button type="button" onClick={onClose}>
            Done
          </Button>
        </div>
      </div>
    )
  }

  // Read-only mode: inherited traits (used for personas)
  return (
    <div className="space-y-4">
      <div className="flex items-start gap-2 p-3 rounded-md bg-muted/50">
        <Info className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
        <p className="text-xs text-muted-foreground">
          Traits are inherited from the {entityType}'s archetype and cannot be
          edited directly. To change traits, assign a different archetype.
        </p>
      </div>

      {traitList.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-4">
          No traits assigned. Assign an archetype to inherit traits.
        </p>
      ) : (
        <div className="space-y-1">
          {traitList.map((trait) => (
            <div
              key={trait.id}
              className="flex items-center gap-2 px-3 py-2 rounded-md bg-accent/50"
            >
              <span className="size-1.5 rounded-full bg-pink-400 shrink-0" />
              <span className="text-sm">{trait.name}</span>
              {trait.description && (
                <span className="text-xs text-muted-foreground truncate ml-auto">
                  {trait.description}
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="flex justify-end pt-4">
        <Button type="button" onClick={onClose}>
          Close
        </Button>
      </div>
    </div>
  )
}
