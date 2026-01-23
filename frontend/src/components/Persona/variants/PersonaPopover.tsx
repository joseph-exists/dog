// src/components/Persona/variants/PersonaPopover.tsx
import { Smile } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import {
  PersonaEmpty,
  PersonaGrid,
  PersonaList,
  PersonaSearch,
} from "../content"
import { PersonaAvatar } from "../primitives"
import type { LibraryPersona, PersonaContentProps } from "../types"

interface PersonaPopoverProps extends PersonaContentProps {
  isOpen: boolean
  setIsOpen: (open: boolean) => void
  searchQuery: string
  setSearchQuery: (query: string) => void
  allPersonas: LibraryPersona[]
  layout?: "list" | "grid"
  trigger?: React.ReactNode
  placeholder?: string
}

export function PersonaPopover({
  personas,
  selectedIds,
  selectionMode,
  onSelect,
  onEditNickname,
  onRemove,
  showActions,
  isOpen,
  setIsOpen,
  searchQuery,
  setSearchQuery,
  allPersonas,
  layout = "list",
  trigger,
  placeholder = "Select persona...",
}: PersonaPopoverProps) {
  const selectedPersona = allPersonas.find(
    (p) => p.personaId === selectedIds[0],
  )

  const defaultTrigger = (
    <Button variant="outline" className="gap-2">
      {selectedPersona ? (
        <>
          <PersonaAvatar name={selectedPersona.name} size="sm" />
          <span>{selectedPersona.nickname || selectedPersona.name}</span>
        </>
      ) : (
        <>
          <Smile className="h-4 w-4" />
          {placeholder}
        </>
      )}
    </Button>
  )

  const ContentComponent = layout === "grid" ? PersonaGrid : PersonaList

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>{trigger || defaultTrigger}</PopoverTrigger>
      <PopoverContent className="w-[400px] p-0" align="start">
        <div className="p-3 border-b">
          <PersonaSearch
            value={searchQuery}
            onChange={setSearchQuery}
            autoFocus
          />
        </div>
        <div className="p-3">
          {personas.length === 0 ? (
            <PersonaEmpty
              context={searchQuery ? "no-results" : "no-personas"}
            />
          ) : (
            <ContentComponent
              personas={personas}
              selectedIds={selectedIds}
              selectionMode={selectionMode}
              onSelect={onSelect}
              onEditNickname={onEditNickname}
              onRemove={onRemove}
              showActions={showActions}
            />
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}
