import { ChevronDown } from "lucide-react"
import type { Dispatch, SetStateAction } from "react"
import { useMemo, useState } from "react"
import type { SvgAssetPublic, SvgAssetVisibility } from "@/client"
import { PanelContainer } from "@/components/Page/primitives"
import {
  PALETTE_FAMILIES,
  STYLE_FAMILIES,
} from "@/components/Svg/constants/svgComposeDomains"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import {
  useCreatePublicSvgCopy,
  useDeleteSvg,
  useSvgsList,
} from "@/hooks/useSvgs"
import { SvgCard } from "../display/SvgCard"

const TIER_FILTERS = [
  "pairwise-core",
  "hero-extreme",
  "safe-utility",
  "compose-studio",
  "tesser",
] as const

type ComplexityFilter = "all" | "low" | "mid" | "high"
type SortField = "name" | "updated" | "created" | "complexity" | "contrast"
type SortDirection = "asc" | "desc"

function GallerySkeleton() {
  return (
    <div className="grid gap-4 p-4 sm:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: 6 }).map((_, index) => (
        <Skeleton key={index} className="h-80 rounded-xl" />
      ))}
    </div>
  )
}

function normalizeVisibilityFilter(
  visibility: "all" | SvgAssetVisibility,
): SvgAssetVisibility | undefined {
  if (visibility === "all") return undefined
  return visibility
}

