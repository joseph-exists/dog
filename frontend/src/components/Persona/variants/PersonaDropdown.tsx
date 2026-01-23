// src/components/Persona/variants/PersonaDropdown.tsx
import { ChevronDown, Smile } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { cn } from "@/lib/utils"
import { PersonaEmpty, PersonaList, PersonaSearch } from "../content"
import { PersonaAvatar } from "../primitives"
import type { LibraryPersona, PersonaContentProps } from "../types"

interface PersonaDropdownProps extends PersonaContentProps {
  isOpen: boolean
  setIsOpen: (open: boolean) => void
  searchQuery: string
  setSearchQuery: (query: string) => void
  allPersonas: LibraryPersona[]
  trigger?: React.ReactNode
  placeholder?: string
}

export function PersonaDropdown({
  personas,
  selectedIds,
  selectionMode,
  onSelect,
  isOpen,
  setIsOpen,
  searchQuery,
  setSearchQuery,
  allPersonas,
  trigger,
  placeholder = "Select persona...",
  className,
}: PersonaDropdownProps) {
  const selectedPersona = allPersonas.find(
    (p) => p.personaId === selectedIds[0],
  )

  const defaultTrigger = (
    <Button
      variant="outline"
      className={cn("w-full justify-between", className)}
    >
      {selectedPersona ? (
        <span className="flex items-center gap-2">
          <PersonaAvatar name={selectedPersona.name} size="sm" />
          <span className="truncate">
            {selectedPersona.nickname || selectedPersona.name}
          </span>
        </span>
      ) : (
        <span className="flex items-center gap-2 text-muted-foreground">
          <Smile className="h-4 w-4" />
          {placeholder}
        </span>
      )}
      <ChevronDown className="h-4 w-4 shrink-0 opacity-50" />
    </Button>
  )

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>{trigger || defaultTrigger}</PopoverTrigger>
      <PopoverContent className="w-[280px] p-0" align="start">
        <div className="p-2 border-b">
          <PersonaSearch
            value={searchQuery}
            onChange={setSearchQuery}
            autoFocus
          />
        </div>
        {personas.length === 0 ? (
          <PersonaEmpty context={searchQuery ? "no-results" : "no-personas"} />
        ) : (
          <PersonaList
            personas={personas}
            selectedIds={selectedIds}
            selectionMode={selectionMode}
            onSelect={(id) => {
              onSelect(id)
              if (selectionMode === "radio") setIsOpen(false)
            }}
            showActions={false}
          />
        )}
      </PopoverContent>
    </Popover>
  )
}
