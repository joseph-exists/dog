import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useMemo, useState } from "react"
import type { ApiError, SvgAssetCreatePrivate } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { svgsQueryKeys } from "@/hooks/useSvgs"
import { SvgAppService } from "@/services/svgService"
import { handleError } from "@/utils"

function buildSeedPayloads(input: {
  prefix: string
  motif: string
  palette: string
  count: number
  includeLabels: boolean
}): SvgAssetCreatePrivate[] {
  return Array.from({ length: input.count }).map((_, index) => {
    const sequence = String(index + 1).padStart(4, "0")
    const hueShift = (index * 21) % 180
    const markup = [
      "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 256 256'>",
      "<defs>",
      `  <linearGradient id='g' x1='0%' y1='0%' x2='100%' y2='100%'>`,
      `    <stop offset='0%' stop-color='hsl(${hueShift}, 74%, 48%)'/>`,
      `    <stop offset='100%' stop-color='hsl(${(hueShift + 66) % 360}, 80%, 55%)'/>`,
      "  </linearGradient>",
      "</defs>",
      "<rect width='256' height='256' rx='40' fill='url(#g)'/>",
      "<circle cx='128' cy='128' r='72' fill='rgba(255,255,255,0.14)'/>",
      "<circle cx='128' cy='128' r='36' fill='rgba(255,255,255,0.22)'/>",
      input.includeLabels
        ? `  <text x='128' y='236' text-anchor='middle' font-size='14' fill='white'>${input.motif}-${sequence}</text>`
        : "",
      "</svg>",
    ]
      .filter(Boolean)
      .join("\n")

    return {
      visibility: "private",
      name: `${input.prefix}-${input.motif}-${sequence}`,
      description: `Seeded ${input.motif} asset (${input.palette})`,
      svg_markup: markup,
      metadata_json: {
        source: "svg-batch-seed-dialog",
        motif: input.motif,
        palette: input.palette,
        sequence,
      },
    }
  })
}

export function BatchSeedSvgDialog() {
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const [prefix, setPrefix] = useState("seed")
  const [motif, setMotif] = useState("nebula")
  const [palette, setPalette] = useState("synthwave")
  const [count, setCount] = useState("12")
  const [includeLabels, setIncludeLabels] = useState(true)

  const parsedCount = useMemo(() => {
    const n = Number.parseInt(count, 10)
    if (Number.isNaN(n)) return 0
    return Math.min(Math.max(n, 1), 100)
  }, [count])

  const seedMutation = useMutation({
    mutationFn: async () => {
      const payloads = buildSeedPayloads({
        prefix: prefix.trim(),
        motif: motif.trim(),
        palette: palette.trim(),
        count: parsedCount,
        includeLabels,
      })
      for (const payload of payloads) {
        await SvgAppService.createPrivateSvg(payload)
      }
      return payloads.length
    },
    onSuccess: async (createdCount) => {
      showSuccessToast(`Seeded ${createdCount} SVG assets`)
      await queryClient.invalidateQueries({ queryKey: svgsQueryKeys.all })
      setOpen(false)
    },
    onError: (error: ApiError) => {
      handleError.call(showErrorToast, error)
    },
  })

  const canSubmit = Boolean(prefix.trim() && motif.trim() && palette.trim() && parsedCount > 0)

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">Batch Seed</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Batch Seed SVG Assets</DialogTitle>
          <DialogDescription>
            Generate multiple private SVG assets using deterministic naming and metadata, similar to the typer seeding flow.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="seed-prefix">Prefix</Label>
              <Input
                id="seed-prefix"
                value={prefix}
                onChange={(event) => setPrefix(event.target.value)}
                placeholder="seed"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="seed-count">Count</Label>
              <Input
                id="seed-count"
                type="number"
                min={1}
                max={100}
                value={count}
                onChange={(event) => setCount(event.target.value)}
              />
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="seed-motif">Motif</Label>
              <Input
                id="seed-motif"
                value={motif}
                onChange={(event) => setMotif(event.target.value)}
                placeholder="nebula"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="seed-palette">Palette</Label>
              <Input
                id="seed-palette"
                value={palette}
                onChange={(event) => setPalette(event.target.value)}
                placeholder="synthwave"
              />
            </div>
          </div>

          <div className="flex items-center justify-between rounded-lg border p-3">
            <div>
              <p className="text-sm font-medium">Embed per-asset labels</p>
              <p className="text-xs text-muted-foreground">
                Adds sequence text in the generated SVG for visual debugging.
              </p>
            </div>
            <Switch checked={includeLabels} onCheckedChange={setIncludeLabels} />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button disabled={!canSubmit || seedMutation.isPending} onClick={() => seedMutation.mutate()}>
            {seedMutation.isPending ? "Seeding..." : `Seed ${parsedCount} SVGs`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
