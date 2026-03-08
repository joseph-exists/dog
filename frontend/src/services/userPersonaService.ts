import type {
  AudiencePresentationSummary,
  UserPersonaSummary,
  WeightedTag,
} from "@/components/UserPage/types"
import type {
  Persona,
  UserPersonaPresentationPublic,
  UserPersonaPublic,
} from "@/client"
import { PersonasService, UserPersonasService } from "@/client"

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function toWeightedTag(input: unknown): WeightedTag | null {
  if (!isObjectRecord(input)) return null

  const label =
    typeof input.label === "string" && input.label.trim().length > 0
      ? input.label.trim()
      : null

  if (!label) return null

  const weight =
    typeof input.weight === "number" && Number.isFinite(input.weight)
      ? Math.min(1, Math.max(0, input.weight))
      : 0.5

  return {
    id:
      typeof input.id === "string" && input.id.trim().length > 0
        ? input.id.trim()
        : label.toLowerCase().replace(/\s+/g, "-"),
    label,
    weight,
    source: input.source === "system" ? "system" : "user",
  }
}

function toFallbackTags(persona: Persona): WeightedTag[] {
  return [persona.general_domain, persona.specific_domain]
    .filter((value): value is string => Boolean(value))
    .map((label, index) => ({
      id: `${persona.id}-domain-${index}`,
      label,
      weight: 0.5,
      source: "system" as const,
    }))
}

function toUserPersonaSummary(
  entry: UserPersonaPublic,
  persona: Persona,
): UserPersonaSummary {
  const tags =
    entry.tags_json?.map((tag) => toWeightedTag(tag)).filter(Boolean) ?? []

  return {
    id: entry.persona_id,
    userPersonaId: entry.id,
    personaVisibility: persona.visibility ?? null,
    name: persona.name,
    nickname: entry.nickname ?? null,
    shortBio: entry.short_bio ?? entry.description ?? persona.description ?? null,
    longBio: entry.long_bio ?? persona.long_description ?? null,
    tags: tags.length > 0 ? tags : toFallbackTags(persona),
    publicationState: entry.publication_state ?? "draft",
    associatedWorkCount: 0,
    isPrimary: entry.is_primary === true,
    isVisibleInCurrentAudience: true,
  }
}

function toAudiencePresentationSummary(
  presentation: UserPersonaPresentationPublic,
  entry: UserPersonaPublic,
): AudiencePresentationSummary {
  const audienceScope = presentation.audience_scope ?? "public"
  const relationCallToAction =
    presentation.relation_call_to_action === "request_contact" ||
    presentation.relation_call_to_action === "invite_collaboration" ||
    presentation.relation_call_to_action === "follow_work"
      ? presentation.relation_call_to_action
      : "none"

  return {
    id: presentation.id,
    userPersonaId: entry.id,
    personaId: entry.persona_id,
    audienceScope,
    audienceLabel: presentation.audience_label,
    headline: presentation.headline,
    framingText: presentation.framing_text ?? null,
    visibleWorkIds: presentation.visible_work_ids_json ?? [],
    relationCallToAction,
  }
}

export interface UserPersonaPageData {
  personas: UserPersonaSummary[]
  presentations: AudiencePresentationSummary[]
}

export const UserPersonaService = {
  async getUserPageData(): Promise<UserPersonaPageData> {
    const userPersonas = await UserPersonasService.readUserPersonas({ limit: 100 })

    if (userPersonas.data.length === 0) {
      return { personas: [], presentations: [] }
    }

    const personaIds = [...new Set(userPersonas.data.map((entry) => entry.persona_id))]
    const personaMap = new Map<string, Persona>()

    await Promise.all(
      personaIds.map(async (personaId) => {
        const persona = await PersonasService.readPersona({ id: personaId })
        personaMap.set(personaId, persona)
      }),
    )

    const presentationsByUserPersonaId = new Map<
      string,
      UserPersonaPresentationPublic[]
    >()

    await Promise.all(
      userPersonas.data.map(async (entry) => {
        const response = await UserPersonasService.readUserPersonaPresentations({
          id: entry.id,
          limit: 100,
        })
        presentationsByUserPersonaId.set(entry.id, response.data)
      }),
    )

    const personas = userPersonas.data
      .filter((entry) => personaMap.has(entry.persona_id))
      .map((entry) => toUserPersonaSummary(entry, personaMap.get(entry.persona_id)!))
      .sort((left, right) => {
        const primaryOrder = Number(right.isPrimary) - Number(left.isPrimary)
        if (primaryOrder !== 0) return primaryOrder
        return left.name.localeCompare(right.name)
      })

    const presentations = userPersonas.data.flatMap((entry) =>
      (presentationsByUserPersonaId.get(entry.id) ?? []).map((presentation) =>
        toAudiencePresentationSummary(presentation, entry),
      ),
    )

    return { personas, presentations }
  },
}
