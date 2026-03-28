import { Compass, Sparkles } from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import type { SvgAssetCreatePrivate } from "@/client"
import { PanelContainer } from "@/components/Page/primitives"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { showSuccessToast } from "@/hooks/useCustomToast"
import { useCreatePrivateSvg } from "@/hooks/useSvgs"
import {
  useEnqueueTesserScript,
  useTesserScriptHelp,
  useTesserScripts,
} from "@/hooks/useTesser"
import type {
  TesserJobStatusResponse,
  TesserRenderPayload,
} from "@/services/tesserService"
import { type LocalTesserJob, TesserJobRow } from "../display/TesserJobRow"
import {
  buildTesserSvgAssetPayload,
  buildTimestampedScriptAssetName,
} from "../utils/buildTesserSvgAssetPayload"

type InputMode = "guided" | "json"

type GuidedField =
  | {
      key: string
      label: string
      description?: string
      required: boolean
      kind: "string"
      defaultValue: string
    }
  | {
      key: string
      label: string
      description?: string
      required: boolean
      kind: "number"
      defaultValue: string
    }
  | {
      key: string
      label: string
      description?: string
      required: boolean
      kind: "boolean"
      defaultValue: boolean
    }
  | {
      key: string
      label: string
      description?: string
      required: boolean
      kind: "enum"
      options: string[]
      defaultValue: string
    }

interface GuidedSchemaSummary {
  supported: boolean
  fields: GuidedField[]
  reason?: string
}

function titleize(value: string): string {
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function parseObjectRecord(value: string): Record<string, unknown> | null {
  try {
    const parsed = JSON.parse(value)
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      return null
    }
    return parsed as Record<string, unknown>
  } catch {
    return null
  }
}

function summarizeGuidedSchema(
  inputSchema: Record<string, unknown> | undefined,
): GuidedSchemaSummary {
  if (!inputSchema || Object.keys(inputSchema).length === 0) {
    return {
      supported: true,
      fields: [],
    }
  }

  if (inputSchema.type !== "object") {
    return {
      supported: false,
      fields: [],
      reason: "Guided mode currently supports top-level object schemas only.",
    }
  }

  const properties = inputSchema.properties
  if (
    !properties ||
    typeof properties !== "object" ||
    Array.isArray(properties)
  ) {
    return {
      supported: true,
      fields: [],
    }
  }

  const requiredSet = new Set(
    Array.isArray(inputSchema.required)
      ? inputSchema.required.filter(
          (value): value is string => typeof value === "string",
        )
      : [],
  )

  const fields: GuidedField[] = []
  for (const [key, rawSpec] of Object.entries(
    properties as Record<string, unknown>,
  )) {
    if (!rawSpec || typeof rawSpec !== "object" || Array.isArray(rawSpec)) {
      return {
        supported: false,
        fields: [],
        reason: `Guided mode cannot interpret "${key}" yet.`,
      }
    }

    const spec = rawSpec as Record<string, unknown>
    if (
      Array.isArray(spec.enum) &&
      spec.enum.every((value) => typeof value === "string")
    ) {
      fields.push({
        key,
        label: typeof spec.title === "string" ? spec.title : titleize(key),
        description:
          typeof spec.description === "string" ? spec.description : undefined,
        required: requiredSet.has(key),
        kind: "enum",
        options: spec.enum,
        defaultValue:
          typeof spec.default === "string" && spec.enum.includes(spec.default)
            ? spec.default
            : (spec.enum[0] ?? ""),
      })
      continue
    }

    if (spec.type === "string") {
      fields.push({
        key,
        label: typeof spec.title === "string" ? spec.title : titleize(key),
        description:
          typeof spec.description === "string" ? spec.description : undefined,
        required: requiredSet.has(key),
        kind: "string",
        defaultValue: typeof spec.default === "string" ? spec.default : "",
      })
      continue
    }

    if (spec.type === "number" || spec.type === "integer") {
      fields.push({
        key,
        label: typeof spec.title === "string" ? spec.title : titleize(key),
        description:
          typeof spec.description === "string" ? spec.description : undefined,
        required: requiredSet.has(key),
        kind: "number",
        defaultValue:
          typeof spec.default === "number" ? String(spec.default) : "",
      })
      continue
    }

    if (spec.type === "boolean") {
      fields.push({
        key,
        label: typeof spec.title === "string" ? spec.title : titleize(key),
        description:
          typeof spec.description === "string" ? spec.description : undefined,
        required: requiredSet.has(key),
        kind: "boolean",
        defaultValue: typeof spec.default === "boolean" ? spec.default : false,
      })
      continue
    }

    return {
      supported: false,
      fields: [],
      reason: `Guided mode currently supports string, number, boolean, and enum fields. "${key}" falls outside that set.`,
    }
  }

  return {
    supported: true,
    fields,
  }
}

