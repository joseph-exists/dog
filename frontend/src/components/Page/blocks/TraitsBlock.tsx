// src/components/Page/blocks/TraitsBlock.tsx
import { useQuery } from "@tanstack/react-query"

import { PersonaTraitsService } from "@/client"
import { BlockContainer } from "../primitives"

export interface TraitsBlockConfig {
  layout?: "badges" | "list"
  maxVisible?: number
}

export interface TraitItem {
  id: string
  label: string
  category?: string
}

export interface TraitsContent {
  items: TraitItem[]
}

export interface TraitsBlockProps {
  config: TraitsBlockConfig
  content?: TraitsContent
  entityId?: string
  className?: string
}

/**
 * TraitsBlock - Displays personality traits as badges or list items.
 *
 * When entityId is provided, fetches real trait data from the
 * persona-traits API. Falls back to static content.items if no
 * entity context or if the API returns no data.
 */
export function TraitsBlock({
  config,
  content,
  entityId,
  className,
}: TraitsBlockProps) {
  const { data: apiTraits } = useQuery({
    queryKey: ["persona-traits", entityId],
    queryFn: () =>
      PersonaTraitsService.readPersonaTraits({ personaId: entityId! }),
    enabled: !!entityId,
  })

  // API traits take priority; fall back to static content
  const items: TraitItem[] =
    apiTraits && apiTraits.length > 0
      ? apiTraits.map((t) => ({ id: t.id, label: t.name, category: undefined }))
      : (content?.items ?? [])

  if (!items.length) {
    return null
  }

  const { layout = "badges", maxVisible = 12 } = config
  const visibleItems = items.slice(0, maxVisible)
  const hiddenCount = items.length - visibleItems.length

  if (layout === "list") {
    return (
      <BlockContainer title="Traits & Qualities" className={className}>
        <div className="p-4">
          <ul className="space-y-1.5">
            {visibleItems.map((trait) => (
              <li
                key={trait.id}
                className="text-sm text-foreground flex items-center gap-2"
              >
                <span className="size-1.5 rounded-full bg-pink-400 shrink-0" />
                <span>{trait.label}</span>
                {trait.category && (
                  <span className="text-xs text-muted-foreground">
                    ({trait.category})
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
    <BlockContainer title="Traits & Qualities" className={className}>
      <div className="p-4">
        <div className="flex flex-wrap gap-2">
          {visibleItems.map((trait) => (
            <span
              key={trait.id}
              className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-300"
              title={trait.category ? `Category: ${trait.category}` : undefined}
            >
              {trait.label}
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
