// src/hooks/usePersonaPicker.ts

import { useCallback, useMemo, useState } from "react"
import type {
  PersonaFilter,
  PersonaLibraryOwner,
  PersonaPickerMode,
} from "@/components/Persona/types"
import { usePersonaLibrary } from "./usePersonaLibrary"

interface UsePersonaPickerOptions {
  owner: PersonaLibraryOwner
  mode: PersonaPickerMode
  initialSelected?: string | string[] | null
  filter?: PersonaFilter
}

export function usePersonaPicker({
  owner,
  mode,
  initialSelected,
  filter: externalFilter,
}: UsePersonaPickerOptions) {
  const library = usePersonaLibrary({ owner })

  // Selection state
  const [selectedIds, setSelectedIds] = useState<string[]>(() => {
    if (!initialSelected) return []
    return Array.isArray(initialSelected) ? initialSelected : [initialSelected]
  })

  // Search state
  const [searchQuery, setSearchQuery] = useState("")

  // UI state
  const [isOpen, setIsOpen] = useState(false)

  // Filter personas
  const filteredPersonas = useMemo(() => {
    let result = library.personas

    // Apply active filter
    if (externalFilter?.isActive !== undefined) {
      result = result.filter((p) => p.isActive === externalFilter.isActive)
    }

    // Apply domain filter
    if (externalFilter?.domains?.length) {
      result = result.filter((p) =>
        p.domains?.some((d) => externalFilter.domains!.includes(d)),
      )
    }

    // Apply search
    const query = (externalFilter?.searchQuery || searchQuery)
      .toLowerCase()
      .trim()
    if (query) {
      result = result.filter(
        (p) =>
          p.name.toLowerCase().includes(query) ||
          p.nickname?.toLowerCase().includes(query) ||
          p.description?.toLowerCase().includes(query),
      )
    }

    return result
  }, [library.personas, externalFilter, searchQuery])

  // Selection helpers
  const selectPersona = useCallback(
    (personaId: string) => {
      if (mode === "select-single") {
        const newSelected = selectedIds[0] === personaId ? [] : [personaId]
        setSelectedIds(newSelected)
      } else if (mode === "select-multiple") {
        setSelectedIds((prev) =>
          prev.includes(personaId)
            ? prev.filter((id) => id !== personaId)
            : [...prev, personaId],
        )
      }
    },
    [mode, selectedIds],
  )

  const clearSelection = useCallback(() => {
    setSelectedIds([])
  }, [])

  // Derive selection mode for UI
  const selectionMode = useMemo(() => {
    if (mode === "browse") return "none" as const
    if (mode === "manage") return "none" as const
    if (mode === "select-single") return "radio" as const
    return "checkbox" as const
  }, [mode])

  return {
    // Library data
    personas: filteredPersonas,
    allPersonas: library.personas,
    isLoading: library.isLoading,
    error: library.error,

    // Selection
    selectedIds,
    selectPersona,
    clearSelection,
    selectionMode,

    // Search
    searchQuery,
    setSearchQuery,

    // UI
    isOpen,
    setIsOpen,

    // Library mutations (pass through)
    addPersona: library.addPersona,
    updateEntry: library.updateEntry,
    removePersona: library.removePersona,
    isAdding: library.isAdding,
    isUpdating: library.isUpdating,
    isRemoving: library.isRemoving,

    // Mode
    mode,
    showActions: mode === "manage",
    readonly: mode === "browse",
  }
}
