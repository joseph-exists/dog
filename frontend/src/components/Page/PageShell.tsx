// src/components/Page/PageShell.tsx
import { useCallback, useState } from "react"

import { PageHeader } from "./PageHeader"
import { PageLayout } from "./PageLayout"
import {
  ProfileImageBlock,
  IdentityBlock,
  BioBlock,
  ContactBlock,
  LinksBlock,
  RelationshipsBlock,
  ActivityFeedBlock,
  GalleryBlock,
  DataTableBlock,
  ChartBlock,
} from "./blocks"
import { getDefaultTemplate, type TemplateBlock } from "./registry"

/**
 * Entity data structure for page display
 */
export interface PageEntity {
  id: string
  typeId: string
  name: string
  slug?: string
  avatarUrl?: string
  tagline?: string
  bio?: string
  email?: string
  phone?: string
  links?: Array<{
    id: string
    type: "website" | "github" | "twitter" | "linkedin" | "other"
    url: string
    label?: string
  }>
  relationships?: Array<{
    id: string
    typeId: string
    name: string
    avatarUrl?: string
    badges?: string[]
    relationshipTypeId: string
  }>
  activities?: Array<{
    id: string
    type: "message" | "joined" | "updated" | "other"
    description: string
    timestamp: Date
  }>
  images?: Array<{
    id: string
    url: string
    alt?: string
    caption?: string
  }>
  createdAt: Date
  updatedAt: Date
}

export interface PageShellProps {
  entity: PageEntity
  isOwner: boolean
  blocks?: TemplateBlock[]
  onDelete?: () => void
}

/**
 * PageShell - Main container that orchestrates the page layout
 *
 * Renders the PageHeader and PageLayout with blocks based on
 * the provided template or the default template for the entity type.
 */
export function PageShell({
  entity,
  isOwner,
  blocks: customBlocks,
  onDelete,
}: PageShellProps) {
  const [editMode, setEditMode] = useState(false)

  // Get blocks from custom override or default template
  const blocks = customBlocks ?? getDefaultTemplate(entity.typeId).defaultBlocks

  /**
   * Copy current URL to clipboard
   */
  const handleShare = useCallback(async () => {
    await navigator.clipboard.writeText(window.location.href)
  }, [])

  /**
   * Placeholder for adding new blocks
   */
  const handleAddBlock = useCallback((column: "primary" | "auxiliary") => {
    console.log("Add block to column:", column)
  }, [])

  /**
   * Render a block component based on its type
   */
  const renderBlock = useCallback(
    (block: TemplateBlock, canEdit: boolean): React.ReactNode => {
      const config = block.config

      switch (block.type) {
        case "profileImage":
          return (
            <ProfileImageBlock
              config={{
                shape: (config.shape as "circle" | "square") ?? "circle",
                size: (config.size as "sm" | "md" | "lg") ?? "md",
              }}
              entity={{ name: entity.name, avatarUrl: entity.avatarUrl }}
              canEdit={canEdit}
            />
          )

        case "identity":
          return (
            <IdentityBlock
              config={{
                showTagline: (config.showTagline as boolean) ?? true,
              }}
              entity={{ name: entity.name, tagline: entity.tagline }}
              canEdit={canEdit}
            />
          )

        case "bio":
          return (
            <BioBlock
              config={{
                maxLength: config.maxLength as number | undefined,
                allowRichText: config.allowRichText as boolean | undefined,
              }}
              bio={entity.bio}
              canEdit={canEdit}
            />
          )

        case "contact":
          return (
            <ContactBlock
              config={{
                showEmail: (config.showEmail as boolean) ?? true,
                showPhone: (config.showPhone as boolean) ?? false,
              }}
              contact={{ email: entity.email, phone: entity.phone }}
            />
          )

        case "links":
          return (
            <LinksBlock
              config={{
                layout: (config.layout as "list" | "grid") ?? "list",
              }}
              links={entity.links ?? []}
            />
          )

        case "relationships":
          return (
            <RelationshipsBlock
              config={{
                groupByType: (config.groupByType as boolean) ?? true,
                maxVisible: (config.maxVisible as number) ?? 10,
              }}
              relationships={entity.relationships ?? []}
              canEdit={canEdit}
            />
          )

        case "activityFeed":
          return (
            <ActivityFeedBlock
              config={{
                maxItems: (config.maxItems as number) ?? 5,
              }}
              activities={entity.activities ?? []}
            />
          )

        case "gallery":
          return (
            <GalleryBlock
              config={{
                columns: (config.columns as number) ?? 3,
                lightbox: (config.lightbox as boolean) ?? true,
              }}
              images={entity.images ?? []}
            />
          )

        case "dataTable":
          return (
            <DataTableBlock
              config={{
                title: (config.title as string) ?? "",
                dataSource: (config.dataSource as string) ?? "",
                columns: (config.columns as Array<{
                  key: string
                  label: string
                  width?: string
                }>) ?? [],
                maxRows: (config.maxRows as number) ?? 10,
              }}
            />
          )

        case "chart":
          return (
            <ChartBlock
              config={{
                title: (config.title as string) ?? "",
                chartType: (config.chartType as "area" | "bar" | "line" | "pie") ?? "bar",
                dataSource: (config.dataSource as string) ?? "",
              }}
            />
          )

        default:
          return null
      }
    },
    [entity]
  )

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        entityTypeId={entity.typeId}
        entityName={entity.name}
        createdAt={entity.createdAt}
        updatedAt={entity.updatedAt}
        isOwner={isOwner}
        editMode={editMode}
        onEditModeChange={setEditMode}
        onShare={handleShare}
        onDelete={onDelete}
      />
      <PageLayout
        blocks={blocks}
        editMode={editMode}
        onAddBlock={handleAddBlock}
        renderBlock={renderBlock}
      />
    </div>
  )
}
