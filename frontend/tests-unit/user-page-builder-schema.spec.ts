import { expect, test } from "@playwright/test"

import {
  addUserPageBuilderDraftBlock,
  deleteUserPageBuilderDraftBlock,
  hydrateUserPageBuilderDraft,
  moveUserPageBuilderDraftBlock,
  resetUserPageBuilderDraftBlock,
  serializeUserPageBuilderDraft,
  toggleUserPageBuilderDraftBlockVisibility,
} from "@/components/UserPage/builder/userPageBuilderAdapter"
import { validateUserPageBuilderDraft } from "@/components/UserPage/builder/userPageBuilderSchema"
import type { TemplateBlock } from "@/components/Page/registry"

test.describe("userPageBuilderSchema", () => {
  test("flags missing primary persona reference", async () => {
    const blocks: TemplateBlock[] = [
      {
        id: "primary-1",
        type: "primaryPersona",
        column: "primary",
        order: 1,
        config: {},
        content: { primaryPersonaId: "persona-missing" },
        visibility: "visible",
      },
      {
        id: "persona-manager-1",
        type: "personaManager",
        column: "auxiliary",
        order: 1,
        config: {},
        content: {
          personas: [
            {
              id: "persona-1",
              name: "Josep",
              publicationState: "published",
              tags: [],
              associatedWorkCount: 0,
              isPrimary: false,
              isVisibleInCurrentAudience: true,
            },
          ],
        },
        visibility: "visible",
      },
    ]

    const issues = validateUserPageBuilderDraft(
      hydrateUserPageBuilderDraft({
        userId: "user-1",
        slug: "user-1",
        blocks,
      }),
    )

    expect(issues.some((issue) => issue.code === "primary_persona_missing")).toBeTruthy()
  })

  test("flags audience presentations and relations that reference missing ids", async () => {
    const blocks: TemplateBlock[] = [
      {
        id: "persona-manager-1",
        type: "personaManager",
        column: "auxiliary",
        order: 1,
        config: {},
        content: {
          personas: [
            {
              id: "persona-1",
              name: "Josep",
              publicationState: "published",
              tags: [],
              associatedWorkCount: 0,
              isPrimary: false,
              isVisibleInCurrentAudience: true,
            },
          ],
        },
        visibility: "visible",
      },
      {
        id: "audiences-1",
        type: "audiencePresentation",
        column: "primary",
        order: 1,
        config: {},
        content: {
          presentations: [
            {
              id: "presentation-1",
              personaId: "persona-missing",
              audienceScope: "public",
              audienceLabel: "Public",
              headline: "Public view",
              visibleWorkIds: ["work-missing"],
              relationCallToAction: "none",
            },
          ],
        },
        visibility: "visible",
      },
      {
        id: "relations-1",
        type: "relationshipManager",
        column: "auxiliary",
        order: 2,
        config: {},
        content: {
          relations: [
            {
              id: "relation-1",
              sourcePersonaId: "persona-missing",
              targetLabel: "Target",
              targetType: "external",
              relationKind: "collaborator",
              audienceScope: "public",
              note: null,
              status: "active",
            },
          ],
        },
        visibility: "visible",
      },
    ]

    const issues = validateUserPageBuilderDraft(
      hydrateUserPageBuilderDraft({
        userId: "user-1",
        slug: "user-1",
        blocks,
      }),
    )

    expect(
      issues.some((issue) => issue.code === "presentation_persona_missing"),
    ).toBeTruthy()
    expect(
      issues.some((issue) => issue.code === "presentation_work_missing"),
    ).toBeTruthy()
    expect(issues.some((issue) => issue.code === "relation_source_missing")).toBeTruthy()
  })

  test("adapter round-trips typed constructs back into page blocks", async () => {
    const draft = hydrateUserPageBuilderDraft({
      userId: "user-1",
      slug: "user-1",
      blocks: [
        {
          id: "identity-1",
          type: "identity",
          column: "primary",
          order: 1,
          config: {},
          content: { name: "Old", tagline: "Old tagline" },
          visibility: "visible",
        },
        {
          id: "work-1",
          type: "workFeed",
          column: "primary",
          order: 2,
          config: {},
          content: { title: "Old work", items: [] },
          visibility: "visible",
        },
      ],
    })

    draft.identity = { name: "New Name", tagline: "New Tagline" }
    draft.workFeed = {
      title: "Work Flow",
      items: [
        {
          id: "artifact-1",
          title: "Artifact",
          workType: "artifact",
          summary: null,
          status: "published",
          tags: ["systems"],
          associatedPersonaIds: [],
          intendedAudienceScopes: ["public"],
          timestampLabel: "Recently updated",
          href: null,
          isRepresentative: true,
        },
      ],
    }

    const blocks = serializeUserPageBuilderDraft(draft)
    const identityBlock = blocks.find((block) => block.type === "identity")
    const workBlock = blocks.find((block) => block.type === "workFeed")

    expect(identityBlock?.content).toEqual({
      name: "New Name",
      tagline: "New Tagline",
    })
    expect(workBlock?.content).toEqual({
      title: "Work Flow",
      items: [
        {
          id: "artifact-1",
          title: "Artifact",
          workType: "artifact",
          summary: null,
          status: "published",
          tags: ["systems"],
          associatedPersonaIds: [],
          intendedAudienceScopes: ["public"],
          timestampLabel: "Recently updated",
          href: null,
          isRepresentative: true,
        },
      ],
    })
  })

  test("deleting a typed construct block resets draft state and removes the block", async () => {
    const draft = hydrateUserPageBuilderDraft({
      userId: "user-1",
      slug: "user-1",
      blocks: [
        {
          id: "work-1",
          type: "workFeed",
          column: "primary",
          order: 1,
          config: {},
          content: {
            title: "Custom Work",
            emptyMessage: "Nothing here yet",
            items: [
              {
                id: "artifact-1",
                title: "Artifact",
                workType: "artifact",
                summary: null,
                status: "published",
                tags: [],
                associatedPersonaIds: [],
                intendedAudienceScopes: ["public"],
                timestampLabel: "Now",
                href: null,
                isRepresentative: true,
              },
            ],
          },
          visibility: "visible",
        },
      ],
    })

    const nextDraft = deleteUserPageBuilderDraftBlock(draft, "work-1")

    expect(nextDraft.workFeed).toEqual({
      title: "Work Flow",
      emptyMessage: "",
      items: [],
    })
    expect(
      serializeUserPageBuilderDraft(nextDraft).some(
        (block) => block.type === "workFeed",
      ),
    ).toBeFalsy()
  })

  test("re-adding a typed construct block restores registry defaults without stale draft content", async () => {
    const hydrated = hydrateUserPageBuilderDraft({
      userId: "user-1",
      slug: "user-1",
      blocks: [
        {
          id: "relations-1",
          type: "relationshipManager",
          column: "auxiliary",
          order: 1,
          config: {},
          content: {
            relations: [
              {
                id: "relation-1",
                sourcePersonaId: "persona-1",
                targetLabel: "Target",
                targetType: "external",
                relationKind: "trusted",
                audienceScope: "public",
                note: null,
                status: "active",
              },
            ],
          },
          visibility: "visible",
        },
      ],
    })

    const deleted = deleteUserPageBuilderDraftBlock(hydrated, "relations-1")
    const readded = addUserPageBuilderDraftBlock(deleted, {
      type: "relationshipManager",
      column: "auxiliary",
      id: "relations-2",
    })

    expect(readded.relationshipManager).toEqual({
      relations: [],
    })

    const relationBlock = serializeUserPageBuilderDraft(readded).find(
      (block) => block.id === "relations-2",
    )
    expect(relationBlock?.content).toEqual({
      relations: [],
    })
  })

  test("resetting a typed construct block restores default config and content", async () => {
    const draft = hydrateUserPageBuilderDraft({
      userId: "user-1",
      slug: "user-1",
      blocks: [
        {
          id: "primary-1",
          type: "primaryPersona",
          column: "primary",
          order: 1,
          config: {
            allowUnset: false,
            emphasizeOptionality: false,
          },
          content: {
            primaryPersonaId: "persona-1",
            explanation: "Custom explanation",
          },
          visibility: "visible",
        },
      ],
    })

    const nextDraft = resetUserPageBuilderDraftBlock(draft, "primary-1")
    const resetBlock = serializeUserPageBuilderDraft(nextDraft).find(
      (block) => block.id === "primary-1",
    )

    expect(nextDraft.primaryPersona).toEqual({
      primaryPersonaId: null,
      explanation: "",
    })
    expect(resetBlock?.config).toEqual({
      allowUnset: true,
      emphasizeOptionality: true,
    })
    expect(resetBlock?.content).toEqual({
      primaryPersonaId: null,
      explanation: "",
    })
  })

  test("moving a block reorders the single primary user-page sequence", async () => {
    const draft = hydrateUserPageBuilderDraft({
      userId: "user-1",
      slug: "user-1",
      blocks: [
        {
          id: "identity-1",
          type: "identity",
          column: "primary",
          order: 1,
          config: {},
          content: { name: "Name" },
          visibility: "visible",
        },
        {
          id: "bio-1",
          type: "bio",
          column: "primary",
          order: 2,
          config: {},
          content: { text: "Bio" },
          visibility: "visible",
        },
        {
          id: "relations-1",
          type: "relationshipManager",
          column: "auxiliary",
          order: 1,
          config: {},
          content: { relations: [] },
          visibility: "visible",
        },
      ],
    })

    const moved = moveUserPageBuilderDraftBlock(draft, "bio-1", "up")
    const serialized = serializeUserPageBuilderDraft(moved)

    const identityBlock = serialized.find((block) => block.id === "identity-1")
    const bioBlock = serialized.find((block) => block.id === "bio-1")
    const relationsBlock = serialized.find((block) => block.id === "relations-1")

    expect(identityBlock?.order).toBe(2)
    expect(bioBlock?.order).toBe(1)
    expect(relationsBlock?.order).toBe(3)
  })

  test("toggling visibility only updates the targeted block", async () => {
    const draft = hydrateUserPageBuilderDraft({
      userId: "user-1",
      slug: "user-1",
      blocks: [
        {
          id: "identity-1",
          type: "identity",
          column: "primary",
          order: 1,
          config: {},
          content: { name: "Name" },
          visibility: "visible",
        },
        {
          id: "bio-1",
          type: "bio",
          column: "primary",
          order: 2,
          config: {},
          content: { text: "Bio" },
          visibility: "hidden",
        },
      ],
    })

    const toggled = toggleUserPageBuilderDraftBlockVisibility(draft, "identity-1")
    const serialized = serializeUserPageBuilderDraft(toggled)

    const identityBlock = serialized.find((block) => block.id === "identity-1")
    const bioBlock = serialized.find((block) => block.id === "bio-1")

    expect(identityBlock?.visibility).toBe("hidden")
    expect(bioBlock?.visibility).toBe("hidden")
  })

  test("hydration normalizes legacy auxiliary user-page blocks into primary order", async () => {
    const draft = hydrateUserPageBuilderDraft({
      userId: "user-1",
      slug: "user-1",
      blocks: [
        {
          id: "identity-1",
          type: "identity",
          column: "primary",
          order: 1,
          config: {},
          content: { name: "Name" },
          visibility: "visible",
        },
        {
          id: "persona-manager-1",
          type: "personaManager",
          column: "auxiliary",
          order: 1,
          config: {},
          content: { personas: [] },
          visibility: "visible",
        },
        {
          id: "relationship-manager-1",
          type: "relationshipManager",
          column: "auxiliary",
          order: 2,
          config: {},
          content: { relations: [] },
          visibility: "visible",
        },
      ],
    })

    expect(draft.blocks.map((block) => block.column)).toEqual([
      "primary",
      "primary",
      "primary",
    ])
    expect(draft.blocks.map((block) => block.order)).toEqual([1, 2, 3])
    expect(draft.blocks.map((block) => block.id)).toEqual([
      "identity-1",
      "persona-manager-1",
      "relationship-manager-1",
    ])
  })
})
