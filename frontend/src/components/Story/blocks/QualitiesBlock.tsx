// src/components/Page/blocks/QualitiesBlock.tsx
import { useQuery } from "@tanstack/react-query"
import { Gem } from "lucide-react"

import { EntityQualitiesService } from "@/services/entityQualitiesService"
import { BlockContainer } from "../primitives"

export interface QualitiesBlockConfig {
  layout?: "badges" | "list"
  maxVisible?: number
}

export interface QualityItem {
  id: string
  label: string
  description?: string
}

export interface QualitiesContent {
  items: QualityItem[]
}

export interface QualitiesBlockProps {
  config: QualitiesBlockConfig
  content?: QualitiesContent
  entityType?: string
  entityId?: string
  className?: string
}

/**
 * QualitiesBlock - Displays entity qualities as badges or list items.
 *
 * Uses EntityQualitiesService to fetch quality data for any supported entity type.
 * Falls back to static content.items if no entity context or API returns empty.
 */
export function QualitiesBlock({
  config,
  content,
  entityType,
  entityId,
  className,
}: QualitiesBlockProps) {
  const { data: apiQualities } = useQuery({
    queryKey: EntityQualitiesService.queryKey(entityType!, entityId!),
    queryFn: () => EntityQualitiesService.getQualities(entityType!, entityId!),
    enabled: !!entityType && !!entityId,
  })

  // API qualities take priority; fall back to static content
  const items: QualityItem[] =
    apiQualities && apiQualities.length > 0
      ? apiQualities.map((q) => ({
          id: q.id,
          label: q.name,
          description: q.description ?? undefined,
        }))
      : (content?.items ?? [])

  const { layout = "badges", maxVisible = 12 } = config

  if (!items.length) {
    return (
      <BlockContainer title="Qualities" className={className}>
        <div className="p-4">
          <p className="text-sm text-muted-foreground italic">
            No qualities assigned yet.
          </p>
        </div>
      </BlockContainer>
    )
  }
  const visibleItems = items.slice(0, maxVisible)
  const hiddenCount = items.length - visibleItems.length

  if (layout === "list") {
    return (
      <BlockContainer title="Qualities" className={className}>
        <div className="p-4">
          <ul className="space-y-1.5">
            {visibleItems.map((quality) => (
              <li
                key={quality.id}
                className="text-sm text-foreground flex items-center gap-2"
              >
                <Gem className="size-3 text-purple-500 shrink-0" />
                <span>{quality.label}</span>
                {quality.description && (
                  <span className="text-xs text-muted-foreground truncate">
                    — {quality.description}
                  </span>
                )}
              </li>
            ))}
          </ul>
          {hiddenCount > 0 && (
            <p className="mt-2 text-xs text-muted-foreground">
              +{hiddenCount} more
            </p>
          )}
        </div>
      </BlockContainer>
    )
  }

  // Badge layout (default)
  return (
    <BlockContainer title="Qualities" className={className}>
      <div className="p-4">
        <div className="flex flex-wrap gap-2">
          {visibleItems.map((quality) => (
            <span
              key={quality.id}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300"
              title={quality.description}
            >
              <Gem className="size-3" />
              {quality.label}
            </span>
          ))}
          {hiddenCount > 0 && (
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground">
              +{hiddenCount} more
            </span>
          )}
        </div>
      </div>
    </BlockContainer>
  )
}
