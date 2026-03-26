import { Edit3, Layers3 } from "lucide-react"

import type { TemplateBlock } from "@/components/Page/registry"
import { getBlockType } from "@/components/Page/registry"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import type { UserPageBuilderSurface } from "./userPageBuilderSchema"
import {
  getSurfaceForBlockType,
  type UserPageBuilderIssue,
} from "./userPageBuilderSchema"

const SURFACE_LABELS: Record<UserPageBuilderSurface, string> = {
  overview: "Overview",
  layout: "Layout",
  work: "Work",
  personas: "Personas",
  audiences: "Audiences",
  relations: "Relations",
}

interface UserPageBuilderNavigatorProps {
  blocks: TemplateBlock[]
  selectedSurface: UserPageBuilderSurface
  issues: UserPageBuilderIssue[]
  onSurfaceSelect: (surface: UserPageBuilderSurface) => void
  onEditBlock: (blockId: string) => void
}

export function UserPageBuilderNavigator({
  blocks,
  selectedSurface,
  issues,
  onSurfaceSelect,
  onEditBlock,
}: UserPageBuilderNavigatorProps) {
  const surfaces = Object.entries(SURFACE_LABELS) as Array<
    [UserPageBuilderSurface, string]
  >

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Composer Surfaces</CardTitle>
          <CardDescription>
            Move between high-level authoring concerns rather than managing the
            runtime page directly.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {surfaces.map(([surface, label]) => {
            const count =
              surface === "overview"
                ? blocks.length
                : blocks.filter(
                    (block) => getSurfaceForBlockType(block.type) === surface,
                  ).length
            return (
              <Button
                key={surface}
                variant={selectedSurface === surface ? "default" : "outline"}
                className="w-full justify-between"
                onClick={() => onSurfaceSelect(surface)}
              >
                <span>{label}</span>
                <span className="text-xs opacity-80">{count}</span>
              </Button>
            )
          })}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers3 className="h-4 w-4" />
            Blocks In Scope
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {blocks
            .filter((block) =>
              selectedSurface === "overview"
                ? true
                : getSurfaceForBlockType(block.type) === selectedSurface,
            )
            .map((block) => {
              const blockType = getBlockType(block.type)
              const issueCount = issues.filter((issue) =>
                issue.path?.startsWith(block.type),
              ).length
              return (
                <div
                  key={block.id}
                  className="flex items-center justify-between rounded border px-3 py-2"
                >
                  <div>
                    <div className="text-sm font-medium">
                      {blockType?.label || block.type}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      order {block.order}
                      {issueCount > 0 ? ` · ${issueCount} issue(s)` : ""}
                    </div>
                  </div>
                  {block.id && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => onEditBlock(block.id!)}
                    >
                      <Edit3 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              )
            })}
        </CardContent>
      </Card>
    </div>
  )
}
