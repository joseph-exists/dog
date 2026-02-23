import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Loader2, Plus, RotateCcw, Save, Trash2 } from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import { DemosService } from "@/client"
import type {
  DemoChatMode,
  DemoConfigPublic,
  DemoLayoutMode,
  DemoPageCompositionBase_Input,
  DemoPageCompositionPublic,
  DemoPersonaPolicy,
  DemoRuntimePolicy,
} from "@/client/types.gen"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"

export const Route = createFileRoute("/_layout/demo-builder")({
  component: DemoBuilderPage,
  head: () => ({
    meta: [{ title: "Demo Builder" }],
  }),
})

// ============================================================================
// Builder Type Aliases
// ============================================================================
// These aliases keep the editor tightly coupled to generated OpenAPI types
// while still being readable during UI implementation.
type EditableComposition = DemoPageCompositionBase_Input
type EditablePanel = NonNullable<EditableComposition["panels"]>[number]
type EditableBlock = NonNullable<EditableComposition["blocks"]>[number]

type PanelProminence = "primary" | "auxiliary"
type BlockRegion = "top" | "primary" | "auxiliary" | "footer"
type BlockVisibility = "visible" | "hidden_unmounted" | "hidden_mounted"

// ============================================================================
// Active Builder Domains
// ============================================================================
// The builder intentionally exposes current active kinds/types instead of every
// compatibility variant from generated unions. This prevents accidental authoring
// of deferred compatibility constructs.
const ACTIVE_PANEL_KINDS = [
  "storyRuntime",
  "chat",
  "content",
  "participantPanel",
  "canvas",
  "a2ui",
  "storyEditor",
  "storyPlayer",
  "debug",
] as const

const ACTIVE_BLOCK_TYPES = [
  "context",
  "content",
  "story",
  "storyMetadata",
  "agentRoster",
  "orchestratorState",
  "toolCapability",
  "contributionFeed",
  "gitView",
  "fileExplorer",
] as const

const LAYOUT_MODES: DemoLayoutMode[] = ["panels", "tabs"]
const RUNTIME_POLICIES: DemoRuntimePolicy[] = ["auto", "manual", "owner_only"]
const PERSONA_POLICIES: DemoPersonaPolicy[] = [
  "first_available",
  "fixed_user_persona",
  "manual_prompt",
]
const CHAT_MODES: DemoChatMode[] = ["participant", "observer"]
const PANEL_PROMINENCE: PanelProminence[] = ["primary", "auxiliary"]
const VIEWPORT_MODES = ["panel", "page"] as const
const BLOCK_REGIONS: BlockRegion[] = ["top", "primary", "auxiliary", "footer"]
const BLOCK_VISIBILITY: BlockVisibility[] = [
  "visible",
  "hidden_unmounted",
  "hidden_mounted",
]

// ============================================================================
// Composition Helpers
// ============================================================================
// These helpers isolate normalization/defaulting concerns so the route remains
// focused on user interactions.
function createEmptyComposition(): EditableComposition {
  return {
    schema_version: 1,
    layout_mode: "panels",
    runtime_policy: "auto",
    persona_policy: "first_available",
    chat_mode: "participant",
    fixed_user_persona_id: null,
    page_theme_id: null,
    cards_theme_id: null,
    presentation_json: {},
    metadata_json: {},
    panels: [],
    blocks: [],
  }
}

function normalizeComposition(
  value: DemoPageCompositionPublic | DemoPageCompositionBase_Input | null | undefined,
): EditableComposition {
  // Deep clone avoids mutating query cache payloads while editing.
  const cloned = value
    ? JSON.parse(JSON.stringify(value))
    : {}

  return {
    ...createEmptyComposition(),
    ...(cloned as EditableComposition),
    panels: Array.isArray((cloned as EditableComposition).panels)
      ? (cloned as EditableComposition).panels
      : [],
    blocks: Array.isArray((cloned as EditableComposition).blocks)
      ? (cloned as EditableComposition).blocks
      : [],
  }
}

