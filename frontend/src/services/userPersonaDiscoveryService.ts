import { OpenAPI } from "@/client"
import type { ApiRequestOptions } from "@/client/core/ApiRequestOptions"
import { request as __request } from "@/client/core/request"

export interface DiscoverableUserPersona {
  id: string
  userId: string
  personaId: string
  name: string
  nickname: string | null
  shortBio: string | null
  publicationState: "draft" | "published"
  ownerDisplayName: string
  isPrimary: boolean
}

interface DiscoverableUserPersonaResponse {
  id: string
  user_id: string
  persona_id: string
  name: string
  nickname?: string | null
  short_bio?: string | null
  publication_state: "draft" | "published"
  owner_display_name: string
  is_primary: boolean
}

interface DiscoverableUserPersonasResponse {
  data: DiscoverableUserPersonaResponse[]
  count: number
}

export const UserPersonaDiscoveryService = {
  async search(
    query: string,
    options?: {
      limit?: number
      excludeCurrentUser?: boolean
    },
  ): Promise<DiscoverableUserPersona[]> {
    const trimmedQuery = query.trim()
    if (trimmedQuery.length < 2) return []

    const requestOptions: ApiRequestOptions<DiscoverableUserPersonasResponse> = {
      method: "GET",
      url: "/api/v1/user-personas/discoverable",
      query: {
        q: trimmedQuery,
        limit: options?.limit ?? 12,
        exclude_current_user: options?.excludeCurrentUser ?? true,
      },
    }

    const response = await __request<DiscoverableUserPersonasResponse>(
      OpenAPI,
      requestOptions,
    )

    return response.data.map((persona) => ({
      id: persona.id,
      userId: persona.user_id,
      personaId: persona.persona_id,
      name: persona.name,
      nickname: persona.nickname ?? null,
      shortBio: persona.short_bio ?? null,
      publicationState: persona.publication_state,
      ownerDisplayName: persona.owner_display_name,
      isPrimary: persona.is_primary,
    }))
  },
}