export function SvgsGalleryPanel() {
  const [search, setSearch] = useState("")
  const [visibility, setVisibility] = useState<"all" | SvgAssetVisibility>(
    "all",
  )
  const [filterFamilies, setFilterFamilies] = useState<Set<string>>(new Set())
  const [filterTiers, setFilterTiers] = useState<Set<string>>(new Set())
  const [filterComplexity, setFilterComplexity] =
    useState<ComplexityFilter>("all")
  const [filterPalette, setFilterPalette] = useState<Set<string>>(new Set())
  const [filterUserTags, setFilterUserTags] = useState<Set<string>>(new Set())
  const [filterBarOpen, setFilterBarOpen] = useState(false)
  const [sortBy, setSortBy] = useState<SortField>("updated")
  const [sortDir, setSortDir] = useState<SortDirection>("desc")
  const [selected, setSelected] = useState<SvgAssetPublic | null>(null)
  const listQuery = useSvgsList({
    limit: 50,
    visibility: normalizeVisibilityFilter(visibility),
  })
  const deleteMutation = useDeleteSvg()
  const copyMutation = useCreatePublicSvgCopy()

  const filteredAndSorted = useMemo(() => {
    const term = search.trim().toLowerCase()
    let rows = listQuery.data?.data ?? []

    if (term) {
      rows = rows.filter((row) => {
        const haystack = [
          row.name,
          row.description ?? "",
          JSON.stringify(row.metadata_json ?? {}),
        ]
          .join(" ")
          .toLowerCase()
        return haystack.includes(term)
      })
    }

    if (filterFamilies.size > 0) {
      rows = rows.filter((row) => {
        const meta = (row.metadata_json ?? {}) as Record<string, unknown>
        return (
          typeof meta.family === "string" && filterFamilies.has(meta.family)
        )
      })
    }

    if (filterTiers.size > 0) {
      rows = rows.filter((row) => {
        const meta = (row.metadata_json ?? {}) as Record<string, unknown>
        const generationTier =
          typeof meta.generation_tier === "string" ? meta.generation_tier : null
        const source = typeof meta.source === "string" ? meta.source : null
        return (
          (generationTier !== null && filterTiers.has(generationTier)) ||
          (source !== null && filterTiers.has(source))
        )
      })
    }

    if (filterComplexity !== "all") {
      rows = rows.filter((row) => {
        const meta = (row.metadata_json ?? {}) as Record<string, unknown>
        const score =
          typeof meta.complexity_score === "number"
            ? meta.complexity_score
            : null
        if (score === null) return false
        if (filterComplexity === "low") return score < 0.33
        if (filterComplexity === "mid") return score >= 0.33 && score < 0.66
        return score >= 0.66
      })
    }

    if (filterPalette.size > 0) {
      rows = rows.filter((row) => {
        const meta = (row.metadata_json ?? {}) as Record<string, unknown>
        const knobs = meta.knobs as Record<string, unknown> | undefined
        return (
          typeof knobs?.palette_family === "string" &&
          filterPalette.has(knobs.palette_family)
        )
      })
    }

    if (filterUserTags.size > 0) {
      rows = rows.filter((row) => {
        const meta = (row.metadata_json ?? {}) as Record<string, unknown>
        const tags = Array.isArray(meta.tags)
          ? meta.tags.filter((tag): tag is string => typeof tag === "string")
          : []
        return [...filterUserTags].every((tag) => tags.includes(tag))
      })
    }

    rows = [...rows].sort((a, b) => {
      let cmp = 0
      if (sortBy === "name") {
        cmp = a.name.localeCompare(b.name)
      } else if (sortBy === "updated") {
        cmp =
          new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime()
      } else if (sortBy === "created") {
        cmp =
          new Date(a.created_at ?? a.updated_at).getTime() -
          new Date(b.created_at ?? b.updated_at).getTime()
      } else if (sortBy === "complexity") {
        const aMeta = (a.metadata_json ?? {}) as Record<string, unknown>
        const bMeta = (b.metadata_json ?? {}) as Record<string, unknown>
        const aScore =
          typeof aMeta.complexity_score === "number"
            ? aMeta.complexity_score
            : 0
        const bScore =
          typeof bMeta.complexity_score === "number"
            ? bMeta.complexity_score
            : 0
        cmp = aScore - bScore
      } else if (sortBy === "contrast") {
        const aMeta = (a.metadata_json ?? {}) as Record<string, unknown>
        const bMeta = (b.metadata_json ?? {}) as Record<string, unknown>
        const aScore =
          typeof aMeta.contrast_score === "number" ? aMeta.contrast_score : 0
        const bScore =
          typeof bMeta.contrast_score === "number" ? bMeta.contrast_score : 0
        cmp = aScore - bScore
      }
      return sortDir === "asc" ? cmp : -cmp
    })

    return rows
  }, [
    filterComplexity,
    filterFamilies,
    filterPalette,
    filterTiers,
    filterUserTags,
    listQuery.data?.data,
    search,
    sortBy,
    sortDir,
  ])

  const activeFilterCount =
    filterFamilies.size +
    filterTiers.size +
    (filterComplexity !== "all" ? 1 : 0) +
    filterPalette.size +
    filterUserTags.size

  const toggleSetValue = (
    value: string,
    setter: Dispatch<SetStateAction<Set<string>>>,
  ) => {
    setter((prev) => {
      const next = new Set(prev)
      if (next.has(value)) next.delete(value)
      else next.add(value)
      return next
    })
  }

  const handleTagFilter = (tag: string) => {
    const normalized = tag.trim()
    if (!normalized) return

    if ((STYLE_FAMILIES as readonly string[]).includes(normalized)) {
      toggleSetValue(normalized, setFilterFamilies)
    } else if ((PALETTE_FAMILIES as readonly string[]).includes(normalized)) {
      toggleSetValue(normalized, setFilterPalette)
    } else if (normalized.startsWith("complexity:")) {
      const nextComplexity = normalized.slice("complexity:".length)
      if (
        nextComplexity === "low" ||
        nextComplexity === "mid" ||
        nextComplexity === "high"
      ) {
        setFilterComplexity(nextComplexity)
      }
    } else {
      const tierCandidate = normalized.replace(/ /g, "-")
      if ((TIER_FILTERS as readonly string[]).includes(tierCandidate)) {
        toggleSetValue(tierCandidate, setFilterTiers)
      } else {
        toggleSetValue(normalized, setFilterUserTags)
      }
    }

    setFilterBarOpen(true)
  }

  const onDelete = (asset: SvgAssetPublic) => {
    if (!window.confirm(`Delete "${asset.name}" from your SVG library?`)) return
    deleteMutation.mutate(asset.id)
  }

  const onCreatePublicCopy = (asset: SvgAssetPublic) => {
    copyMutation.mutate({
      visibility: "public",
      source_private_id: asset.id,
      name: `${asset.name}-public`,
      description: asset.description ?? null,
      metadata_json: asset.metadata_json ?? {},
    })
  }

  return (
    <PanelContainer
      title="Gallery"
      scrollable
      headerActions={
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant={visibility === "all" ? "default" : "outline"}
            onClick={() => setVisibility("all")}
          >
            All
          </Button>
          <Button
            size="sm"
            variant={visibility === "private" ? "default" : "outline"}
            onClick={() => setVisibility("private")}
          >
            Private
          </Button>
          <Button
            size="sm"
            variant={visibility === "public" ? "default" : "outline"}
            onClick={() => setVisibility("public")}
          >
            Public
          </Button>
        </div>
      }
    >
      <div className="space-y-4 p-4">
        <div className="space-y-1.5">
          <Label htmlFor="svg-search">Search</Label>
          <Input
            id="svg-search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="name, description, metadata fields"
          />
        </div>

        <Collapsible open={filterBarOpen} onOpenChange={setFilterBarOpen}>
          <CollapsibleTrigger asChild>
            <Button variant="outline" size="sm" className="gap-2">
              Filters
              {activeFilterCount > 0 ? (
                <Badge variant="secondary" className="h-4 px-1 text-[10px]">
                  {activeFilterCount}
                </Badge>
              ) : null}
              <ChevronDown
                className={[
                  "size-3.5 transition-transform",
                  filterBarOpen ? "rotate-180" : "",
                ].join(" ")}
              />
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="mt-2 space-y-3 rounded-lg border bg-muted/10 p-3">
              <div className="space-y-1.5">
                <Label className="text-xs">Family</Label>
                <div className="flex flex-wrap gap-1.5">
                  {STYLE_FAMILIES.map((family) => (
                    <Badge
                      key={family}
                      variant={
                        filterFamilies.has(family) ? "default" : "outline"
                      }
                      className="cursor-pointer capitalize"
                      onClick={() => toggleSetValue(family, setFilterFamilies)}
                    >
                      {family}
                    </Badge>
                  ))}
                </div>
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs">Tier</Label>
                <div className="flex flex-wrap gap-1.5">
                  {TIER_FILTERS.map((tier) => (
                    <Badge
                      key={tier}
                      variant={filterTiers.has(tier) ? "default" : "outline"}
                      className="cursor-pointer"
                      onClick={() => toggleSetValue(tier, setFilterTiers)}
                    >
                      {tier}
                    </Badge>
                  ))}
                </div>
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs">Complexity</Label>
                <ToggleGroup
                  type="single"
                  value={filterComplexity}
                  onValueChange={(value) =>
                    setFilterComplexity((value || "all") as ComplexityFilter)
                  }
                  variant="outline"
                >
                  {(["all", "low", "mid", "high"] as const).map(
                    (complexity) => (
                      <ToggleGroupItem
                        key={complexity}
                        value={complexity}
                        className="h-7 text-xs"
                      >
                        {complexity}
                      </ToggleGroupItem>
                    ),
                  )}
                </ToggleGroup>
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs">Palette</Label>
                <div className="flex flex-wrap gap-1.5">
                  {PALETTE_FAMILIES.map((palette) => (
                    <Badge
                      key={palette}
                      variant={
                        filterPalette.has(palette) ? "default" : "outline"
                      }
                      className="cursor-pointer"
                      onClick={() => toggleSetValue(palette, setFilterPalette)}
                    >
                      {palette}
                    </Badge>
                  ))}
                </div>
              </div>

              {filterUserTags.size > 0 ? (
                <div className="space-y-1.5">
                  <Label className="text-xs">User Tags</Label>
                  <div className="flex flex-wrap gap-1.5">
                    {[...filterUserTags].map((tag) => (
                      <Badge
                        key={tag}
                        variant="default"
                        className="cursor-pointer"
                        onClick={() => toggleSetValue(tag, setFilterUserTags)}
                      >
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              ) : null}

              {activeFilterCount > 0 ? (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setFilterFamilies(new Set())
                    setFilterTiers(new Set())
                    setFilterComplexity("all")
                    setFilterPalette(new Set())
                    setFilterUserTags(new Set())
                  }}
                >
                  Clear all filters
                </Button>
              ) : null}
            </div>
          </CollapsibleContent>
        </Collapsible>

        <div className="flex items-center justify-end gap-1 flex-wrap">
          <span className="mr-1 text-xs text-muted-foreground">Sort:</span>
          {(
            ["name", "updated", "created", "complexity", "contrast"] as const
          ).map((field) => (
            <Button
              key={field}
              size="sm"
              variant={sortBy === field ? "default" : "ghost"}
              className="h-7 px-2 text-xs capitalize"
              onClick={() => {
                if (sortBy === field)
                  setSortDir((direction) =>
                    direction === "asc" ? "desc" : "asc",
                  )
                else {
                  setSortBy(field)
                  setSortDir("desc")
                }
              }}
            >
              {field}
              {sortBy === field ? (sortDir === "asc" ? " ↑" : " ↓") : null}
            </Button>
          ))}
        </div>

        {listQuery.isLoading ? <GallerySkeleton /> : null}

        {listQuery.error ? (
          <Alert variant="destructive">
            <AlertTitle>Failed to load SVGs</AlertTitle>
            <AlertDescription>{listQuery.error.message}</AlertDescription>
          </Alert>
        ) : null}

        {!listQuery.isLoading &&
        !listQuery.error &&
        filteredAndSorted.length === 0 ? (
          <Alert>
            <AlertTitle>No SVG assets found</AlertTitle>
            <AlertDescription>
              Adjust filters or create new SVG assets from the header controls.
            </AlertDescription>
          </Alert>
        ) : null}

        {!listQuery.isLoading &&
        !listQuery.error &&
        filteredAndSorted.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {filteredAndSorted.map((asset) => (
              <SvgCard
                key={asset.id}
                asset={asset}
                onPreview={setSelected}
                onDelete={onDelete}
                onCreatePublicCopy={onCreatePublicCopy}
                onTagFilter={handleTagFilter}
              />
            ))}
          </div>
        ) : null}
      </div>

      <Dialog
        open={Boolean(selected)}
        onOpenChange={(open) => !open && setSelected(null)}
      >
        <DialogContent className="sm:max-w-3xl">
          <DialogHeader>
            <DialogTitle>{selected?.name ?? "SVG Preview"}</DialogTitle>
          </DialogHeader>
          {selected ? (
            <div className="space-y-4">
              <div className="h-72 overflow-hidden rounded-lg border bg-muted/30 p-3">
                <img
                  alt={selected.name}
                  className="h-full w-full object-contain"
                  src={`data:image/svg+xml,${encodeURIComponent(selected.svg_markup)}`}
                />
              </div>
              <pre className="max-h-64 overflow-auto rounded-md border bg-muted/30 p-3 text-xs">
                {selected.svg_markup}
              </pre>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </PanelContainer>
  )
}
