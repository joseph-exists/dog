// src/services/personaLibraryService.ts

import type {
  AgentPersonaPublic,
  Persona,
  PersonaPublic,
  UserPersonaPublic,
} from "@/client"
import {
  AgentPersonasService,
  PersonasService,
  UserPersonasService,
} from "@/client"
import type {
  LibraryPersona,
  PersonaLibraryOwner,
} from "@/components/Persona/types"

// ============================================================================
// Transformation
// ============================================================================

function toLibraryPersona(
  entry: UserPersonaPublic | AgentPersonaPublic,
  persona: Persona,
  ownerType: "user" | "agent",
): LibraryPersona {
  const ownerId =
    ownerType === "user"
      ? (entry as UserPersonaPublic).user_id
      : (entry as AgentPersonaPublic).agent_id

  return {
    libraryEntryId: entry.id,
    ownerId,
    ownerType,
    personaId: entry.persona_id,
    name: persona.name,
    nickname: entry.nickname ?? null,
    description: persona.description ?? null,
    isActive: entry.is_active ?? true,
    longDescription: persona.long_description ?? null,
    domains: [persona.general_domain, persona.specific_domain].filter(
      Boolean,
    ) as string[],
  }
}

// ============================================================================
// Service
// ============================================================================

export const PersonaLibraryService = {
  /**
   * Fetch the full library for an owner.
   * Joins junction entries with persona data.
   */
  async getLibrary(owner: PersonaLibraryOwner): Promise<LibraryPersona[]> {
    // 1. Fetch junction entries
    let entries: (UserPersonaPublic | AgentPersonaPublic)[]

    if (owner.type === "user") {
      const result = await UserPersonasService.readUserPersonas({ limit: 100 })
      entries = result.data
    } else {
      const result = await AgentPersonasService.readAgentPersonas({
        agentId: owner.id,
        limit: 100,
      })
      entries = result.data
    }

    if (entries.length === 0) return []

    // 2. Fetch all persona details in batch
    const personaIds = [...new Set(entries.map((e) => e.persona_id))]
    const personaMap = new Map<string, Persona>()

    // Fetch personas individually (no batch endpoint available)
    const personaPromises = personaIds.map(async (id) => {
      try {
        const persona = await PersonasService.readPersona({ id })
        personaMap.set(id, persona)
      } catch {
        // Skip personas that can't be fetched
      }
    })
    await Promise.all(personaPromises)

    // 3. Join and transform
    return entries
      .filter((entry) => personaMap.has(entry.persona_id))
      .map((entry) =>
        toLibraryPersona(entry, personaMap.get(entry.persona_id)!, owner.type),
      )
  },

  /**
   * Add a persona to the library.
   */
  async addToLibrary(
    owner: PersonaLibraryOwner,
    personaId: string,
    nickname?: string,
  ): Promise<LibraryPersona> {
    let entry: UserPersonaPublic | AgentPersonaPublic

    if (owner.type === "user") {
      entry = await UserPersonasService.createUserPersona({
        requestBody: { persona_id: personaId, nickname },
      })
    } else {
      entry = await AgentPersonasService.createAgentPersona({
        agentId: owner.id,
        requestBody: { persona_id: personaId, nickname },
      })
    }

    const persona = await PersonasService.readPersona({ id: personaId })
    return toLibraryPersona(entry, persona, owner.type)
  },

  /**
   * Update a library entry (nickname, is_active).
   */
  async updateEntry(
    owner: PersonaLibraryOwner,
    entryId: string,
    updates: { nickname?: string | null; is_active?: boolean },
  ): Promise<void> {
    if (owner.type === "user") {
      await UserPersonasService.updateUserPersona({
        id: entryId,
        requestBody: updates,
      })
    } else {
      await AgentPersonasService.updateAgentPersona({
        agentId: owner.id,
        id: entryId,
        requestBody: updates,
      })
    }
  },

  /**
   * Remove a persona from the library.
   */
  async removeFromLibrary(
    owner: PersonaLibraryOwner,
    entryId: string,
  ): Promise<void> {
    if (owner.type === "user") {
      await UserPersonasService.deleteUserPersona({ id: entryId })
    } else {
      await AgentPersonasService.deleteAgentPersona({
        agentId: owner.id,
        id: entryId,
      })
    }
  },

  /**
   * Fetch all available personas (for adding new ones).
   */
  async getAvailablePersonas(): Promise<PersonaPublic[]> {
    const result = await PersonasService.readPersonas({ limit: 100 })
    return result.data
  },
}
