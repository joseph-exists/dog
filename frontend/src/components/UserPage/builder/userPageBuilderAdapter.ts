import type { BioContent, IdentityContent } from "@/components/Page/blocks"
import { getBlockType, type TemplateBlock } from "@/components/Page/registry"
import type {
  AudiencePresentationBlockContent,
  PersonaManagerBlockContent,
  PrimaryPersonaBlockContent,
  RelationshipManagerBlockContent,
  WorkFeedBlockContent,
} from "@/components/UserPage/types"
import type { UserPageBuilderSurface } from "./userPageBuilderSchema"

export interface UserPageBuilderDraft {
  userId: string
  slug: string
  selectedSurface: UserPageBuilderSurface
  blocks: TemplateBlock[]
  identity: IdentityContent
  bio: BioContent
  primaryPersona: PrimaryPersonaBlockContent
  workFeed: WorkFeedBlockContent
  personaManager: PersonaManagerBlockContent
  audiencePresentation: AudiencePresentationBlockContent
  relationshipManager: RelationshipManagerBlockContent
}

export const USER_PAGE_TYPED_CONSTRUCT_BLOCK_TYPES = [
  "identity",
  "bio",
  "primaryPersona",
  "workFeed",
  "personaManager",
  "audiencePresentation",
  "relationshipManager",
] as const

type UserPageTypedConstructBlockType =
  (typeof USER_PAGE_TYPED_CONSTRUCT_BLOCK_TYPES)[number]

function getBlockContent(
  blocks: TemplateBlock[],
  type: TemplateBlock["type"],
): Record<string, unknown> | undefined {
  return blocks.find((block) => block.type === type)?.content
}

function cloneBlocks(blocks: TemplateBlock[]): TemplateBlock[] {
  return blocks.map((block) => ({
    ...block,
    config: { ...block.config },
    content: block.content ? { ...block.content } : block.content,
  }))
}

function normalizeUserPageBlocksToPrimary(
  blocks: TemplateBlock[],
): TemplateBlock[] {
  return cloneBlocks(blocks)
    .map((block, index) => ({ block, index }))
    .sort((left, right) => {
      const leftColumnRank = left.block.column === "primary" ? 0 : 1
      const rightColumnRank = right.block.column === "primary" ? 0 : 1
      if (leftColumnRank !== rightColumnRank) {
        return leftColumnRank - rightColumnRank
      }
      if (left.block.order !== right.block.order) {
        return left.block.order - right.block.order
      }
      return left.index - right.index
    })
    .map(({ block }, index) => ({
      ...block,
      column: "primary" as const,
      order: index + 1,
    }))
}

function cloneValue<T>(value: T): T {
  return structuredClone(value)
}

function isTypedConstructBlockType(
  type: TemplateBlock["type"],
): type is UserPageTypedConstructBlockType {
  return USER_PAGE_TYPED_CONSTRUCT_BLOCK_TYPES.includes(
    type as UserPageTypedConstructBlockType,
  )
}

function getDefaultBlockConfig(
  type: TemplateBlock["type"],
): Record<string, unknown> {
  return cloneValue(
    (getBlockType(type)?.defaultConfig ?? {}) as Record<string, unknown>,
  )
}

function getDefaultBlockContent(
  type: TemplateBlock["type"],
): Record<string, unknown> {
  return cloneValue(
    (getBlockType(type)?.defaultContent ?? {}) as Record<string, unknown>,
  )
}

function getDefaultTypedConstructContent(
  type: UserPageTypedConstructBlockType,
): UserPageBuilderDraft[UserPageTypedConstructBlockType] {
  switch (type) {
    case "identity":
      return {
        name: "",
        tagline: "",
      } as UserPageBuilderDraft[UserPageTypedConstructBlockType]
    case "bio":
      return {
        text: "",
      } as UserPageBuilderDraft[UserPageTypedConstructBlockType]
    case "primaryPersona":
      return {
        primaryPersonaId: null,
        explanation: getDefaultBlockContent("primaryPersona").explanation as
          | string
          | undefined,
      } as UserPageBuilderDraft[UserPageTypedConstructBlockType]
    case "workFeed":
      return {
        title: getDefaultBlockContent("workFeed").title as string | undefined,
        emptyMessage: getDefaultBlockContent("workFeed").emptyMessage as
          | string
          | undefined,
        items: [],
      } as UserPageBuilderDraft[UserPageTypedConstructBlockType]
    case "personaManager":
      return {
        personas: [],
      } as UserPageBuilderDraft[UserPageTypedConstructBlockType]
    case "audiencePresentation":
      return {
        presentations: [],
      } as UserPageBuilderDraft[UserPageTypedConstructBlockType]
    case "relationshipManager":
      return {
        relations: [],
      } as UserPageBuilderDraft[UserPageTypedConstructBlockType]
  }
}

