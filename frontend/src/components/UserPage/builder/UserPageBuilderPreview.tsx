import { useMemo } from "react"

import {
  AudiencePresentationBlock,
  BioBlock,
  IdentityBlock,
  PersonaManagerBlock,
  PrimaryPersonaBlock,
  RelationshipManagerBlock,
  WorkFeedBlock,
} from "@/components/Page/blocks"
import { PageLayout } from "@/components/Page/PageLayout"
import type { TemplateBlock } from "@/components/Page/registry"
import type { UserPageViewModel } from "@/components/UserPage/types"

interface UserPageBuilderPreviewProps {
  blocks: TemplateBlock[]
  entityId: string
  viewModel: UserPageViewModel
}

export function UserPageBuilderPreview({
  blocks,
  entityId,
  viewModel,
}: UserPageBuilderPreviewProps) {
  const visibleBlocks = useMemo(
    () => blocks.filter((block) => block.visibility !== "hidden"),
    [blocks],
  )

  const renderBlock = (block: TemplateBlock) => {
    const config = block.config
    const content = block.content as Record<string, unknown> | undefined

    switch (block.type) {
      case "identity":
        return (
          <IdentityBlock
            config={{ showTagline: (config.showTagline as boolean) ?? true }}
            content={
              content
                ? {
                    name: (content.name as string) ?? "",
                    tagline: content.tagline as string | undefined,
                  }
                : undefined
            }
          />
        )
      case "bio":
        return (
          <BioBlock
            config={{
              maxLength: config.maxLength as number | undefined,
              allowRichText: config.allowRichText as boolean | undefined,
            }}
            content={
              content?.text ? { text: content.text as string } : undefined
            }
          />
        )
      case "primaryPersona":
        return (
          <PrimaryPersonaBlock
            config={{
              allowUnset: (config.allowUnset as boolean) ?? true,
              emphasizeOptionality:
                (config.emphasizeOptionality as boolean) ?? true,
            }}
            content={
              content
                ? {
                    primaryPersonaId:
                      (content.primaryPersonaId as string | null) ?? null,
                    explanation: content.explanation as string | undefined,
                  }
                : undefined
            }
            viewModel={viewModel}
            entityId={entityId}
            isOwner
            isEditing={false}
          />
        )
      case "workFeed":
        return (
          <WorkFeedBlock
            config={{
              layout: "stack",
              maxVisible: (config.maxVisible as number) ?? 8,
              showPersonaBadges:
                (config.showPersonaBadges as boolean) ?? true,
              showAudienceBadges:
                (config.showAudienceBadges as boolean) ?? true,
            }}
            content={
              content
                ? {
                    title: content.title as string | undefined,
                    emptyMessage: content.emptyMessage as string | undefined,
                    items:
                      (content.items as UserPageViewModel["workFeed"]) ?? [],
                  }
                : undefined
            }
            viewModel={viewModel}
            entityId={entityId}
          />
        )
      case "personaManager":
        return (
          <PersonaManagerBlock
            config={{
              allowCreate: false,
              allowPrimarySelection: true,
              allowPublishing: true,
              allowTagEditing: true,
            }}
            content={
              content
                ? {
                    personas:
                      (content.personas as UserPageViewModel["personas"]) ?? [],
                  }
                : undefined
            }
            viewModel={viewModel}
            entityId={entityId}
          />
        )
      case "audiencePresentation":
        return (
          <AudiencePresentationBlock
            config={{
              allowAudienceSwitching:
                (config.allowAudienceSwitching as boolean) ?? true,
              showPreviewCards:
                (config.showPreviewCards as boolean) ?? true,
            }}
            content={
              content
                ? {
                    presentations:
                      (content.presentations as UserPageViewModel["audiencePresentations"]) ??
                      [],
                  }
                : undefined
            }
            viewModel={viewModel}
            entityId={entityId}
          />
        )
      case "relationshipManager":
        return (
          <RelationshipManagerBlock
            config={{
              allowCreate: false,
              allowEditing: true,
              audienceScoped: (config.audienceScoped as boolean) ?? true,
            }}
            content={
              content
                ? {
                    relations:
                      (content.relations as UserPageViewModel["relations"]) ?? [],
                  }
                : undefined
            }
            viewModel={viewModel}
            entityId={entityId}
          />
        )
      default:
        return null
    }
  }

  return (
    <div className="h-full overflow-hidden rounded-lg border bg-background">
      <div className="border-b px-4 py-3">
        <div className="text-sm font-medium">Runtime Preview</div>
        <div className="text-xs text-muted-foreground">
          Preview of the current unsaved user-page draft.
        </div>
      </div>
      <div className="h-[calc(100%-57px)] overflow-hidden">
        <PageLayout
          blocks={visibleBlocks}
          editMode={false}
          renderBlock={renderBlock}
        />
      </div>
    </div>
  )
}