function buildGuidedState(
  fields: GuidedField[],
  source?: Record<string, unknown> | null,
): Record<string, unknown> {
  const next: Record<string, unknown> = {}

  for (const field of fields) {
    const sourceValue = source?.[field.key]
    if (field.kind === "boolean") {
      next[field.key] =
        typeof sourceValue === "boolean" ? sourceValue : field.defaultValue
      continue
    }
    if (field.kind === "number") {
      next[field.key] =
        typeof sourceValue === "number"
          ? String(sourceValue)
          : typeof sourceValue === "string"
            ? sourceValue
            : field.defaultValue
      continue
    }
    next[field.key] =
      typeof sourceValue === "string" ? sourceValue : field.defaultValue
  }

  return next
}

function guidedStateToScriptInput(
  fields: GuidedField[],
  guidedState: Record<string, unknown>,
) {
  const result: Record<string, unknown> = {}

  for (const field of fields) {
    const value = guidedState[field.key]
    if (field.kind === "boolean") {
      result[field.key] = Boolean(value)
      continue
    }

    if (field.kind === "number") {
      if (typeof value !== "string" || value.trim() === "") continue
      const parsed = Number(value)
      if (!Number.isNaN(parsed)) {
        result[field.key] = parsed
      }
      continue
    }

    if (typeof value !== "string") continue
    if (!field.required && value.trim() === "") continue
    result[field.key] = value
  }

  return result
}

function buildSvgAssetPayload(input: {
  scriptName: string
  job: TesserJobStatusResponse
  render: TesserRenderPayload
  scriptInput: Record<string, unknown>
}): SvgAssetCreatePrivate | null {
  return buildTesserSvgAssetPayload({
    ...input,
    name: buildTimestampedScriptAssetName(input.scriptName),
  })
}

function ScriptsSkeleton() {
  return (
    <div className="space-y-4 p-4">
      <Skeleton className="h-9 w-full" />
      <Skeleton className="h-28 w-full rounded-xl" />
      <Skeleton className="h-52 w-full rounded-xl" />
    </div>
  )
}

