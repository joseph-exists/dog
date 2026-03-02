import {
  ArrowDown,
  ArrowUp,
  Eye,
  EyeOff,
  Pencil,
  RotateCcw,
  Trash2,
} from "lucide-react"

import type { TemplateBlock } from "@/components/Page/registry"
import { getBlockType } from "@/components/Page/registry"
import type { UserPageViewModel } from "@/components/UserPage/types"
import {
  getSurfaceForBlockType,
  type UserPageBuilderSurface,
} from "./userPageBuilderSchema"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

const SURFACE_DESCRIPTIONS: Record<UserPageBuilderSurface, string> = {
  overview:
    "A high-level inventory of the current user-page composition and its references.",
  layout:
    "Structural blocks that shape the page shell and general presentation.",
  work:
    "Work flow blocks and the representative artifacts they surface.",
  personas:
    "Persona constructs, including primary persona framing and persona management.",
  audiences:
    "Audience-specific views and the work those views expose.",
  relations:
    "Persona-mediated relations and their audience-specific framing.",
}

interface UserPageBuilderSurfaceEditorProps {
  selectedSurface: UserPageBuilderSurface
  blocks: TemplateBlock[]
  viewModel: UserPageViewModel
  selectedBlockId: string | null
  onSelectBlock: (blockId: string) => void
  onMoveBlock: (blockId: string, direction: "up" | "down") => void
  onToggleVisibility: (blockId: string) => void
  onResetBlock: (blockId: string) => void
  onDeleteBlock: (blockId: string) => void
}

function getSurfaceMetrics(
  surface: UserPageBuilderSurface,
  viewModel: UserPageViewModel,
  blocks: TemplateBlock[],
) {
  if (surface === "overview") {
    return [
      { label: "Work Items", value: viewModel.workFeed.length },
      { label: "Personas", value: viewModel.personas.length },
      { label: "Audience Views", value: viewModel.audiencePresentations.length },
      { label: "Relations", value: viewModel.relations.length },
    ]
  }
  if (surface === "work") {
    return [
      { label: "Representative", value: viewModel.workFeed.filter((item) => item.isRepresentative).length },
      { label: "Associated Personas", value: new Set(viewModel.workFeed.flatMap((item) => item.associatedPersonaIds)).size },
    ]
  }
  if (surface === "personas") {
    return [
      { label: "Primary Persona", value: viewModel.primaryPersonaId ? 1 : 0 },
      { label: "Published", value: viewModel.personas.filter((persona) => persona.publicationState === "published").length },
    ]
  }
  if (surface === "audiences") {
    return [
      { label: "Audience Views", value: viewModel.audiencePresentations.length },
      { label: "Visible Work Links", value: viewModel.audiencePresentations.reduce((count, item) => count + item.visibleWorkIds.length, 0) },
    ]
  }
  if (surface === "relations") {
    return [
      { label: "Active Relations", value: viewModel.relations.filter((relation) => relation.status === "active").length },
      { label: "Pending Relations", value: viewModel.relations.filter((relation) => relation.status === "pending").length },
    ]
  }
  return [{ label: "Blocks", value: blocksForSurface(surface, blocks) }]
}

function blocksForSurface(surface: UserPageBuilderSurface, blocks: TemplateBlock[]) {
  if (surface === "overview") return blocks.length
  return blocks.filter((block) => getSurfaceForBlockType(block.type) === surface).length
}

export function UserPageBuilderSurfaceEditor({
  selectedSurface,
  blocks,
  viewModel,
  selectedBlockId,
  onSelectBlock,
  onMoveBlock,
  onToggleVisibility,
  onResetBlock,
  onDeleteBlock,
}: UserPageBuilderSurfaceEditorProps) {
  const scopedBlocks =
    selectedSurface === "overview"
      ? blocks
      : blocks.filter(
          (block) => getSurfaceForBlockType(block.type) === selectedSurface,
        )

  const metrics = getSurfaceMetrics(selectedSurface, viewModel, blocks)

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>
            {selectedSurface === "overview"
              ? "Composition Overview"
              : `${selectedSurface[0]?.toUpperCase()}${selectedSurface.slice(1)} Surface`}
          </CardTitle>
          <CardDescription>{SURFACE_DESCRIPTIONS[selectedSurface]}</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2">
          {metrics.map((metric) => (
            <div key={metric.label} className="rounded border px-3 py-2">
              <div className="text-xs text-muted-foreground">{metric.label}</div>
              <div className="text-lg font-semibold">{metric.value}</div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Scoped Blocks</CardTitle>
          <CardDescription>
            Select blocks to edit their content, and manage structure directly
            from the compositor.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {scopedBlocks.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No blocks are currently assigned to this surface.
            </p>
          ) : (
            scopedBlocks
              .slice()
              .sort((a, b) => a.order - b.order)
              .map((block, index, allBlocks) => {
                const blockType = getBlockType(block.type)
                const isSelected = selectedBlockId === block.id
                const previous = allBlocks[index - 1]
                const next = allBlocks[index + 1]
                const isFirstInColumn = !previous
                const isLastInColumn = !next

                return (
                  <div
                    key={block.id}
                    className={`rounded border px-3 py-3 ${isSelected ? "border-primary ring-1 ring-primary" : ""}`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-sm font-medium">
                          {blockType?.label || block.type}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          order {block.order} · {block.visibility ?? "visible"}
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        {block.id && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => onSelectBlock(block.id!)}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                        )}
                        {block.id && (
                          <>
                            <Button
                              variant="ghost"
                              size="icon"
                              disabled={isFirstInColumn}
                              onClick={() => onMoveBlock(block.id!, "up")}
                            >
                              <ArrowUp className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              disabled={isLastInColumn}
                              onClick={() => onMoveBlock(block.id!, "down")}
                            >
                              <ArrowDown className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => onToggleVisibility(block.id!)}
                            >
                              {block.visibility === "hidden" ? (
                                <EyeOff className="h-4 w-4" />
                              ) : (
                                <Eye className="h-4 w-4" />
                              )}
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => onResetBlock(block.id!)}
                            >
                              <RotateCcw className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => onDeleteBlock(block.id!)}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })
          )}
        </CardContent>
      </Card>
    </div>
  )
}
