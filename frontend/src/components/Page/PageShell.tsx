// src/components/Page/PageShell.tsx
import { useEffect, useMemo, useState } from "react"

import { usePageEditor } from "@/hooks/usePageEditor"
import { BlockWrapper } from "./BlockWrapper"
import {
  ActivityFeedBlock,
  BioBlock,
  ChartBlock,
  ContactBlock,
  DataTableBlock,
  GalleryBlock,
  IdentityBlock,
  LinksBlock,
  ProfileImageBlock,
  RelationshipsBlock,
} from "./blocks"
import { BlockEditorSheet, BlockPalette } from "./editor"
import { PageHeader } from "./PageHeader"
import { PageLayout } from "./PageLayout"
import type { TemplateBlock } from "./registry"

interface PageShellProps {
  entityType: string
  entityId: string
  isOwner: boolean
  onDelete?: () => void
}

/**
 * PageShell - Main container that orchestrates the page layout
 *
 * Uses usePageEditor hook to manage layout state and editing.
 * Renders the PageHeader, PageLayout with blocks, and editor components.
 */
export function PageShell({
  entityType,
  entityId,
  isOwner,
  onDelete,
}: PageShellProps) {
  const [paletteOpen, setPaletteOpen] = useState(true)
  const [targetColumn, setTargetColumn] = useState<"primary" | "auxiliary">(
    "primary",
  )

  const {
    blocks,
    isLoading,
    isEditing,
    isDirty,
    isSaving,
    selectedBlockId,
    selectedBlock,
    startEditing,
    cancelEditing,
    save,
    selectBlock,
    updateBlockContent,
    addBlock,
    removeBlock,
    reorderBlocks,
    toggleBlockVisibility,
  } = usePageEditor(entityType, entityId)

  // Compute entity name from identity block content
  const entityName = useMemo(() => {
    if (!blocks) return "Page"
    const identityBlock = blocks.find((b) => b.type === "identity")
    const name = identityBlock?.content?.name as string | undefined
    return name || "Untitled Page"
  }, [blocks])

  // Warn user about unsaved changes when leaving the page
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault()
        // Modern browsers show a generic message, but we set returnValue for compatibility
        e.returnValue =
          "You have unsaved changes. Are you sure you want to leave?"
        return e.returnValue
      }
    }

    window.addEventListener("beforeunload", handleBeforeUnload)
    return () => window.removeEventListener("beforeunload", handleBeforeUnload)
  }, [isDirty])

  const handleShare = async () => {
    await navigator.clipboard.writeText(window.location.href)
  }

  const handleEditModeChange = async (editing: boolean) => {
    if (editing) {
      startEditing()
    } else {
      if (isDirty) {
        await save()
      } else {
        cancelEditing()
      }
    }
  }

  const handleAddBlock = (column: "primary" | "auxiliary") => {
    setTargetColumn(column)
    // The palette is used to pick block types
  }

  const handleSaveBlock = (
    blockId: string,
    content: Record<string, unknown>,
  ) => {
    updateBlockContent(blockId, content)
  }

  const handleMoveBlock = (blockId: string, direction: "up" | "down") => {
    if (!blocks) return

    const block = blocks.find((b) => b.id === blockId)
    if (!block) return

    const columnBlocks = blocks
      .filter((b) => b.column === block.column)
      .sort((a, b) => a.order - b.order)

    const currentIndex = columnBlocks.findIndex((b) => b.id === blockId)
    if (currentIndex === -1) return

    const newIndex = direction === "up" ? currentIndex - 1 : currentIndex + 1
    if (newIndex < 0 || newIndex >= columnBlocks.length) return

    // Swap positions in the ordered array
    const newOrder = columnBlocks.map((b) => b.id!)
    ;[newOrder[currentIndex], newOrder[newIndex]] = [
      newOrder[newIndex],
      newOrder[currentIndex],
    ]

    reorderBlocks(block.column, newOrder)
  }

  const getBlockPosition = (blockId: string) => {
    if (!blocks) return { isFirst: true, isLast: true }

    const block = blocks.find((b) => b.id === blockId)
    if (!block) return { isFirst: true, isLast: true }

    const columnBlocks = blocks
      .filter((b) => b.column === block.column)
      .sort((a, b) => a.order - b.order)

    const index = columnBlocks.findIndex((b) => b.id === blockId)
    return {
      isFirst: index === 0,
      isLast: index === columnBlocks.length - 1,
    }
  }

  const renderBlock = (block: TemplateBlock): React.ReactNode => {
    const config = block.config
    // Content is stored as Record<string, unknown>, blocks handle missing fields gracefully
    const content = block.content as Record<string, unknown> | undefined

    const blockContent = (() => {
      switch (block.type) {
        case "profileImage":
          return (
            <ProfileImageBlock
              config={{
                shape: (config.shape as "circle" | "square") ?? "circle",
                size: (config.size as "sm" | "md" | "lg") ?? "md",
              }}
              content={
                content
                  ? {
                      imageUrl: content.imageUrl as string | undefined,
                      alt: content.alt as string | undefined,
                    }
                  : undefined
              }
            />
          )

        case "identity":
          return (
            <IdentityBlock
              config={{
                showTagline: (config.showTagline as boolean) ?? true,
              }}
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

        case "contact":
          return (
            <ContactBlock
              config={{
                showEmail: (config.showEmail as boolean) ?? true,
                showPhone: (config.showPhone as boolean) ?? false,
              }}
              content={
                content
                  ? {
                      email: content.email as string | undefined,
                      phone: content.phone as string | undefined,
                    }
                  : undefined
              }
            />
          )

        case "links":
          return (
            <LinksBlock
              config={{
                layout: (config.layout as "list" | "grid") ?? "list",
              }}
              content={
                content?.items
                  ? {
                      items: content.items as Array<{
                        id: string
                        type:
                          | "website"
                          | "github"
                          | "twitter"
                          | "linkedin"
                          | "other"
                        url: string
                        label?: string
                      }>,
                    }
                  : undefined
              }
            />
          )

        case "relationships":
          return (
            <RelationshipsBlock
              config={{
                groupByType: (config.groupByType as boolean) ?? true,
                maxVisible: (config.maxVisible as number) ?? 10,
              }}
              content={
                content?.items
                  ? {
                      items: content.items as Array<{
                        id: string
                        typeId: string
                        name: string
                        avatarUrl?: string
                        badges?: string[]
                        relationshipTypeId: string
                      }>,
                    }
                  : undefined
              }
            />
          )

        case "activityFeed":
          return (
            <ActivityFeedBlock
              config={{
                maxItems: (config.maxItems as number) ?? 5,
              }}
              content={
                content?.activities
                  ? {
                      activities: content.activities as Array<{
                        id: string
                        type: "message" | "joined" | "updated" | "other"
                        description: string
                        timestamp: Date
                      }>,
                    }
                  : undefined
              }
            />
          )

        case "gallery":
          return (
            <GalleryBlock
              config={{
                columns: (config.columns as number) ?? 3,
                lightbox: (config.lightbox as boolean) ?? true,
              }}
              content={
                content?.images
                  ? {
                      images: content.images as Array<{
                        id: string
                        url: string
                        alt?: string
                        caption?: string
                      }>,
                    }
                  : undefined
              }
            />
          )

        case "dataTable":
          return (
            <DataTableBlock
              config={{
                title: (config.title as string) ?? "",
                dataSource: (config.dataSource as string) ?? "",
                columns:
                  (config.columns as Array<{
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
                chartType:
                  (config.chartType as "area" | "bar" | "line" | "pie") ??
                  "bar",
                dataSource: (config.dataSource as string) ?? "",
              }}
            />
          )

        default:
          return null
      }
    })()

    // Wrap with BlockWrapper for selection in edit mode
    const { isFirst, isLast } = getBlockPosition(block.id ?? "")

    return (
      <BlockWrapper
        blockId={block.id ?? ""}
        isEditing={isEditing}
        isSelected={selectedBlockId === block.id}
        isVisible={block.visibility !== "hidden"}
        isFirst={isFirst}
        isLast={isLast}
        onSelect={selectBlock}
        onMoveUp={(id) => handleMoveBlock(id, "up")}
        onMoveDown={(id) => handleMoveBlock(id, "down")}
        onToggleVisibility={toggleBlockVisibility}
        onDelete={removeBlock}
      >
        {blockContent}
      </BlockWrapper>
    )
  }

  if (isLoading) {
    return <div className="p-4">Loading...</div>
  }

  return (
    <div className="flex h-full">
      {/* Block Palette (edit mode only) */}
      {isEditing && (
        <BlockPalette
          onAddBlock={addBlock}
          targetColumn={targetColumn}
          isOpen={paletteOpen}
          onToggle={() => setPaletteOpen(!paletteOpen)}
        />
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        <PageHeader
          entityTypeId={entityType}
          entityName={entityName}
          createdAt={new Date()}
          updatedAt={new Date()}
          isOwner={isOwner}
          editMode={isEditing}
          onEditModeChange={handleEditModeChange}
          onSave={save}
          onShare={handleShare}
          onDelete={onDelete}
          isSaving={isSaving}
          isDirty={isDirty}
        />
        <div className="flex-1 overflow-hidden">
          <PageLayout
            blocks={blocks ?? []}
            editMode={isEditing}
            onAddBlock={handleAddBlock}
            renderBlock={renderBlock}
          />
        </div>
      </div>

      {/* Block Editor Sheet */}
      <BlockEditorSheet
        block={selectedBlock}
        onSave={handleSaveBlock}
        onClose={() => selectBlock(null)}
      />
    </div>
  )
}
