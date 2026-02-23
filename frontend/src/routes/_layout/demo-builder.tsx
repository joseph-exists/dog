import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Loader2, Plus } from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import { DemosService } from "@/client"
import type {
  DemoChatMode,
  DemoConfigPublic,
  PersonaPublic,
  DemoPersonaPolicy,
  StoryPublic,
} from "@/client/types.gen"
import { PersonasService, StoriesService } from "@/client"
import {
  BUILDER_COMPOSITION_TEMPLATES,
  createCompositionTemplate,
  createBlockTemplate,
  createEmptyComposition,
  createPanelTemplate,
  getTemplateSetupState,
  getBuilderCompositionTemplateSchema,
  normalizeComposition,
  resolveTemplateChecklistStatus,
  withTemplateSetupState,
  type BuilderValidationIssue,
  type BuilderTemplateConfirmations,
  type BuilderTemplateId,
  validateCompositionSemantics,
  type EditableBlock,
  type EditableComposition,
  type EditablePanel,
} from "@/components/Demo/builder/demoBuilderSchema"
import {
  getBlockCapabilityByType,
  getPanelCapabilityByKind,
  normalizeBlockCapabilityPatch,
  normalizePanelCapabilityPatch,
  runBlockCapabilitySemanticValidators,
  runPanelCapabilitySemanticValidators,
} from "@/components/Demo/builder/demoBuilderCapabilityRegistry"
import { DemoBlockEditor } from "@/components/Demo/builder/DemoBlockEditor"
import { DemoPanelEditor } from "@/components/Demo/builder/DemoPanelEditor"
import { DemoRawJsonEditor } from "@/components/Demo/builder/DemoRawJsonEditor"
import { DemoSaveBar } from "@/components/Demo/builder/DemoSaveBar"
import { DemoTemplateSetupChecklist } from "@/components/Demo/builder/DemoTemplateSetupChecklist"
import { DemoTopLevelEditor } from "@/components/Demo/builder/DemoTopLevelEditor"
import { DemoValidationPanel } from "@/components/Demo/builder/DemoValidationPanel"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { useAvailableThemes } from "@/hooks/useThemeRegistry"

export const Route = createFileRoute("/_layout/demo-builder")({
  component: DemoBuilderPage,
  head: () => ({
    meta: [{ title: "Demo Builder" }],
  }),
})