function withUpdatedTypedConstructState(
  draft: UserPageBuilderDraft,
  type: UserPageTypedConstructBlockType,
  value: UserPageBuilderDraft[UserPageTypedConstructBlockType],
): UserPageBuilderDraft {
  return {
    ...draft,
    [type]: value,
  }
}

function createDraftBlock(input: {
  type: TemplateBlock["type"]
  column: "primary" | "auxiliary"
  order: number
  id?: string
}): TemplateBlock {
  return {
    id: input.id ?? crypto.randomUUID(),
    type: input.type,
    column: input.column,
    order: input.order,
    config: getDefaultBlockConfig(input.type),
    content: getDefaultBlockContent(input.type),
    visibility: "visible",
  }
}

function reorderColumnBlocks(
  blocks: TemplateBlock[],
  column: "primary" | "auxiliary",
  reorderedIds: string[],
): TemplateBlock[] {
  return blocks.map((block) => {
    if (block.column !== column || !block.id) return block
    const nextOrder = reorderedIds.indexOf(block.id)
    if (nextOrder === -1) return block
    return { ...block, order: nextOrder + 1 }
  })
}

export function hydrateUserPageBuilderDraft(input: {
  userId: string
  slug: string
  blocks: TemplateBlock[]
  selectedSurface?: UserPageBuilderSurface
}): UserPageBuilderDraft {
  const blocks = normalizeUserPageBlocksToPrimary(input.blocks)
  const identityContent = getBlockContent(blocks, "identity")
  const bioContent = getBlockContent(blocks, "bio")
  const primaryPersonaContent = getBlockContent(blocks, "primaryPersona")
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

  return {
    userId: input.userId,
    slug: input.slug,
    selectedSurface: input.selectedSurface ?? "overview",
    blocks,
    identity: {
      name: (identityContent?.name as string) ?? "",
      tagline: identityContent?.tagline as string | undefined,
    },
    bio: {
      text: (bioContent?.text as string) ?? "",
    },
    primaryPersona: {
      primaryPersonaId:
        (primaryPersonaContent?.primaryPersonaId as string | null) ?? null,
      explanation: primaryPersonaContent?.explanation as string | undefined,
    },
    workFeed: {
      title: workFeedContent?.title as string | undefined,
      emptyMessage: workFeedContent?.emptyMessage as string | undefined,
      items: (workFeedContent?.items as WorkFeedBlockContent["items"]) ?? [],
    },
    personaManager: {
      personas:
        (personaManagerContent?.personas as PersonaManagerBlockContent["personas"]) ??
        [],
    },
    audiencePresentation: {
      presentations:
        (audiencePresentationContent?.presentations as AudiencePresentationBlockContent["presentations"]) ??
        [],
    },
    relationshipManager: {
      relations:
        (relationshipManagerContent?.relations as RelationshipManagerBlockContent["relations"]) ??
        [],
    },
  }
}

function contentForBlockType(
  draft: UserPageBuilderDraft,
  type: TemplateBlock["type"],
  fallback?: Record<string, unknown>,
): Record<string, unknown> | undefined {
  switch (type) {
    case "identity":
      return draft.identity as unknown as Record<string, unknown>
    case "bio":
      return draft.bio as unknown as Record<string, unknown>
    case "primaryPersona":
      return draft.primaryPersona as Record<string, unknown>
    case "workFeed":
      return draft.workFeed as Record<string, unknown>
    case "personaManager":
      return draft.personaManager as Record<string, unknown>
    case "audiencePresentation":
      return draft.audiencePresentation as Record<string, unknown>
    case "relationshipManager":
      return draft.relationshipManager as Record<string, unknown>
    default:
      return fallback
  }
}

export function serializeUserPageBuilderDraft(
  draft: UserPageBuilderDraft,
): TemplateBlock[] {
  return draft.blocks.map((block) => ({
    ...block,
    config: { ...block.config },
    content: contentForBlockType(
      draft,
      block.type,
      block.content ? { ...block.content } : block.content,
    ),
  }))
}

