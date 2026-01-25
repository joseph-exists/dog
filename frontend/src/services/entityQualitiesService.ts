// src/services/entityQualitiesService.ts

/**
 * Entity Qualities Service
 *
 * Provides entity-type-aware quality operations via ViewModels.
 * Dispatches to the correct API client based on entityType.
 *
 * Supported entity types:
 * - "persona" → PersonaQualitiesService
 * - "archetype" → ArchetypeQualitiesService
 *
 * @example
 * ```ts
 * const qualities = await EntityQualitiesService.getQualities("persona", personaId)
 * await EntityQualitiesService.addQuality("persona", personaId, qualityId)
 * ```
 */

import {
  ArchetypeQualitiesService,
  PersonaQualitiesService,
  QualityTraitLinksService,
} from "@/client"

// ============================================================================
// ViewModels
// ============================================================================

/** UI-optimized quality representation */
export interface QualityViewModel {
  id: string
  name: string
  description?: string
}

// ============================================================================
// Fetcher Registry
// ============================================================================

type QualityFetcher = (entityId: string) => Promise<QualityViewModel[]>
type QualityMutator = (entityId: string, qualityId: string) => Promise<void>

const fetchers: Record<string, QualityFetcher> = {
  persona: async (entityId) => {
    const qualities = await PersonaQualitiesService.readPersonaQualities({
      personaId: entityId,
    })
    return qualities.map((q) => ({
      id: q.id,
      name: q.name,
      description: q.description ?? undefined,
    }))
  },
  archetype: async (entityId) => {
    const qualities = await ArchetypeQualitiesService.readArchetypeQualities({
      archetypeId: entityId,
    })
    return qualities.map((q) => ({
      id: q.id,
      name: q.name,
      description: q.description ?? undefined,
    }))
  },
  trait: async (entityId) => {
    const qualities = await QualityTraitLinksService.readTraitQualities({
      traitId: entityId,
    })
    return qualities.map((q) => ({
      id: q.id,
      name: q.name,
      description: q.description ?? undefined,
    }))
  },
}

const adders: Record<string, QualityMutator> = {
  persona: async (entityId, qualityId) => {
    await PersonaQualitiesService.addQualityToPersona({
      personaId: entityId,
      qualityId,
    })
  },
  archetype: async (entityId, qualityId) => {
    await ArchetypeQualitiesService.addQualityToArchetype({
      archetypeId: entityId,
      qualityId,
    })
  },
  trait: async (entityId, qualityId) => {
    await QualityTraitLinksService.createQualityTraitLink({
      requestBody: { quality_id: qualityId, trait_id: entityId },
    })
  },
}

const removers: Record<string, QualityMutator> = {
  persona: async (entityId, qualityId) => {
    await PersonaQualitiesService.removeQualityFromPersona({
      personaId: entityId,
      qualityId,
    })
  },
  archetype: async (entityId, qualityId) => {
    await ArchetypeQualitiesService.removeQualityFromArchetype({
      archetypeId: entityId,
      qualityId,
    })
  },
  trait: async (entityId, qualityId) => {
    await QualityTraitLinksService.deleteQualityTraitLink({
      qualityId,
      traitId: entityId,
    })
  },
}

// ============================================================================
// Service
// ============================================================================

export const EntityQualitiesService = {
  /**
   * Fetch qualities for an entity.
   * Returns empty array if entityType is unsupported.
   */
  async getQualities(
    entityType: string,
    entityId: string,
  ): Promise<QualityViewModel[]> {
    const fetcher = fetchers[entityType]
    if (!fetcher) return []
    return fetcher(entityId)
  },

  /**
   * Add a quality to an entity.
   * Supported for both persona and archetype entity types.
   */
  async addQuality(
    entityType: string,
    entityId: string,
    qualityId: string,
  ): Promise<void> {
    const adder = adders[entityType]
    if (!adder) {
      throw new Error(`addQuality not supported for entity type: ${entityType}`)
    }
    return adder(entityId, qualityId)
  },

  /**
   * Remove a quality from an entity.
   * Supported for both persona and archetype entity types.
   */
  async removeQuality(
    entityType: string,
    entityId: string,
    qualityId: string,
  ): Promise<void> {
    const remover = removers[entityType]
    if (!remover) {
      throw new Error(
        `removeQuality not supported for entity type: ${entityType}`,
      )
    }
    return remover(entityId, qualityId)
  },

  /**
   * Whether the entity type supports write operations (add/remove).
   */
  isEditable(entityType: string): boolean {
    return entityType in adders
  },

  /**
   * TanStack Query key for entity qualities.
   */
  queryKey(entityType: string, entityId: string) {
    return ["entity-qualities", entityType, entityId] as const
  },
}
