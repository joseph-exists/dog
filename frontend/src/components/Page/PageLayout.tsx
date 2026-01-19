// src/components/Page/PageLayout.tsx
import { Plus } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"
import { useIsMobile } from "@/hooks/use-mobile"
import { cn } from "@/lib/utils"

import type { TemplateBlock } from "./registry"

interface PageLayoutProps {
  blocks: TemplateBlock[]
  editMode: boolean
  onAddBlock?: (column: "primary" | "auxiliary") => void
  renderBlock: (block: TemplateBlock, editMode: boolean) => React.ReactNode
}

/**
 * Sorts blocks by their order property.
 */
function sortByOrder(blocks: TemplateBlock[]): TemplateBlock[] {
  return [...blocks].sort((a, b) => a.order - b.order)
}

/**
 * Renders a column of blocks with optional add button.
 */
function BlockColumn({
  blocks,
  editMode,
  onAddBlock,
  renderBlock,
  columnType,
}: {
  blocks: TemplateBlock[]
  editMode: boolean
  onAddBlock?: () => void
  renderBlock: (block: TemplateBlock, editMode: boolean) => React.ReactNode
  columnType: "primary" | "auxiliary"
}) {
  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      {blocks.map((block, index) => (
        <div key={`${block.type}-${index}`}>{renderBlock(block, editMode)}</div>
      ))}
      {editMode && onAddBlock && (
        <Button
          variant="outline"
          className={cn(
            "w-full border-dashed border-2",
            "hover:border-solid hover:bg-muted/50"
          )}
          onClick={onAddBlock}
        >
          <Plus className="mr-2 size-4" />
          Add Block to {columnType === "primary" ? "Primary" : "Auxiliary"}
        </Button>
      )}
    </div>
  )
}

/**
 * PageLayout handles responsive two-column layout for page blocks.
 *
 * Desktop (md+): Resizable panels with primary (70%) and auxiliary (30%) columns.
 * Mobile: Single stacked column with primary blocks first, then auxiliary.
 */
export function PageLayout({
  blocks,
  editMode,
  onAddBlock,
  renderBlock,
}: PageLayoutProps) {
  const isMobile = useIsMobile()

  // Split and sort blocks by column
  const primaryBlocks = sortByOrder(
    blocks.filter((b) => b.column === "primary")
  )
  const auxiliaryBlocks = sortByOrder(
    blocks.filter((b) => b.column === "auxiliary")
  )

  // Show auxiliary column if it has blocks or we're in edit mode
  const hasAuxiliary = auxiliaryBlocks.length > 0 || editMode

  // Mobile: single stacked column
  if (isMobile) {
    return (
      <div className="flex flex-col h-full overflow-y-auto p-4 space-y-4">
        {/* Primary blocks */}
        {primaryBlocks.map((block, index) => (
          <div key={`primary-${block.type}-${index}`}>
            {renderBlock(block, editMode)}
          </div>
        ))}
        {editMode && onAddBlock && (
          <Button
            variant="outline"
            className="w-full border-dashed border-2 hover:border-solid hover:bg-muted/50"
            onClick={() => onAddBlock("primary")}
          >
            <Plus className="mr-2 size-4" />
            Add Block to Primary
          </Button>
        )}

        {/* Auxiliary blocks (if any or edit mode) */}
        {hasAuxiliary && (
          <>
            {auxiliaryBlocks.map((block, index) => (
              <div key={`auxiliary-${block.type}-${index}`}>
                {renderBlock(block, editMode)}
              </div>
            ))}
            {editMode && onAddBlock && (
              <Button
                variant="outline"
                className="w-full border-dashed border-2 hover:border-solid hover:bg-muted/50"
                onClick={() => onAddBlock("auxiliary")}
              >
                <Plus className="mr-2 size-4" />
                Add Block to Auxiliary
              </Button>
            )}
          </>
        )}
      </div>
    )
  }

  // Desktop: resizable panels
  if (!hasAuxiliary) {
    // No auxiliary column - just render primary full width
    return (
      <BlockColumn
        blocks={primaryBlocks}
        editMode={editMode}
        onAddBlock={onAddBlock ? () => onAddBlock("primary") : undefined}
        renderBlock={renderBlock}
        columnType="primary"
      />
    )
  }

  return (
    <ResizablePanelGroup direction="horizontal" className="h-full">
      <ResizablePanel defaultSize={70} minSize={40}>
        <BlockColumn
          blocks={primaryBlocks}
          editMode={editMode}
          onAddBlock={onAddBlock ? () => onAddBlock("primary") : undefined}
          renderBlock={renderBlock}
          columnType="primary"
        />
      </ResizablePanel>
      <ResizableHandle withHandle />
      <ResizablePanel defaultSize={30} minSize={20} maxSize={40}>
        <BlockColumn
          blocks={auxiliaryBlocks}
          editMode={editMode}
          onAddBlock={onAddBlock ? () => onAddBlock("auxiliary") : undefined}
          renderBlock={renderBlock}
          columnType="auxiliary"
        />
      </ResizablePanel>
    </ResizablePanelGroup>
  )
}
