// src/components/Page/blocks/PersonasBlock.tsx

import type { PersonaLibraryOwner } from "@/components/Persona"
import { PersonaPicker } from "@/components/Persona"
import { cn } from "@/lib/utils"
import { BlockContainer } from "../primitives"

export interface PersonasBlockConfig {
  layout: "list" | "grid"
  maxVisible: number
  showAddButton: boolean
}

export interface PersonasBlockProps {
  config: PersonasBlockConfig
  entityType: string
  entityId: string
  entityName?: string
  isEditing?: boolean
  className?: string
}

/**
 * PersonasBlock - Displays persona library inline on a Page.
 *
 * In view mode: browse-only display of persona library.
 * In edit mode: full management UI with add/edit/remove.
 */
export function PersonasBlock({
  config,
  entityType,
  entityId,
  entityName,
  isEditing = false,
  className,
}: PersonasBlockProps) {
  const owner: PersonaLibraryOwner = {
    type: entityType as "user" | "agent",
    id: entityId,
    name: entityName || (entityType === "user" ? "Your" : "Agent's"),
  }

  return (
    <BlockContainer title="Personas" className={cn(className)}>
      <div className="p-4">
        <PersonaPicker
          owner={owner}
          mode={isEditing ? "manage" : "browse"}
          variant="inline"
          layout={config.layout}
          maxVisible={config.maxVisible}
        />
      </div>
    </BlockContainer>
  )
}
