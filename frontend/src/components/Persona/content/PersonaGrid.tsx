// src/components/Persona/content/PersonaGrid.tsx
import { cn } from "@/lib/utils"
import { PersonaCard } from "../primitives"
import type { PersonaContentProps } from "../types"

export function PersonaGrid({
  personas,
  selectedIds,
  onSelect,
  onEditNickname,
  onRemove,
  showActions,
  className,
}: PersonaContentProps) {
  return (
    <div
      className={cn(
        "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 overflow-y-auto max-h-[400px]",
        className,
      )}
    >
      {personas.map((persona) => (
        <PersonaCard
          key={persona.libraryEntryId}
          persona={persona}
          isSelected={selectedIds.includes(persona.personaId)}
          onSelect={() => onSelect(persona.personaId)}
          onEditNickname={
            showActions && onEditNickname
              ? (nickname) => onEditNickname(persona.libraryEntryId, nickname)
              : undefined
          }
          onRemove={
            showActions && onRemove
              ? () => onRemove(persona.libraryEntryId)
              : undefined
          }
          readonly={!showActions}
        />
      ))}
    </div>
  )
}
