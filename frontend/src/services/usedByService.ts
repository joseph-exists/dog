// src/services/usedByService.ts

/**
 * Used By Service
 *
 * Provides reverse-lookup "who uses this entity" data via ViewModels.
 * Fetches archetypes and personas that reference a given trait or quality.
 *
 * Supported entity types:
 * - "trait" → TraitUsersService (archetypes + personas using this trait)
 * - "quality" → QualityUsersService (archetypes + personas using this quality)
 *
 * @example
 * ```ts
 * const { archetypes, personas } = await UsedByService.getUsedBy("trait", traitId)
 * ```
 */

import { TraitUsersService, QualityUsersService } from "@/client"

// ============================================================================
// ViewModels
// ============================================================================

/** Minimal entity reference for display in the UsedByBlock */
export interface UsedByEntityViewModel {
  id: string
  name: string
  description?: string
  entityType: "archetype" | "persona"
}

/** Combined result with grouped entities */
export interface UsedByResult {
  archetypes: UsedByEntityViewModel[]
  personas: UsedByEntityViewModel[]
}

// ============================================================================
// Fetcher Registry
// ============================================================================

type UsedByFetcher = (entityId: string) => Promise<UsedByResult>

const fetchers: Record<string, UsedByFetcher> = {
  trait: async (entityId) => {
    const [archetypes, personas] = await Promise.all([
      TraitUsersService.readTraitArchetypes({ traitId: entityId }),
      TraitUsersService.readTraitPersonas({ traitId: entityId }),
    ])
    return {
      archetypes: archetypes.map((a) => ({
        id: a.id,
        name: a.name,
        description: a.description ?? undefined,
        entityType: "archetype" as const,
      })),
      personas: personas.map((p) => ({
        id: p.id,
        name: p.name,
        description: p.description ?? undefined,
        entityType: "persona" as const,
      })),
    }
  },
  quality: async (entityId) => {
    const [archetypes, personas] = await Promise.all([
      QualityUsersService.readQualityArchetypes({ qualityId: entityId }),
      QualityUsersService.readQualityPersonas({ qualityId: entityId }),
    ])
    return {
      archetypes: archetypes.map((a) => ({
        id: a.id,
        name: a.name,
        description: a.description ?? undefined,
        entityType: "archetype" as const,
      })),
      personas: personas.map((p) => ({
        id: p.id,
        name: p.name,
        description: p.description ?? undefined,
        entityType: "persona" as const,
      })),
    }
  },
}

// ============================================================================
// Service
// ============================================================================

export const UsedByService = {
  /**
   * Fetch archetypes and personas that reference this entity.
   * Returns empty result if entityType is unsupported.
   */
  async getUsedBy(
    entityType: string,
    entityId: string,
  ): Promise<UsedByResult> {
    const fetcher = fetchers[entityType]
    if (!fetcher) return { archetypes: [], personas: [] }
    return fetcher(entityId)
  },

  /**
   * Whether this entity type supports "used by" lookups.
   */
  isSupported(entityType: string): boolean {
    return entityType in fetchers
  },

  /**
   * TanStack Query key for used-by data.
   */
  queryKey(entityType: string, entityId: string) {
    return ["used-by", entityType, entityId] as const
  },
}
