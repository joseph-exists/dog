import { useMemo, useState } from "react"
import type { SvgAssetPublic, SvgAssetVisibility } from "@/client"
import { PanelContainer } from "@/components/Page/primitives"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { useCreatePublicSvgCopy, useDeleteSvg, useSvgsList } from "@/hooks/useSvgs"
import { SvgCard } from "../display/SvgCard"

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
  const [visibility, setVisibility] = useState<"all" | SvgAssetVisibility>("all")
  const [selected, setSelected] = useState<SvgAssetPublic | null>(null)
  const listQuery = useSvgsList({
    limit: 50,
    visibility: normalizeVisibilityFilter(visibility),
  })
  const deleteMutation = useDeleteSvg()
  const copyMutation = useCreatePublicSvgCopy()

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase()
    const rows = listQuery.data?.data ?? []
    if (!term) {
      return rows
    }
    return rows.filter((row) => {
      const haystack = [row.name, row.description ?? "", JSON.stringify(row.metadata_json ?? {})]
        .join(" ")
        .toLowerCase()
      return haystack.includes(term)
    })
  }, [listQuery.data?.data, search])

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

        {listQuery.isLoading ? <GallerySkeleton /> : null}

        {listQuery.error ? (
          <Alert variant="destructive">
            <AlertTitle>Failed to load SVGs</AlertTitle>
            <AlertDescription>{listQuery.error.message}</AlertDescription>
          </Alert>
        ) : null}

        {!listQuery.isLoading && !listQuery.error && filtered.length === 0 ? (
          <Alert>
            <AlertTitle>No SVG assets found</AlertTitle>
            <AlertDescription>
              Adjust filters or create new SVG assets from the header controls.
            </AlertDescription>
          </Alert>
        ) : null}

        {!listQuery.isLoading && !listQuery.error && filtered.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {filtered.map((asset) => (
              <SvgCard
                key={asset.id}
                asset={asset}
                onPreview={setSelected}
                onDelete={onDelete}
                onCreatePublicCopy={onCreatePublicCopy}
              />
            ))}
          </div>
        ) : null}
      </div>

      <Dialog open={Boolean(selected)} onOpenChange={(open) => !open && setSelected(null)}>
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
