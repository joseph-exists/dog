import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import {
  ChevronDown,
  ChevronRight,
  Loader2,
  Plus,
  RefreshCcw,
} from "lucide-react"
import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import {
  AgentsService,
  DemosService,
  PersonasService,
  StoriesService,
} from "@/client"
import type {
  DemoChatMode,
  DemoConfigPublic,
  DemoPersonaPolicy,
  PersonaPublic,
  StoryPublic,
} from "@/client/types.gen"
import { DemoBlockEditor } from "@/components/Demo/builder/DemoBlockEditor"
import { DemoBuilderPreview } from "@/components/Demo/builder/DemoBuilderPreview"
import { DemoCompositionTree } from "@/components/Demo/builder/DemoCompositionTree"
import { DemoPanelEditor } from "@/components/Demo/builder/DemoPanelEditor"
import { DemoRawJsonEditor } from "@/components/Demo/builder/DemoRawJsonEditor"
import { DemoSaveBar } from "@/components/Demo/builder/DemoSaveBar"
import { DemoTemplateSetupChecklist } from "@/components/Demo/builder/DemoTemplateSetupChecklist"
import { DemoTopLevelEditor } from "@/components/Demo/builder/DemoTopLevelEditor"
import { DemoValidationPanel } from "@/components/Demo/builder/DemoValidationPanel"
import {
  getBlockCapabilityAvailability,
  getBlockCapabilityByType,
  getPanelCapabilityAvailability,
  getPanelCapabilityByKind,
  normalizeBlockCapabilityPatch,
  normalizePanelCapabilityPatch,
  runBlockCapabilitySemanticValidators,
  runPanelCapabilitySemanticValidators,
} from "@/components/Demo/builder/demoBuilderCapabilityRegistry"
import {
  BUILDER_COMPOSITION_TEMPLATES,
  type BuilderTemplateConfirmations,
  type BuilderTemplateId,
  type BuilderValidationIssue,
  createBlockTemplate,
  createCompositionTemplate,
  createEmptyComposition,
  createPanelTemplate,
  type EditableBlock,
  type EditableComposition,
  type EditablePanel,
  getCompositionStoryId,
  getBuilderCompositionTemplateSchema,
  getTemplateSetupState,
  normalizeComposition,
  resolveTemplateChecklistStatus,
  validateCompositionSemantics,
  withTemplateSetupState,
} from "@/components/Demo/builder/demoBuilderSchema"
import { ThemeManagerPanel } from "@/components/Themes"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"
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

