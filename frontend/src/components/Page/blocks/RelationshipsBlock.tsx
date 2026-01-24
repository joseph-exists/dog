// src/components/Page/blocks/RelationshipsBlock.tsx

import { useMemo } from "react"

import { BlockContainer, EntityCard } from "../primitives"
import { getEntityType } from "../registry"

export interface RelationshipItem {
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

export interface RelationshipsContent {
  items: RelationshipItem[]
}

export interface RelationshipsBlockProps {
  config: RelationshipsBlockConfig
  content?: RelationshipsContent
  className?: string
  onEntityClick?: (entity: RelationshipItem) => void
}

interface GroupedRelationships {
  typeId: string
  label: string
  entities: RelationshipItem[]
}

/**
 * RelationshipsBlock - Displays related entities in a grid
 *
 * Groups entities by type when config.groupByType is true.
 * Shows entity cards with optional click handling.
 * Returns null if no relationships exist.
 * View-only block - no edit functionality.
 */
export function RelationshipsBlock({
  config,
  content,
  className,
  onEntityClick,
}: RelationshipsBlockProps) {
  const relationships = content?.items || []

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
    const groupMap = new Map<string, RelationshipItem[]>()
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

  // Empty state — show placeholder so block is visible in edit mode
  if (relationships.length === 0) {
    return (
      <BlockContainer title="Relationships" className={className}>
        <div className="p-4">
          <p className="text-sm text-muted-foreground italic">
            No relationships yet.
          </p>
        </div>
      </BlockContainer>
    )
  }

  return (
    <BlockContainer title="Relationships" className={className}>
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
