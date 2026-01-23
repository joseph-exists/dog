// src/components/Persona/variants/PersonaInline.tsx
import { cn } from "@/lib/utils"
import {
  PersonaEmpty,
  PersonaGrid,
  PersonaList,
  PersonaSearch,
} from "../content"
import type { PersonaContentProps } from "../types"

interface PersonaInlineProps extends PersonaContentProps {
  layout?: "list" | "grid"
  searchQuery: string
  setSearchQuery: (query: string) => void
  showSearch?: boolean
  maxVisible?: number
  onAddNew?: () => void
}

export function PersonaInline({
  personas,
  selectedIds,
  selectionMode,
  onSelect,
  onEditNickname,
  onRemove,
  showActions,
  layout = "grid",
  searchQuery,
  setSearchQuery,
  showSearch = true,
  maxVisible,
  onAddNew,
  className,
}: PersonaInlineProps) {
  const visiblePersonas = maxVisible ? personas.slice(0, maxVisible) : personas

  const ContentComponent = layout === "grid" ? PersonaGrid : PersonaList

  return (
    <div className={cn("space-y-3", className)}>
      {showSearch && personas.length > 3 && (
        <PersonaSearch value={searchQuery} onChange={setSearchQuery} />
      )}

      {visiblePersonas.length === 0 ? (
        <PersonaEmpty
          context={searchQuery ? "no-results" : "no-personas"}
          onAction={onAddNew}
        />
      ) : (
        <ContentComponent
          personas={visiblePersonas}
          selectedIds={selectedIds}
          selectionMode={selectionMode}
          onSelect={onSelect}
          onEditNickname={onEditNickname}
          onRemove={onRemove}
          showActions={showActions}
          className="max-h-none overflow-visible"
        />
      )}

      {maxVisible && personas.length > maxVisible && (
        <p className="text-xs text-muted-foreground text-center">
          +{personas.length - maxVisible} more
        </p>
      )}
    </div>
  )
}