function parseNullableObjectJsonOrThrow(
  raw: string,
): Record<string, unknown> | null {
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

function isArrayValue(value: unknown): value is unknown[] {
  return Array.isArray(value)
}

function buildTemplateWithSetupState(
  templateId: BuilderTemplateId,
): EditableComposition {
  return withTemplateSetupState(createCompositionTemplate(templateId), {
    templateId,
    dismissed: false,
    confirmations: {},
  })
}

function toPathTokens(path: string): Array<string | number> {
  const tokens: Array<string | number> = []
  const matcher = /([^[.\]]+)|\[(\d+)\]/g
  let match: RegExpExecArray | null = matcher.exec(path)
  while (match) {
    if (typeof match[1] === "string") {
      tokens.push(match[1])
    } else if (typeof match[2] === "string") {
      tokens.push(Number.parseInt(match[2], 10))
    }
    match = matcher.exec(path)
  }
  return tokens
}

function getValueAtPath(source: unknown, path: string): unknown {
  const tokens = toPathTokens(path)
  let cursor: unknown = source
  for (const token of tokens) {
    if (typeof token === "number") {
      if (!isArrayValue(cursor)) return undefined
      cursor = cursor[token]
      continue
    }
    if (!isObjectRecord(cursor)) return undefined
    cursor = cursor[token]
  }
  return cursor
}

function setValueAtPath(
  source: Record<string, unknown>,
  path: string,
  value: unknown,
): Record<string, unknown> {
  const tokens = toPathTokens(path)
  if (tokens.length === 0) return source

  const root: Record<string, unknown> = { ...source }
  let cursor: unknown = root

  for (let index = 0; index < tokens.length - 1; index += 1) {
    const token = tokens[index]!
    const nextToken = tokens[index + 1]
    if (typeof token === "number") {
      if (!isArrayValue(cursor)) return root
      const existing = cursor[token]
      const branch =
        typeof nextToken === "number"
          ? isArrayValue(existing)
            ? [...existing]
            : []
          : isObjectRecord(existing)
            ? { ...existing }
            : {}
      cursor[token] = branch
      cursor = branch
      continue
    }

    if (!isObjectRecord(cursor)) return root
    const existing = cursor[token]
    const branch =
      typeof nextToken === "number"
        ? isArrayValue(existing)
          ? [...existing]
          : []
        : isObjectRecord(existing)
          ? { ...existing }
          : {}
    cursor[token] = branch
    cursor = branch
  }

  const leaf = tokens[tokens.length - 1]!
  if (typeof leaf === "number") {
    if (!isArrayValue(cursor)) return root
    cursor[leaf] = value
    return root
  }
  if (!isObjectRecord(cursor)) return root
  if (value === null || typeof value === "undefined") {
    delete cursor[leaf]
  } else {
    cursor[leaf] = value
  }
  return root
}

function deepCloneJsonLike<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

function pathMatchesCandidate(path: string, candidate: string): boolean {
  return (
    path === candidate ||
    path.startsWith(`${candidate}.`) ||
    path.startsWith(`${candidate}[`)
  )
}

function findBestPathFocusTarget(path: string): HTMLElement | null {
  const candidates = Array.from(
    document.querySelectorAll<HTMLElement>("[data-builder-path]"),
  )
  let bestMatch: HTMLElement | null = null
  let bestLength = -1
  for (const candidate of candidates) {
    const candidatePath = candidate.dataset.builderPath
    if (!candidatePath) continue
    if (!pathMatchesCandidate(path, candidatePath)) continue
    if (candidatePath.length > bestLength) {
      bestMatch = candidate
      bestLength = candidatePath.length
    }
  }
  return bestMatch
}

function openParentDetails(target: HTMLElement) {
  let cursor: HTMLElement | null = target
  while (cursor) {
    if (cursor instanceof HTMLDetailsElement) {
      cursor.open = true
    }
    cursor = cursor.parentElement
  }
}

function focusBuilderTarget(target: HTMLElement) {
  openParentDetails(target)
  target.scrollIntoView({ behavior: "smooth", block: "center" })
  target.animate(
    [
      { boxShadow: "0 0 0 0 rgba(59, 130, 246, 0.0)" },
      { boxShadow: "0 0 0 3px rgba(59, 130, 246, 0.55)" },
      { boxShadow: "0 0 0 0 rgba(59, 130, 246, 0.0)" },
    ],
    {
      duration: 1100,
      easing: "ease-out",
    },
  )
}

function deriveUniqueId(
  candidate: string | null | undefined,
  existingIds: Set<string>,
  prefix: "panel" | "block",
): string {
  const base =
    typeof candidate === "string" && candidate.trim().length > 0
      ? candidate.trim()
      : `${prefix}`
  if (!existingIds.has(base)) return base
  let suffix = 1
  let next = `${base}-copy-${suffix}`
  while (existingIds.has(next)) {
    suffix += 1
    next = `${base}-copy-${suffix}`
  }
  return next
}

function collectIdsFromValue(value: unknown, output: Set<string>) {
  if (Array.isArray(value)) {
    for (const item of value) collectIdsFromValue(item, output)
    return
  }
  if (!isObjectRecord(value)) return
  if (typeof value.id === "string" && value.id.trim().length > 0) {
    output.add(value.id.trim())
  }
  for (const nested of Object.values(value)) {
    collectIdsFromValue(nested, output)
  }
}

function collectCapabilityValidationIssues(
  composition: EditableComposition,
): BuilderValidationIssue[] {
  const issues: BuilderValidationIssue[] = []
  const panels = composition.panels ?? []
  for (const [index, panel] of panels.entries()) {
    const capability = getPanelCapabilityByKind(
      typeof panel.kind === "string" ? panel.kind : null,
    )
    if (!capability) continue
    for (const validationIssue of runPanelCapabilitySemanticValidators(
      capability,
      composition,
    )) {
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
    const capability = getBlockCapabilityByType(
      typeof block.type === "string" ? block.type : null,
    )
    if (!capability) continue
    for (const validationIssue of runBlockCapabilitySemanticValidators(
      capability,
      composition,
    )) {
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
  type BuilderSectionKey =
    | "top_level"
    | "composition_tree"
    | "theme_manager"
    | "validation"
    | "panels"
    | "blocks"
    | "raw_json"
    | "local_preview"

  const SECTION_VISIBILITY_STORAGE_KEY = "demo-builder-section-visibility-v1"
  const defaultSectionVisibility: Record<BuilderSectionKey, boolean> = {
    top_level: true,
    composition_tree: true,
    theme_manager: false,
    validation: true,
    panels: true,
    blocks: true,
    raw_json: false,
    local_preview: true,
  }
  const [sectionVisibility, setSectionVisibility] = useState<
    Record<BuilderSectionKey, boolean>
  >(() => {
    if (typeof window === "undefined") return defaultSectionVisibility
    try {
      const raw = window.localStorage.getItem(SECTION_VISIBILITY_STORAGE_KEY)
      if (!raw) return defaultSectionVisibility
      const parsed = JSON.parse(raw) as Partial<
        Record<BuilderSectionKey, boolean>
      >
      return {
        ...defaultSectionVisibility,
        ...parsed,
      }
    } catch {
      return defaultSectionVisibility
    }
  })

  useEffect(() => {
    if (typeof window === "undefined") return
    window.localStorage.setItem(
      SECTION_VISIBILITY_STORAGE_KEY,
      JSON.stringify(sectionVisibility),
    )
  }, [sectionVisibility])

  // Demo selector + optional create form state
  const [selectedDemoConfigId, setSelectedDemoConfigId] = useState<string>("")
  const [newSlug, setNewSlug] = useState("")
  const [newTitle, setNewTitle] = useState("")
  const [newDemoScope, setNewDemoScope] = useState<"personal" | "shared">(
    "personal",
  )
  const [isSlugLoading, setIsSlugLoading] = useState(false)
  const slugFetched = useRef(false)
  const [selectedTemplateId, setSelectedTemplateId] =
    useState<BuilderTemplateId>(BUILDER_COMPOSITION_TEMPLATES[0].id)

  // Local editable composition state + raw JSON draft for power-edit mode.
  const [composition, setComposition] = useState<EditableComposition>(
    createEmptyComposition(),
  )
  const [rawJsonDraft, setRawJsonDraft] = useState<string>(
    toPrettyJson(createEmptyComposition()),
  )
  const [isDirty, setIsDirty] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [isStoryPickerOpen, setIsStoryPickerOpen] = useState(false)
  const [isPersonaPickerOpen, setIsPersonaPickerOpen] = useState(false)
  const [storyPickerSearch, setStoryPickerSearch] = useState("")
  const [personaPickerSearch, setPersonaPickerSearch] = useState("")
  const [isThemeQuickAddEnabled, setIsThemeQuickAddEnabled] = useState(false)
  const [previewMode, setPreviewMode] = useState<"off" | "global" | "local">(
    "off",
  )
  const [isRefreshingThemeOptions, setIsRefreshingThemeOptions] =
    useState(false)
  const [cloneScope, setCloneScope] = useState<"panel" | "block" | null>(null)
  const [cloneSourceKind, setCloneSourceKind] = useState<"demo" | "template">(
    "demo",
  )
  const [cloneSourceDemoConfigId, setCloneSourceDemoConfigId] = useState("")
  const [cloneSourceTemplateId, setCloneSourceTemplateId] =
    useState<BuilderTemplateId>(BUILDER_COMPOSITION_TEMPLATES[0].id)
  const [cloneSourceItemKey, setCloneSourceItemKey] = useState("")

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
  const {
    data: cloneSourceDemoCompositionRaw,
    isLoading: isLoadingCloneSourceDemoComposition,
  } = useQuery({
    queryKey: ["demo-builder", "clone-source-composition", cloneSourceDemoConfigId],
    queryFn: () =>
      DemosService.getDemoComposition({
        demoConfigId: cloneSourceDemoConfigId,
      }),
    enabled: Boolean(cloneScope) && cloneSourceKind === "demo" && Boolean(cloneSourceDemoConfigId),
  })
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
  const {
    themes: availablePageThemes,
    isLoading: isLoadingPageThemes,
    refetch: refetchPageThemes,
  } = useAvailableThemes("page")
  const {
    themes: availableCardThemes,
    isLoading: isLoadingCardThemes,
    refetch: refetchCardThemes,
  } = useAvailableThemes("card")
  const filteredStories = useMemo(() => {
    const needle = storyPickerSearch.trim().toLowerCase()
    if (!needle) return stories
    return stories.filter((story) => story.title.toLowerCase().includes(needle))
  }, [stories, storyPickerSearch])
  const filteredPersonas = useMemo(() => {
    const needle = personaPickerSearch.trim().toLowerCase()
    if (!needle) return personas
    return personas.filter((persona) =>
      persona.name.toLowerCase().includes(needle),
    )
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
  const blockingIssues = semanticIssues.filter(
    (issue) => issue.severity === "error",
  )
  const templateSetupState = useMemo(
    () => getTemplateSetupState(composition),
    [composition],
  )
  const activeTemplateSetupId = templateSetupState?.templateId ?? null
  const isTemplateSetupDismissed = templateSetupState?.dismissed ?? false
  const templateConfirmations: BuilderTemplateConfirmations =
    templateSetupState?.confirmations ?? {}
  const activeTemplateChecklist = useMemo(
    () =>
      activeTemplateSetupId
        ? resolveTemplateChecklistStatus({
            templateId: activeTemplateSetupId,
            composition,
            semanticIssues,
            confirmations: templateConfirmations,
          })
        : null,
    [activeTemplateSetupId, composition, semanticIssues, templateConfirmations],
  )
  const cloneSourceComposition = useMemo(() => {
    if (cloneSourceKind === "template") {
      return createCompositionTemplate(cloneSourceTemplateId)
    }
    if (!cloneSourceDemoCompositionRaw) return null
    return normalizeComposition(cloneSourceDemoCompositionRaw)
  }, [
    cloneSourceDemoCompositionRaw,
    cloneSourceKind,
    cloneSourceTemplateId,
  ])
  const cloneSourceItems = useMemo(() => {
    if (!cloneScope || !cloneSourceComposition) return []
    if (cloneScope === "block") {
      return (cloneSourceComposition.blocks ?? []).map((block, index) => ({
        key: String(index),
        label: `${block.title ?? block.type ?? "Block"} · ${block.type ?? "unknown"} · ${block.id}`,
      }))
    }
    return (cloneSourceComposition.panels ?? []).map((panel, index) => ({
      key: String(index),
      label: `${panel.title ?? panel.kind ?? "Panel"} · ${panel.kind ?? "unknown"} · ${panel.id}`,
    }))
  }, [cloneScope, cloneSourceComposition])

  // Load composition when a demo is selected.
  const { data: selectedComposition, isLoading: isLoadingComposition } =
    useQuery({
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
  // Slug Auto-Generation
  // --------------------------------------------------------------------------
  const generateSlugValue = useCallback(async (): Promise<string> => {
    if (isSlugLoading) return ""
    setIsSlugLoading(true)
    try {
      const generated = await AgentsService.generateAgentSlug()
      const slug =
        typeof generated === "string"
          ? generated
          : (generated as { slug?: string })?.slug
      return typeof slug === "string" ? slug.trim() : ""
    } catch (error) {
      console.error("Failed to generate slug:", error)
      return ""
    } finally {
      setIsSlugLoading(false)
    }
  }, [isSlugLoading])

  const fetchSlug = useCallback(async () => {
    const slug = await generateSlugValue()
    if (!slug) return
    setNewSlug(slug)
    setNewTitle(slug)
  }, [generateSlugValue])

  useEffect(() => {
    if (slugFetched.current || newSlug) return
    slugFetched.current = true
    void fetchSlug()
  }, [newSlug, fetchSlug])

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
      queryClient.invalidateQueries({
        queryKey: ["demo-builder", "composition", selectedDemoConfigId],
      })
      showSuccessToast("Composition saved.")
    },
    onError: (error: unknown) => {
      const detail = extractApiErrorDetail(error)
      const message =
        error instanceof Error ? error.message : "Failed to save composition."
      showErrorToast(detail ?? message)
    },
  })

  interface CreateDemoMutationVars {
    slug?: string
    title?: string
    scope?: "personal" | "shared"
    suppressFeedback?: boolean
  }

  const createDemoMutation = useMutation({
    mutationFn: async (variables?: CreateDemoMutationVars) => {
      const slug = (variables?.slug ?? newSlug).trim()
      const title = (variables?.title ?? newTitle).trim()
      if (!slug || !title) {
        throw new Error("Slug and title are required.")
      }
      return DemosService.createNewDemoConfig({
        requestBody: {
          slug,
          title,
          scope: variables?.scope ?? newDemoScope,
          is_active: true,
          default_auto_respond: true,
          metadata_json: {
            created_by: "demo-builder",
          },
        },
      })
    },
    onSuccess: (created, variables) => {
      if (!variables?.suppressFeedback) {
        showSuccessToast("Demo created.")
      }
      setNewSlug("")
      setNewTitle("")
      queryClient.invalidateQueries({ queryKey: ["demo-builder", "configs"] })
      setSelectedDemoConfigId(created.id)
    },
    onError: (error: unknown, variables) => {
      if (variables?.suppressFeedback) return
      const detail = extractApiErrorDetail(error)
      const message =
        error instanceof Error ? error.message : "Failed to create demo."
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
      const effectiveKind =
        patchKind ?? (typeof existing.kind === "string" ? existing.kind : null)
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
      const effectiveType =
        patchType ?? (typeof existing.type === "string" ? existing.type : null)
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

  function openCloneDialog(scope: "panel" | "block") {
    setCloneScope(scope)
    setCloneSourceKind("demo")
    setCloneSourceDemoConfigId(selectedDemoConfigId || "")
    setCloneSourceTemplateId(selectedTemplateId)
    setCloneSourceItemKey("")
  }

  function closeCloneDialog() {
    setCloneScope(null)
    setCloneSourceItemKey("")
  }

  function cloneSelectedItemIntoCurrentComposition() {
    if (!cloneScope) return
    const parsedIndex = Number.parseInt(cloneSourceItemKey, 10)
    if (!Number.isFinite(parsedIndex) || parsedIndex < 0) {
      showErrorToast("Select a source item to clone.")
      return
    }
    if (!cloneSourceComposition) {
      showErrorToast("Source composition is not loaded yet.")
      return
    }

    if (cloneScope === "block") {
      const sourceBlock = cloneSourceComposition.blocks?.[parsedIndex]
      if (!sourceBlock) {
        showErrorToast("Selected source block is not available.")
        return
      }
      updateComposition((current) => {
        const blocks = [...(current.blocks ?? [])]
        const cloned = deepCloneJsonLike(sourceBlock)
        const existingIds = new Set(
          blocks
            .map((item) => (typeof item.id === "string" ? item.id : ""))
            .filter((id) => id.length > 0),
        )
        cloned.id = deriveUniqueId(
          typeof cloned.id === "string" ? cloned.id : null,
          existingIds,
          "block",
        )
        const maxOrder = blocks.reduce(
          (max, item) =>
            typeof item.order === "number" && Number.isFinite(item.order)
              ? Math.max(max, item.order)
              : max,
          0,
        )
        cloned.order = maxOrder + 1
        blocks.push(cloned)
        return { ...current, blocks }
      })
      showSuccessToast("Cloned block into current composition.")
      closeCloneDialog()
      return
    }

    const sourcePanel = cloneSourceComposition.panels?.[parsedIndex]
    if (!sourcePanel) {
      showErrorToast("Selected source panel is not available.")
      return
    }
    updateComposition((current) => {
      const panels = [...(current.panels ?? [])]
      const cloned = deepCloneJsonLike(sourcePanel)
      const existingIds = new Set(
        panels
          .map((item) => (typeof item.id === "string" ? item.id : ""))
          .filter((id) => id.length > 0),
      )
      cloned.id = deriveUniqueId(
        typeof cloned.id === "string" ? cloned.id : null,
        existingIds,
        "panel",
      )
      const maxOrder = panels.reduce(
        (max, item) =>
          typeof item.order === "number" && Number.isFinite(item.order)
            ? Math.max(max, item.order)
            : max,
        0,
      )
      cloned.order = maxOrder + 1
      panels.push(cloned)
      return { ...current, panels }
    })
    showSuccessToast("Cloned panel into current composition.")
    closeCloneDialog()
  }

  function addChildFromTree(params: {
    parentPath: string
    childKind: "panel" | "block"
  }) {
    const { parentPath, childKind } = params
    updateComposition((current) => {
      const parent = getValueAtPath(current, parentPath)
      if (!isObjectRecord(parent)) return current

      const existingChildrenRaw = parent.children
      const existingChildren = Array.isArray(existingChildrenRaw)
        ? [...existingChildrenRaw]
        : []

      const nextChild =
        childKind === "panel"
          ? createPanelTemplate("content")
          : createBlockTemplate("content")

      const existingIds = new Set<string>()
      collectIdsFromValue(current, existingIds)
      nextChild.id = deriveUniqueId(
        typeof nextChild.id === "string" ? nextChild.id : null,
        existingIds,
        childKind,
      )
      const maxOrder = existingChildren.reduce((max, child) => {
        if (!isObjectRecord(child)) return max
        const order = child.order
        return typeof order === "number" && Number.isFinite(order)
          ? Math.max(max, order)
          : max
      }, 0)
      nextChild.order = maxOrder + 1
      if (typeof nextChild.title !== "string" || nextChild.title.trim().length === 0) {
        nextChild.title = childKind === "panel" ? "Nested Panel" : "Nested Block"
      }

      const updatedChildren = [...existingChildren, deepCloneJsonLike(nextChild)]
      return setValueAtPath(
        current as Record<string, unknown>,
        `${parentPath}.children`,
        updatedChildren,
      ) as EditableComposition
    })
    showSuccessToast(
      `Added nested ${childKind} under ${parentPath}.`,
    )
  }

  function focusNodeFromTree(params: { nodePath: string }) {
    const { nodePath } = params
    let targetId: string | null = null
    const panelMatch = nodePath.match(/^panels\[(\d+)\]/)
    const blockMatch = nodePath.match(/^blocks\[(\d+)\]/)
    if (panelMatch) {
      const index = panelMatch[1]
      targetId = `builder-panel-${index}`
      setSectionVisibility((current) => ({ ...current, panels: true }))
    } else if (blockMatch) {
      const index = blockMatch[1]
      targetId = `builder-block-${index}`
      setSectionVisibility((current) => ({ ...current, blocks: true }))
    }
    if (!targetId) return

    window.setTimeout(() => {
      const nestedTarget = findBestPathFocusTarget(nodePath)
      if (nestedTarget) {
        focusBuilderTarget(nestedTarget)
        return
      }
      const fallback = document.getElementById(targetId)
      if (!fallback) return
      focusBuilderTarget(fallback)
    }, 120)
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
        [fieldKey]:
          error instanceof Error ? error.message : "Invalid JSON object.",
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
    const template = buildTemplateWithSetupState(selectedTemplateId)
    setComposition(template)
    setRawJsonDraft(toPrettyJson(template))
    setFieldErrors({})
    markDirty()
    showSuccessToast(`Applied ${selectedTemplateId} template.`)
  }

  async function createFromTemplate() {
    const existingSlug = newSlug.trim()
    const slug = existingSlug || (await generateSlugValue())
    if (!slug) {
      showErrorToast("Failed to generate slug for template creation.")
      return
    }

    if (!existingSlug) {
      setNewSlug(slug)
    }

    const template =
      activeTemplateSetupId === selectedTemplateId
        ? normalizeComposition(composition)
        : buildTemplateWithSetupState(selectedTemplateId)
    const templateIssues = [
      ...validateCompositionSemantics(template),
      ...collectCapabilityValidationIssues(template),
    ]
    if (templateIssues.some((issue) => issue.severity === "error")) {
      showErrorToast(
        "Template requires a valid setup before creation. Apply it to the editor, resolve the checklist, then create the demo.",
      )
      return
    }

    try {
      const created = await createDemoMutation.mutateAsync({
        slug,
        title: slug,
        scope: newDemoScope,
        suppressFeedback: true,
      })

      await DemosService.putDemoComposition({
        demoConfigId: created.id,
        requestBody: template,
      })

      const normalized = normalizeComposition(template)
      setComposition(normalized)
      setRawJsonDraft(toPrettyJson(normalized))
      setFieldErrors({})
      setIsDirty(false)
      setSelectedDemoConfigId(created.id)

      queryClient.invalidateQueries({ queryKey: ["demo-builder", "configs"] })
      queryClient.invalidateQueries({
        queryKey: ["demo-builder", "composition", created.id],
      })

      showSuccessToast(
        `Created "${slug}" from ${selectedTemplateId} template and saved composition.`,
      )
    } catch (error) {
      const detail = extractApiErrorDetail(error)
      const message =
        error instanceof Error
          ? error.message
          : "Failed to create demo from template."
      showErrorToast(detail ?? message)
    }
  }

  function updateTemplateSetupState(
    updater: (current: {
      templateId: BuilderTemplateId
      dismissed: boolean
      confirmations: BuilderTemplateConfirmations
    }) => {
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

  function setRepoId(value: string | null) {
    updateComposition((current) => {
      const metadata = isObjectRecord(current.metadata_json)
        ? { ...current.metadata_json }
        : {}
      if (value) {
        metadata.repo_id = value
      } else {
        delete metadata.repo_id
      }
      return {
        ...current,
        metadata_json: metadata,
      }
    })
  }

  function setSecondaryRepoId(value: string | null) {
    updateComposition((current) => {
      const metadata = isObjectRecord(current.metadata_json)
        ? { ...current.metadata_json }
        : {}
      if (value) {
        metadata.repo_id_secondary = value
      } else {
        delete metadata.repo_id_secondary
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

    const effectivePageThemeId =
      typeof nextPageThemeId === "undefined"
        ? typeof input.page_theme_id === "string"
          ? input.page_theme_id
          : null
        : nextPageThemeId
    const effectiveCardsThemeId =
      typeof nextCardsThemeId === "undefined"
        ? typeof input.cards_theme_id === "string"
          ? input.cards_theme_id
          : null
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

  function applyThemeQuickSelection(
    slot: "page" | "cards",
    themeId: string | null,
  ) {
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

  async function refreshThemeOptions() {
    setIsRefreshingThemeOptions(true)
    try {
      await Promise.all([refetchPageThemes(), refetchCardThemes()])
      showSuccessToast("Theme options refreshed.")
    } catch {
      showErrorToast("Failed to refresh theme options.")
    } finally {
      setIsRefreshingThemeOptions(false)
    }
  }

  const availableThemeOptions = useMemo(
    () => [
      ...availablePageThemes.map((theme) => ({
        id: theme.id,
        name: theme.name,
        category: "page" as const,
      })),
      ...availableCardThemes.map((theme) => ({
        id: theme.id,
        name: theme.name,
        category: "card" as const,
      })),
    ],
    [availableCardThemes, availablePageThemes],
  )

  const previewDiagnostics = useMemo(() => {
    const items: Array<{
      id: string
      severity: "error" | "warning"
      message: string
      targetId: string
    }> = []

    for (const issue of semanticIssues) {
      let targetId = "builder-composition-editor"
      if (issue.path?.startsWith("panels[")) {
        const match = issue.path.match(/^panels\[(\d+)\]/)
        if (match) targetId = `builder-panel-${match[1]}`
      } else if (issue.path?.startsWith("blocks[")) {
        const match = issue.path.match(/^blocks\[(\d+)\]/)
        if (match) targetId = `builder-block-${match[1]}`
      }
      items.push({
        id: `semantic-${issue.code}-${issue.path ?? "root"}`,
        severity: issue.severity,
        message: issue.message,
        targetId,
      })
    }

    for (const [index, panel] of (composition.panels ?? []).entries()) {
      const capability = getPanelCapabilityByKind(
        typeof panel.kind === "string" ? panel.kind : null,
      )
      if (!capability) continue
      const availability = getPanelCapabilityAvailability(
        capability,
        composition,
      )
      if (availability.available) continue
      items.push({
        id: `panel-req-${index}`,
        severity: "warning",
        message: `Panel "${panel.title ?? panel.kind ?? `#${index + 1}`}" requires ${availability.unmetRequirements.join(" + ")}.`,
        targetId: `builder-panel-${index}`,
      })
    }

    for (const [index, block] of (composition.blocks ?? []).entries()) {
      const capability = getBlockCapabilityByType(
        typeof block.type === "string" ? block.type : null,
      )
      if (!capability) continue
      const availability = getBlockCapabilityAvailability(
        capability,
        composition,
      )
      if (availability.available) continue
      items.push({
        id: `block-req-${index}`,
        severity: "warning",
        message: `Block "${block.title ?? block.type ?? `#${index + 1}`}" requires ${availability.unmetRequirements.join(" + ")}.`,
        targetId: `builder-block-${index}`,
      })
    }

    const dedup = new Map<string, (typeof items)[number]>()
    for (const item of items) {
      const key = `${item.severity}:${item.message}:${item.targetId}`
      if (!dedup.has(key)) dedup.set(key, item)
    }
    return Array.from(dedup.values())
  }, [composition, semanticIssues])

  const previewPane = (
    <div className="h-full min-h-0 flex flex-col gap-2">
      {previewDiagnostics.length > 0 && (
        <div className="rounded border p-2 bg-muted/30">
          <p className="text-xs font-medium mb-1">Preview Diagnostics</p>
          <div className="space-y-1 max-h-32 overflow-auto">
            {previewDiagnostics.map((diagnostic) => (
              <div key={diagnostic.id} className="text-xs">
                <a
                  href={`#${diagnostic.targetId}`}
                  className={
                    diagnostic.severity === "error"
                      ? "text-red-700 underline"
                      : "text-amber-700 underline"
                  }
                >
                  [{diagnostic.severity}] {diagnostic.message}
                </a>
              </div>
            ))}
          </div>
        </div>
      )}
      <div className="flex-1 min-h-0">
        <DemoBuilderPreview
          demoConfigId={selectedDemo?.id ?? null}
          demoSlug={selectedDemo?.slug ?? null}
          composition={composition}
          demoTitle={selectedDemo?.title ?? "Demo Builder Preview"}
          isDirty={isDirty}
          availablePageThemes={availablePageThemes}
          availableCardThemes={availableCardThemes}
          onPageThemeChange={(themeId) =>
            applyThemeQuickSelection("page", themeId)
          }
          onCardsThemeChange={(themeId) =>
            applyThemeQuickSelection("cards", themeId)
          }
        />
      </div>
    </div>
  )

  const editorSections = (
    <>
      <Card>
        <details open className="group">
          <summary className="list-none cursor-pointer [&::-webkit-details-marker]:hidden">
            <CardHeader>
              <div className="flex items-start justify-between gap-2">
                <div>
                  <CardTitle>Select Or Create Demo</CardTitle>
                  <CardDescription>
                    Load an existing demo config or create a new one before
                    editing composition.
                  </CardDescription>
                </div>
                <div className="flex items-center gap-1 pt-1">
                  <ChevronRight className="h-4 w-4 group-open:hidden" />
                  <ChevronDown className="h-4 w-4 hidden group-open:block" />
                  <span className="text-xs text-muted-foreground">
                    <span className="group-open:hidden">Expand</span>
                    <span className="hidden group-open:inline">Collapse</span>
                  </span>
                </div>
              </div>
            </CardHeader>
          </summary>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
            <label className="text-sm font-medium">Create New Demo</label>
            <div className="grid gap-2">
              <div className="space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <label className="text-xs text-muted-foreground">
                    Slug <span className="opacity-70">(auto)</span>
                  </label>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => void fetchSlug()}
                    disabled={isSlugLoading}
                  >
                    {isSlugLoading ? (
                      <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                    ) : (
                      <RefreshCcw className="h-3 w-3 mr-1" />
                    )}
                    {isSlugLoading ? "Generating..." : "Regenerate"}
                  </Button>
                </div>
                <Input
                  placeholder={
                    isSlugLoading
                      ? "Generating..."
                      : "slug (e.g. qa-builder-demo)"
                  }
                  value={newSlug}
                  onChange={(event) => setNewSlug(event.target.value)}
                  className="font-mono"
                />
              </div>
              <Input
                placeholder="title"
                value={newTitle}
                onChange={(event) => setNewTitle(event.target.value)}
              />
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground">
                  Access Scope
                </label>
                <Select
                  value={newDemoScope}
                  onValueChange={(value) =>
                    setNewDemoScope(value as "personal" | "shared")
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select scope..." />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="personal">Personal</SelectItem>
                    <SelectItem value="shared">Shared</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Shared demos are visible to all logged-in users.
                </p>
              </div>
              <Button
                type="button"
                onClick={() => createDemoMutation.mutate({})}
                disabled={createDemoMutation.isPending || isSlugLoading}
              >
                {createDemoMutation.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Plus className="h-4 w-4 mr-2" />
                )}
                Create Demo
              </Button>
            </div>
            <div className="pt-3 border-t mt-3 space-y-2">
              <label className="text-sm font-medium">
                Composition Template
              </label>
              <div className="grid gap-2 md:grid-cols-2">
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">
                    Demo Config
                  </label>
                  <Select
                    value={selectedDemoConfigId || "_none"}
                    onValueChange={(value) =>
                      setSelectedDemoConfigId(value === "_none" ? "" : value)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select demo config..." />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="_none">None</SelectItem>
                      {isLoadingDemos && (
                        <SelectItem value="_loading" disabled>
                          Loading...
                        </SelectItem>
                      )}
                      {demoConfigs.map((demo) => (
                        <SelectItem key={demo.id} value={demo.id}>
                          {demo.slug} · {demo.title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">
                    Template
                  </label>
                  <Select
                    value={selectedTemplateId}
                    onValueChange={(value) =>
                      setSelectedTemplateId(value as BuilderTemplateId)
                    }
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
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => void createFromTemplate()}
                  disabled={createDemoMutation.isPending || isSlugLoading}
                >
                  {createDemoMutation.isPending || isSlugLoading ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Plus className="h-4 w-4 mr-2" />
                  )}
                  Create From Template
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={applyTemplateToEditor}
                >
                  Apply Template To Editor
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                {
                  BUILDER_COMPOSITION_TEMPLATES.find(
                    (template) => template.id === selectedTemplateId,
                  )?.description
                }
              </p>
            </div>
            </div>
          </CardContent>
        </details>
      </Card>

      {activeTemplateSetupId && activeTemplateChecklist && (
        <DemoTemplateSetupChecklist
          templateId={activeTemplateSetupId}
          templateLabel={
            getBuilderCompositionTemplateSchema(activeTemplateSetupId).label
          }
          checklistStatus={activeTemplateChecklist}
          isDismissed={isTemplateSetupDismissed}
          composition={composition}
          confirmations={templateConfirmations}
          onDismiss={() =>
            updateTemplateSetupState((current) => ({
              ...current,
              dismissed: true,
            }))
          }
          onResume={() =>
            updateTemplateSetupState((current) => ({
              ...current,
              dismissed: false,
            }))
          }
          onStoryIdChange={setStoryId}
          onRepoIdChange={setRepoId}
          onSecondaryRepoIdChange={setSecondaryRepoId}
          onRuntimePolicyChange={(value) =>
            updateComposition((current) => ({
              ...current,
              runtime_policy: value,
            }))
          }
          onPersonaPolicyChange={(value) =>
            updateComposition((current) => ({
              ...current,
              persona_policy: value,
            }))
          }
          onChatModeChange={(value) =>
            updateComposition((current) => ({
              ...current,
              chat_mode: value,
            }))
          }
          onFixedUserPersonaIdChange={(value) =>
            updateComposition((current) => ({
              ...current,
              fixed_user_persona_id: value,
            }))
          }
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
                <p className="text-sm text-muted-foreground">
                  Loading stories...
                </p>
              )}
              {!isLoadingStories && filteredStories.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  No stories found.
                </p>
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
                  <div className="text-xs text-muted-foreground font-mono">
                    {story.id}
                  </div>
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
              Pick a persona to set `persona_policy=fixed_user_persona` and
              populate `fixed_user_persona_id`.
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
                <p className="text-sm text-muted-foreground">
                  Loading personas...
                </p>
              )}
              {!isLoadingPersonas && filteredPersonas.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  No personas found.
                </p>
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
                  <div className="text-xs text-muted-foreground font-mono">
                    {persona.id}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={Boolean(cloneScope)} onOpenChange={(open) => !open && closeCloneDialog()}>
        <DialogContent className="sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>
              Clone Existing {cloneScope === "panel" ? "Panel" : "Block"}
            </DialogTitle>
            <DialogDescription>
              Copy one item from another DemoConfig or composition template into
              this working composition. Cloned items are detached and get a
              unique id/order in the current draft.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground">Source Type</label>
                <Select
                  value={cloneSourceKind}
                  onValueChange={(value) => {
                    setCloneSourceKind(value as "demo" | "template")
                    setCloneSourceItemKey("")
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select source type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="demo">Demo Config</SelectItem>
                    <SelectItem value="template">Composition Template</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {cloneSourceKind === "demo" ? (
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">
                    Source Demo Config
                  </label>
                  <Select
                    value={cloneSourceDemoConfigId || "_none"}
                    onValueChange={(value) => {
                      setCloneSourceDemoConfigId(value === "_none" ? "" : value)
                      setCloneSourceItemKey("")
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select source demo config" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="_none">None</SelectItem>
                      {demoConfigs.map((demo) => (
                        <SelectItem key={demo.id} value={demo.id}>
                          {demo.slug} · {demo.title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              ) : (
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">
                    Source Template
                  </label>
                  <Select
                    value={cloneSourceTemplateId}
                    onValueChange={(value) => {
                      setCloneSourceTemplateId(value as BuilderTemplateId)
                      setCloneSourceItemKey("")
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select source template" />
                    </SelectTrigger>
                    <SelectContent>
                      {BUILDER_COMPOSITION_TEMPLATES.map((template) => (
                        <SelectItem key={template.id} value={template.id}>
                          {template.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>

            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">
                Select {cloneScope === "panel" ? "Panel" : "Block"} To Clone
              </label>
              <Select
                value={cloneSourceItemKey || "_none"}
                onValueChange={(value) =>
                  setCloneSourceItemKey(value === "_none" ? "" : value)
                }
                disabled={
                  cloneSourceKind === "demo" &&
                  (isLoadingCloneSourceDemoComposition ||
                    !cloneSourceDemoConfigId)
                }
              >
                <SelectTrigger>
                  <SelectValue
                    placeholder={
                      cloneSourceKind === "demo" &&
                      isLoadingCloneSourceDemoComposition
                        ? "Loading source composition..."
                        : "Select item"
                    }
                  />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="_none">None</SelectItem>
                  {cloneSourceItems.map((item) => (
                    <SelectItem key={item.key} value={item.key}>
                      {item.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {cloneSourceItems.length === 0 && (
                <p className="text-xs text-muted-foreground">
                  No {cloneScope === "panel" ? "panels" : "blocks"} available
                  in selected source.
                </p>
              )}
            </div>

            <div className="flex items-center justify-end gap-2">
              <Button type="button" variant="outline" onClick={closeCloneDialog}>
                Cancel
              </Button>
              <Button
                type="button"
                onClick={cloneSelectedItemIntoCurrentComposition}
                disabled={
                  cloneSourceItemKey.length === 0 ||
                  (cloneSourceKind === "demo" &&
                    (isLoadingCloneSourceDemoComposition ||
                      !cloneSourceDemoConfigId))
                }
              >
                Clone Into Current Composition
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <Collapsible
        open={sectionVisibility.top_level}
        onOpenChange={(open) =>
          setSectionVisibility((current) => ({ ...current, top_level: open }))
        }
      >
        <div className="flex items-center justify-between rounded border px-3 py-2 bg-muted/20">
          <div>
            <p className="text-sm font-medium">Composition Editor</p>
            <p className="text-xs text-muted-foreground">
              Top-level demo composition fields and theme quick-add controls.
            </p>
          </div>
          <CollapsibleTrigger asChild>
            <Button type="button" variant="outline" size="sm">
              {sectionVisibility.top_level ? (
                <ChevronDown className="h-4 w-4 mr-1" />
              ) : (
                <ChevronRight className="h-4 w-4 mr-1" />
              )}
              {sectionVisibility.top_level ? "Collapse" : "Expand"}
            </Button>
          </CollapsibleTrigger>
        </div>
        <CollapsibleContent
          forceMount
          className="data-[state=closed]:hidden mt-3"
        >
          <div className="rounded border p-3 mb-3 space-y-2 max-w-md">
            <div className="text-sm font-medium">Preview Mode</div>
            <p className="text-xs text-muted-foreground">
              Choose one preview instance at a time. Global mode uses
              split-pane; local mode renders inline.
            </p>
            <Select
              value={previewMode}
              onValueChange={(value) =>
                setPreviewMode(value as "off" | "global" | "local")
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Select preview mode" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="off">Off</SelectItem>
                <SelectItem value="global">Global Split Pane</SelectItem>
                <SelectItem value="local">Local Inline</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <DemoTopLevelEditor
            selectedDemoConfigId={selectedDemoConfigId}
            isLoadingComposition={isLoadingComposition}
            composition={composition}
            fieldErrors={fieldErrors}
            onLayoutModeChange={(value) =>
              updateComposition((current) => ({
                ...current,
                layout_mode: value,
              }))
            }
            onRuntimePolicyChange={(value) =>
              updateComposition((current) => ({
                ...current,
                runtime_policy: value,
              }))
            }
            onPersonaPolicyChange={(value: DemoPersonaPolicy) =>
              updateComposition((current) => ({
                ...current,
                persona_policy: value,
              }))
            }
            onChatModeChange={(value: DemoChatMode) =>
              updateComposition((current) => ({
                ...current,
                chat_mode: value,
              }))
            }
            onFixedUserPersonaIdChange={(value) =>
              updateComposition((current) => ({
                ...current,
                fixed_user_persona_id: value,
              }))
            }
            onPageThemeIdChange={(value) =>
              updateComposition((current) => ({
                ...current,
                page_theme_id: value,
              }))
            }
            onCardsThemeIdChange={(value) =>
              updateComposition((current) => ({
                ...current,
                cards_theme_id: value,
              }))
            }
            onCapabilityFieldChange={(key, value) =>
              updateComposition(
                (current) =>
                  setValueAtPath(
                    current as Record<string, unknown>,
                    key,
                    value,
                  ) as EditableComposition,
              )
            }
            onMetadataJsonBlur={(raw) =>
              commitJsonField("metadata_json", raw, (value) => {
                updateComposition((current) => ({
                  ...current,
                  metadata_json: value ?? {},
                }))
              })
            }
            onPresentationJsonBlur={(raw) =>
              commitJsonField("presentation_json", raw, (value) => {
                updateComposition((current) => ({
                  ...current,
                  presentation_json: value ?? {},
                }))
              })
            }
            storyId={getCompositionStoryId(composition)}
            onStoryIdChange={setStoryId}
            onOpenStoryPicker={() => setIsStoryPickerOpen(true)}
            isThemeQuickAddEnabled={isThemeQuickAddEnabled}
            onThemeQuickAddEnabledChange={setIsThemeQuickAddEnabled}
            availablePageThemes={availablePageThemes}
            availableCardThemes={availableCardThemes}
            isLoadingThemeOptions={isLoadingPageThemes || isLoadingCardThemes}
            onPageThemeQuickSelect={(value) =>
              applyThemeQuickSelection("page", value)
            }
            onCardsThemeQuickSelect={(value) =>
              applyThemeQuickSelection("cards", value)
            }
          />
        </CollapsibleContent>
      </Collapsible>

      <Collapsible
        open={sectionVisibility.composition_tree}
        onOpenChange={(open) =>
          setSectionVisibility((current) => ({
            ...current,
            composition_tree: open,
          }))
        }
      >
        <div className="flex items-center justify-between rounded border px-3 py-2 bg-muted/20">
          <div>
            <p className="text-sm font-medium">Composition Tree</p>
            <p className="text-xs text-muted-foreground">
              Read-only map of roots and detected nested panel/block nodes.
            </p>
          </div>
          <CollapsibleTrigger asChild>
            <Button type="button" variant="outline" size="sm">
              {sectionVisibility.composition_tree ? (
                <ChevronDown className="h-4 w-4 mr-1" />
              ) : (
                <ChevronRight className="h-4 w-4 mr-1" />
              )}
              {sectionVisibility.composition_tree ? "Collapse" : "Expand"}
            </Button>
          </CollapsibleTrigger>
        </div>
        <CollapsibleContent
          forceMount
          className="data-[state=closed]:hidden mt-3"
        >
          <DemoCompositionTree
            composition={composition}
            onAddChild={addChildFromTree}
            onFocusNode={focusNodeFromTree}
          />
        </CollapsibleContent>
      </Collapsible>

      <Collapsible
        open={sectionVisibility.theme_manager}
        onOpenChange={(open) =>
          setSectionVisibility((current) => ({
            ...current,
            theme_manager: open,
          }))
        }
      >
        <div className="flex items-center justify-between rounded border px-3 py-2 bg-muted/20">
          <div>
            <p className="text-sm font-medium">Theme Manager</p>
            <p className="text-xs text-muted-foreground">
              Create and edit themes without leaving Demo Builder.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={refreshThemeOptions}
              disabled={isRefreshingThemeOptions}
            >
              {isRefreshingThemeOptions ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <RefreshCcw className="h-4 w-4 mr-2" />
              )}
              Refresh
            </Button>
            <CollapsibleTrigger asChild>
              <Button type="button" variant="outline" size="sm">
                {sectionVisibility.theme_manager ? (
                  <ChevronDown className="h-4 w-4 mr-1" />
                ) : (
                  <ChevronRight className="h-4 w-4 mr-1" />
                )}
                {sectionVisibility.theme_manager ? "Collapse" : "Expand"}
              </Button>
            </CollapsibleTrigger>
          </div>
        </div>
        <CollapsibleContent
          forceMount
          className="data-[state=closed]:hidden mt-3"
        >
          <Card>
            <CardHeader>
              <CardDescription>
                Create/edit themes in-context, then apply them to composition,
                panels, and blocks.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ThemeManagerPanel />
            </CardContent>
          </Card>
        </CollapsibleContent>
      </Collapsible>

      {previewMode === "local" && (
        <Collapsible
          open={sectionVisibility.local_preview}
          onOpenChange={(open) =>
            setSectionVisibility((current) => ({
              ...current,
              local_preview: open,
            }))
          }
        >
          <div className="flex items-center justify-between rounded border px-3 py-2 bg-muted/20">
            <div>
              <p className="text-sm font-medium">Live Preview (Local)</p>
              <p className="text-xs text-muted-foreground">
                Inline preview of current unsaved composition.
              </p>
            </div>
            <CollapsibleTrigger asChild>
              <Button type="button" variant="outline" size="sm">
                {sectionVisibility.local_preview ? (
                  <ChevronDown className="h-4 w-4 mr-1" />
                ) : (
                  <ChevronRight className="h-4 w-4 mr-1" />
                )}
                {sectionVisibility.local_preview ? "Collapse" : "Expand"}
              </Button>
            </CollapsibleTrigger>
          </div>
          <CollapsibleContent
            forceMount
            className="data-[state=closed]:hidden mt-3"
          >
            <Card>
              <CardContent className="h-[560px] min-h-0 pt-6">
                {previewPane}
              </CardContent>
            </Card>
          </CollapsibleContent>
        </Collapsible>
      )}

      <Collapsible
        open={sectionVisibility.validation}
        onOpenChange={(open) =>
          setSectionVisibility((current) => ({ ...current, validation: open }))
        }
      >
        <div className="flex items-center justify-between rounded border px-3 py-2 bg-muted/20">
          <div>
            <p className="text-sm font-medium">Validation</p>
            <p className="text-xs text-muted-foreground">
              Semantic and capability-level validation issues.
            </p>
          </div>
          <CollapsibleTrigger asChild>
            <Button type="button" variant="outline" size="sm">
              {sectionVisibility.validation ? (
                <ChevronDown className="h-4 w-4 mr-1" />
              ) : (
                <ChevronRight className="h-4 w-4 mr-1" />
              )}
              {sectionVisibility.validation ? "Collapse" : "Expand"}
            </Button>
          </CollapsibleTrigger>
        </div>
        <CollapsibleContent
          forceMount
          className="data-[state=closed]:hidden mt-3"
        >
          <DemoValidationPanel issues={semanticIssues} />
        </CollapsibleContent>
      </Collapsible>

      <Collapsible
        open={sectionVisibility.panels}
        onOpenChange={(open) =>
          setSectionVisibility((current) => ({ ...current, panels: open }))
        }
      >
        <div className="flex items-center justify-between rounded border px-3 py-2 bg-muted/20">
          <div>
            <p className="text-sm font-medium">Panel Editor</p>
            <p className="text-xs text-muted-foreground">
              Configure panel kinds, layout, and panel presentation.
            </p>
          </div>
          <CollapsibleTrigger asChild>
            <Button type="button" variant="outline" size="sm">
              {sectionVisibility.panels ? (
                <ChevronDown className="h-4 w-4 mr-1" />
              ) : (
                <ChevronRight className="h-4 w-4 mr-1" />
              )}
              {sectionVisibility.panels ? "Collapse" : "Expand"}
            </Button>
          </CollapsibleTrigger>
        </div>
        <CollapsibleContent
          forceMount
          className="data-[state=closed]:hidden mt-3"
        >
          <DemoPanelEditor
            composition={composition}
            panels={composition.panels ?? []}
            fieldErrors={fieldErrors}
            onAddPanel={(kind) =>
              updateComposition((current) => ({
                ...current,
                panels: [...(current.panels ?? []), createPanelTemplate(kind)],
              }))
            }
            onOpenCloneDialog={() => openCloneDialog("panel")}
            onRemovePanel={removePanel}
            onUpdatePanel={updatePanel}
            onCommitPanelJsonField={(index, fieldKey, raw) =>
              commitJsonField(`panel:${index}:${fieldKey}`, raw, (value) => {
                updatePanel(index, { [fieldKey]: value ?? {} })
              })
            }
            availableThemeOptions={availableThemeOptions}
          />
        </CollapsibleContent>
      </Collapsible>

      <Collapsible
        open={sectionVisibility.blocks}
        onOpenChange={(open) =>
          setSectionVisibility((current) => ({ ...current, blocks: open }))
        }
      >
        <div className="flex items-center justify-between rounded border px-3 py-2 bg-muted/20">
          <div>
            <p className="text-sm font-medium">Block Editor</p>
            <p className="text-xs text-muted-foreground">
              Configure block regions, visibility, and block presentation.
            </p>
          </div>
          <CollapsibleTrigger asChild>
            <Button type="button" variant="outline" size="sm">
              {sectionVisibility.blocks ? (
                <ChevronDown className="h-4 w-4 mr-1" />
              ) : (
                <ChevronRight className="h-4 w-4 mr-1" />
              )}
              {sectionVisibility.blocks ? "Collapse" : "Expand"}
            </Button>
          </CollapsibleTrigger>
        </div>
        <CollapsibleContent
          forceMount
          className="data-[state=closed]:hidden mt-3"
        >
          <DemoBlockEditor
            composition={composition}
            blocks={composition.blocks ?? []}
            fieldErrors={fieldErrors}
            onAddBlock={(type) =>
              updateComposition((current) => ({
                ...current,
                blocks: [...(current.blocks ?? []), createBlockTemplate(type)],
              }))
            }
            onOpenCloneDialog={() => openCloneDialog("block")}
            onRemoveBlock={removeBlock}
            onUpdateBlock={updateBlock}
            onCommitBlockJsonField={(index, fieldKey, raw) =>
              commitJsonField(`block:${index}:${fieldKey}`, raw, (value) => {
                if (fieldKey === "content_json") {
                  updateBlock(index, { content_json: value ?? null })
                  return
                }
                updateBlock(index, { [fieldKey]: value ?? {} })
              })
            }
            availableThemeOptions={availableThemeOptions}
          />
        </CollapsibleContent>
      </Collapsible>

      <Collapsible
        open={sectionVisibility.raw_json}
        onOpenChange={(open) =>
          setSectionVisibility((current) => ({ ...current, raw_json: open }))
        }
      >
        <div className="flex items-center justify-between rounded border px-3 py-2 bg-muted/20">
          <div>
            <p className="text-sm font-medium">Raw JSON Editor</p>
            <p className="text-xs text-muted-foreground">
              Advanced direct editing fallback for the full composition payload.
            </p>
          </div>
          <CollapsibleTrigger asChild>
            <Button type="button" variant="outline" size="sm">
              {sectionVisibility.raw_json ? (
                <ChevronDown className="h-4 w-4 mr-1" />
              ) : (
                <ChevronRight className="h-4 w-4 mr-1" />
              )}
              {sectionVisibility.raw_json ? "Collapse" : "Expand"}
            </Button>
          </CollapsibleTrigger>
        </div>
        <CollapsibleContent
          forceMount
          className="data-[state=closed]:hidden mt-3"
        >
          <DemoRawJsonEditor
            rawJsonDraft={rawJsonDraft}
            rawJsonError={fieldErrors.raw_json}
            onRawJsonDraftChange={setRawJsonDraft}
            onResetFromCurrent={() =>
              setRawJsonDraft(toPrettyJson(composition))
            }
            onApplyRawJson={applyRawJsonDraft}
          />
        </CollapsibleContent>
      </Collapsible>

      <DemoSaveBar
        selectedDemoLabel={
          selectedDemo
            ? `${selectedDemo.slug} (${selectedDemo.id.slice(0, 8)}...)`
            : "No demo selected"
        }
        isDirty={isDirty}
        canSave={Boolean(selectedDemoConfigId) && blockingIssues.length === 0}
        isSaving={saveCompositionMutation.isPending}
        onSave={() => saveCompositionMutation.mutate()}
      />
    </>
  )

  return (
    <div className="flex flex-col gap-4 pb-6">
      <div>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold">Demo Builder (MVP)</h1>
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
        <p className="text-sm text-muted-foreground mt-1">
          Build and save demo compositions using generated OpenAPI contract
          types.
        </p>
      </div>

      {previewMode === "global" ? (
        <ResizablePanelGroup direction="horizontal" className="min-h-[80vh]">
          <ResizablePanel defaultSize={60} minSize={40}>
            <div className="h-full overflow-y-auto pr-2 space-y-4">
              {editorSections}
            </div>
          </ResizablePanel>
          <ResizableHandle withHandle />
          <ResizablePanel defaultSize={40} minSize={25}>
            <Card className="h-full">
              <CardHeader>
                <CardTitle>Live Preview (Global)</CardTitle>
                <CardDescription>
                  Full composition preview updates with unsaved edits.
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[calc(100%-96px)] min-h-0">
                {previewPane}
              </CardContent>
            </Card>
          </ResizablePanel>
        </ResizablePanelGroup>
      ) : (
        <div className="space-y-4">{editorSections}</div>
      )}
    </div>
  )
}