export function updateUserPageBuilderDraftBlockContent(
  draft: UserPageBuilderDraft,
  blockId: string,
  content: Record<string, unknown>,
): UserPageBuilderDraft {
  const block = draft.blocks.find((candidate) => candidate.id === blockId)
  if (!block) return draft

  switch (block.type) {
    case "identity":
      return {
        ...draft,
        identity: {
          name: (content.name as string) ?? "",
          tagline: content.tagline as string | undefined,
        },
      }
    case "bio":
      return {
        ...draft,
        bio: {
          text: (content.text as string) ?? "",
        },
      }
    case "primaryPersona":
      return {
        ...draft,
        primaryPersona: {
          primaryPersonaId: (content.primaryPersonaId as string | null) ?? null,
          explanation: content.explanation as string | undefined,
        },
      }
    case "workFeed":
      return {
        ...draft,
        workFeed: content as WorkFeedBlockContent,
      }
    case "personaManager":
      return {
        ...draft,
        personaManager: content as PersonaManagerBlockContent,
      }
    case "audiencePresentation":
      return {
        ...draft,
        audiencePresentation: content as AudiencePresentationBlockContent,
      }
    case "relationshipManager":
      return {
        ...draft,
        relationshipManager: content as RelationshipManagerBlockContent,
      }
    default:
      return {
        ...draft,
        blocks: draft.blocks.map((candidate) =>
          candidate.id === blockId ? { ...candidate, content } : candidate,
        ),
      }
  }
}

export function addUserPageBuilderDraftBlock(
  draft: UserPageBuilderDraft,
  input: {
    type: TemplateBlock["type"]
    column: "primary" | "auxiliary"
    id?: string
  },
): UserPageBuilderDraft {
  if (
    isTypedConstructBlockType(input.type) &&
    draft.blocks.some((block) => block.type === input.type)
  ) {
    return draft
  }

  const order =
    draft.blocks
      .filter((block) => block.column === input.column)
      .reduce((max, block) => Math.max(max, block.order), 0) + 1

  const nextDraft = {
    ...draft,
    blocks: [
      ...draft.blocks,
      createDraftBlock({
        type: input.type,
        column: input.column,
        order,
        id: input.id,
      }),
    ],
  }

  if (!isTypedConstructBlockType(input.type)) {
    return nextDraft
  }

  return withUpdatedTypedConstructState(
    nextDraft,
    input.type,
    getDefaultTypedConstructContent(input.type),
  )
}

export function deleteUserPageBuilderDraftBlock(
  draft: UserPageBuilderDraft,
  blockId: string,
): UserPageBuilderDraft {
  const block = draft.blocks.find((candidate) => candidate.id === blockId)
  if (!block) return draft

  const nextDraft = {
    ...draft,
    blocks: draft.blocks.filter((candidate) => candidate.id !== blockId),
  }

  if (!isTypedConstructBlockType(block.type)) {
    return nextDraft
  }

  return withUpdatedTypedConstructState(
    nextDraft,
    block.type,
    getDefaultTypedConstructContent(block.type),
  )
}

export function resetUserPageBuilderDraftBlock(
  draft: UserPageBuilderDraft,
  blockId: string,
): UserPageBuilderDraft {
  const block = draft.blocks.find((candidate) => candidate.id === blockId)
  if (!block) return draft

  const nextBlock = {
    ...block,
    config: getDefaultBlockConfig(block.type),
    content: getDefaultBlockContent(block.type),
  }

  const nextDraft = {
    ...draft,
    blocks: draft.blocks.map((candidate) =>
      candidate.id === blockId ? nextBlock : candidate,
    ),
  }

  if (!isTypedConstructBlockType(block.type)) {
    return nextDraft
  }

  return withUpdatedTypedConstructState(
    nextDraft,
    block.type,
    getDefaultTypedConstructContent(block.type),
  )
}

export function moveUserPageBuilderDraftBlock(
  draft: UserPageBuilderDraft,
  blockId: string,
  direction: "up" | "down",
): UserPageBuilderDraft {
  const block = draft.blocks.find((candidate) => candidate.id === blockId)
  if (!block) return draft

  const columnBlocks = draft.blocks
    .filter((candidate) => candidate.column === block.column)
    .sort((a, b) => a.order - b.order)

  const currentIndex = columnBlocks.findIndex(
    (candidate) => candidate.id === blockId,
  )
  if (currentIndex === -1) return draft

  const nextIndex = direction === "up" ? currentIndex - 1 : currentIndex + 1
  if (nextIndex < 0 || nextIndex >= columnBlocks.length) return draft

  const reorderedIds = columnBlocks.map((candidate) => candidate.id!)
  ;[reorderedIds[currentIndex], reorderedIds[nextIndex]] = [
    reorderedIds[nextIndex],
    reorderedIds[currentIndex],
  ]

  return {
    ...draft,
    blocks: reorderColumnBlocks(draft.blocks, block.column, reorderedIds),
  }
}

export function toggleUserPageBuilderDraftBlockVisibility(
  draft: UserPageBuilderDraft,
  blockId: string,
): UserPageBuilderDraft {
  const block = draft.blocks.find((candidate) => candidate.id === blockId)
  if (!block) return draft

  return {
    ...draft,
    blocks: draft.blocks.map((candidate) =>
      candidate.id === blockId
        ? {
            ...candidate,
            visibility:
              (candidate.visibility ?? "visible") === "visible"
                ? "hidden"
                : "visible",
          }
        : candidate,
    ),
  }
}