export function TesserStudioPanel() {
  const scriptsQuery = useTesserScripts({ format: "svg" })
  const enqueueMutation = useEnqueueTesserScript()
  const createSvgMutation = useCreatePrivateSvg()

  const scripts = scriptsQuery.data?.data ?? []
  const [selectedScriptName, setSelectedScriptName] = useState("")
  const [inputMode, setInputMode] = useState<InputMode>("guided")
  const [configJson, setConfigJson] = useState("{}")
  const [configError, setConfigError] = useState<string | null>(null)
  const [jobs, setJobs] = useState<LocalTesserJob[]>([])
  const [savedAssetIdByJobId, setSavedAssetIdByJobId] = useState<
    Record<string, string>
  >({})
  const [guidedState, setGuidedState] = useState<Record<string, unknown>>({})

  useEffect(() => {
    if (
      selectedScriptName &&
      scripts.some((script) => script.name === selectedScriptName)
    )
      return
    if (scripts[0]?.name) {
      setSelectedScriptName(scripts[0].name)
    }
  }, [scripts, selectedScriptName])

  const helpQuery = useTesserScriptHelp(selectedScriptName, {
    enabled: Boolean(selectedScriptName),
  })

  const selectedScript = useMemo(
    () => scripts.find((script) => script.name === selectedScriptName) ?? null,
    [scripts, selectedScriptName],
  )
  const inputSchema =
    helpQuery.data?.input_schema ?? selectedScript?.input_schema
  const guidedSchema = useMemo(
    () => summarizeGuidedSchema(inputSchema),
    [inputSchema],
  )

  useEffect(() => {
    const parsedJson = parseObjectRecord(configJson)
    setGuidedState(buildGuidedState(guidedSchema.fields, parsedJson))
  }, [guidedSchema.fields, configJson])

  useEffect(() => {
    if (inputMode !== "guided") return
    const nextJson = JSON.stringify(
      guidedStateToScriptInput(guidedSchema.fields, guidedState),
      null,
      2,
    )
    setConfigJson(nextJson)
    setConfigError(null)
  }, [guidedSchema.fields, guidedState, inputMode])

  useEffect(() => {
    if (guidedSchema.supported) return
    setInputMode("json")
  }, [guidedSchema.supported])

  const handleEnqueue = async () => {
    if (!selectedScriptName || enqueueMutation.isPending) return

    let parsedConfig: Record<string, unknown> = {}
    if (inputMode === "guided") {
      parsedConfig = guidedStateToScriptInput(guidedSchema.fields, guidedState)
      setConfigJson(JSON.stringify(parsedConfig, null, 2))
    } else {
      const trimmed = configJson.trim()
      if (trimmed.length > 0) {
        const parsed = parseObjectRecord(trimmed)
        if (!parsed) {
          setConfigError("Script input must be a JSON object.")
          return
        }
        parsedConfig = parsed
      }
    }

    setConfigError(null)
    const response = await enqueueMutation.mutateAsync({
      scriptName: selectedScriptName,
      payload: { script_input: parsedConfig },
    })

    setJobs((previous) => [
      {
        jobId: response.job_id,
        requestId: response.request_id,
        scriptName: response.script_name,
        queuedAt: response.queued_at,
        scriptInput: parsedConfig,
      },
      ...previous.filter((job) => job.jobId !== response.job_id),
    ])

    showSuccessToast(`Queued ${response.script_name}`)
  }

  const handleSaveJob = async (input: {
    scriptName: string
    job: TesserJobStatusResponse
    scriptInput: Record<string, unknown>
  }) => {
    if (savedAssetIdByJobId[input.job.job_id]) return
    const payload = buildSvgAssetPayload({
      scriptName: input.scriptName,
      job: input.job,
      render: input.job.render ?? {},
      scriptInput: input.scriptInput,
    })
    if (!payload) return

    const created = await createSvgMutation.mutateAsync(payload)
    setSavedAssetIdByJobId((previous) => ({
      ...previous,
      [input.job.job_id]: String(created.id),
    }))
  }

  if (scriptsQuery.isLoading) {
    return (
      <PanelContainer title="Tesser Studio" scrollable>
        <ScriptsSkeleton />
      </PanelContainer>
    )
  }

  return (
    <PanelContainer
      title="Tesser Studio"
      scrollable
      headerActions={
        <div className="flex items-center gap-2">
          <Badge variant="outline">{scripts.length} scripts</Badge>
          <Button
            size="sm"
            variant="outline"
            onClick={() => scriptsQuery.refetch()}
            disabled={scriptsQuery.isFetching}
          >
            Refresh
          </Button>
        </div>
      }
    >
      <div className="space-y-4 p-4">
        <div className="rounded-2xl border bg-[linear-gradient(135deg,rgba(251,191,36,0.15),rgba(249,115,22,0.08)_38%,rgba(15,23,42,0.03)_100%)] p-1">
          <Alert className="border-0 bg-transparent">
            <Sparkles className="h-4 w-4" />
            <AlertTitle>Tesser Studio</AlertTitle>
            <AlertDescription>
              Script-driven SVG making for the moments when the gallery should
              feel less like storage and more like a workshop. Start with JSON,
              move quickly, and keep the output visible while the wider
              interface catches up.
            </AlertDescription>
          </Alert>
        </div>

        <Alert className="border-dashed bg-muted/20">
          <Sparkles className="h-4 w-4" />
          <AlertTitle>JSON-First MVP</AlertTitle>
          <AlertDescription>
            Choose a script, provide `script_input` as JSON, enqueue the render
            job, and inspect the result in-session. Guided controls arrive next;
            raw reach comes first.
          </AlertDescription>
        </Alert>

        {scriptsQuery.error ? (
          <Alert variant="destructive">
            <AlertTitle>Failed to load Tesser scripts</AlertTitle>
            <AlertDescription>{scriptsQuery.error.message}</AlertDescription>
          </Alert>
        ) : null}

        {!scriptsQuery.error && scripts.length === 0 ? (
          <Alert>
            <AlertTitle>No Tesser scripts available</AlertTitle>
            <AlertDescription>
              The Tesser script list is currently empty.
            </AlertDescription>
          </Alert>
        ) : null}

        {scripts.length > 0 ? (
          <>
            <div className="space-y-1.5">
              <Label htmlFor="tesser-script">Script</Label>
              <Select
                value={selectedScriptName}
                onValueChange={setSelectedScriptName}
              >
                <SelectTrigger id="tesser-script" className="w-full">
                  <SelectValue placeholder="Select a Tesser script" />
                </SelectTrigger>
                <SelectContent>
                  {scripts.map((script) => (
                    <SelectItem key={script.name} value={script.name}>
                      {script.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {selectedScript ? (
              <div className="space-y-3 rounded-xl border bg-[linear-gradient(180deg,rgba(255,255,255,0.02),rgba(148,163,184,0.08))] p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="secondary">
                    {selectedScript.kind ?? "script"}
                  </Badge>
                  {selectedScript.source_path ? (
                    <Badge variant="outline">
                      {selectedScript.source_path}
                    </Badge>
                  ) : null}
                </div>
                <p className="text-sm text-muted-foreground">
                  {helpQuery.data?.description ||
                    selectedScript.description ||
                    "No description."}
                </p>
                {helpQuery.data?.input_schema ? (
                  <div className="text-xs text-muted-foreground">
                    input schema detected; guided mode supports simple top-level
                    fields and falls back to JSON when needed.
                  </div>
                ) : null}
                {helpQuery.isLoading ? (
                  <Skeleton className="h-20 w-full" />
                ) : helpQuery.data?.help_text ? (
                  <pre className="max-h-48 overflow-auto rounded-lg border bg-background/90 p-3 text-xs">
                    {helpQuery.data.help_text}
                  </pre>
                ) : null}
              </div>
            ) : null}

            <div className="space-y-2">
              <div className="space-y-2 rounded-xl border bg-[linear-gradient(135deg,rgba(14,165,233,0.08),rgba(249,115,22,0.08))] p-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-medium">Input Mode</div>
                    <div className="text-xs text-muted-foreground">
                      Guided mode makes the common path lighter. JSON keeps the
                      full surface area available.
                    </div>
                  </div>
                  <ToggleGroup
                    type="single"
                    value={inputMode}
                    onValueChange={(value) => {
                      if (!value) return
                      setInputMode(value as InputMode)
                    }}
                    variant="outline"
                  >
                    <ToggleGroupItem
                      value="guided"
                      disabled={!guidedSchema.supported}
                      aria-label="Guided input mode"
                    >
                      <Compass className="mr-1 size-4" />
                      Guided
                    </ToggleGroupItem>
                    <ToggleGroupItem value="json" aria-label="JSON input mode">
                      JSON
                    </ToggleGroupItem>
                  </ToggleGroup>
                </div>
                {!guidedSchema.supported ? (
                  <div className="text-xs text-muted-foreground">
                    {guidedSchema.reason ??
                      "This script currently needs JSON mode."}
                  </div>
                ) : guidedSchema.fields.length === 0 ? (
                  <div className="text-xs text-muted-foreground">
                    This script can run without configuration, but JSON is still
                    available if you want to experiment.
                  </div>
                ) : (
                  <div className="text-xs text-muted-foreground">
                    Guided mode is ready for {guidedSchema.fields.length} field
                    {guidedSchema.fields.length === 1 ? "" : "s"}.
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between gap-2">
                <Label htmlFor="tesser-script-input">
                  {inputMode === "guided"
                    ? "Guided Script Input"
                    : "Script Input JSON"}
                </Label>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    setConfigJson("{}")
                    setGuidedState(buildGuidedState(guidedSchema.fields, {}))
                    setConfigError(null)
                  }}
                >
                  Reset
                </Button>
              </div>

              {inputMode === "guided" && guidedSchema.supported ? (
                <div className="space-y-3 rounded-xl border bg-[linear-gradient(180deg,rgba(255,255,255,0.03),rgba(15,23,42,0.03))] p-3">
                  {guidedSchema.fields.length === 0 ? (
                    <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
                      No guided fields are required for this script. You can run
                      it as-is or switch to JSON mode to explore optional
                      inputs.
                    </div>
                  ) : (
                    guidedSchema.fields.map((field) => (
                      <div
                        key={field.key}
                        className="space-y-1.5 rounded-lg border bg-background/70 p-3"
                      >
                        <div className="flex flex-wrap items-center gap-2">
                          <Label htmlFor={`guided-${field.key}`}>
                            {field.label}
                          </Label>
                          {field.required ? (
                            <Badge variant="secondary">required</Badge>
                          ) : null}
                          <Badge variant="outline">{field.kind}</Badge>
                        </div>
                        {field.description ? (
                          <div className="text-xs text-muted-foreground">
                            {field.description}
                          </div>
                        ) : null}

                        {field.kind === "string" ? (
                          <Input
                            id={`guided-${field.key}`}
                            value={String(guidedState[field.key] ?? "")}
                            onChange={(event) =>
                              setGuidedState((previous) => ({
                                ...previous,
                                [field.key]: event.target.value,
                              }))
                            }
                            placeholder={field.label}
                          />
                        ) : null}

                        {field.kind === "number" ? (
                          <Input
                            id={`guided-${field.key}`}
                            inputMode="decimal"
                            value={String(guidedState[field.key] ?? "")}
                            onChange={(event) =>
                              setGuidedState((previous) => ({
                                ...previous,
                                [field.key]: event.target.value,
                              }))
                            }
                            placeholder="0"
                          />
                        ) : null}

                        {field.kind === "enum" ? (
                          <Select
                            value={String(
                              guidedState[field.key] ?? field.defaultValue,
                            )}
                            onValueChange={(value) =>
                              setGuidedState((previous) => ({
                                ...previous,
                                [field.key]: value,
                              }))
                            }
                          >
                            <SelectTrigger
                              id={`guided-${field.key}`}
                              className="w-full"
                            >
                              <SelectValue placeholder={field.label} />
                            </SelectTrigger>
                            <SelectContent>
                              {field.options.map((option) => (
                                <SelectItem key={option} value={option}>
                                  {option}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        ) : null}

                        {field.kind === "boolean" ? (
                          <div className="flex items-center justify-between rounded-lg border bg-muted/20 px-3 py-2">
                            <div className="text-xs text-muted-foreground">
                              Toggle this option on or off.
                            </div>
                            <Switch
                              id={`guided-${field.key}`}
                              checked={Boolean(guidedState[field.key])}
                              onCheckedChange={(checked) =>
                                setGuidedState((previous) => ({
                                  ...previous,
                                  [field.key]: checked,
                                }))
                              }
                            />
                          </div>
                        ) : null}
                      </div>
                    ))
                  )}

                  <div className="rounded-lg border border-dashed bg-muted/10 p-3">
                    <div className="text-xs font-medium text-foreground">
                      Live JSON Mirror
                    </div>
                    <pre className="mt-2 max-h-40 overflow-auto rounded-md bg-background p-3 text-xs">
                      {configJson}
                    </pre>
                  </div>
                </div>
              ) : (
                <Textarea
                  id="tesser-script-input"
                  value={configJson}
                  onChange={(event) => setConfigJson(event.target.value)}
                  placeholder='{"title":"Hello","subtitle":"World"}'
                  className="min-h-[220px] rounded-xl border-muted-foreground/20 bg-[linear-gradient(180deg,rgba(15,23,42,0.02),rgba(15,23,42,0.05))] font-mono text-sm"
                />
              )}
              {configError ? (
                <p className="text-xs text-destructive">{configError}</p>
              ) : null}
              <p className="text-xs text-muted-foreground">
                Guided mode handles the approachable path. JSON remains the
                escape hatch that keeps the broader library reachable without
                frontend rewrites.
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                onClick={() => void handleEnqueue()}
                disabled={enqueueMutation.isPending}
              >
                {enqueueMutation.isPending ? "Queueing..." : "Enqueue Render"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() =>
                  setConfigJson(
                    '{\n  "title": "Signal Bloom",\n  "subtitle": "Tesser Studio"\n}',
                  )
                }
              >
                Seed Example
              </Button>
            </div>

            <div className="space-y-3 border-t pt-4">
              <div className="flex items-center justify-between gap-2">
                <div className="text-sm font-medium">Jobs</div>
                <Badge variant="outline">{jobs.length}</Badge>
              </div>
              {jobs.length === 0 ? (
                <Alert>
                  <AlertTitle>No jobs yet</AlertTitle>
                  <AlertDescription>
                    Enqueue a Tesser script to inspect job state and SVG output
                    here.
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="space-y-3">
                  {jobs.map((job) => (
                    <TesserJobRow
                      key={job.jobId}
                      job={job}
                      onSave={handleSaveJob}
                      savedAssetId={savedAssetIdByJobId[job.jobId] ?? null}
                    />
                  ))}
                </div>
              )}
            </div>
          </>
        ) : null}
      </div>
    </PanelContainer>
  )
}
