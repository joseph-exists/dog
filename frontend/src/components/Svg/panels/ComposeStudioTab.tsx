/**
 * ComposeStudioTab
 *
 * Knob-driven interface for the svg.compose Tesser script.
 * Family presets prime the config; all 30 knobs remain individually overridable.
 *
 * Script: svg.compose (via useEnqueueTesserScript)
 * Knob reference: src/components/Svg/constants/svgComposeDomains.ts
 * Python source: backend/app/test_scripts/render_things/svg_combinatorics_reference_card.md
 */
import { ChevronDown, HelpCircle, Shuffle, Zap } from "lucide-react"
import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { showSuccessToast } from "@/hooks/useCustomToast"
import { useCreatePrivateSvg } from "@/hooks/useSvgs"
import { useEnqueueTesserScript } from "@/hooks/useTesser"
import { type TesserJobStatusResponse } from "@/services/tesserService"
import {
  applyFamilyBias,
  buildDefaultKnobs,
  FAMILY_ACCENT,
  FAMILY_DESCRIPTORS,
  KNOB_GROUPS,
  type KnobState,
  makeSeededRandom,
  STYLE_FAMILIES,
  type StyleFamily,
} from "../constants/svgComposeDomains"
import { type LocalTesserJob, TesserJobRow } from "../display/TesserJobRow"
import { buildTesserSvgAssetPayload } from "../utils/buildTesserSvgAssetPayload"

// ---------------------------------------------------------------------------
// Text layer state — forwarded to svg.compose script_input as text_layer.
// text_layer is a frontend extension: svg.compose may silently ignore unknown
// keys until the script is updated to consume them.
// See: tesserax_service/scripts/svg_compose.py for current consumption support.
// ---------------------------------------------------------------------------
interface TextLayerState {
  enabled: boolean
  content: string
  font_size: string
  anchor: "start" | "middle" | "end"
  fill: string
  x_pct: string
  y_pct: string
}

const DEFAULT_TEXT_LAYER: TextLayerState = {
  enabled: false,
  content: "",
  font_size: "24",
  anchor: "middle",
  fill: "#ffffff",
  x_pct: "50",
  y_pct: "90",
}

function buildScriptInput(
  knobs: KnobState,
  textLayer: TextLayerState,
): Record<string, unknown> {
  const input: Record<string, unknown> = { ...knobs }
  if (textLayer.enabled) {
    input.text_layer = {
      enabled: true,
      content: textLayer.content,
      font_size: Number(textLayer.font_size) || 24,
      anchor: textLayer.anchor,
      fill: textLayer.fill,
      x_pct: Number(textLayer.x_pct) || 50,
      y_pct: Number(textLayer.y_pct) || 90,
    }
  }
  return input
}

function buildSavedAssetName(knobs: KnobState): string {
  const family = knobs.style_family ?? "compose"
  const palette = knobs.palette_family ?? ""
  const stamp = new Date().toISOString().replace(/[:.]/g, "-")
  return `compose-${family}-${palette}-${stamp}`
}

// ---------------------------------------------------------------------------
// FamilyPresetRow — 6 clickable cards, active family highlighted
// ---------------------------------------------------------------------------
function FamilyPresetRow({
  active,
  onSelect,
}: {
  active: StyleFamily | null
  onSelect: (family: StyleFamily) => void
}) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
      {STYLE_FAMILIES.map((family) => (
        <button
          key={family}
          type="button"
          onClick={() => onSelect(family)}
          className={[
            "rounded-lg border p-2 text-left transition-all hover:opacity-90",
            active === family
              ? `${FAMILY_ACCENT[family]} ring-1 ring-current`
              : "border-border bg-muted/20 hover:bg-muted/40",
          ].join(" ")}
        >
          <div className="text-xs font-semibold capitalize">{family}</div>
          <div className="mt-0.5 text-[10px] leading-tight text-muted-foreground">
            {FAMILY_DESCRIPTORS[family]}
          </div>
        </button>
      ))}
    </div>
  )
}

