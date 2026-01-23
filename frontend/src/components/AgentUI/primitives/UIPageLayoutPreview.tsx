import {
  type BlockType,
  getBlockType,
  type TemplateBlock,
} from "@/components/Page/registry"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import type { UIPageLayoutPreviewData } from "../types"

export function UIPageLayoutPreview({
  data,
}: {
  data: UIPageLayoutPreviewData
}) {
  const layoutBlocks = Array.isArray(data.layout_json) ? data.layout_json : []
  const primaryBlocks = layoutBlocks.filter(
    (block) => block.column === "primary",
  )
  const auxiliaryBlocks = layoutBlocks.filter(
    (block) => block.column === "auxiliary",
  )

  const renderBlockLabel = (block: TemplateBlock) => {
    const def = getBlockType(block.type as BlockType)
    return def?.label ?? block.type
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Proposed Page Layout</CardTitle>
        {data.summary && (
          <CardDescription className="text-xs">{data.summary}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-1">
            Primary
          </p>
          <div className="flex flex-wrap gap-2">
            {primaryBlocks.length > 0 ? (
              primaryBlocks.map((block, index) => (
                <Badge key={`${block.type}-${index}`} variant="secondary">
                  {renderBlockLabel(block)}
                </Badge>
              ))
            ) : (
              <span className="text-xs text-muted-foreground">None</span>
            )}
          </div>
        </div>
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-1">
            Auxiliary
          </p>
          <div className="flex flex-wrap gap-2">
            {auxiliaryBlocks.length > 0 ? (
              auxiliaryBlocks.map((block, index) => (
                <Badge key={`${block.type}-${index}`} variant="outline">
                  {renderBlockLabel(block)}
                </Badge>
              ))
            ) : (
              <span className="text-xs text-muted-foreground">None</span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
