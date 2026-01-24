// src/components/Page/editor/forms/QualitiesForm.tsx

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Check, Loader2 } from "lucide-react"
import { QualitiesService } from "@/client"
import type { QualitiesBlockConfig } from "@/components/Page/blocks"
import { Button } from "@/components/ui/button"
import { EntityQualitiesService } from "@/services/entityQualitiesService"

interface QualitiesFormProps {
  config: QualitiesBlockConfig
  entityType: string
  entityId: string
  onClose: () => void
}

/**
 * QualitiesForm - Entity-type-aware quality toggle editor
 *
 * Fetches all available qualities and shows which are assigned to the entity.
 * Dispatches add/remove via EntityQualitiesService based on entityType.
 * Toggles happen immediately via API calls (no page content save needed).
 */
export function QualitiesForm({
  config: _config,
  entityType,
  entityId,
  onClose,
}: QualitiesFormProps) {
  const queryClient = useQueryClient()

  /** All available qualities in the system */
  const { data: allQualities, isLoading: loadingAll } = useQuery({
    queryKey: ["qualities"],
    queryFn: () => QualitiesService.readQualities({ limit: 100 }),
  })

  /** Qualities currently assigned to this entity */
  const { data: assignedQualities, isLoading: loadingAssigned } = useQuery({
    queryKey: EntityQualitiesService.queryKey(entityType, entityId),
    queryFn: () =>
      EntityQualitiesService.getQualities(entityType, entityId),
  })

  const addMutation = useMutation({
    mutationFn: (qualityId: string) =>
      EntityQualitiesService.addQuality(entityType, entityId, qualityId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: EntityQualitiesService.queryKey(entityType, entityId),
      })
    },
  })

  const removeMutation = useMutation({
    mutationFn: (qualityId: string) =>
      EntityQualitiesService.removeQuality(entityType, entityId, qualityId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: EntityQualitiesService.queryKey(entityType, entityId),
      })
    },
  })

  const isLoading = loadingAll || loadingAssigned
  const qualities = allQualities?.data ?? []
  const assignedIds = new Set(assignedQualities?.map((q) => q.id) ?? [])

  /** Toggle a quality on or off for this entity */
  const handleToggle = (quality: { id: string; name: string; description?: string | null }) => {
    if (assignedIds.has(quality.id)) {
      removeMutation.mutate(quality.id)
    } else {
      addMutation.mutate(quality.id)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (qualities.length === 0) {
    return (
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground text-center py-4">
          No qualities available. Create qualities first via the Qualities
          management page.
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
        Toggle qualities on or off for this {entityType}. Changes are saved
        immediately.
      </p>

      <div className="space-y-1 max-h-[400px] overflow-y-auto">
        {qualities.map((quality) => {
          const isAssigned = assignedIds.has(quality.id)
          const isPending = addMutation.isPending || removeMutation.isPending

          return (
            <button
              key={quality.id}
              type="button"
              onClick={() => handleToggle(quality)}
              disabled={isPending}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-left hover:bg-accent transition-colors disabled:opacity-50"
            >
              <div
                className={`flex h-5 w-5 shrink-0 items-center justify-center rounded border ${
                  isAssigned
                    ? "bg-purple-600 border-purple-600 text-white"
                    : "border-muted-foreground/30"
                }`}
              >
                {isAssigned && <Check className="h-3 w-3" />}
              </div>
              <div className="min-w-0 flex-1">
                <span className="text-sm font-medium">{quality.name}</span>
                {quality.description && (
                  <p className="text-xs text-muted-foreground truncate">
                    {quality.description}
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
