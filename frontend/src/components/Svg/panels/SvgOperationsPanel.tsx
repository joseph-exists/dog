import { useMutation, useQueryClient } from "@tanstack/react-query"
import { FlaskConical, WandSparkles } from "lucide-react"
import { useMemo, useState } from "react"
import type { ApiError, SvgAssetCreatePrivate, SvgAssetPublic } from "@/client"
import { PanelContainer } from "@/components/Page/primitives"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { svgsQueryKeys, usePatchSvg, useSvgsList } from "@/hooks/useSvgs"
import { SvgAppService } from "@/services/svgService"
import { handleError } from "@/utils"
import { BatchSeedSvgDialog } from "../dialogs/BatchSeedSvgDialog"

type PatternMode = "rings" | "weave" | "tiles"

interface VariantDraft {
  name: string
  svg_markup: string
  metadata_json: Record<string, unknown>
}

function buildPatternSvg(input: {
  columns: number
  rows: number
  hueStep: number
  variantSeed: number
  pattern: PatternMode
}): string {
  const cell = 64
  const width = input.columns * cell
  const height = input.rows * cell
  const elements: string[] = []

  for (let row = 0; row < input.rows; row += 1) {
    for (let col = 0; col < input.columns; col += 1) {
      const x = col * cell
      const y = row * cell
      const hue = (input.variantSeed * 27 + (row + col) * input.hueStep) % 360
      const fill = `hsl(${hue}, 72%, 48%)`
      const accent = `hsl(${(hue + 42) % 360}, 82%, 56%)`

      if (input.pattern === "rings") {
        elements.push(
          `<circle cx='${x + cell / 2}' cy='${y + cell / 2}' r='18' fill='${fill}' opacity='0.85'/>`,
          `<circle cx='${x + cell / 2}' cy='${y + cell / 2}' r='8' fill='${accent}' opacity='0.9'/>`,
        )
      } else if (input.pattern === "weave") {
        elements.push(
          `<rect x='${x + 8}' y='${y + 18}' width='${cell - 16}' height='10' rx='5' fill='${fill}' opacity='0.9'/>`,
          `<rect x='${x + 18}' y='${y + 8}' width='10' height='${cell - 16}' rx='5' fill='${accent}' opacity='0.85'/>`,
        )
      } else {
        elements.push(
          `<rect x='${x + 6}' y='${y + 6}' width='${cell - 12}' height='${cell - 12}' rx='14' fill='${fill}' opacity='0.86'/>`,
          `<path d='M${x + 16},${y + 36} Q${x + 32},${y + 12} ${x + 48},${y + 36}' stroke='${accent}' stroke-width='3' fill='none' opacity='0.9'/>`,
        )
      }
    }
  }

  return [
    `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 ${width} ${height}'>`,
    `<rect width='${width}' height='${height}' fill='hsl(${(input.variantSeed * 19) % 360}, 20%, 8%)'/>`,
    ...elements,
    "</svg>",
  ].join("\n")
}

