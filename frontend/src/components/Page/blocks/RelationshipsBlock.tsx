// src/components/Page/blocks/RelationshipsBlock.tsx
import { useMemo } from "react"
import { Plus } from "lucide-react"

import { Button } from "@/components/ui/button"
import { BlockContainer, EntityCard } from "../primitives"
import { getEntityType } from "../registry"

export interface RelatedEntity {
  id: string
  typeId: string
  name: string
  avatarUrl?: string
  badges?: string[]
  relationshipTypeId: string
}

export interface RelationshipsBlockConfig {
  groupByType: boolean
  maxVisible: number
}

export interface RelationshipsBlockProps {
  config: RelationshipsBlockConfig
  relationships: RelatedEntity[]
  canEdit?: boolean
  onAdd?: () => void
  onEntityClick?: (entity: RelatedEntity) => void
}

interface GroupedRelationships {
  typeId: string
  label: string
  entities: RelatedEntity[]
}

/**
 * RelationshipsBlock - Displays related entities in a grid
 *
 * Groups entities by type when config.groupByType is true.
 * Shows entity cards with optional click handling.
 * Supports edit mode with an Add button.
 */
export function RelationshipsBlock({
  config,
  relationships,
  canEdit = false,
  onAdd,
  onEntityClick,
}: RelationshipsBlockProps) {
  const { groups, visibleCount, totalCount } = useMemo(() => {
    if (relationships.length === 0) {
      return { groups: [], visibleCount: 0, totalCount: 0 }
    }

    const total = relationships.length
    const visible = Math.min(total, config.maxVisible)
    const limitedRelationships = relationships.slice(0, visible)

    if (!config.groupByType) {
      return {
        groups: [
          {
            typeId: "all",
            label: "Related",
            entities: limitedRelationships,
          },
        ],
        visibleCount: visible,
        totalCount: total,
      }
    }

    // Group by typeId
    const groupMap = new Map<string, RelatedEntity[]>()
    for (const entity of limitedRelationships) {
      const existing = groupMap.get(entity.typeId) || []
      existing.push(entity)
      groupMap.set(entity.typeId, existing)
    }

    const groupedResult: GroupedRelationships[] = []
    for (const [typeId, entities] of groupMap) {
      const entityType = getEntityType(typeId)
      groupedResult.push({
        typeId,
        label: entityType?.labelPlural || typeId,
        entities,
      })
    }

    return {
      groups: groupedResult,
      visibleCount: visible,
      totalCount: total,
    }
  }, [relationships, config.groupByType, config.maxVisible])

  const hasMore = totalCount > visibleCount

  const headerActions = canEdit ? (
    <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onAdd}>
      <Plus className="h-3.5 w-3.5" />
    </Button>
  ) : undefined

  // Empty state with edit capability
  if (relationships.length === 0 && canEdit) {
    return (
      <BlockContainer title="Relationships" headerActions={headerActions}>
        <div className="p-4 text-center">
          <p className="text-sm text-muted-foreground">
            No relationships yet. Click the + button to add one.
          </p>
        </div>
      </BlockContainer>
    )
  }

  // Empty state without edit capability
  if (relationships.length === 0) {
    return null
  }

  return (
    <BlockContainer title="Relationships" headerActions={headerActions}>
      <div className="p-4 space-y-4">
        {groups.map((group) => (
          <div key={group.typeId} className="space-y-2">
            {config.groupByType && (
              <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                {group.label} ({group.entities.length})
              </h4>
            )}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {group.entities.map((entity) => (
                <EntityCard
                  key={entity.id}
                  entity={{
                    id: entity.id,
                    typeId: entity.typeId,
                    name: entity.name,
                    avatarUrl: entity.avatarUrl,
                    badges: entity.badges,
                  }}
                  relationship={{ typeId: entity.relationshipTypeId }}
                  onClick={
                    onEntityClick ? () => onEntityClick(entity) : undefined
                  }
                  size="sm"
                />
              ))}
            </div>
          </div>
        ))}
        {hasMore && (
          <p className="text-sm text-muted-foreground text-center">
            +{totalCount - visibleCount} more
          </p>
        )}
      </div>
    </BlockContainer>
  )
}
