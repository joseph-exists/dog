// src/components/Persona/content/PersonaList.tsx
import { cn } from "@/lib/utils"
import { PersonaItem } from "../primitives"
import type { PersonaContentProps } from "../types"

export function PersonaList({
  personas,
  selectedIds,
  selectionMode,
  onSelect,
  onEditNickname,
  onRemove,
  showActions,
  className,
}: PersonaContentProps) {
  return (
    <div
      className={cn("space-y-1 overflow-y-auto max-h-[300px]", className)}
      role="listbox"
      aria-multiselectable={selectionMode === "checkbox"}
    >
      {personas.map((persona) => (
        <PersonaItem
          key={persona.libraryEntryId}
          persona={persona}
          isSelected={selectedIds.includes(persona.personaId)}
          selectionMode={selectionMode}
          onSelect={() => onSelect(persona.personaId)}
          onEdit={
            onEditNickname
              ? () =>
                  onEditNickname(persona.libraryEntryId, persona.nickname || "")
              : undefined
          }
          onRemove={
            onRemove ? () => onRemove(persona.libraryEntryId) : undefined
          }
          showActions={showActions}
        />
      ))}
    </div>
  )
}