function toPrettyJson(value: unknown): string {
  return JSON.stringify(value ?? {}, null, 2)
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

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function getCompositionStoryId(composition: EditableComposition): string | null {
  if (!isObjectRecord(composition.metadata_json)) return null
  const raw = composition.metadata_json.story_id
  return typeof raw === "string" && raw.trim().length > 0 ? raw : null
}

function collectCapabilityValidationIssues(composition: EditableComposition): BuilderValidationIssue[] {
  const issues: BuilderValidationIssue[] = []
  const panels = composition.panels ?? []
  for (const [index, panel] of panels.entries()) {
    const capability = getPanelCapabilityByKind(typeof panel.kind === "string" ? panel.kind : null)
    if (!capability) continue
    for (const validationIssue of runPanelCapabilitySemanticValidators(capability, composition)) {
      issues.push({
        code: "capability_validation",
        severity: validationIssue.severity,
        message: `[${validationIssue.code}] ${validationIssue.message}`,
        path: `panels[${index}]`,
      })
    }
  }

  const blocks = composition.blocks ?? []
  for (const [index, block] of blocks.entries()) {
    const capability = getBlockCapabilityByType(typeof block.type === "string" ? block.type : null)
    if (!capability) continue
    for (const validationIssue of runBlockCapabilitySemanticValidators(capability, composition)) {
      issues.push({
        code: "capability_validation",
        severity: validationIssue.severity,
        message: `[${validationIssue.code}] ${validationIssue.message}`,
        path: `blocks[${index}]`,
      })
    }
  }
  return issues
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
  const [selectedTemplateId, setSelectedTemplateId] = useState<BuilderTemplateId>(
    BUILDER_COMPOSITION_TEMPLATES[0].id,
  )

  // Local editable composition state + raw JSON draft for power-edit mode.
  const [composition, setComposition] = useState<EditableComposition>(createEmptyComposition())
  const [rawJsonDraft, setRawJsonDraft] = useState<string>(toPrettyJson(createEmptyComposition()))
  const [isDirty, setIsDirty] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [isStoryPickerOpen, setIsStoryPickerOpen] = useState(false)
  const [isPersonaPickerOpen, setIsPersonaPickerOpen] = useState(false)
  const [storyPickerSearch, setStoryPickerSearch] = useState("")
  const [personaPickerSearch, setPersonaPickerSearch] = useState("")
  const [isThemeQuickAddEnabled, setIsThemeQuickAddEnabled] = useState(false)

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
  const { data: storiesPayload, isLoading: isLoadingStories } = useQuery({
    queryKey: ["demo-builder", "stories"],
    queryFn: () => StoriesService.readStories({ skip: 0, limit: 200 }),
  })
  const { data: personasPayload, isLoading: isLoadingPersonas } = useQuery({
    queryKey: ["demo-builder", "personas"],
    queryFn: () => PersonasService.readPersonas({ skip: 0, limit: 200 }),
  })
  const stories: StoryPublic[] = storiesPayload?.data ?? []
  const personas: PersonaPublic[] = personasPayload?.data ?? []
  const { themes: availablePageThemes, isLoading: isLoadingPageThemes } = useAvailableThemes("page")
  const { themes: availableCardThemes, isLoading: isLoadingCardThemes } = useAvailableThemes("card")
  const filteredStories = useMemo(() => {
    const needle = storyPickerSearch.trim().toLowerCase()
    if (!needle) return stories
    return stories.filter((story) => story.title.toLowerCase().includes(needle))
  }, [stories, storyPickerSearch])
  const filteredPersonas = useMemo(() => {
    const needle = personaPickerSearch.trim().toLowerCase()
    if (!needle) return personas
    return personas.filter((persona) => persona.name.toLowerCase().includes(needle))
  }, [personas, personaPickerSearch])

  const selectedDemo = useMemo(
    () => demoConfigs.find((demo) => demo.id === selectedDemoConfigId) ?? null,
    [demoConfigs, selectedDemoConfigId],
  )
  const semanticIssues = useMemo(
    () => [
      ...validateCompositionSemantics(composition),
      ...collectCapabilityValidationIssues(composition),
    ],
    [composition],
  )
  const blockingIssues = semanticIssues.filter((issue) => issue.severity === "error")
  const templateSetupState = useMemo(
    () => getTemplateSetupState(composition),
    [composition],
  )
  const activeTemplateSetupId = templateSetupState?.templateId ?? null
  const isTemplateSetupDismissed = templateSetupState?.dismissed ?? false
  const templateConfirmations: BuilderTemplateConfirmations = templateSetupState?.confirmations ?? {}
  const activeTemplateChecklist = useMemo(
    () => activeTemplateSetupId
      ? resolveTemplateChecklistStatus({
        templateId: activeTemplateSetupId,
        composition,
        semanticIssues,
        confirmations: templateConfirmations,
      })
      : null,
    [activeTemplateSetupId, composition, semanticIssues, templateConfirmations],
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
      if (blockingIssues.length > 0) {
        throw new Error("Resolve semantic validation errors before saving.")
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
      const patchKind = typeof patch.kind === "string" ? patch.kind : null
      const effectiveKind = patchKind ?? (typeof existing.kind === "string" ? existing.kind : null)
      const capability = getPanelCapabilityByKind(effectiveKind)
      const normalizedPatch = capability
        ? normalizePanelCapabilityPatch(capability, patch, current)
        : patch
      panels[index] = { ...existing, ...normalizedPatch } as EditablePanel
      return { ...current, panels }
    })
  }

  function updateBlock(index: number, patch: Record<string, unknown>) {
    updateComposition((current) => {
      const blocks = [...(current.blocks ?? [])]
      const existing = (blocks[index] ?? {}) as EditableBlock
      const patchType = typeof patch.type === "string" ? patch.type : null
      const effectiveType = patchType ?? (typeof existing.type === "string" ? existing.type : null)
      const capability = getBlockCapabilityByType(effectiveType)
      const normalizedPatch = capability
        ? normalizeBlockCapabilityPatch(capability, patch, current)
        : patch
      blocks[index] = { ...existing, ...normalizedPatch } as EditableBlock
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

  function applyTemplateToEditor() {
    const template = withTemplateSetupState(
      createCompositionTemplate(selectedTemplateId),
      {
        templateId: selectedTemplateId,
        dismissed: false,
        confirmations: {},
      },
    )
    setComposition(template)
    setRawJsonDraft(toPrettyJson(template))
    setFieldErrors({})
    markDirty()
    showSuccessToast(`Applied ${selectedTemplateId} template.`)
  }

  function updateTemplateSetupState(
    updater: (
      current: {
        templateId: BuilderTemplateId
        dismissed: boolean
        confirmations: BuilderTemplateConfirmations
      },
    ) => {
      templateId: BuilderTemplateId
      dismissed: boolean
      confirmations: BuilderTemplateConfirmations
    },
  ) {
    if (!activeTemplateSetupId) return
    updateComposition((current) => {
      const setupState = getTemplateSetupState(current)
      if (!setupState) return current
      return withTemplateSetupState(current, updater(setupState))
    })
  }

  function setStoryId(value: string | null) {
    updateComposition((current) => {
      const metadata = isObjectRecord(current.metadata_json)
        ? { ...current.metadata_json }
        : {}
      if (value) {
        metadata.story_id = value
      } else {
        delete metadata.story_id
      }
      return {
        ...current,
        metadata_json: metadata,
      }
    })
  }

  function withPresentationThemeRefs(
    input: EditableComposition,
    nextPageThemeId: string | null | undefined,
    nextCardsThemeId: string | null | undefined,
  ): EditableComposition {
    const presentationJson = isObjectRecord(input.presentation_json)
      ? { ...input.presentation_json }
      : {}

    const effectivePageThemeId = typeof nextPageThemeId === "undefined"
      ? (typeof input.page_theme_id === "string" ? input.page_theme_id : null)
      : nextPageThemeId
    const effectiveCardsThemeId = typeof nextCardsThemeId === "undefined"
      ? (typeof input.cards_theme_id === "string" ? input.cards_theme_id : null)
      : nextCardsThemeId

    if (!effectivePageThemeId && !effectiveCardsThemeId) {
      delete presentationJson.theme_refs
      return { ...input, presentation_json: presentationJson }
    }

    presentationJson.theme_refs = {
      page_theme_id: effectivePageThemeId,
      cards_theme_id: effectiveCardsThemeId,
    }
    return { ...input, presentation_json: presentationJson }
  }

  function applyThemeQuickSelection(slot: "page" | "cards", themeId: string | null) {
    updateComposition((current) => {
      const next = {
        ...current,
        page_theme_id: slot === "page" ? themeId : current.page_theme_id,
        cards_theme_id: slot === "cards" ? themeId : current.cards_theme_id,
      }

      if (!isThemeQuickAddEnabled) return next
      return withPresentationThemeRefs(
        next,
        slot === "page" ? themeId : undefined,
        slot === "cards" ? themeId : undefined,
      )
    })
  }

  function applyPersonaFromPicker(personaId: string) {
    updateComposition((current) => ({
      ...current,
      persona_policy: "fixed_user_persona",
      fixed_user_persona_id: personaId,
    }))
    updateTemplateSetupState((current) => ({
      ...current,
      confirmations: {
        ...current.confirmations,
        persona_policy: true,
      },
    }))
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
            <div className="pt-3 border-t mt-3 space-y-2">
              <label className="text-sm font-medium">Composition Template</label>
              <Select
                value={selectedTemplateId}
                onValueChange={(value) => setSelectedTemplateId(value as BuilderTemplateId)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select template..." />
                </SelectTrigger>
                <SelectContent>
                  {BUILDER_COMPOSITION_TEMPLATES.map((template) => (
                    <SelectItem key={template.id} value={template.id}>
                      {template.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                {BUILDER_COMPOSITION_TEMPLATES.find((template) => template.id === selectedTemplateId)?.description}
              </p>
              <Button type="button" variant="secondary" onClick={applyTemplateToEditor}>
                Apply Template To Editor
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {activeTemplateSetupId && activeTemplateChecklist && (
        <DemoTemplateSetupChecklist
          templateId={activeTemplateSetupId}
          templateLabel={getBuilderCompositionTemplateSchema(activeTemplateSetupId).label}
          checklistStatus={activeTemplateChecklist}
          isDismissed={isTemplateSetupDismissed}
          composition={composition}
          confirmations={templateConfirmations}
          onDismiss={() => updateTemplateSetupState((current) => ({ ...current, dismissed: true }))}
          onResume={() => updateTemplateSetupState((current) => ({ ...current, dismissed: false }))}
          onStoryIdChange={setStoryId}
          onRuntimePolicyChange={(value) => updateComposition((current) => ({
            ...current,
            runtime_policy: value,
          }))}
          onPersonaPolicyChange={(value) => updateComposition((current) => ({
            ...current,
            persona_policy: value,
          }))}
          onChatModeChange={(value) => updateComposition((current) => ({
            ...current,
            chat_mode: value,
          }))}
          onFixedUserPersonaIdChange={(value) => updateComposition((current) => ({
            ...current,
            fixed_user_persona_id: value,
          }))}
          onAssumptionConfirmed={(assumption, checked) => {
            updateTemplateSetupState((current) => ({
              ...current,
              confirmations: {
                ...current.confirmations,
                [assumption]: checked,
              },
            }))
          }}
          onOpenStoryPicker={() => setIsStoryPickerOpen(true)}
          onOpenPersonaPicker={() => setIsPersonaPickerOpen(true)}
        />
      )}

      <Dialog open={isStoryPickerOpen} onOpenChange={setIsStoryPickerOpen}>
        <DialogContent className="sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>Select Story</DialogTitle>
            <DialogDescription>
              Pick a story to populate `metadata_json.story_id`.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <Input
              placeholder="Search stories..."
              value={storyPickerSearch}
              onChange={(event) => setStoryPickerSearch(event.target.value)}
            />
            <div className="max-h-72 overflow-auto space-y-2">
              {isLoadingStories && (
                <p className="text-sm text-muted-foreground">Loading stories...</p>
              )}
              {!isLoadingStories && filteredStories.length === 0 && (
                <p className="text-sm text-muted-foreground">No stories found.</p>
              )}
              {filteredStories.map((story) => (
                <button
                  key={story.id}
                  type="button"
                  className="w-full rounded border px-3 py-2 text-left hover:bg-muted"
                  onClick={() => {
                    setStoryId(story.id)
                    setIsStoryPickerOpen(false)
                  }}
                >
                  <div className="text-sm font-medium">{story.title}</div>
                  <div className="text-xs text-muted-foreground font-mono">{story.id}</div>
                </button>
              ))}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={isPersonaPickerOpen} onOpenChange={setIsPersonaPickerOpen}>
        <DialogContent className="sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>Select Persona</DialogTitle>
            <DialogDescription>
              Pick a persona to set `persona_policy=fixed_user_persona` and populate `fixed_user_persona_id`.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <Input
              placeholder="Search personas..."
              value={personaPickerSearch}
              onChange={(event) => setPersonaPickerSearch(event.target.value)}
            />
            <div className="max-h-72 overflow-auto space-y-2">
              {isLoadingPersonas && (
                <p className="text-sm text-muted-foreground">Loading personas...</p>
              )}
              {!isLoadingPersonas && filteredPersonas.length === 0 && (
                <p className="text-sm text-muted-foreground">No personas found.</p>
              )}
              {filteredPersonas.map((persona) => (
                <button
                  key={persona.id}
                  type="button"
                  className="w-full rounded border px-3 py-2 text-left hover:bg-muted"
                  onClick={() => {
                    applyPersonaFromPicker(persona.id)
                    setIsPersonaPickerOpen(false)
                  }}
                >
                  <div className="text-sm font-medium">{persona.name}</div>
                  <div className="text-xs text-muted-foreground font-mono">{persona.id}</div>
                </button>
              ))}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <DemoTopLevelEditor
        selectedDemoConfigId={selectedDemoConfigId}
        isLoadingComposition={isLoadingComposition}
        composition={composition}
        fieldErrors={fieldErrors}
        onLayoutModeChange={(value) => updateComposition((current) => ({
          ...current,
          layout_mode: value,
        }))}
        onRuntimePolicyChange={(value) => updateComposition((current) => ({
          ...current,
          runtime_policy: value,
        }))}
        onPersonaPolicyChange={(value: DemoPersonaPolicy) => updateComposition((current) => ({
          ...current,
          persona_policy: value,
        }))}
        onChatModeChange={(value: DemoChatMode) => updateComposition((current) => ({
          ...current,
          chat_mode: value,
        }))}
        onFixedUserPersonaIdChange={(value) => updateComposition((current) => ({
          ...current,
          fixed_user_persona_id: value,
        }))}
        onPageThemeIdChange={(value) => updateComposition((current) => ({
          ...current,
          page_theme_id: value,
        }))}
        onCardsThemeIdChange={(value) => updateComposition((current) => ({
          ...current,
          cards_theme_id: value,
        }))}
        onMetadataJsonBlur={(raw) => commitJsonField("metadata_json", raw, (value) => {
          updateComposition((current) => ({ ...current, metadata_json: value ?? {} }))
        })}
        onPresentationJsonBlur={(raw) => commitJsonField("presentation_json", raw, (value) => {
          updateComposition((current) => ({ ...current, presentation_json: value ?? {} }))
        })}
        storyId={getCompositionStoryId(composition)}
        onStoryIdChange={setStoryId}
        onOpenStoryPicker={() => setIsStoryPickerOpen(true)}
        isThemeQuickAddEnabled={isThemeQuickAddEnabled}
        onThemeQuickAddEnabledChange={setIsThemeQuickAddEnabled}
        availablePageThemes={availablePageThemes}
        availableCardThemes={availableCardThemes}
        isLoadingThemeOptions={isLoadingPageThemes || isLoadingCardThemes}
        onPageThemeQuickSelect={(value) => applyThemeQuickSelection("page", value)}
        onCardsThemeQuickSelect={(value) => applyThemeQuickSelection("cards", value)}
      />

      <DemoValidationPanel issues={semanticIssues} />

      <DemoPanelEditor
        composition={composition}
        panels={composition.panels ?? []}
        fieldErrors={fieldErrors}
        onAddPanel={(kind) => updateComposition((current) => ({
          ...current,
          panels: [...(current.panels ?? []), createPanelTemplate(kind)],
        }))}
        onRemovePanel={removePanel}
        onUpdatePanel={updatePanel}
        onCommitPanelJsonField={(index, fieldKey, raw) => commitJsonField(`panel:${index}:${fieldKey}`, raw, (value) => {
          updatePanel(index, { [fieldKey]: value ?? {} })
        })}
      />

      <DemoBlockEditor
        composition={composition}
        blocks={composition.blocks ?? []}
        fieldErrors={fieldErrors}
        onAddBlock={(type) => updateComposition((current) => ({
          ...current,
          blocks: [...(current.blocks ?? []), createBlockTemplate(type)],
        }))}
        onRemoveBlock={removeBlock}
        onUpdateBlock={updateBlock}
        onCommitBlockJsonField={(index, fieldKey, raw) => commitJsonField(`block:${index}:${fieldKey}`, raw, (value) => {
          if (fieldKey === "content_json") {
            updateBlock(index, { content_json: value ?? null })
            return
          }
          updateBlock(index, { [fieldKey]: value ?? {} })
        })}
      />

      <DemoRawJsonEditor
        rawJsonDraft={rawJsonDraft}
        rawJsonError={fieldErrors.raw_json}
        onRawJsonDraftChange={setRawJsonDraft}
        onResetFromCurrent={() => setRawJsonDraft(toPrettyJson(composition))}
        onApplyRawJson={applyRawJsonDraft}
      />

      <DemoSaveBar
        selectedDemoLabel={selectedDemo
          ? `${selectedDemo.slug} (${selectedDemo.id.slice(0, 8)}...)`
          : "No demo selected"}
        isDirty={isDirty}
        canSave={Boolean(selectedDemoConfigId) && blockingIssues.length === 0}
        isSaving={saveCompositionMutation.isPending}
        onSave={() => saveCompositionMutation.mutate()}
      />
    </div>
  )
}