function toPrettyJson(value: unknown): string {
  return JSON.stringify(value ?? {}, null, 2)
}

function parseInteger(value: string): number | undefined {
  const trimmed = value.trim()
  if (!trimmed) return undefined
  const parsed = Number.parseInt(trimmed, 10)
  return Number.isFinite(parsed) ? parsed : undefined
}

function parseObjectJsonOrThrow(raw: string): Record<string, unknown> {
  const parsed = JSON.parse(raw)
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("Expected a JSON object.")
  }
  return parsed as Record<string, unknown>
}

function parseNullableObjectJsonOrThrow(raw: string): Record<string, unknown> | null {
  const trimmed = raw.trim()
  if (!trimmed) return {}
  if (trimmed === "null") return null
  return parseObjectJsonOrThrow(trimmed)
}

function extractApiErrorDetail(error: unknown): string | null {
  if (!error || typeof error !== "object") return null
  const maybe = error as { body?: unknown; message?: string }
  if (!maybe.body || typeof maybe.body !== "object") return null
  const detail = (maybe.body as { detail?: unknown }).detail
  return typeof detail === "string" ? detail : null
}

function createPanelTemplate(kind: (typeof ACTIVE_PANEL_KINDS)[number]): EditablePanel {
  return {
    id: `${kind}-${Date.now()}`,
    kind,
    prominence: kind === "chat" || kind === "participantPanel" || kind === "debug"
      ? "auxiliary"
      : "primary",
    order: 1,
    title: kind,
    viewport_mode: "panel",
    options: {},
    presentation_json: {},
  }
}

function createBlockTemplate(type: (typeof ACTIVE_BLOCK_TYPES)[number]): EditableBlock {
  return {
    id: `${type}-${Date.now()}`,
    type,
    region: "top",
    order: 1,
    title: type,
    visibility: "visible",
    config_json: {},
    presentation_json: {},
  }
}

