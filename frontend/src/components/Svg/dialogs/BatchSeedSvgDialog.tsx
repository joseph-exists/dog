/**
 * BatchSeedSvgDialog — rebuilt
 *
 * Three-phase flow: Configure → Preview & Override → Enqueue & Track
 *
 * Scenario generation uses buildScenarios() from svgComposeDomains.ts,
 * a simplified approximation of the Python pairwise planner.
 * Each scenario is enqueued as an individual svg.compose Tesser job.
 *
 * For exhaustive library population, use the CLI instead:
 *   python -m app.test_scripts.typer svgs seed --count N
 *
 * See: backend/app/test_scripts/render_things/svg_combinatorics_reference_card.md
 */
import { ChevronDown, ChevronUp, Shuffle } from "lucide-react"
import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { showSuccessToast } from "@/hooks/useCustomToast"
import { useEnqueueTesserScript } from "@/hooks/useTesser"
import {
  buildScenarios,
  FAMILY_ACCENT,
  KNOB_GROUPS,
  type Scenario,
  type ScenarioTier,
  STYLE_FAMILIES,
  type StyleFamily,
} from "../constants/svgComposeDomains"
import { type LocalTesserJob, TesserJobRow } from "../display/TesserJobRow"

type Phase = "configure" | "preview" | "enqueuing" | "done"

