// src/components/Page/blocks/QualitiesBlock.tsx
import { useQuery } from "@tanstack/react-query"
import { Gem } from "lucide-react"

import { PersonaQualitiesService } from "@/client"
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
  entityId?: string
  className?: string
}

/**
 * QualitiesBlock - Displays persona qualities as badges or list items.
 *
 * When entityId is provided, fetches enabled qualities from the
 * persona-qualities API. Falls back to static content.items if
 * no entity context or if the API returns no data.
 */
export function QualitiesBlock({
  config,
  content,
  entityId,
  className,
}: QualitiesBlockProps) {
  const { data: apiQualities } = useQuery({
    queryKey: ["persona-qualities", entityId],
    queryFn: () =>
      PersonaQualitiesService.readPersonaQualities({ personaId: entityId! }),
    enabled: !!entityId,
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

  if (!items.length) {
    return null
  }

  const { layout = "badges", maxVisible = 12 } = config
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