export function SvgOperationsPanel() {
  const queryClient = useQueryClient()
  const patchMutation = usePatchSvg()
  const listQuery = useSvgsList({ limit: 250 })

  const [pattern, setPattern] = useState<PatternMode>("rings")
  const [columns, setColumns] = useState("5")
  const [rows, setRows] = useState("4")
  const [hueStep, setHueStep] = useState("17")
  const [variantCount, setVariantCount] = useState("6")
  const [namePrefix, setNamePrefix] = useState("combo")
  const [generated, setGenerated] = useState<VariantDraft[]>([])

  const [selectedAssetId, setSelectedAssetId] = useState("")
  const [editName, setEditName] = useState("")
  const [editDescription, setEditDescription] = useState("")
  const [editVisibility, setEditVisibility] = useState<"private" | "public">("private")
  const [editMarkup, setEditMarkup] = useState("")
  const [editMetadataJson, setEditMetadataJson] = useState("{}")

  const selectedAsset = useMemo(
    () => (listQuery.data?.data ?? []).find((row) => row.id === selectedAssetId) ?? null,
    [listQuery.data?.data, selectedAssetId],
  )

  const createManyMutation = useMutation({
    mutationFn: async (payloads: SvgAssetCreatePrivate[]) => {
      for (const payload of payloads) {
        await SvgAppService.createPrivateSvg(payload)
      }
      return payloads.length
    },
    onSuccess: async (count) => {
      showSuccessToast(`Created ${count} SVG variants`)
      await queryClient.invalidateQueries({ queryKey: svgsQueryKeys.all })
    },
    onError: (error: ApiError) => {
      handleError.call(showErrorToast, error)
    },
  })

  const numbers = useMemo(() => {
    const c = Math.max(1, Math.min(Number.parseInt(columns, 10) || 1, 16))
    const r = Math.max(1, Math.min(Number.parseInt(rows, 10) || 1, 16))
    const h = Math.max(1, Math.min(Number.parseInt(hueStep, 10) || 1, 90))
    const v = Math.max(1, Math.min(Number.parseInt(variantCount, 10) || 1, 24))
    return { c, r, h, v }
  }, [columns, rows, hueStep, variantCount])

  const generateCombinatorics = () => {
    const next: VariantDraft[] = Array.from({ length: numbers.v }).map((_, index) => {
      const seed = index + 1
      return {
        name: `${namePrefix.trim() || "combo"}-${pattern}-${String(seed).padStart(3, "0")}`,
        svg_markup: buildPatternSvg({
          columns: numbers.c,
          rows: numbers.r,
          hueStep: numbers.h,
          variantSeed: seed,
          pattern,
        }),
        metadata_json: {
          source: "svg-combinatorics-studio",
          pattern,
          columns: numbers.c,
          rows: numbers.r,
          hue_step: numbers.h,
          seed,
        },
      }
    })
    setGenerated(next)
  }

  const saveAllGenerated = () => {
    if (generated.length === 0) return
    createManyMutation.mutate(
      generated.map((item) => ({
        visibility: "private",
        name: item.name,
        description: `Generated ${pattern} combinatoric variant`,
        svg_markup: item.svg_markup,
        metadata_json: item.metadata_json,
      })),
    )
  }

  const loadAssetForEditing = (asset: SvgAssetPublic | null) => {
    if (!asset) return
    setEditName(asset.name)
    setEditDescription(asset.description ?? "")
    setEditVisibility(asset.visibility ?? "private")
    setEditMarkup(asset.svg_markup)
    setEditMetadataJson(JSON.stringify(asset.metadata_json ?? {}, null, 2))
  }

  const savePatch = async () => {
    if (!selectedAsset) return
    try {
      const metadata = JSON.parse(editMetadataJson || "{}")
      if (typeof metadata !== "object" || metadata === null || Array.isArray(metadata)) {
        throw new Error("metadata must be a JSON object")
      }
      await patchMutation.mutateAsync({
        svgId: selectedAsset.id,
        patch: {
          name: editName.trim() || null,
          description: editDescription.trim() || null,
          visibility: editVisibility,
          svg_markup: editMarkup,
          metadata_json: metadata as Record<string, unknown>,
        },
      })
    } catch (error) {
      showErrorToast(
        error instanceof Error ? `Invalid edit payload: ${error.message}` : "Invalid edit payload",
      )
    }
  }

  const revalidateMarkup = async () => {
    if (!selectedAsset || !editMarkup.trim()) return
    await patchMutation.mutateAsync({
      svgId: selectedAsset.id,
      patch: {
        svg_markup: editMarkup,
      },
    })
  }

  return (
    <PanelContainer title="Library Operations" scrollable headerActions={<BatchSeedSvgDialog />}>
      <div className="space-y-4 p-4">
        <Alert>
          <WandSparkles className="h-4 w-4" />
          <AlertTitle>Combinatorics + Canonical Validation</AlertTitle>
          <AlertDescription>
            Generate pattern variants for review, then patch selected assets. PATCH saves go through canonical validation on the backend.
          </AlertDescription>
        </Alert>

        <Tabs defaultValue="studio" className="space-y-4">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="studio">Combinatorics Studio</TabsTrigger>
            <TabsTrigger value="editor">Asset Editor</TabsTrigger>
          </TabsList>

          <TabsContent value="studio" className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Pattern</Label>
                <div className="flex flex-wrap gap-2">
                  {(["rings", "weave", "tiles"] as PatternMode[]).map((candidate) => (
                    <Button
                      key={candidate}
                      size="sm"
                      variant={pattern === candidate ? "default" : "outline"}
                      onClick={() => setPattern(candidate)}
                    >
                      {candidate}
                    </Button>
                  ))}
                </div>
              </div>
              <div className="space-y-1.5">
                <Label>Name Prefix</Label>
                <Input
                  value={namePrefix}
                  onChange={(event) => setNamePrefix(event.target.value)}
                  placeholder="combo"
                />
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-4">
              <div className="space-y-1.5">
                <Label>Columns</Label>
                <Input value={columns} onChange={(event) => setColumns(event.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label>Rows</Label>
                <Input value={rows} onChange={(event) => setRows(event.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label>Hue Step</Label>
                <Input value={hueStep} onChange={(event) => setHueStep(event.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label>Variants</Label>
                <Input value={variantCount} onChange={(event) => setVariantCount(event.target.value)} />
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button onClick={generateCombinatorics}>
                <FlaskConical className="mr-2 size-4" />
                Generate Variants
              </Button>
              <Button
                variant="outline"
                onClick={saveAllGenerated}
                disabled={generated.length === 0 || createManyMutation.isPending}
              >
                {createManyMutation.isPending ? "Saving..." : `Save All (${generated.length})`}
              </Button>
              <Badge variant="secondary">{pattern}</Badge>
            </div>

            {generated.length > 0 ? (
              <div className="grid gap-4 sm:grid-cols-2">
                {generated.map((item) => (
                  <div key={item.name} className="space-y-2 rounded-lg border p-3">
                    <div className="text-xs font-medium">{item.name}</div>
                    <div className="h-40 overflow-hidden rounded border bg-muted/30 p-2">
                      <img
                        alt={item.name}
                        className="h-full w-full object-contain"
                        src={`data:image/svg+xml,${encodeURIComponent(item.svg_markup)}`}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
          </TabsContent>

          <TabsContent value="editor" className="space-y-3">
            <div className="space-y-1.5">
              <Label>Select Asset</Label>
              <select
                className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                value={selectedAssetId}
                onChange={(event) => {
                  const value = event.target.value
                  setSelectedAssetId(value)
                  const asset = (listQuery.data?.data ?? []).find((row) => row.id === value) ?? null
                  loadAssetForEditing(asset)
                }}
              >
                <option value="">Choose an SVG asset</option>
                {(listQuery.data?.data ?? []).map((asset) => (
                  <option key={asset.id} value={asset.id}>
                    {asset.name} ({asset.visibility ?? "private"})
                  </option>
                ))}
              </select>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Name</Label>
                <Input value={editName} onChange={(event) => setEditName(event.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label>Visibility</Label>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant={editVisibility === "private" ? "default" : "outline"}
                    onClick={() => setEditVisibility("private")}
                  >
                    private
                  </Button>
                  <Button
                    size="sm"
                    variant={editVisibility === "public" ? "default" : "outline"}
                    onClick={() => setEditVisibility("public")}
                  >
                    public
                  </Button>
                </div>
              </div>
            </div>

            <div className="space-y-1.5">
              <Label>Description</Label>
              <Input
                value={editDescription}
                onChange={(event) => setEditDescription(event.target.value)}
              />
            </div>

            <div className="space-y-1.5">
              <Label>SVG Markup</Label>
              <Textarea
                className="min-h-40 font-mono text-xs"
                value={editMarkup}
                onChange={(event) => setEditMarkup(event.target.value)}
              />
            </div>

            <div className="space-y-1.5">
              <Label>Metadata JSON</Label>
              <Textarea
                className="min-h-28 font-mono text-xs"
                value={editMetadataJson}
                onChange={(event) => setEditMetadataJson(event.target.value)}
              />
            </div>

            <div className="flex flex-wrap gap-2">
              <Button disabled={!selectedAsset || patchMutation.isPending} onClick={savePatch}>
                {patchMutation.isPending ? "Saving..." : "Save Patch"}
              </Button>
              <Button
                variant="outline"
                disabled={!selectedAsset || patchMutation.isPending || !editMarkup.trim()}
                onClick={revalidateMarkup}
              >
                Revalidate Markup
              </Button>
              <Badge variant="outline">patch-merge-enabled</Badge>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </PanelContainer>
  )
}
