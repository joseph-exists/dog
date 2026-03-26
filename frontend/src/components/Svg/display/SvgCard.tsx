import { CalendarClock, Eye, Globe2, Lock, Plus, Tag, X } from "lucide-react"
import { useState } from "react"
import type { SvgAssetPublic } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { usePatchSvg } from "@/hooks/useSvgs"

// ---------------------------------------------------------------------------
// deriveTags — computes display tags from metadata without writing to backend.
// Combines user-defined tags (metadata_json.tags) with tags derived from knobs.
// ---------------------------------------------------------------------------
function deriveTags(asset: SvgAssetPublic): string[] {
  const meta = (asset.metadata_json ?? {}) as Record<string, unknown>
  const tags: string[] = []

  // User-defined tags stored in metadata_json.tags
  const userTags = meta.tags
  if (Array.isArray(userTags)) {
    for (const t of userTags) {
      if (typeof t === "string" && t.trim()) tags.push(t.trim())
    }
  }

  // Derived: style family
  if (typeof meta.family === "string") tags.push(meta.family)

  // Derived: generation tier (short form)
  if (typeof meta.generation_tier === "string") {
    tags.push(meta.generation_tier.replace("-", " "))
  }

  // Derived: palette family from knobs
  const knobs = meta.knobs as Record<string, unknown> | undefined
  if (knobs && typeof knobs.palette_family === "string") {
    tags.push(knobs.palette_family)
  }

  // Derived: source
  if (typeof meta.source === "string") tags.push(meta.source.replace(/-/g, " "))

  // Derived: complexity bucket
  if (typeof meta.complexity_score === "number") {
    const score = meta.complexity_score
    tags.push(
      score < 0.33
        ? "complexity:low"
        : score < 0.66
          ? "complexity:mid"
          : "complexity:high",
    )
  }

  // Deduplicate while preserving order
  return [...new Set(tags)].slice(0, 8)
}

function getUserTags(asset: SvgAssetPublic): string[] {
  const meta = (asset.metadata_json ?? {}) as Record<string, unknown>
  const userTags = meta.tags
  if (!Array.isArray(userTags)) return []
  return userTags.filter(
    (t): t is string => typeof t === "string" && Boolean(t.trim()),
  )
}

// ---------------------------------------------------------------------------
// TagEditor — popover for adding/removing user-defined tags
// ---------------------------------------------------------------------------
function TagEditor({ asset }: { asset: SvgAssetPublic }) {
  const patchMutation = usePatchSvg()
  const [input, setInput] = useState("")
  const userTags = getUserTags(asset)

  async function addTag(tag: string) {
    const trimmed = tag.trim()
    if (!trimmed || userTags.includes(trimmed)) return
    const next = [...userTags, trimmed]
    await patchMutation.mutateAsync({
      svgId: asset.id,
      patch: {
        metadata_json: {
          ...((asset.metadata_json as Record<string, unknown>) ?? {}),
          tags: next,
        },
      },
    })
    setInput("")
  }

  async function removeTag(tag: string) {
    const next = userTags.filter((t) => t !== tag)
    await patchMutation.mutateAsync({
      svgId: asset.id,
      patch: {
        metadata_json: {
          ...((asset.metadata_json as Record<string, unknown>) ?? {}),
          tags: next,
        },
      },
    })
  }

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="sm" className="h-5 w-5 rounded-full p-0">
          <Plus className="size-3" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-56 p-2" align="start">
        <div className="space-y-2">
          <div className="text-xs font-medium">User Tags</div>
          {userTags.length > 0 ? (
            <div className="flex flex-wrap gap-1">
              {userTags.map((tag) => (
                <span
                  key={tag}
                  className="flex items-center gap-0.5 rounded bg-muted px-1.5 py-0.5 text-[10px]"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => void removeTag(tag)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <X className="size-2.5" />
                  </button>
                </span>
              ))}
            </div>
          ) : null}
          <div className="flex gap-1">
            <Input
              className="h-6 text-xs"
              placeholder="new tag"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") void addTag(input)
              }}
            />
            <Button
              type="button"
              size="sm"
              className="h-6 px-2 text-xs"
              onClick={() => void addTag(input)}
              disabled={patchMutation.isPending}
            >
              Add
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}

// ---------------------------------------------------------------------------
// SvgCard
// ---------------------------------------------------------------------------
interface SvgCardProps {
  asset: SvgAssetPublic
  onPreview: (asset: SvgAssetPublic) => void
  onDelete: (asset: SvgAssetPublic) => void
  onCreatePublicCopy: (asset: SvgAssetPublic) => void
  onTagFilter?: (tag: string) => void
}

export function SvgCard({
  asset,
  onPreview,
  onDelete,
  onCreatePublicCopy,
  onTagFilter,
}: SvgCardProps) {
  const isPublic = asset.visibility === "public"
  const svgDataUrl = `data:image/svg+xml,${encodeURIComponent(asset.svg_markup)}`
  const updatedLabel = new Date(asset.updated_at).toLocaleString()
  const allTags = deriveTags(asset)
  const visibleTags = allTags.slice(0, 4)
  const overflowCount = allTags.length - visibleTags.length

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
          <Badge
            variant={isPublic ? "secondary" : "outline"}
            className="gap-1 shrink-0"
          >
            {isPublic ? (
              <Globe2 className="size-3" />
            ) : (
              <Lock className="size-3" />
            )}
            {asset.visibility ?? "private"}
          </Badge>
        </div>
        <CardDescription className="line-clamp-2">
          {asset.description || "No description"}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Tag row */}
        <div className="flex flex-wrap items-center gap-1">
          <Tag className="size-3 shrink-0 text-muted-foreground" />
          {visibleTags.map((tag) => (
            <Badge
              key={tag}
              variant="outline"
              className="cursor-pointer px-1.5 py-0 text-[10px] hover:bg-muted transition-colors"
              onClick={() => onTagFilter?.(tag)}
            >
              {tag}
            </Badge>
          ))}
          {overflowCount > 0 ? (
            <span className="text-[10px] text-muted-foreground">
              +{overflowCount}
            </span>
          ) : null}
          <TagEditor asset={asset} />
        </div>

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