// ---------------------------------------------------------------------------
// KnobGroupPanel — collapsible section for one group of knobs
// ---------------------------------------------------------------------------
function KnobGroupPanel({
  group,
  knobs,
  open,
  onOpenChange,
  onChange,
}: {
  group: (typeof KNOB_GROUPS)[number]
  knobs: KnobState
  open: boolean
  onOpenChange: (open: boolean) => void
  onChange: (key: string, value: string) => void
}) {
  return (
    <Collapsible open={open} onOpenChange={onOpenChange}>
      <CollapsibleTrigger asChild>
        <button
          type="button"
          className="flex w-full items-center justify-between rounded-lg border bg-muted/20 px-3 py-2 text-sm font-medium transition-colors hover:bg-muted/40"
        >
          <div className="flex items-center gap-2">
            {group.label}
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <HelpCircle className="size-3.5 text-muted-foreground" />
                </TooltipTrigger>
                <TooltipContent className="max-w-60">
                  <p className="text-xs">{group.tooltip}</p>
                  <p className="mt-1 text-[10px] text-muted-foreground">
                    {group.referenceSection}
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <ChevronDown
            className={[
              "size-4 transition-transform",
              open ? "rotate-180" : "",
            ].join(" ")}
          />
        </button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="mt-1 space-y-3 rounded-lg border border-t-0 bg-background/50 p-3">
          {group.knobs.map((knob) => (
            <div key={knob.key} className="space-y-1">
              <Label className="text-xs">{knob.label}</Label>
              {knob.kind === "enum-short" && knob.options ? (
                <ToggleGroup
                  type="single"
                  value={knobs[knob.key] ?? knob.defaultValue}
                  onValueChange={(v) => {
                    if (v) onChange(knob.key, v)
                  }}
                  variant="outline"
                  className="flex-wrap justify-start"
                >
                  {knob.options.map((opt) => (
                    <ToggleGroupItem
                      key={opt}
                      value={opt}
                      className="h-7 px-2 text-xs"
                    >
                      {opt}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
              ) : knob.kind === "enum-long" && knob.options ? (
                <Select
                  value={knobs[knob.key] ?? knob.defaultValue}
                  onValueChange={(v) => onChange(knob.key, v)}
                >
                  <SelectTrigger className="h-8 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {knob.options.map((opt) => (
                      <SelectItem key={opt} value={opt} className="text-xs">
                        {opt}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : knob.kind === "number" ? (
                <Input
                  type="number"
                  className="h-8 text-xs"
                  value={knobs[knob.key] ?? knob.defaultValue}
                  onChange={(e) => onChange(knob.key, e.target.value)}
                />
              ) : null}
            </div>
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
}

// ---------------------------------------------------------------------------
// TextLayerPanel — 8th knob group, off by default
// ---------------------------------------------------------------------------
function TextLayerPanel({
  state,
  open,
  onOpenChange,
  onChange,
}: {
  state: TextLayerState
  open: boolean
  onOpenChange: (open: boolean) => void
  onChange: (patch: Partial<TextLayerState>) => void
}) {
  return (
    <Collapsible open={open} onOpenChange={onOpenChange}>
      <CollapsibleTrigger asChild>
        <button
          type="button"
          className="flex w-full items-center justify-between rounded-lg border bg-muted/20 px-3 py-2 text-sm font-medium transition-colors hover:bg-muted/40"
        >
          <div className="flex items-center gap-2">
            Text Layer
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <HelpCircle className="size-3.5 text-muted-foreground" />
                </TooltipTrigger>
                <TooltipContent className="max-w-60">
                  <p className="text-xs">
                    Adds a text element to the SVG output. Forwarded to
                    svg.compose as <code>text_layer</code>. Script may silently
                    ignore if not yet supported.
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <ChevronDown
            className={[
              "size-4 transition-transform",
              open ? "rotate-180" : "",
            ].join(" ")}
          />
        </button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="mt-1 space-y-3 rounded-lg border border-t-0 bg-background/50 p-3">
          <div className="flex items-center justify-between">
            <Label className="text-xs">Enable Text Layer</Label>
            <Switch
              checked={state.enabled}
              onCheckedChange={(checked) => onChange({ enabled: checked })}
            />
          </div>
          {state.enabled ? (
            <>
              <div className="space-y-1">
                <Label className="text-xs">Content</Label>
                <Input
                  className="h-8 text-xs"
                  value={state.content}
                  onChange={(e) => onChange({ content: e.target.value })}
                  placeholder="Text to render"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <Label className="text-xs">Font Size</Label>
                  <Input
                    type="number"
                    className="h-8 text-xs"
                    value={state.font_size}
                    onChange={(e) => onChange({ font_size: e.target.value })}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Fill Color</Label>
                  <Input
                    className="h-8 text-xs"
                    value={state.fill}
                    onChange={(e) => onChange({ fill: e.target.value })}
                    placeholder="#ffffff"
                  />
                </div>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Anchor</Label>
                <ToggleGroup
                  type="single"
                  value={state.anchor}
                  onValueChange={(v) => {
                    if (v) onChange({ anchor: v as TextLayerState["anchor"] })
                  }}
                  variant="outline"
                >
                  {(["start", "middle", "end"] as const).map((a) => (
                    <ToggleGroupItem
                      key={a}
                      value={a}
                      className="h-7 px-2 text-xs"
                    >
                      {a}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <Label className="text-xs">X Position %</Label>
                  <Input
                    type="number"
                    min={0}
                    max={100}
                    className="h-8 text-xs"
                    value={state.x_pct}
                    onChange={(e) => onChange({ x_pct: e.target.value })}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Y Position %</Label>
                  <Input
                    type="number"
                    min={0}
                    max={100}
                    className="h-8 text-xs"
                    value={state.y_pct}
                    onChange={(e) => onChange({ y_pct: e.target.value })}
                  />
                </div>
              </div>
            </>
          ) : (
            <p className="text-xs text-muted-foreground">
              Enable to add a text overlay to the rendered SVG.
            </p>
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
}

// ---------------------------------------------------------------------------
// ComposeStudioTab — main export
// ---------------------------------------------------------------------------
export function ComposeStudioTab() {
  const enqueueMutation = useEnqueueTesserScript()
  const createSvgMutation = useCreatePrivateSvg()

  const [activeFamily, setActiveFamily] = useState<StyleFamily | null>(null)
  const [knobs, setKnobs] = useState<KnobState>(buildDefaultKnobs)
  const [seed, setSeed] = useState(String(Math.floor(Math.random() * 99999)))
  const [openGroups, setOpenGroups] = useState<Set<string>>(
    new Set(["geometry"]),
  )
  const [textLayerOpen, setTextLayerOpen] = useState(false)
  const [textLayer, setTextLayer] = useState<TextLayerState>(DEFAULT_TEXT_LAYER)
  const [jobs, setJobs] = useState<LocalTesserJob[]>([])
  const [savedAssetIdByJobId, setSavedAssetIdByJobId] = useState<
    Record<string, string>
  >({})

  function handleFamilySelect(family: StyleFamily) {
    setActiveFamily(family)
    const rng = makeSeededRandom(Number(seed) || 42)
    setKnobs((prev) => applyFamilyBias(family, prev, rng))
  }

  function handleRandomize() {
    const newSeed = Math.floor(Math.random() * 99999)
    setSeed(String(newSeed))
    const rng = makeSeededRandom(newSeed)
    const family = activeFamily ?? "organic"
    const base: KnobState = {}
    for (const group of KNOB_GROUPS) {
      for (const knob of group.knobs) {
        const opts = knob.options ?? []
        base[knob.key] =
          opts[Math.floor(rng() * opts.length)] ?? knob.defaultValue
      }
    }
    setKnobs(applyFamilyBias(family as StyleFamily, base, rng))
  }

  function handleKnobChange(key: string, value: string) {
    setKnobs((prev) => ({ ...prev, [key]: value }))
  }

  function toggleGroup(key: string) {
    setOpenGroups((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  async function handleEnqueue() {
    if (enqueueMutation.isPending) return
    const scriptInput = buildScriptInput(knobs, textLayer)
    const response = await enqueueMutation.mutateAsync({
      scriptName: "svg.compose",
      payload: { script_input: scriptInput },
    })
    setJobs((prev) => [
      {
        jobId: response.job_id,
        requestId: response.request_id,
        scriptName: response.script_name,
        queuedAt: response.queued_at,
        scriptInput,
      },
      ...prev,
    ])
    showSuccessToast("Compose job enqueued")
  }

  async function handleSaveJob(input: {
    scriptName: string
    job: TesserJobStatusResponse
    scriptInput: Record<string, unknown>
  }) {
    if (savedAssetIdByJobId[input.job.job_id]) return
    const payload = buildTesserSvgAssetPayload({
      scriptName: input.scriptName,
      job: input.job,
      render: input.job.render ?? {},
      scriptInput: input.scriptInput,
      name: buildSavedAssetName(knobs),
      description: `Compose Studio render — family: ${knobs.style_family ?? "—"}, palette: ${knobs.palette_family ?? "—"}`,
      metadataJson: {
        source: "compose-studio",
        script_name: input.scriptName,
        script_input: input.scriptInput,
        family: knobs.style_family ?? null,
        knobs,
      },
    })
    if (!payload) return

    const created = await createSvgMutation.mutateAsync(payload)
    setSavedAssetIdByJobId((prev) => ({
      ...prev,
      [input.job.job_id]: String(created.id),
    }))
  }

  return (
    <div className="space-y-4">
      {/* Family preset row */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <Label className="text-sm">Style Family</Label>
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={handleRandomize}
          >
            <Shuffle className="mr-1 size-3.5" />
            Randomize
          </Button>
        </div>
        <FamilyPresetRow active={activeFamily} onSelect={handleFamilySelect} />
      </div>

      {/* Knob groups */}
      <div className="space-y-1.5">
        {KNOB_GROUPS.map((group) => (
          <KnobGroupPanel
            key={group.key}
            group={group}
            knobs={knobs}
            open={openGroups.has(group.key)}
            onOpenChange={() => toggleGroup(group.key)}
            onChange={handleKnobChange}
          />
        ))}
        <TextLayerPanel
          state={textLayer}
          open={textLayerOpen}
          onOpenChange={setTextLayerOpen}
          onChange={(patch) => setTextLayer((prev) => ({ ...prev, ...patch }))}
        />
      </div>

      {/* Seed + action bar */}
      <div className="flex flex-wrap items-end gap-2">
        <div className="min-w-32 flex-1 space-y-1">
          <Label className="text-xs">Seed</Label>
          <div className="flex gap-1">
            <Input
              className="h-8 font-mono text-xs"
              value={seed}
              onChange={(e) => setSeed(e.target.value)}
            />
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="h-8 px-2"
              onClick={() => setSeed(String(Math.floor(Math.random() * 99999)))}
            >
              <Shuffle className="size-3.5" />
            </Button>
          </div>
        </div>
        <Button
          onClick={() => void handleEnqueue()}
          disabled={enqueueMutation.isPending}
        >
          <Zap className="mr-1.5 size-4" />
          {enqueueMutation.isPending ? "Queueing..." : "Enqueue Render"}
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => {
            setKnobs(buildDefaultKnobs())
            setActiveFamily(null)
            setTextLayer(DEFAULT_TEXT_LAYER)
          }}
        >
          Reset
        </Button>
      </div>

      {/* Jobs section */}
      {jobs.length > 0 ? (
        <div className="space-y-2 border-t pt-4">
          <div className="flex items-center justify-between">
            <div className="text-sm font-medium">Render Jobs</div>
            <Badge variant="outline">{jobs.length}</Badge>
          </div>
          {jobs.map((job) => (
            <TesserJobRow
              key={job.jobId}
              job={job}
              onSave={handleSaveJob}
              savedAssetId={savedAssetIdByJobId[job.jobId] ?? null}
            />
          ))}
        </div>
      ) : null}
    </div>
  )
}
