import { useQuery } from "@tanstack/react-query"
import { useMemo } from "react"

import type { LibraryPersona, PersonaLibraryOwner } from "@/components/Persona"
import type { TemplateBlock } from "@/components/Page/registry"
import type {
  AudiencePresentationSummary,
  AudienceScope,
  PersonaRelationSummary,
  PrimaryPersonaBlockContent,
  UserPageViewModel,
  UserPersonaSummary,
  UserWorkFeedItem,
  WeightedTag,
} from "@/components/UserPage/types"
import { PersonaLibraryService } from "@/services/personaLibraryService"
import { UserPersonaService } from "@/services/userPersonaService"
import useAuth from "./useAuth"
import { usePageEditor } from "./usePageEditor"

const DEFAULT_AUDIENCE_SCOPE: AudienceScope = "public"

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function slugToDisplayLabel(scope: AudienceScope): string {
  switch (scope) {
    case "public":
      return "Public"
    case "trusted":
      return "Trusted"
    case "collaborators":
      return "Collaborators"
    case "custom":
      return "Custom"
  }
}

function getBlockContent(
  blocks: TemplateBlock[] | undefined,
  type: string,
): Record<string, unknown> | undefined {
  return blocks?.find((block) => block.type === type)?.content
}

export function normalizeWeightedTag(input: unknown): WeightedTag | null {
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

function normalizeWorkItem(input: unknown): UserWorkFeedItem | null {
  if (!isObjectRecord(input)) return null
  const title =
    typeof input.title === "string" && input.title.trim().length > 0
      ? input.title.trim()
      : null
  if (!title) return null

  const workType =
    input.workType === "demo" ||
    input.workType === "prompt" ||
    input.workType === "story" ||
    input.workType === "page" ||
    input.workType === "artifact" ||
    input.workType === "other"
      ? input.workType
      : "other"

  const status = input.status === "published" ? "published" : "draft"
  const intendedAudienceScopes = Array.isArray(input.intendedAudienceScopes)
    ? input.intendedAudienceScopes.filter(
        (scope): scope is AudienceScope =>
          scope === "public" ||
          scope === "trusted" ||
          scope === "collaborators" ||
          scope === "custom",
      )
    : [DEFAULT_AUDIENCE_SCOPE]

  return {
    id:
      typeof input.id === "string" && input.id.trim().length > 0
        ? input.id.trim()
        : crypto.randomUUID(),
    title,
    workType,
    summary: typeof input.summary === "string" ? input.summary : null,
    status,
    tags: Array.isArray(input.tags)
      ? input.tags.filter((tag): tag is string => typeof tag === "string")
      : [],
    associatedPersonaIds: Array.isArray(input.associatedPersonaIds)
      ? input.associatedPersonaIds.filter(
          (personaId): personaId is string => typeof personaId === "string",
        )
      : [],
    intendedAudienceScopes:
      intendedAudienceScopes.length > 0
        ? Array.from(new Set(intendedAudienceScopes))
        : [DEFAULT_AUDIENCE_SCOPE],
    timestampLabel:
      typeof input.timestampLabel === "string" && input.timestampLabel.trim()
        ? input.timestampLabel.trim()
        : "Recently",
    href: typeof input.href === "string" && input.href.trim() ? input.href : null,
    isRepresentative: input.isRepresentative !== false,
  }
}

function normalizeAudiencePresentation(
  input: unknown,
): AudiencePresentationSummary | null {
  if (!isObjectRecord(input)) return null
  if (
    typeof input.personaId !== "string" ||
    input.personaId.trim().length === 0 ||
    typeof input.headline !== "string" ||
    input.headline.trim().length === 0
  ) {
    return null
  }

  const audienceScope =
    input.audienceScope === "trusted" ||
    input.audienceScope === "collaborators" ||
    input.audienceScope === "custom"
      ? input.audienceScope
      : DEFAULT_AUDIENCE_SCOPE

  const relationCallToAction =
    input.relationCallToAction === "request_contact" ||
    input.relationCallToAction === "invite_collaboration" ||
    input.relationCallToAction === "follow_work"
      ? input.relationCallToAction
      : "none"

  return {
    id:
      typeof input.id === "string" && input.id.trim().length > 0
        ? input.id.trim()
        : crypto.randomUUID(),
    userPersonaId:
      typeof input.userPersonaId === "string" && input.userPersonaId.trim().length > 0
        ? input.userPersonaId.trim()
        : null,
    personaId: input.personaId.trim(),
    audienceScope,
    audienceLabel:
      typeof input.audienceLabel === "string" && input.audienceLabel.trim()
        ? input.audienceLabel.trim()
        : slugToDisplayLabel(audienceScope),
    headline: input.headline.trim(),
    framingText: typeof input.framingText === "string" ? input.framingText : null,
    visibleWorkIds: Array.isArray(input.visibleWorkIds)
      ? input.visibleWorkIds.filter((id): id is string => typeof id === "string")
      : [],
    relationCallToAction,
  }
}

function normalizeRelation(input: unknown): PersonaRelationSummary | null {
  if (!isObjectRecord(input)) return null
  if (
    typeof input.sourcePersonaId !== "string" ||
    input.sourcePersonaId.trim().length === 0 ||
    typeof input.targetLabel !== "string" ||
    input.targetLabel.trim().length === 0
  ) {
    return null
  }

  return {
    id:
      typeof input.id === "string" && input.id.trim().length > 0
        ? input.id.trim()
        : crypto.randomUUID(),
    sourcePersonaId: input.sourcePersonaId.trim(),
    targetLabel: input.targetLabel.trim(),
    targetType: input.targetType === "persona" ? "persona" : "external",
    relationKind:
      input.relationKind === "trusted" ||
      input.relationKind === "learning_from" ||
      input.relationKind === "working_with"
        ? input.relationKind
        : "collaborator",
    audienceScope:
      input.audienceScope === "trusted" ||
      input.audienceScope === "collaborators" ||
      input.audienceScope === "custom"
        ? input.audienceScope
        : DEFAULT_AUDIENCE_SCOPE,
    note: typeof input.note === "string" ? input.note : null,
    status: input.status === "pending" ? "pending" : "active",
  }
}

function normalizeStoredPersona(input: unknown): UserPersonaSummary | null {
  if (!isObjectRecord(input)) return null
  if (typeof input.id !== "string" || input.id.trim().length === 0) return null
  if (typeof input.name !== "string" || input.name.trim().length === 0) return null

  const publicationState =
    input.publicationState === "published" ? "published" : "draft"

  return {
    id: input.id.trim(),
    userPersonaId:
      typeof input.userPersonaId === "string" &&
      input.userPersonaId.trim().length > 0
        ? input.userPersonaId.trim()
        : null,
    personaVisibility:
      input.personaVisibility === "private" || input.personaVisibility === "system"
        ? input.personaVisibility
        : null,
    name: input.name.trim(),
    nickname:
      typeof input.nickname === "string" && input.nickname.trim().length > 0
        ? input.nickname.trim()
        : null,
    shortBio: typeof input.shortBio === "string" ? input.shortBio : null,
    longBio: typeof input.longBio === "string" ? input.longBio : null,
    tags: Array.isArray(input.tags)
      ? input.tags
          .map((tag) => normalizeWeightedTag(tag))
          .filter((tag): tag is WeightedTag => tag !== null)
      : [],
    publicationState,
    associatedWorkCount:
      typeof input.associatedWorkCount === "number" &&
      Number.isFinite(input.associatedWorkCount)
        ? Math.max(0, Math.floor(input.associatedWorkCount))
        : 0,
    isPrimary: input.isPrimary === true,
    isVisibleInCurrentAudience: input.isVisibleInCurrentAudience !== false,
  }
}

function buildPersonaFromLibrary(persona: LibraryPersona): UserPersonaSummary {
  return {
    id: persona.personaId,
    userPersonaId: persona.libraryEntryId,
    personaVisibility: null,
    name: persona.name,
    nickname: persona.nickname,
    shortBio: persona.description,
    longBio: persona.longDescription ?? null,
    tags: (persona.domains ?? []).map((label, index) => ({
      id: `${persona.personaId}-domain-${index}`,
      label,
      weight: 0.5,
      source: "system" as const,
    })),
    publicationState: persona.isActive ? "published" : "draft",
    associatedWorkCount: 0,
    isPrimary: false,
    isVisibleInCurrentAudience: true,
  }
}

function personaMatchesId(persona: UserPersonaSummary, candidateId: string): boolean {
  return candidateId === persona.id || candidateId === persona.userPersonaId
}

function resolvePersonaReference(
  candidateId: string | null | undefined,
  personas: UserPersonaSummary[],
): string | null {
  if (!candidateId) return null
  const trimmedId = candidateId.trim()
  if (!trimmedId) return null
  return personas.find((persona) => personaMatchesId(persona, trimmedId))?.id ?? null
}

export function resolvePrimaryPersonaId(
  rawPrimaryPersonaId: string | null | undefined,
  personaIds: string[],
): string | null {
  if (!rawPrimaryPersonaId) return null
  return personaIds.includes(rawPrimaryPersonaId) ? rawPrimaryPersonaId : null
}

export function getActiveAudiencePresentation(
  presentations: AudiencePresentationSummary[],
  selectedAudienceScope: AudienceScope,
): AudiencePresentationSummary | null {
  return (
    presentations.find(
      (presentation) => presentation.audienceScope === selectedAudienceScope,
    ) ?? null
  )
}

export function filterWorkFeedForAudience(
  workFeed: UserWorkFeedItem[],
  presentations: AudiencePresentationSummary[],
  selectedAudienceScope: AudienceScope,
  isOwner: boolean,
): UserWorkFeedItem[] {
  if (isOwner) {
    return workFeed.filter((item) => item.isRepresentative)
  }

  const activePresentation = getActiveAudiencePresentation(
    presentations,
    selectedAudienceScope,
  )

  if (!activePresentation) return []

  const visibleIds = new Set(activePresentation.visibleWorkIds)
  return workFeed.filter((item) => visibleIds.has(item.id))
}

export function buildUserPageViewModel(input: {
  slug: string
  userId: string
  isOwner: boolean
  pageExists: boolean
  blocks: TemplateBlock[] | undefined
  libraryPersonas: LibraryPersona[]
  ownerPersonas?: UserPersonaSummary[]
  ownerPresentations?: AudiencePresentationSummary[]
}): UserPageViewModel {
  const {
    slug,
    userId,
    isOwner,
    pageExists,
    blocks,
    libraryPersonas,
    ownerPersonas = [],
    ownerPresentations = [],
  } = input

  const primaryContent = getBlockContent(
    blocks,
    "primaryPersona",
  ) as PrimaryPersonaBlockContent | undefined
  const workFeedContent = getBlockContent(blocks, "workFeed")
  const personaManagerContent = getBlockContent(blocks, "personaManager")
  const audiencePresentationContent = getBlockContent(
    blocks,
    "audiencePresentation",
  )
  const relationshipManagerContent = getBlockContent(
    blocks,
    "relationshipManager",
  )
  const rawWorkItems = Array.isArray(workFeedContent?.items)
    ? (workFeedContent.items as unknown[])
    : []
  const rawStoredPersonas = Array.isArray(personaManagerContent?.personas)
    ? (personaManagerContent.personas as unknown[])
    : []
  const rawPresentations = Array.isArray(audiencePresentationContent?.presentations)
    ? (audiencePresentationContent.presentations as unknown[])
    : []
  const rawRelations = Array.isArray(relationshipManagerContent?.relations)
    ? (relationshipManagerContent.relations as unknown[])
    : []

  const workItems = rawWorkItems.length > 0
    ? rawWorkItems
        .map((item) => normalizeWorkItem(item))
        .filter((item): item is UserWorkFeedItem => item !== null)
    : []
  const storedPersonas = rawStoredPersonas.length > 0
    ? rawStoredPersonas
        .map((persona) => normalizeStoredPersona(persona))
        .filter((persona): persona is UserPersonaSummary => persona !== null)
    : []
  const storedPresentations = rawPresentations.length > 0
    ? rawPresentations
        .map((presentation) => normalizeAudiencePresentation(presentation))
        .filter(
          (presentation): presentation is AudiencePresentationSummary =>
            presentation !== null,
        )
    : []
  const relations = rawRelations.length > 0
    ? rawRelations
        .map((relation) => normalizeRelation(relation))
        .filter((relation): relation is PersonaRelationSummary => relation !== null)
    : []

  const personaMap = new Map<string, UserPersonaSummary>()
  const authoritativePersonas =
    isOwner && ownerPersonas.length > 0
      ? ownerPersonas
      : libraryPersonas.map((persona) => buildPersonaFromLibrary(persona))

  for (const persona of authoritativePersonas) {
    personaMap.set(persona.id, persona)
  }

  for (const storedPersona of storedPersonas) {
    const matchedPersona = Array.from(personaMap.values()).find((persona) =>
      personaMatchesId(persona, storedPersona.id),
    )

    if (!matchedPersona) {
      personaMap.set(storedPersona.id, storedPersona)
    }
  }

  const personas = Array.from(personaMap.values())
  const presentations =
    isOwner && ownerPresentations.length > 0
      ? [
          ...ownerPresentations,
          ...storedPresentations.filter(
            (storedPresentation) =>
              !ownerPresentations.some(
                (presentation) =>
                  presentation.id === storedPresentation.id ||
                  (presentation.personaId === storedPresentation.personaId &&
                    presentation.audienceScope ===
                      storedPresentation.audienceScope),
              ),
          ),
        ]
      : storedPresentations

  const personaIds = personas.map((persona) => persona.id)
  const primaryPersonaId =
    resolvePersonaReference(primaryContent?.primaryPersonaId ?? null, personas) ??
    resolvePrimaryPersonaId(primaryContent?.primaryPersonaId ?? null, personaIds)
  const selectedAudienceScope =
    presentations[0]?.audienceScope ?? DEFAULT_AUDIENCE_SCOPE
  const selectedAudienceLabel =
    presentations[0]?.audienceLabel ?? slugToDisplayLabel(selectedAudienceScope)

  const resolvedPersonas = personas.map((persona) => {
    const associatedWorkCount = workItems.filter((item) =>
      item.associatedPersonaIds.some((personaId) => personaMatchesId(persona, personaId)),
    ).length
    const isVisibleInCurrentAudience = presentations.some(
      (presentation) =>
        presentation.audienceScope === selectedAudienceScope &&
        personaMatchesId(persona, presentation.personaId),
    )

    return {
      ...persona,
      associatedWorkCount,
      isPrimary: primaryPersonaId === persona.id,
      isVisibleInCurrentAudience,
    }
  })

  const selectedPersonaId =
    primaryPersonaId ??
    resolvePersonaReference(
      presentations.find(
        (presentation) => presentation.audienceScope === selectedAudienceScope,
      )?.personaId,
      resolvedPersonas,
    ) ??
    resolvedPersonas[0]?.id ??
    null

  return {
    userId,
    slug,
    isOwner,
    mode: !pageExists && isOwner
      ? "owner-empty"
      : isOwner
        ? "owner-manage"
        : "visitor-view",
    primaryPersonaId,
    selectedPersonaId,
    selectedAudienceScope,
    selectedAudienceLabel,
    workFeed: workItems,
    personas: resolvedPersonas,
    audiencePresentations: presentations,
    relations,
  }
}

export function useUserPageViewModel(slug: string) {
  const { user } = useAuth()
  const userId = slug
  const isOwner = user?.id === userId
  const pageEditor = usePageEditor("user", userId)

  const owner: PersonaLibraryOwner = {
    type: "user",
    id: userId,
    name: user?.full_name || user?.email || slug,
  }

  const personaLibraryQuery = useQuery({
    queryKey: ["persona-library", "user", userId],
    queryFn: () => PersonaLibraryService.getLibrary(owner),
    enabled: Boolean(userId) && isOwner,
  })

  const ownerPersonaQuery = useQuery({
    queryKey: ["user-persona-page-data", userId],
    queryFn: () => UserPersonaService.getUserPageData(),
    enabled: Boolean(userId) && isOwner,
  })

  const viewModel = useMemo(
    () =>
      buildUserPageViewModel({
        slug,
        userId,
        isOwner,
        pageExists: pageEditor.pageExists,
        blocks: pageEditor.blocks,
        libraryPersonas: personaLibraryQuery.data ?? [],
        ownerPersonas: ownerPersonaQuery.data?.personas ?? [],
        ownerPresentations: ownerPersonaQuery.data?.presentations ?? [],
      }),
    [
      slug,
      userId,
      isOwner,
      pageEditor.pageExists,
      pageEditor.blocks,
      personaLibraryQuery.data,
      ownerPersonaQuery.data,
    ],
  )

  return {
    ...pageEditor,
    viewModel,
    userId,
    isOwner,
    isLoading:
      pageEditor.isLoading ||
      personaLibraryQuery.isLoading ||
      ownerPersonaQuery.isLoading,
    personaLibrary: personaLibraryQuery.data ?? [],
  }
}
