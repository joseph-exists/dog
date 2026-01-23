// src/components/Persona/variants/PersonaSheet.tsx
import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetContent,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { PersonaEmpty, PersonaGrid, PersonaSearch } from "../content"
import type { PersonaContentProps } from "../types"

interface PersonaSheetProps extends PersonaContentProps {
  isOpen: boolean
  setIsOpen: (open: boolean) => void
  searchQuery: string
  setSearchQuery: (query: string) => void
  title?: string
  onAddNew?: () => void
}

export function PersonaSheet({
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
  title = "Persona Library",
  onAddNew,
}: PersonaSheetProps) {
  return (
    <Sheet open={isOpen} onOpenChange={setIsOpen}>
      <SheetContent
        side="right"
        className="w-[400px] sm:w-[540px] flex flex-col"
      >
        <SheetHeader>
          <SheetTitle>{title}</SheetTitle>
        </SheetHeader>

        <div className="py-3">
          <PersonaSearch
            value={searchQuery}
            onChange={setSearchQuery}
            autoFocus
          />
        </div>

        <div className="flex-1 overflow-y-auto">
          {personas.length === 0 ? (
            <PersonaEmpty
              context={searchQuery ? "no-results" : "no-personas"}
              onAction={onAddNew}
            />
          ) : (
            <PersonaGrid
              personas={personas}
              selectedIds={selectedIds}
              selectionMode={selectionMode}
              onSelect={onSelect}
              onEditNickname={onEditNickname}
              onRemove={onRemove}
              showActions={showActions}
              className="max-h-none"
            />
          )}
        </div>

        <SheetFooter className="pt-4 border-t">
          <Button variant="outline" onClick={() => setIsOpen(false)}>
            Done
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}
