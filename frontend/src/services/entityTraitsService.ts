// src/services/entityTraitsService.ts

/**
 * Entity Traits Service
 *
 * Provides entity-type-aware trait operations via ViewModels.
 * Dispatches to the correct API client based on entityType.
 *
 * Supported entity types:
 * - "persona" → PersonaTraitsService
 * - "archetype" → ArchetypeTraitsService
 *
 * @example
 * ```ts
 * const traits = await EntityTraitsService.getTraits("persona", personaId)
 * ```
 */

import {
  ArchetypeTraitsService,
  PersonaTraitsService,
  QualityTraitLinksService,
} from "@/client"

// ============================================================================
// ViewModels
// ============================================================================

/** UI-optimized trait representation */
export interface TraitViewModel {
  id: string
  name: string
  description?: string
}

// ============================================================================
// Fetcher Registry
// ============================================================================

type TraitFetcher = (entityId: string) => Promise<TraitViewModel[]>
type TraitMutator = (entityId: string, traitId: string) => Promise<void>

const fetchers: Record<string, TraitFetcher> = {
  persona: async (entityId) => {
    const traits = await PersonaTraitsService.readPersonaTraits({
      personaId: entityId,
    })
    return traits.map((t) => ({
      id: t.id,
      name: t.name,
      description: t.description ?? undefined,
    }))
  },
  archetype: async (entityId) => {
    const traits = await ArchetypeTraitsService.readArchetypeTraits({
      archetypeId: entityId,
    })
    return traits.map((t) => ({
      id: t.id,
      name: t.name,
      description: t.description ?? undefined,
    }))
  },
  quality: async (entityId) => {
    const traits = await QualityTraitLinksService.readQualityTraits({
      qualityId: entityId,
    })
    return traits.map((t) => ({
      id: t.id,
      name: t.name,
      description: t.description ?? undefined,
    }))
  },
}

const adders: Record<string, TraitMutator> = {
  archetype: async (entityId, traitId) => {
    await ArchetypeTraitsService.addTraitToArchetype({
      archetypeId: entityId,
      traitId,
    })
  },
  quality: async (entityId, traitId) => {
    await QualityTraitLinksService.createQualityTraitLink({
      requestBody: { quality_id: entityId, trait_id: traitId },
    })
  },
}

const removers: Record<string, TraitMutator> = {
  archetype: async (entityId, traitId) => {
    await ArchetypeTraitsService.removeTraitFromArchetype({
      archetypeId: entityId,
      traitId,
    })
  },
  quality: async (entityId, traitId) => {
    await QualityTraitLinksService.deleteQualityTraitLink({
      qualityId: entityId,
      traitId,
    })
  },
}

// ============================================================================
// Service
// ============================================================================

export const EntityTraitsService = {
  /**
   * Fetch traits for an entity.
   * Returns empty array if entityType is unsupported.
   */
  async getTraits(
    entityType: string,
    entityId: string,
  ): Promise<TraitViewModel[]> {
    const fetcher = fetchers[entityType]
    if (!fetcher) return []
    return fetcher(entityId)
  },

  /**
   * Add a trait to an entity.
   * Only supported for entity types with write access (e.g., archetype).
   */
  async addTrait(
    entityType: string,
    entityId: string,
    traitId: string,
  ): Promise<void> {
    const adder = adders[entityType]
    if (!adder) {
      throw new Error(
        `addTrait not supported for entity type: ${entityType}`,
      )
    }
    return adder(entityId, traitId)
  },

  /**
   * Remove a trait from an entity.
   * Only supported for entity types with write access (e.g., archetype).
   */
  async removeTrait(
    entityType: string,
    entityId: string,
    traitId: string,
  ): Promise<void> {
    const remover = removers[entityType]
    if (!remover) {
      throw new Error(
        `removeTrait not supported for entity type: ${entityType}`,
      )
    }
    return remover(entityId, traitId)
  },

  /**
   * Whether the entity type supports write operations (add/remove).
   */
  isEditable(entityType: string): boolean {
    return entityType in adders
  },

  /**
   * TanStack Query key for entity traits.
   */
  queryKey(entityType: string, entityId: string) {
    return ["entity-traits", entityType, entityId] as const
  },
}
