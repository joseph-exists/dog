import { CalendarClock, Eye, Globe2, Lock } from "lucide-react"
import type { SvgAssetPublic } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

interface SvgCardProps {
  asset: SvgAssetPublic
  onPreview: (asset: SvgAssetPublic) => void
  onDelete: (asset: SvgAssetPublic) => void
  onCreatePublicCopy: (asset: SvgAssetPublic) => void
}

export function SvgCard({
  asset,
  onPreview,
  onDelete,
  onCreatePublicCopy,
}: SvgCardProps) {
  const isPublic = asset.visibility === "public"
  const svgDataUrl = `data:image/svg+xml,${encodeURIComponent(asset.svg_markup)}`
  const updatedLabel = new Date(asset.updated_at).toLocaleString()

  return (
    <Card className="overflow-hidden">
      <div className="relative h-36 w-full bg-muted/30">
        <img
          src={svgDataUrl}
          alt={asset.name}
          className="h-full w-full object-cover"
          loading="lazy"
        />
      </div>
      <CardHeader className="space-y-1">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="line-clamp-1 text-base">{asset.name}</CardTitle>
          <Badge variant={isPublic ? "secondary" : "outline"} className="gap-1">
            {isPublic ? <Globe2 className="size-3" /> : <Lock className="size-3" />}
            {asset.visibility ?? "private"}
          </Badge>
        </div>
        <CardDescription className="line-clamp-2">
          {asset.description || "No description"}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <CalendarClock className="size-3.5" />
          Updated {updatedLabel}
        </div>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="outline" onClick={() => onPreview(asset)}>
            <Eye className="mr-1 size-3.5" />
            Preview
          </Button>
          {!isPublic ? (
            <Button
              size="sm"
              variant="outline"
              onClick={() => onCreatePublicCopy(asset)}
            >
              Make Public
            </Button>
          ) : null}
          <Button
            size="sm"
            variant="destructive"
            onClick={() => onDelete(asset)}
          >
            Delete
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

