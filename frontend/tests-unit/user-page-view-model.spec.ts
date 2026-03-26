import { expect, test } from "@playwright/test"

import type { TemplateBlock } from "@/components/Page/registry"
import {
  buildUserPageViewModel,
  filterWorkFeedForAudience,
  normalizeWeightedTag,
  resolvePrimaryPersonaId,
} from "@/hooks/useUserPageViewModel"

test.describe("user page view model helpers", () => {
  test("normalizeWeightedTag clamps weight and defaults source", async () => {
    const tag = normalizeWeightedTag({
      label: "Systems",
      weight: 4,
    })

    expect(tag).not.toBeNull()
    expect(tag?.weight).toBe(1)
    expect(tag?.source).toBe("user")
  })

  test("resolvePrimaryPersonaId accepts only known persona ids", async () => {
    expect(resolvePrimaryPersonaId("persona-1", ["persona-1"])).toBe(
      "persona-1",
    )
    expect(resolvePrimaryPersonaId("persona-2", ["persona-1"])).toBeNull()
  })

  test("filterWorkFeedForAudience keeps only visible work ids for visitors", async () => {
    const visible = filterWorkFeedForAudience(
      [
        {
          id: "work-1",
          title: "Visible",
          workType: "artifact",
          summary: null,
          status: "published",
          tags: [],
          associatedPersonaIds: [],
          intendedAudienceScopes: ["public"],
          timestampLabel: "Recently",
          href: null,
          isRepresentative: true,
        },
        {
          id: "work-2",
          title: "Hidden",
          workType: "artifact",
          summary: null,
          status: "published",
          tags: [],
          associatedPersonaIds: [],
          intendedAudienceScopes: ["public"],
          timestampLabel: "Recently",
          href: null,
          isRepresentative: true,
        },
      ],
      [
        {
          id: "presentation-1",
          personaId: "persona-1",
          audienceScope: "public",
          audienceLabel: "Public",
          headline: "Public View",
          framingText: null,
          visibleWorkIds: ["work-1"],
          relationCallToAction: "none",
        },
      ],
      "public",
      false,
    )

    expect(visible).toHaveLength(1)
    expect(visible[0]?.id).toBe("work-1")
  })

  test("buildUserPageViewModel derives owner-manage mode and associated counts", async () => {
    const blocks: TemplateBlock[] = [
      {
        id: "primary-1",
        type: "primaryPersona",
        column: "primary",
        order: 1,
        config: {},
        content: { primaryPersonaId: "persona-1" },
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
              shortBio: "Writes and builds.",
              publicationState: "published",
              tags: [{ id: "tag-1", label: "writing", weight: 0.7 }],
            },
          ],
        },
        visibility: "visible",
      },
      {
        id: "work-feed-1",
        type: "workFeed",
        column: "primary",
        order: 2,
        config: {},
        content: {
          items: [
            {
              id: "work-1",
              title: "Prompt Builder Revision",
              workType: "prompt",
              associatedPersonaIds: ["persona-1"],
              intendedAudienceScopes: ["public"],
              tags: ["builder"],
              isRepresentative: true,
            },
          ],
        },
        visibility: "visible",
      },
      {
        id: "audience-1",
        type: "audiencePresentation",
        column: "primary",
        order: 3,
        config: {},
        content: {
          presentations: [
            {
              id: "presentation-1",
              personaId: "persona-1",
              audienceScope: "public",
              audienceLabel: "Public",
              headline: "Public Work",
              visibleWorkIds: ["work-1"],
              relationCallToAction: "follow_work",
            },
          ],
        },
        visibility: "visible",
      },
    ]

    const viewModel = buildUserPageViewModel({
      slug: "user-1",
      userId: "user-1",
      isOwner: true,
      pageExists: true,
      blocks,
      libraryPersonas: [],
    })

    expect(viewModel.mode).toBe("owner-manage")
    expect(viewModel.primaryPersonaId).toBe("persona-1")
    expect(viewModel.personas[0]?.associatedWorkCount).toBe(1)
    expect(viewModel.selectedAudienceScope).toBe("public")
  })
})