// ============================================================================
// Route Component
// ============================================================================
function DemoBuilderPage() {
  const queryClient = useQueryClient()

  // Demo selector + optional create form state
  const [selectedDemoConfigId, setSelectedDemoConfigId] = useState<string>("")
  const [newSlug, setNewSlug] = useState("")
  const [newTitle, setNewTitle] = useState("")

  // Local editable composition state + raw JSON draft for power-edit mode.
  const [composition, setComposition] = useState<EditableComposition>(createEmptyComposition())
  const [rawJsonDraft, setRawJsonDraft] = useState<string>(toPrettyJson(createEmptyComposition()))
  const [isDirty, setIsDirty] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  // Load all visible demo configs for builder selection.
  const { data: demosPayload, isLoading: isLoadingDemos } = useQuery({
    queryKey: ["demo-builder", "configs"],
    queryFn: () =>
      DemosService.listAllDemoConfigs({
        limit: 200,
        includeInactive: true,
        includeSystem: true,
      }),
  })
  const demoConfigs: DemoConfigPublic[] = demosPayload?.data ?? []

  const selectedDemo = useMemo(
    () => demoConfigs.find((demo) => demo.id === selectedDemoConfigId) ?? null,
    [demoConfigs, selectedDemoConfigId],
  )

  // Load composition when a demo is selected.
  const {
    data: selectedComposition,
    isLoading: isLoadingComposition,
  } = useQuery({
    queryKey: ["demo-builder", "composition", selectedDemoConfigId],
    queryFn: () =>
      DemosService.getDemoComposition({
        demoConfigId: selectedDemoConfigId,
      }),
    enabled: Boolean(selectedDemoConfigId),
  })

  // Keep local editor state synchronized to latest server payload.
  useEffect(() => {
    if (!selectedComposition) return
    const normalized = normalizeComposition(selectedComposition)
    setComposition(normalized)
    setRawJsonDraft(toPrettyJson(normalized))
    setFieldErrors({})
    setIsDirty(false)
  }, [selectedComposition])

  // --------------------------------------------------------------------------
  // Mutations
  // --------------------------------------------------------------------------
  const saveCompositionMutation = useMutation({
    mutationFn: async () => {
      if (!selectedDemoConfigId) {
        throw new Error("Select a demo before saving composition.")
      }
      return DemosService.putDemoComposition({
        demoConfigId: selectedDemoConfigId,
        requestBody: composition,
      })
    },
    onSuccess: (savedComposition) => {
      const normalized = normalizeComposition(savedComposition)
      setComposition(normalized)
      setRawJsonDraft(toPrettyJson(normalized))
      setFieldErrors({})
      setIsDirty(false)
      queryClient.invalidateQueries({ queryKey: ["demo-builder", "composition", selectedDemoConfigId] })
      showSuccessToast("Composition saved.")
    },
    onError: (error: unknown) => {
      const detail = extractApiErrorDetail(error)
      const message = error instanceof Error ? error.message : "Failed to save composition."
      showErrorToast(detail ?? message)
    },
  })

  const createDemoMutation = useMutation({
    mutationFn: async () => {
      const slug = newSlug.trim()
      const title = newTitle.trim()
      if (!slug || !title) {
        throw new Error("Slug and title are required.")
      }
      return DemosService.createNewDemoConfig({
        requestBody: {
          slug,
          title,
          scope: "personal",
          is_active: true,
          default_auto_respond: true,
          metadata_json: {
            created_by: "demo-builder",
          },
        },
      })
    },
    onSuccess: (created) => {
      showSuccessToast("Demo created.")
      setNewSlug("")
      setNewTitle("")
      queryClient.invalidateQueries({ queryKey: ["demo-builder", "configs"] })
      setSelectedDemoConfigId(created.id)
    },
    onError: (error: unknown) => {
      const detail = extractApiErrorDetail(error)
      const message = error instanceof Error ? error.message : "Failed to create demo."
      showErrorToast(detail ?? message)
    },
  })

  // --------------------------------------------------------------------------
  // Composition Update Helpers
  // --------------------------------------------------------------------------
  const markDirty = () => setIsDirty(true)

  function updateComposition(
    updater: (current: EditableComposition) => EditableComposition,
  ) {
    setComposition((current) => {
      const updated = updater(current)
      return updated
    })
    markDirty()
  }

  function updatePanel(index: number, patch: Record<string, unknown>) {
    updateComposition((current) => {
      const panels = [...(current.panels ?? [])]
      const existing = (panels[index] ?? {}) as EditablePanel
      panels[index] = { ...existing, ...patch } as EditablePanel
      return { ...current, panels }
    })
  }

  function updateBlock(index: number, patch: Record<string, unknown>) {
    updateComposition((current) => {
      const blocks = [...(current.blocks ?? [])]
      const existing = (blocks[index] ?? {}) as EditableBlock
      blocks[index] = { ...existing, ...patch } as EditableBlock
      return { ...current, blocks }
    })
  }

  function removePanel(index: number) {
    updateComposition((current) => {
      const panels = [...(current.panels ?? [])]
      panels.splice(index, 1)
      return { ...current, panels }
    })
  }

  function removeBlock(index: number) {
    updateComposition((current) => {
      const blocks = [...(current.blocks ?? [])]
      blocks.splice(index, 1)
      return { ...current, blocks }
    })
  }

  function commitJsonField(
    fieldKey: string,
    raw: string,
    onSuccess: (value: Record<string, unknown> | null) => void,
  ) {
    try {
      const parsed = parseNullableObjectJsonOrThrow(raw)
      setFieldErrors((current) => {
        const { [fieldKey]: _removed, ...remaining } = current
        return remaining
      })
      onSuccess(parsed)
    } catch (error) {
      setFieldErrors((current) => ({
        ...current,
        [fieldKey]: error instanceof Error ? error.message : "Invalid JSON object.",
      }))
    }
  }

  function applyRawJsonDraft() {
    try {
      const parsed = JSON.parse(rawJsonDraft) as EditableComposition
      const normalized = normalizeComposition(parsed)
      setComposition(normalized)
      setFieldErrors((current) => {
        const { raw_json: _removed, ...remaining } = current
        return remaining
      })
      markDirty()
      showSuccessToast("Applied raw composition JSON.")
    } catch (error) {
      setFieldErrors((current) => ({
        ...current,
        raw_json: error instanceof Error ? error.message : "Invalid JSON.",
      }))
    }
  }

  return (
    <div className="flex flex-col gap-4 pb-6">
      <div>
        <h1 className="text-2xl font-semibold">Demo Builder (MVP)</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Build and save demo compositions using generated OpenAPI contract types.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Select Or Create Demo</CardTitle>
          <CardDescription>
            Load an existing demo config or create a new one before editing composition.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <label className="text-sm font-medium">Demo Config</label>
            <Select
              value={selectedDemoConfigId || "_none"}
              onValueChange={(value) => setSelectedDemoConfigId(value === "_none" ? "" : value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select demo config..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="_none">None</SelectItem>
                {isLoadingDemos && (
                  <SelectItem value="_loading" disabled>Loading...</SelectItem>
                )}
                {demoConfigs.map((demo) => (
                  <SelectItem key={demo.id} value={demo.id}>
                    {demo.slug} · {demo.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {selectedDemo?.slug && (
              <a
                href={`/demo/${selectedDemo.slug}`}
                target="_blank"
                rel="noreferrer"
                className="text-xs text-primary underline"
              >
                Open Preview: /demo/{selectedDemo.slug}
              </a>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Create New Demo</label>
            <div className="grid gap-2">
              <Input
                placeholder="slug (e.g. qa-builder-demo)"
                value={newSlug}
                onChange={(event) => setNewSlug(event.target.value)}
              />
              <Input
                placeholder="title"
                value={newTitle}
                onChange={(event) => setNewTitle(event.target.value)}
              />
              <Button
                type="button"
                onClick={() => createDemoMutation.mutate()}
                disabled={createDemoMutation.isPending}
              >
                {createDemoMutation.isPending
                  ? <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  : <Plus className="h-4 w-4 mr-2" />}
                Create Demo
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Composition</CardTitle>
          <CardDescription>
            Edit top-level composition behavior before tuning panels and blocks.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!selectedDemoConfigId ? (
            <div className="text-sm text-muted-foreground">
              Select or create a demo config to begin editing.
            </div>
          ) : isLoadingComposition ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading composition...
            </div>
          ) : (
            <>
              <div className="grid gap-3 md:grid-cols-4">
                <Select
                  value={composition.layout_mode ?? "panels"}
                  onValueChange={(value: DemoLayoutMode) => updateComposition((current) => ({
                    ...current,
                    layout_mode: value,
                  }))}
                >
                  <SelectTrigger><SelectValue placeholder="layout_mode" /></SelectTrigger>
                  <SelectContent>
                    {LAYOUT_MODES.map((mode) => (
                      <SelectItem key={mode} value={mode}>{mode}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Select
                  value={composition.runtime_policy ?? "auto"}
                  onValueChange={(value: DemoRuntimePolicy) => updateComposition((current) => ({
                    ...current,
                    runtime_policy: value,
                  }))}
                >
                  <SelectTrigger><SelectValue placeholder="runtime_policy" /></SelectTrigger>
                  <SelectContent>
                    {RUNTIME_POLICIES.map((policy) => (
                      <SelectItem key={policy} value={policy}>{policy}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Select
                  value={composition.persona_policy ?? "first_available"}
                  onValueChange={(value: DemoPersonaPolicy) => updateComposition((current) => ({
                    ...current,
                    persona_policy: value,
                  }))}
                >
                  <SelectTrigger><SelectValue placeholder="persona_policy" /></SelectTrigger>
                  <SelectContent>
                    {PERSONA_POLICIES.map((policy) => (
                      <SelectItem key={policy} value={policy}>{policy}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Select
                  value={composition.chat_mode ?? "participant"}
                  onValueChange={(value: DemoChatMode) => updateComposition((current) => ({
                    ...current,
                    chat_mode: value,
                  }))}
                >
                  <SelectTrigger><SelectValue placeholder="chat_mode" /></SelectTrigger>
                  <SelectContent>
                    {CHAT_MODES.map((mode) => (
                      <SelectItem key={mode} value={mode}>{mode}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">metadata_json</label>
                  <Textarea
                    rows={6}
                    defaultValue={toPrettyJson(composition.metadata_json ?? {})}
                    onBlur={(event) => commitJsonField("metadata_json", event.target.value, (value) => {
                      updateComposition((current) => ({ ...current, metadata_json: value ?? {} }))
                    })}
                  />
                  {fieldErrors.metadata_json && (
                    <p className="text-xs text-destructive">{fieldErrors.metadata_json}</p>
                  )}
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">presentation_json</label>
                  <Textarea
                    rows={6}
                    defaultValue={toPrettyJson(composition.presentation_json ?? {})}
                    onBlur={(event) => commitJsonField("presentation_json", event.target.value, (value) => {
                      updateComposition((current) => ({ ...current, presentation_json: value ?? {} }))
                    })}
                  />
                  {fieldErrors.presentation_json && (
                    <p className="text-xs text-destructive">{fieldErrors.presentation_json}</p>
                  )}
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Panels</CardTitle>
          <CardDescription>
            Add and tune panel specs. Each panel row mirrors shared composition primitives.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-2">
            {ACTIVE_PANEL_KINDS.map((kind) => (
              <Button
                key={kind}
                type="button"
                variant="outline"
                size="sm"
                onClick={() => updateComposition((current) => ({
                  ...current,
                  panels: [...(current.panels ?? []), createPanelTemplate(kind)],
                }))}
              >
                <Plus className="h-3.5 w-3.5 mr-1" />
                {kind}
              </Button>
            ))}
          </div>

          {(composition.panels ?? []).length === 0 ? (
            <div className="text-sm text-muted-foreground">No panels configured.</div>
          ) : (
            (composition.panels ?? []).map((panel, index) => (
              <Card key={`${String((panel as { id?: unknown }).id ?? index)}-${index}`}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between gap-2">
                    <CardTitle className="text-sm">Panel {index + 1}</CardTitle>
                    <Button variant="ghost" size="sm" onClick={() => removePanel(index)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-4">
                  <Input
                    value={String((panel as { id?: unknown }).id ?? "")}
                    onChange={(event) => updatePanel(index, { id: event.target.value })}
                    placeholder="id"
                  />
                  <Select
                    value={String((panel as { kind?: unknown }).kind ?? "content")}
                    onValueChange={(value) => updatePanel(index, { kind: value as EditablePanel["kind"] })}
                  >
                    <SelectTrigger><SelectValue placeholder="kind" /></SelectTrigger>
                    <SelectContent>
                      {ACTIVE_PANEL_KINDS.map((kind) => (
                        <SelectItem key={kind} value={kind}>{kind}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Select
                    value={String((panel as { prominence?: unknown }).prominence ?? "primary")}
                    onValueChange={(value: PanelProminence) => updatePanel(index, { prominence: value })}
                  >
                    <SelectTrigger><SelectValue placeholder="prominence" /></SelectTrigger>
                    <SelectContent>
                      {PANEL_PROMINENCE.map((prominence) => (
                        <SelectItem key={prominence} value={prominence}>{prominence}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Input
                    value={String((panel as { title?: unknown }).title ?? "")}
                    onChange={(event) => updatePanel(index, { title: event.target.value })}
                    placeholder="title"
                  />
                  <Input
                    value={String((panel as { order?: unknown }).order ?? "")}
                    onChange={(event) => updatePanel(index, { order: parseInteger(event.target.value) })}
                    placeholder="order"
                  />
                  <Input
                    value={String((panel as { default_size?: unknown }).default_size ?? "")}
                    onChange={(event) => updatePanel(index, { default_size: parseInteger(event.target.value) })}
                    placeholder="default_size"
                  />
                  <Input
                    value={String((panel as { min_size?: unknown }).min_size ?? "")}
                    onChange={(event) => updatePanel(index, { min_size: parseInteger(event.target.value) })}
                    placeholder="min_size"
                  />
                  <Input
                    value={String((panel as { max_size?: unknown }).max_size ?? "")}
                    onChange={(event) => updatePanel(index, { max_size: parseInteger(event.target.value) })}
                    placeholder="max_size"
                  />
                  <Select
                    value={String((panel as { viewport_mode?: unknown }).viewport_mode ?? "panel")}
                    onValueChange={(value: "panel" | "page") => updatePanel(index, { viewport_mode: value })}
                  >
                    <SelectTrigger><SelectValue placeholder="viewport_mode" /></SelectTrigger>
                    <SelectContent>
                      {VIEWPORT_MODES.map((mode) => (
                        <SelectItem key={mode} value={mode}>{mode}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  <div className="md:col-span-3 space-y-1">
                    <label className="text-xs text-muted-foreground">options (JSON object)</label>
                    <Textarea
                      rows={4}
                      defaultValue={toPrettyJson((panel as { options?: unknown }).options ?? {})}
                      onBlur={(event) => commitJsonField(`panel:${index}:options`, event.target.value, (value) => {
                        updatePanel(index, { options: (value ?? {}) as EditablePanel["options"] })
                      })}
                    />
                    {fieldErrors[`panel:${index}:options`] && (
                      <p className="text-xs text-destructive">{fieldErrors[`panel:${index}:options`]}</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Blocks</CardTitle>
          <CardDescription>
            Add and tune block specs, including region and visibility semantics.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-2">
            {ACTIVE_BLOCK_TYPES.map((type) => (
              <Button
                key={type}
                type="button"
                variant="outline"
                size="sm"
                onClick={() => updateComposition((current) => ({
                  ...current,
                  blocks: [...(current.blocks ?? []), createBlockTemplate(type)],
                }))}
              >
                <Plus className="h-3.5 w-3.5 mr-1" />
                {type}
              </Button>
            ))}
          </div>

          {(composition.blocks ?? []).length === 0 ? (
            <div className="text-sm text-muted-foreground">No blocks configured.</div>
          ) : (
            (composition.blocks ?? []).map((block, index) => (
              <Card key={`${String((block as { id?: unknown }).id ?? index)}-${index}`}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between gap-2">
                    <CardTitle className="text-sm">Block {index + 1}</CardTitle>
                    <Button variant="ghost" size="sm" onClick={() => removeBlock(index)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-4">
                  <Input
                    value={String((block as { id?: unknown }).id ?? "")}
                    onChange={(event) => updateBlock(index, { id: event.target.value })}
                    placeholder="id"
                  />
                  <Select
                    value={String((block as { type?: unknown }).type ?? "content")}
                    onValueChange={(value) => updateBlock(index, { type: value as EditableBlock["type"] })}
                  >
                    <SelectTrigger><SelectValue placeholder="type" /></SelectTrigger>
                    <SelectContent>
                      {ACTIVE_BLOCK_TYPES.map((type) => (
                        <SelectItem key={type} value={type}>{type}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Select
                    value={String((block as { region?: unknown }).region ?? "top")}
                    onValueChange={(value: BlockRegion) => updateBlock(index, { region: value })}
                  >
                    <SelectTrigger><SelectValue placeholder="region" /></SelectTrigger>
                    <SelectContent>
                      {BLOCK_REGIONS.map((region) => (
                        <SelectItem key={region} value={region}>{region}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Select
                    value={String((block as { visibility?: unknown }).visibility ?? "visible")}
                    onValueChange={(value: BlockVisibility) => updateBlock(index, { visibility: value })}
                  >
                    <SelectTrigger><SelectValue placeholder="visibility" /></SelectTrigger>
                    <SelectContent>
                      {BLOCK_VISIBILITY.map((visibility) => (
                        <SelectItem key={visibility} value={visibility}>{visibility}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Input
                    value={String((block as { title?: unknown }).title ?? "")}
                    onChange={(event) => updateBlock(index, { title: event.target.value })}
                    placeholder="title"
                  />
                  <Input
                    value={String((block as { order?: unknown }).order ?? "")}
                    onChange={(event) => updateBlock(index, { order: parseInteger(event.target.value) })}
                    placeholder="order"
                  />

                  <div className="md:col-span-4 grid gap-3 md:grid-cols-3">
                    <div className="space-y-1">
                      <label className="text-xs text-muted-foreground">config_json</label>
                      <Textarea
                        rows={4}
                        defaultValue={toPrettyJson((block as { config_json?: unknown }).config_json ?? {})}
                        onBlur={(event) => commitJsonField(`block:${index}:config`, event.target.value, (value) => {
                          updateBlock(index, { config_json: value ?? {} })
                        })}
                      />
                      {fieldErrors[`block:${index}:config`] && (
                        <p className="text-xs text-destructive">{fieldErrors[`block:${index}:config`]}</p>
                      )}
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs text-muted-foreground">content_json</label>
                      <Textarea
                        rows={4}
                        defaultValue={toPrettyJson((block as { content_json?: unknown }).content_json ?? {})}
                        onBlur={(event) => commitJsonField(`block:${index}:content`, event.target.value, (value) => {
                          updateBlock(index, { content_json: value ?? null })
                        })}
                      />
                      {fieldErrors[`block:${index}:content`] && (
                        <p className="text-xs text-destructive">{fieldErrors[`block:${index}:content`]}</p>
                      )}
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs text-muted-foreground">presentation_json</label>
                      <Textarea
                        rows={4}
                        defaultValue={toPrettyJson((block as { presentation_json?: unknown }).presentation_json ?? {})}
                        onBlur={(event) => commitJsonField(`block:${index}:presentation`, event.target.value, (value) => {
                          updateBlock(index, { presentation_json: value ?? {} })
                        })}
                      />
                      {fieldErrors[`block:${index}:presentation`] && (
                        <p className="text-xs text-destructive">{fieldErrors[`block:${index}:presentation`]}</p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Raw Composition JSON</CardTitle>
          <CardDescription>
            Power-user editor for bulk edits and copy/paste between environments.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <Textarea
            rows={16}
            value={rawJsonDraft}
            onChange={(event) => setRawJsonDraft(event.target.value)}
          />
          {fieldErrors.raw_json && (
            <p className="text-xs text-destructive">{fieldErrors.raw_json}</p>
          )}
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" onClick={() => setRawJsonDraft(toPrettyJson(composition))}>
              <RotateCcw className="h-4 w-4 mr-2" />
              Reset Raw JSON From Current
            </Button>
            <Button type="button" variant="outline" onClick={applyRawJsonDraft}>
              Apply Raw JSON To Editor
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="sticky bottom-4 flex items-center justify-between rounded-md border bg-background/95 backdrop-blur px-4 py-3">
        <div className="text-sm text-muted-foreground">
          {selectedDemo
            ? `${selectedDemo.slug} (${selectedDemo.id.slice(0, 8)}...)`
            : "No demo selected"}
          {isDirty ? " · unsaved changes" : " · saved"}
        </div>
        <Button
          type="button"
          onClick={() => saveCompositionMutation.mutate()}
          disabled={!selectedDemoConfigId || saveCompositionMutation.isPending}
        >
          {saveCompositionMutation.isPending
            ? <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            : <Save className="h-4 w-4 mr-2" />}
          Save Composition
        </Button>
      </div>
    </div>
  )
}