// ---------------------------------------------------------------------------
// ScenarioRow — shows one scenario in the preview accordion
// ---------------------------------------------------------------------------
function ScenarioRow({
  scenario,
  onKnobChange,
}: {
  scenario: Scenario
  onKnobChange: (index: number, key: string, value: string) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const keyKnobs = [
    "palette_family",
    "shape_family",
    "displacement_scale",
    "density",
    "gaussian_blur",
  ]

  return (
    <div className="rounded-lg border bg-muted/10">
      <div className="flex items-center justify-between gap-2 px-3 py-2">
        <div className="flex flex-wrap items-center gap-1.5 min-w-0">
          <Badge
            variant="outline"
            className={`text-[10px] capitalize ${FAMILY_ACCENT[scenario.family]}`}
          >
            {scenario.family}
          </Badge>
          {keyKnobs.map((k) =>
            scenario.knobs[k] ? (
              <span key={k} className="text-[10px] text-muted-foreground">
                {scenario.knobs[k]}
              </span>
            ) : null,
          )}
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="h-6 px-2 text-xs"
          onClick={() => setExpanded((p) => !p)}
        >
          {expanded ? (
            <ChevronUp className="size-3" />
          ) : (
            <ChevronDown className="size-3" />
          )}
          Edit
        </Button>
      </div>

      {expanded ? (
        <div className="border-t px-3 py-2 space-y-3">
          {KNOB_GROUPS.map((group) => (
            <div key={group.key} className="space-y-1.5">
              <div className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
                {group.label}
              </div>
              <div className="grid gap-1.5 sm:grid-cols-2">
                {group.knobs.map((knob) => (
                  <div key={knob.key} className="space-y-0.5">
                    <Label className="text-[10px]">{knob.label}</Label>
                    {knob.options && knob.options.length <= 4 ? (
                      <ToggleGroup
                        type="single"
                        value={scenario.knobs[knob.key] ?? knob.defaultValue}
                        onValueChange={(v) => {
                          if (v) onKnobChange(scenario.index, knob.key, v)
                        }}
                        variant="outline"
                        className="flex-wrap justify-start"
                      >
                        {knob.options.map((opt) => (
                          <ToggleGroupItem
                            key={opt}
                            value={opt}
                            className="h-6 px-1.5 text-[10px]"
                          >
                            {opt}
                          </ToggleGroupItem>
                        ))}
                      </ToggleGroup>
                    ) : knob.options ? (
                      <Select
                        value={scenario.knobs[knob.key] ?? knob.defaultValue}
                        onValueChange={(v) =>
                          onKnobChange(scenario.index, knob.key, v)
                        }
                      >
                        <SelectTrigger className="h-6 text-[10px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {knob.options.map((opt) => (
                            <SelectItem
                              key={opt}
                              value={opt}
                              className="text-[10px]"
                            >
                              {opt}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    ) : (
                      <Input
                        className="h-6 text-[10px]"
                        value={scenario.knobs[knob.key] ?? knob.defaultValue}
                        onChange={(e) =>
                          onKnobChange(scenario.index, knob.key, e.target.value)
                        }
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  )
}

// ---------------------------------------------------------------------------
// BatchSeedSvgDialog
// ---------------------------------------------------------------------------
export function BatchSeedSvgDialog() {
  const enqueueMutation = useEnqueueTesserScript()

  const [open, setOpen] = useState(false)
  const [phase, setPhase] = useState<Phase>("configure")

  // Configure state
  const [count, setCount] = useState("8")
  const [seed, setSeed] = useState(String(Math.floor(Math.random() * 99999)))
  const [families, setFamilies] = useState<StyleFamily[]>([...STYLE_FAMILIES])
  const [tier, setTier] = useState<ScenarioTier>("pairwise")

  // Preview state
  const [scenarios, setScenarios] = useState<Scenario[]>([])

  // Enqueue state
  const [jobs, setJobs] = useState<LocalTesserJob[]>([])
  const [progress, setProgress] = useState({ done: 0, total: 0 })
  const [savedAssetIdByJobId, setSavedAssetIdByJobId] = useState<
    Record<string, string>
  >({})

  const parsedCount = Math.min(Math.max(Number.parseInt(count, 10) || 1, 1), 24)

  function handleGeneratePlan() {
    const generated = buildScenarios({
      count: parsedCount,
      seed: Number(seed) || 42,
      families,
      tier,
    })
    setScenarios(generated)
    setPhase("preview")
  }

  function handleKnobChange(index: number, key: string, value: string) {
    setScenarios((prev) =>
      prev.map((s) =>
        s.index === index ? { ...s, knobs: { ...s.knobs, [key]: value } } : s,
      ),
    )
  }

  async function handleEnqueueAll() {
    setPhase("enqueuing")
    setProgress({ done: 0, total: scenarios.length })
    const newJobs: LocalTesserJob[] = []

    for (const scenario of scenarios) {
      const scriptInput: Record<string, unknown> = { ...scenario.knobs }
      try {
        const response = await enqueueMutation.mutateAsync({
          scriptName: "svg.compose",
          payload: { script_input: scriptInput },
        })
        newJobs.push({
          jobId: response.job_id,
          requestId: response.request_id,
          scriptName: response.script_name,
          queuedAt: response.queued_at,
          scriptInput,
        })
        setProgress((p) => ({ ...p, done: p.done + 1 }))
      } catch {
        setProgress((p) => ({ ...p, done: p.done + 1 }))
      }
    }

    setJobs(newJobs)
    setPhase("done")
    showSuccessToast(`Enqueued ${newJobs.length} compose jobs`)
  }

  function handleReset() {
    setPhase("configure")
    setScenarios([])
    setJobs([])
    setProgress({ done: 0, total: 0 })
    setSavedAssetIdByJobId({})
  }

  function handleClose(isOpen: boolean) {
    setOpen(isOpen)
    if (!isOpen) handleReset()
  }

  function toggleFamily(family: StyleFamily) {
    setFamilies((prev) =>
      prev.includes(family)
        ? prev.length > 1
          ? prev.filter((f) => f !== family)
          : prev // keep at least one
        : [...prev, family],
    )
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          Batch Seed
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Batch Seed SVG Library</DialogTitle>
          <DialogDescription>
            Generate scenarios from combinatoric domains and enqueue as{" "}
            <code>svg.compose</code> Tesser jobs. Review and override any
            scenario before queueing.
          </DialogDescription>
        </DialogHeader>

        {/* Phase: configure */}
        {phase === "configure" ? (
          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>
                  Count{" "}
                  <span className="text-xs text-muted-foreground">
                    (max 24 — use CLI for bulk)
                  </span>
                </Label>
                <Input
                  type="number"
                  min={1}
                  max={24}
                  value={count}
                  onChange={(e) => setCount(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Seed</Label>
                <div className="flex gap-1">
                  <Input
                    value={seed}
                    onChange={(e) => setSeed(e.target.value)}
                    className="font-mono"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="px-2"
                    onClick={() =>
                      setSeed(String(Math.floor(Math.random() * 99999)))
                    }
                  >
                    <Shuffle className="size-3.5" />
                  </Button>
                </div>
              </div>
            </div>

            <div className="space-y-1.5">
              <Label>Style Families</Label>
              <div className="flex flex-wrap gap-1.5">
                {STYLE_FAMILIES.map((family) => (
                  <button
                    key={family}
                    type="button"
                    onClick={() => toggleFamily(family)}
                    className={[
                      "rounded-md border px-2 py-1 text-xs capitalize transition-all",
                      families.includes(family)
                        ? `${FAMILY_ACCENT[family]} font-medium`
                        : "border-border bg-muted/20 text-muted-foreground",
                    ].join(" ")}
                  >
                    {family}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-1.5">
              <Label>Generation Tier</Label>
              <ToggleGroup
                type="single"
                value={tier}
                onValueChange={(v) => {
                  if (v) setTier(v as ScenarioTier)
                }}
                variant="outline"
              >
                <ToggleGroupItem value="pairwise" className="text-xs">
                  Pairwise
                  <span className="ml-1 hidden sm:inline text-muted-foreground">
                    broad coverage
                  </span>
                </ToggleGroupItem>
                <ToggleGroupItem value="hero" className="text-xs">
                  Hero
                  <span className="ml-1 hidden sm:inline text-muted-foreground">
                    maxed drama
                  </span>
                </ToggleGroupItem>
                <ToggleGroupItem value="safe" className="text-xs">
                  Safe
                  <span className="ml-1 hidden sm:inline text-muted-foreground">
                    sparse utility
                  </span>
                </ToggleGroupItem>
              </ToggleGroup>
            </div>

            <Button onClick={handleGeneratePlan} className="w-full">
              Generate Plan ({parsedCount} scenarios)
            </Button>
          </div>
        ) : null}

        {/* Phase: preview */}
        {phase === "preview" ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium">
                {scenarios.length} scenarios — review and edit before enqueuing
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setPhase("configure")}
              >
                ← Back
              </Button>
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
              {scenarios.map((scenario) => (
                <ScenarioRow
                  key={scenario.index}
                  scenario={scenario}
                  onKnobChange={handleKnobChange}
                />
              ))}
            </div>

            <Button onClick={() => void handleEnqueueAll()} className="w-full">
              Enqueue All {scenarios.length} Jobs
            </Button>
          </div>
        ) : null}

        {/* Phase: enqueuing */}
        {phase === "enqueuing" ? (
          <div className="space-y-3 py-4">
            <div className="text-sm font-medium text-center">
              Enqueuing {progress.done} / {progress.total}...
            </div>
            <Progress
              value={(progress.done / Math.max(progress.total, 1)) * 100}
            />
          </div>
        ) : null}

        {/* Phase: done */}
        {phase === "done" ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium">
                {jobs.length} jobs queued
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={handleReset}
              >
                Seed Again
              </Button>
            </div>
            <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
              {jobs.map((job) => (
                <TesserJobRow
                  key={job.jobId}
                  job={job}
                  onSave={async () => {}}
                  savedAssetId={savedAssetIdByJobId[job.jobId] ?? null}
                />
              ))}
            </div>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}
