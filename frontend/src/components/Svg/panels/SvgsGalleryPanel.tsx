import { useQueryClient } from "@tanstack/react-query"
import {
  CheckSquare,
  ChevronDown,
  Copy,
  Expand,
  PencilLine,
  Trash2,
} from "lucide-react"
import type { Dispatch, SetStateAction } from "react"
import { useEffect, useMemo, useState } from "react"
import type { SvgAssetPublic, SvgAssetVisibility } from "@/client"
import { PanelContainer } from "@/components/Page/primitives"
import { CodeHighlight } from "@/components/Page/primitives/ContentRenderer"
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
import { Textarea } from "@/components/ui/textarea"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { useCopyToClipboard } from "@/hooks/useCopyToClipboard"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import {
  svgsQueryKeys,
  useCreatePublicSvgCopy,
  useDeleteSvg,
  usePatchSvg,
  useSvgsList,
} from "@/hooks/useSvgs"
import { SvgAppService } from "@/services/svgService"
import { deriveTags, SvgCard, TagEditor } from "../display/SvgCard"

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
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [renameDraft, setRenameDraft] = useState("")
  const [descriptionDraft, setDescriptionDraft] = useState("")
  const [previewCodeOpen, setPreviewCodeOpen] = useState(false)
  const [exactSizeOpen, setExactSizeOpen] = useState(false)

  const listQuery = useSvgsList({
    limit: 50,
    visibility: normalizeVisibilityFilter(visibility),
  })
  const queryClient = useQueryClient()
  const deleteMutation = useDeleteSvg()
  const copyMutation = useCreatePublicSvgCopy()
  const patchMutation = usePatchSvg()
  const [copiedText, copyToClipboard] = useCopyToClipboard()

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

  const selectedAsset = useMemo(
    () =>
      (listQuery.data?.data ?? []).find(
        (asset) => asset.id === selectedAssetId,
      ) ?? null,
    [listQuery.data?.data, selectedAssetId],
  )

  const selectedAssetTags = useMemo(
    () => (selectedAsset ? deriveTags(selectedAsset) : []),
    [selectedAsset],
  )

  const activeFilterCount =
    filterFamilies.size +
    filterTiers.size +
    (filterComplexity !== "all" ? 1 : 0) +
    filterPalette.size +
    filterUserTags.size

  const visibleSelectedCount = useMemo(
    () => filteredAndSorted.filter((asset) => selectedIds.has(asset.id)).length,
    [filteredAndSorted, selectedIds],
  )

  useEffect(() => {
    if (!selectedAsset) return
    setRenameDraft(selectedAsset.name)
    setDescriptionDraft(selectedAsset.description ?? "")
  }, [selectedAsset])

  useEffect(() => {
    if (!selectedAsset) {
      setExactSizeOpen(false)
      setPreviewCodeOpen(false)
    }
  }, [selectedAsset])

  useEffect(() => {
    const validIds = new Set(
      (listQuery.data?.data ?? []).map((asset) => asset.id),
    )
    setSelectedIds((previous) => {
      const next = new Set([...previous].filter((id) => validIds.has(id)))
      return next
    })
  }, [listQuery.data?.data])

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
    if (selectedAssetId === asset.id) {
      setSelectedAssetId(null)
      setExactSizeOpen(false)
    }
    setSelectedIds((previous) => {
      const next = new Set(previous)
      next.delete(asset.id)
      return next
    })
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

  const toggleSelection = (assetId: string, checked: boolean) => {
    setSelectedIds((previous) => {
      const next = new Set(previous)
      if (checked) next.add(assetId)
      else next.delete(assetId)
      return next
    })
  }

  const selectVisible = () => {
    setSelectedIds(new Set(filteredAndSorted.map((asset) => asset.id)))
  }

  const clearSelection = () => {
    setSelectedIds(new Set())
  }

  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) return
    const rows = filteredAndSorted.filter((asset) => selectedIds.has(asset.id))
    if (
      !window.confirm(
        `Delete ${rows.length} selected SVG asset${rows.length === 1 ? "" : "s"}?`,
      )
    ) {
      return
    }

    let deletedCount = 0
    for (const asset of rows) {
      try {
        await SvgAppService.deleteSvg(asset.id)
        deletedCount += 1
      } catch (error) {
        showErrorToast(
          error instanceof Error
            ? `Failed to delete "${asset.name}": ${error.message}`
            : `Failed to delete "${asset.name}"`,
        )
      }
    }

    if (deletedCount > 0) {
      showSuccessToast(
        `Deleted ${deletedCount} SVG asset${deletedCount === 1 ? "" : "s"}`,
      )
      await queryClient.invalidateQueries({ queryKey: svgsQueryKeys.all })
      setSelectedIds(new Set())
      if (
        selectedAssetId &&
        rows.some((asset) => asset.id === selectedAssetId)
      ) {
        setSelectedAssetId(null)
        setExactSizeOpen(false)
      }
    }
  }

  const handleRenameSave = async () => {
    if (!selectedAsset) return
    const nextName = renameDraft.trim()
    const nextDescription = descriptionDraft.trim() || null
    if (
      !nextName ||
      (nextName === selectedAsset.name &&
        nextDescription === (selectedAsset.description ?? null))
    ) {
      return
    }
    await patchMutation.mutateAsync({
      svgId: selectedAsset.id,
      patch: {
        name: nextName,
        description: nextDescription,
      },
    })
  }

  const handleCopySource = async () => {
    if (!selectedAsset) return
    const copied = await copyToClipboard(selectedAsset.svg_markup)
    if (!copied) {
      showErrorToast("Failed to copy SVG source")
    }
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

        <div className="flex flex-wrap items-center gap-2 rounded-lg border bg-muted/10 p-2">
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={selectVisible}
            disabled={filteredAndSorted.length === 0}
          >
            <CheckSquare className="mr-1 size-3.5" />
            Select Visible
          </Button>
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={clearSelection}
            disabled={selectedIds.size === 0}
          >
            Clear Selection
          </Button>
          <Button
            type="button"
            size="sm"
            variant="destructive"
            onClick={() => void handleBulkDelete()}
            disabled={visibleSelectedCount === 0}
          >
            <Trash2 className="mr-1 size-3.5" />
            Delete Selected
          </Button>
          <span className="text-xs text-muted-foreground">
            {visibleSelectedCount} selected in current view
          </span>
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
                if (sortBy === field) {
                  setSortDir((direction) =>
                    direction === "asc" ? "desc" : "asc",
                  )
                } else {
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
                onPreview={(row) => setSelectedAssetId(row.id)}
                onDelete={onDelete}
                onCreatePublicCopy={onCreatePublicCopy}
                onTagFilter={handleTagFilter}
                selected={selectedIds.has(asset.id)}
                onSelectedChange={(checked) =>
                  toggleSelection(asset.id, checked)
                }
              />
            ))}
          </div>
        ) : null}
      </div>

      <Dialog
        open={Boolean(selectedAsset)}
        onOpenChange={(open) => {
          if (!open) setSelectedAssetId(null)
        }}
      >
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-5xl">
          <DialogHeader>
            <DialogTitle>{selectedAsset?.name ?? "SVG Preview"}</DialogTitle>
          </DialogHeader>
          {selectedAsset ? (
            <div className="space-y-5">
              <div className="grid gap-5 lg:grid-cols-[minmax(0,1.3fr)_minmax(320px,0.9fr)]">
                <div className="space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge
                        variant={
                          selectedAsset.visibility === "public"
                            ? "secondary"
                            : "outline"
                        }
                      >
                        {selectedAsset.visibility ?? "private"}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        Updated{" "}
                        {new Date(selectedAsset.updated_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => void handleCopySource()}
                      >
                        <Copy className="mr-1 size-3.5" />
                        {copiedText === selectedAsset.svg_markup
                          ? "Copied"
                          : "Copy SVG"}
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => setExactSizeOpen(true)}
                      >
                        <Expand className="mr-1 size-3.5" />
                        Exact Size
                      </Button>
                    </div>
                  </div>

                  <div className="flex min-h-[26rem] items-center justify-center overflow-auto rounded-xl border bg-[radial-gradient(circle_at_top,rgba(251,191,36,0.12),transparent_45%),linear-gradient(180deg,rgba(15,23,42,0.02),rgba(15,23,42,0.06))] p-6">
                    <div
                      className="flex items-center justify-center [&_svg]:block [&_svg]:max-h-full [&_svg]:max-w-full"
                      dangerouslySetInnerHTML={{
                        __html: selectedAsset.svg_markup,
                      }}
                    />
                  </div>

                  <Collapsible
                    open={previewCodeOpen}
                    onOpenChange={setPreviewCodeOpen}
                  >
                    <CollapsibleTrigger asChild>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        className="gap-2"
                      >
                        <ChevronDown
                          className={[
                            "size-3.5 transition-transform",
                            previewCodeOpen ? "rotate-180" : "",
                          ].join(" ")}
                        />
                        SVG Source
                      </Button>
                    </CollapsibleTrigger>
                    <CollapsibleContent>
                      <div className="mt-3 overflow-hidden rounded-xl border">
                        <div className="[&_pre]:!m-0 [&_pre]:max-h-[28rem] [&_pre]:overflow-auto [&_pre]:whitespace-pre-wrap [&_pre]:break-words [&_code]:whitespace-pre-wrap [&_code]:break-words">
                          <CodeHighlight
                            className="language-xml"
                            options={{
                              language: "xml",
                              copyable: false,
                              forceBlock: true,
                            }}
                          >
                            {selectedAsset.svg_markup}
                          </CodeHighlight>
                        </div>
                      </div>
                    </CollapsibleContent>
                  </Collapsible>
                </div>

                <div className="space-y-4">
                  <div className="space-y-2 rounded-xl border bg-muted/10 p-4">
                    <div className="flex items-center gap-2 text-sm font-medium">
                      <PencilLine className="size-4" />
                      Rename
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="svg-preview-name">Name</Label>
                      <Input
                        id="svg-preview-name"
                        value={renameDraft}
                        onChange={(event) => setRenameDraft(event.target.value)}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="svg-preview-description">
                        Description
                      </Label>
                      <Textarea
                        id="svg-preview-description"
                        value={descriptionDraft}
                        onChange={(event) =>
                          setDescriptionDraft(event.target.value)
                        }
                        className="min-h-24"
                      />
                    </div>
                    <Button
                      type="button"
                      size="sm"
                      onClick={() => void handleRenameSave()}
                      disabled={
                        patchMutation.isPending ||
                        !renameDraft.trim() ||
                        (renameDraft.trim() === selectedAsset.name &&
                          (descriptionDraft.trim() || null) ===
                            (selectedAsset.description ?? null))
                      }
                    >
                      Save Metadata
                    </Button>
                  </div>

                  <div className="space-y-3 rounded-xl border bg-muted/10 p-4">
                    <div className="flex items-center justify-between gap-2">
                      <div className="text-sm font-medium">Tags</div>
                      <TagEditor
                        asset={selectedAsset}
                        triggerClassName="h-7 rounded-md px-2 text-xs"
                        triggerLabel="Add Tag"
                      />
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedAssetTags.map((tag) => (
                        <Badge
                          key={tag}
                          variant="outline"
                          className="cursor-pointer"
                          onClick={() => handleTagFilter(tag)}
                        >
                          {tag}
                        </Badge>
                      ))}
                      {selectedAssetTags.length === 0 ? (
                        <span className="text-xs text-muted-foreground">
                          No tags yet.
                        </span>
                      ) : null}
                    </div>
                  </div>

                  <div className="space-y-1 rounded-xl border bg-muted/10 p-4">
                    <div className="text-sm font-medium">Asset Notes</div>
                    <div className="text-xs text-muted-foreground">
                      Public/private conversion, tag edits, rename, and delete
                      all happen from this preview without leaving the gallery.
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {selectedAsset.visibility !== "public" ? (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onCreatePublicCopy(selectedAsset)}
                      >
                        Make Public
                      </Button>
                    ) : null}
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => onDelete(selectedAsset)}
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

      <Dialog open={exactSizeOpen} onOpenChange={setExactSizeOpen}>
        <DialogContent className="h-[92vh] max-h-[92vh] overflow-hidden sm:max-w-[92vw]">
          <DialogHeader>
            <DialogTitle>
              {selectedAsset?.name ?? "Exact Size Preview"}
            </DialogTitle>
          </DialogHeader>
          {selectedAsset ? (
            <div className="h-full overflow-auto rounded-xl border bg-white p-8">
              <div
                dangerouslySetInnerHTML={{ __html: selectedAsset.svg_markup }}
              />
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </PanelContainer>
  )
}
