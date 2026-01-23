// src/components/Persona/PersonaPicker.tsx
import { usePersonaPicker } from "@/hooks/usePersonaPicker"
import type { PersonaPickerProps } from "./types"
import {
  PersonaDropdown,
  PersonaInline,
  PersonaPopover,
  PersonaSheet,
} from "./variants"

/**
 * PersonaPicker - Unified persona selection component.
 *
 * Routes to the correct variant shell based on the `variant` prop.
 * Uses usePersonaPicker hook for all state management.
 */
export function PersonaPicker({
  owner,
  mode,
  variant,
  selected,
  onSelect,
  filter,
  layout = "list",
  maxVisible,
  className,
  trigger,
  placeholder,
}: PersonaPickerProps) {
  const picker = usePersonaPicker({
    owner,
    mode,
    initialSelected: selected,
    filter,
  })

  // Sync external selection changes
  const handleSelect = (personaId: string) => {
    picker.selectPersona(personaId)
    if (mode === "select-single") {
      onSelect?.(personaId)
    } else if (mode === "select-multiple") {
      const newSelected = picker.selectedIds.includes(personaId)
        ? picker.selectedIds.filter((id) => id !== personaId)
        : [...picker.selectedIds, personaId]
      onSelect?.(newSelected)
    }
  }

  const handleEditNickname = (entryId: string, nickname: string) => {
    picker.updateEntry({ entryId, updates: { nickname } })
  }

  const handleRemove = (entryId: string) => {
    picker.removePersona(entryId)
  }

  // Shared content props
  const contentProps = {
    personas: picker.personas,
    selectedIds: picker.selectedIds,
    selectionMode: picker.selectionMode,
    onSelect: handleSelect,
    onEditNickname: picker.showActions ? handleEditNickname : undefined,
    onRemove: picker.showActions ? handleRemove : undefined,
    showActions: picker.showActions,
  }

  switch (variant) {
    case "dropdown":
      return (
        <PersonaDropdown
          {...contentProps}
          isOpen={picker.isOpen}
          setIsOpen={picker.setIsOpen}
          searchQuery={picker.searchQuery}
          setSearchQuery={picker.setSearchQuery}
          allPersonas={picker.allPersonas}
          trigger={trigger}
          placeholder={placeholder}
          className={className}
        />
      )

    case "popover":
      return (
        <PersonaPopover
          {...contentProps}
          isOpen={picker.isOpen}
          setIsOpen={picker.setIsOpen}
          searchQuery={picker.searchQuery}
          setSearchQuery={picker.setSearchQuery}
          allPersonas={picker.allPersonas}
          layout={layout}
          trigger={trigger}
          placeholder={placeholder}
        />
      )

    case "sheet":
      return (
        <PersonaSheet
          {...contentProps}
          isOpen={picker.isOpen}
          setIsOpen={picker.setIsOpen}
          searchQuery={picker.searchQuery}
          setSearchQuery={picker.setSearchQuery}
          title={`${owner.name}'s Personas`}
        />
      )

    case "inline":
      return (
        <PersonaInline
          {...contentProps}
          layout={layout}
          searchQuery={picker.searchQuery}
          setSearchQuery={picker.setSearchQuery}
          maxVisible={maxVisible}
          className={className}
        />
      )
  }
}
