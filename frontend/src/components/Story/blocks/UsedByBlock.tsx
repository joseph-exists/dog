// src/components/Page/blocks/UsedByBlock.tsx
import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { Crown, Smile } from "lucide-react"

import { UsedByService } from "@/services/usedByService"
import { BlockContainer } from "../primitives"

export interface UsedByBlockConfig {
  maxVisible?: number
}

export interface UsedByBlockProps {
  config: UsedByBlockConfig
  entityType?: string
  entityId?: string
  className?: string
}

/**
 * UsedByBlock - Displays archetypes and personas that reference this entity.
 *
 * Read-only block that performs reverse lookups via UsedByService.
 * Shows grouped lists with icons and links to entity detail pages.
 */
export function UsedByBlock({
  config,
  entityType,
  entityId,
  className,
}: UsedByBlockProps) {
  const { data, isLoading } = useQuery({
    queryKey: UsedByService.queryKey(entityType!, entityId!),
    queryFn: () => UsedByService.getUsedBy(entityType!, entityId!),
    enabled:
      !!entityType && !!entityId && UsedByService.isSupported(entityType!),
  })

  const { maxVisible = 10 } = config
  const archetypes = data?.archetypes ?? []
  const personas = data?.personas ?? []
  const totalCount = archetypes.length + personas.length

  if (isLoading) {
    return (
      <BlockContainer title="Used By" className={className}>
        <div className="p-4">
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-5 w-32 bg-muted animate-pulse rounded"
              />
            ))}
          </div>
        </div>
      </BlockContainer>
    )
  }

  if (totalCount === 0) {
    return (
      <BlockContainer title="Used By" className={className}>
        <div className="p-4">
          <p className="text-sm text-muted-foreground italic">
            Not used by any archetypes or personas yet.
          </p>
        </div>
      </BlockContainer>
    )
  }

  return (
    <BlockContainer title="Used By" className={className}>
      <div className="p-4 space-y-4">
        {archetypes.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
              Archetypes ({archetypes.length})
            </h4>
            <ul className="space-y-1.5">
              {archetypes.slice(0, maxVisible).map((item) => (
                <li key={item.id}>
                  <Link
                    to="/archetype/$archetypeId"
                    params={{ archetypeId: item.id }}
                    className="flex items-center gap-2 text-sm text-foreground hover:text-amber-600 transition-colors"
                  >
                    <Crown className="size-3.5 text-amber-500 shrink-0" />
                    <span>{item.name}</span>
                  </Link>
                </li>
              ))}
              {archetypes.length > maxVisible && (
                <li className="text-xs text-muted-foreground pl-5">
                  +{archetypes.length - maxVisible} more
                </li>
              )}
            </ul>
          </div>
        )}

        {personas.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
              Personas ({personas.length})
            </h4>
            <ul className="space-y-1.5">
              {personas.slice(0, maxVisible).map((item) => (
                <li key={item.id}>
                  <Link
                    to="/persona/$personaId"
                    params={{ personaId: item.id }}
                    className="flex items-center gap-2 text-sm text-foreground hover:text-pink-600 transition-colors"
                  >
                    <Smile className="size-3.5 text-pink-500 shrink-0" />
                    <span>{item.name}</span>
                  </Link>
                </li>
              ))}
              {personas.length > maxVisible && (
                <li className="text-xs text-muted-foreground pl-5">
                  +{personas.length - maxVisible} more
                </li>
              )}
            </ul>
          </div>
        )}
      </div>
    </BlockContainer>
  )
}
