// src/hooks/usePersonaLibrary.ts

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { PersonaLibraryOwner } from "@/components/Persona/types"
import { PersonaLibraryService } from "@/services/personaLibraryService"

interface UsePersonaLibraryOptions {
  owner: PersonaLibraryOwner
  enabled?: boolean
}

export function usePersonaLibrary({
  owner,
  enabled = true,
}: UsePersonaLibraryOptions) {
  const queryClient = useQueryClient()
  const queryKey = ["persona-library", owner.type, owner.id] as const

  const libraryQuery = useQuery({
    queryKey,
    queryFn: () => PersonaLibraryService.getLibrary(owner),
    enabled,
  })

  const addMutation = useMutation({
    mutationFn: ({
      personaId,
      nickname,
    }: {
      personaId: string
      nickname?: string
    }) => PersonaLibraryService.addToLibrary(owner, personaId, nickname),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({
      entryId,
      updates,
    }: {
      entryId: string
      updates: { nickname?: string | null; is_active?: boolean }
    }) => PersonaLibraryService.updateEntry(owner, entryId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey })
    },
  })

  const removeMutation = useMutation({
    mutationFn: (entryId: string) =>
      PersonaLibraryService.removeFromLibrary(owner, entryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey })
    },
  })

  return {
    // Data
    personas: libraryQuery.data ?? [],
    isLoading: libraryQuery.isLoading,
    error: libraryQuery.error,

    // Mutations
    addPersona: addMutation.mutate,
    updateEntry: updateMutation.mutate,
    removePersona: removeMutation.mutate,

    // Mutation states
    isAdding: addMutation.isPending,
    isUpdating: updateMutation.isPending,
    isRemoving: removeMutation.isPending,
  }
}
