import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { ChevronDown, ChevronRight } from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import { OpenAPI } from "@/client"
import { request } from "@/client/core/request"
import {
  AgentsService,
  LlmCatalogService,
  LlmProvidersService,
  PromptConfigsService,
} from "@/client/sdk.gen"
import { PromptTopLevelEditor } from "@/components/Prompt/builder/PromptTopLevelEditor"
import {
  buildPromptValidationContext,
  hydratePromptDraftProviderAndModel,
  mapUserAgentConfigToPromptDraft,
} from "@/components/Prompt/builder/promptBuilderAdapters"
import { validatePromptDraftWithCapabilityHooks } from "@/components/Prompt/builder/promptBuilderCapabilityRegistry"
import {
  createEmptyPromptDraft,
  normalizePromptDraft,
  type PromptConfigDraft,
} from "@/components/Prompt/builder/promptBuilderSchema"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"

export const Route = createFileRoute("/_layout/prompt-builder")({
  component: PromptBuilderPage,
  head: () => ({
    meta: [{ title: "Prompt Builder" }],
  }),
})

function extractApiErrorDetail(error: unknown): string | null {
  if (!error || typeof error !== "object") return null
  const maybe = error as { body?: unknown; message?: string }
  if (!maybe.body || typeof maybe.body !== "object")
    return maybe.message ?? null
  const detail = (maybe.body as { detail?: unknown }).detail
  return typeof detail === "string" ? detail : (maybe.message ?? null)
}

function isUuid(value: string | null | undefined): value is string {
  if (!value) return false
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
    value,
  )
}

function asTrimmedString(value: string | null | undefined): string {
  return value?.trim() ?? ""
}

function PromptBuilderPage() {
  const queryClient = useQueryClient()
  type PromptSectionKey =
    | "persistence"
    | "top_level"
    | "planned_integrations"
    | "raw_json"
    | "validation"
  const SECTION_VISIBILITY_STORAGE_KEY = "prompt-builder-section-visibility-v1"
  const defaultSectionVisibility: Record<PromptSectionKey, boolean> = {
    persistence: true,
    top_level: true,
    planned_integrations: false,
    raw_json: false,
    validation: true,
  }
  const [sectionVisibility, setSectionVisibility] = useState<
    Record<PromptSectionKey, boolean>
  >(() => {
    if (typeof window === "undefined") return defaultSectionVisibility
    try {
      const raw = window.localStorage.getItem(SECTION_VISIBILITY_STORAGE_KEY)
      if (!raw) return defaultSectionVisibility
      const parsed = JSON.parse(raw) as Partial<
        Record<PromptSectionKey, boolean>
      >
      return {
        ...defaultSectionVisibility,
        ...parsed,
      }
    } catch {
      return defaultSectionVisibility
    }
  })
  const [draft, setDraft] = useState<PromptConfigDraft>(() =>
    createEmptyPromptDraft(),
  )
  const [baselineDraft, setBaselineDraft] = useState<PromptConfigDraft>(() =>
    createEmptyPromptDraft(),
  )
  const [rawJsonDraft, setRawJsonDraft] = useState<string>(() =>
    JSON.stringify(createEmptyPromptDraft(), null, 2),
  )
  const [rawJsonError, setRawJsonError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [selectedPromptConfigId, setSelectedPromptConfigId] =
    useState<string>("")
  const [selectedAgentId, setSelectedAgentId] = useState<string>("")
  const [lastSavedAt, setLastSavedAt] = useState<string | null>(null)
  const [isResetFromAgentConfirmOpen, setIsResetFromAgentConfirmOpen] =
    useState(false)
  const [newPromptConfigSlug, setNewPromptConfigSlug] = useState("")
  const [newPromptConfigName, setNewPromptConfigName] = useState("")
  const [newPromptConfigDescription, setNewPromptConfigDescription] = useState(
    "Created from Prompt Builder",
  )
  const [bindingVersionPolicy, setBindingVersionPolicy] = useState<
    "latest" | "pinned"
  >("latest")
  const [bindingVersionNumber, setBindingVersionNumber] = useState<string>("")
  const [persistencePath, setPersistencePath] = useState<
    "resume_prompt_config" | "start_from_agent"
  >("resume_prompt_config")
  const selectedProviderId = draft.provider.user_access_provider_id
  const selectedProviderIdForCatalog = isUuid(selectedProviderId)
    ? selectedProviderId
    : null
  const workingCopyStorageKey = useMemo(
    () => `prompt-builder:working-copy:${selectedPromptConfigId || "global"}`,
    [selectedPromptConfigId],
  )

  const { data: providersResponse, isLoading: isLoadingProviders } = useQuery({
    queryKey: ["prompt-builder", "providers"],
    queryFn: () => LlmProvidersService.listProviders({ limit: 300 }),
  })
  const { data: modelsResponse, isLoading: isLoadingModels } = useQuery({
    queryKey: [
      "prompt-builder",
      "models",
      selectedProviderIdForCatalog ?? "all",
    ],
    queryFn: () =>
      selectedProviderIdForCatalog
        ? LlmCatalogService.listModelsForUap({
            userAccessProviderId: selectedProviderIdForCatalog,
            limit: 400,
          })
        : LlmCatalogService.listModels({ limit: 400 }),
  })
  const { data: agentsResponse, isLoading: isLoadingAgents } = useQuery({
    queryKey: ["prompt-builder", "agents"],
    queryFn: () => AgentsService.listAgents({ limit: 200 }),
  })
  const { data: promptConfigsResponse, isLoading: isLoadingPromptConfigs } =
    useQuery({
      queryKey: ["prompt-builder", "prompt-configs"],
      queryFn: () => PromptConfigsService.listPromptConfigs({ limit: 200 }),
    })
  const { data: workingCopyResponse, isLoading: isLoadingWorkingCopy } =
    useQuery({
      queryKey: ["prompt-builder", "working-copy", selectedPromptConfigId],
      queryFn: () =>
        PromptConfigsService.getPromptConfigWorkingCopy({
          promptConfigId: selectedPromptConfigId,
        }),
      enabled: Boolean(selectedPromptConfigId),
      retry: false,
    })

  const providers = providersResponse?.data ?? []
  const models = modelsResponse?.data ?? []
  const agents = agentsResponse?.data ?? []
  const promptConfigs = promptConfigsResponse?.data ?? []
  const activeWorkingCopy = workingCopyResponse ?? null
  const selectedAgent = useMemo(
    () => agents.find((agent) => agent.id === selectedAgentId) ?? null,
    [agents, selectedAgentId],
  )
  const selectedPromptConfig = useMemo(
    () =>
      promptConfigs.find((config) => config.id === selectedPromptConfigId) ??
      null,
    [promptConfigs, selectedPromptConfigId],
  )
  const selectedAgentBoundPromptConfig = useMemo(
    () =>
      promptConfigs.find(
        (config) => config.id === selectedAgent?.prompt_config_id,
      ) ?? null,
    [promptConfigs, selectedAgent?.prompt_config_id],
  )
  const hydration = useMemo(
    () => hydratePromptDraftProviderAndModel(draft, providers, models),
    [draft, providers, models],
  )
  const validationContext = useMemo(
    () => buildPromptValidationContext(hydration),
    [hydration],
  )

  const semanticIssues = useMemo(
    () =>
      validatePromptDraftWithCapabilityHooks(
        hydration.draft,
        validationContext,
      ),
    [hydration, validationContext],
  )
  const blockingIssues = semanticIssues.filter(
    (issue) => issue.severity === "error",
  )
  const isDirty = useMemo(
    () => JSON.stringify(draft) !== JSON.stringify(baselineDraft),
    [draft, baselineDraft],
  )
  const canSaveOrCommit =
    blockingIssues.length === 0 &&
    Object.keys(fieldErrors).length === 0 &&
    !rawJsonError
  const capabilityOptions = useMemo(
    () => ({
      "provider.user_access_provider_id": providers.map((provider) => ({
        value: provider.id,
        label:
          provider.is_enabled === false
            ? `${provider.name} (disabled)`
            : provider.name,
        disabled: provider.is_enabled === false,
      })),
      "model.model_id": models.map((model) => ({
        value: model.model_id,
        label: model.display_name
          ? `${model.display_name} (${model.model_id})`
          : model.model_id,
      })),
    }),
    [providers, models],
  )
  const loadFromAgentMutation = useMutation({
    mutationFn: async (agentId: string) => {
      const agent = await AgentsService.getAgent({ agentId })
      return mapUserAgentConfigToPromptDraft(agent)
    },
    onSuccess: (nextDraft) => {
      setDraft(nextDraft)
      setBaselineDraft(nextDraft)
      setRawJsonDraft(JSON.stringify(nextDraft, null, 2))
      setRawJsonError(null)
      setFieldErrors({})
      showSuccessToast(
        "Loaded local draft from selected agent (no PromptConfig changes yet).",
      )
    },
    onError: () => {
      showErrorToast("Failed to load selected agent into Prompt Builder.")
    },
  })
  async function generateSharedSlugValue(): Promise<string> {
    try {
      const generated = await AgentsService.generateAgentSlug()
      const slug =
        typeof generated === "string"
          ? generated
          : (generated as { slug?: string })?.slug
      return typeof slug === "string" ? slug.trim() : ""
    } catch (error) {
      console.error("Failed to generate shared slug:", error)
      return ""
    }
  }
  const resetFromAgentMutation = useMutation({
    mutationFn: async (input: { promptConfigId: string; agentId: string }) => {
      const agent = await AgentsService.getAgent({ agentId: input.agentId })
      const nextDraft = mapUserAgentConfigToPromptDraft(agent)
      await request(OpenAPI, {
        method: "DELETE",
        url: "/api/v1/prompt-configs/{prompt_config_id}",
        path: {
          prompt_config_id: input.promptConfigId,
        },
        errors: {
          404: "PromptConfig not found",
          422: "Validation Error",
        },
      })
      return nextDraft
    },
    onSuccess: async (nextDraft, variables) => {
      setDraft(nextDraft)
      setBaselineDraft(nextDraft)
      setRawJsonDraft(JSON.stringify(nextDraft, null, 2))
      setRawJsonError(null)
      setFieldErrors({})
      setLastSavedAt(null)
      setSelectedPromptConfigId("")
      setIsResetFromAgentConfirmOpen(false)
      await queryClient.invalidateQueries({
        queryKey: ["prompt-builder", "prompt-configs"],
      })
      await queryClient.invalidateQueries({
        queryKey: ["prompt-builder", "working-copy", variables.promptConfigId],
      })
      showSuccessToast(
        "Deleted PromptConfig and loaded a fresh local draft from selected agent.",
      )
    },
    onError: (error: unknown) => {
      const detail = extractApiErrorDetail(error)
      showErrorToast(detail ?? "Failed to reset from agent.")
    },
  })
  const createPromptConfigMutation = useMutation({
    mutationFn: async () => {
      const generatedSlug =
        asTrimmedString(newPromptConfigSlug) ||
        (await generateSharedSlugValue())
      if (!generatedSlug) {
        throw new Error("Unable to generate prompt config slug.")
      }
      const title =
        asTrimmedString(newPromptConfigName) ||
        generatedSlug ||
        `Prompt Config ${new Date().toISOString()}`
      return PromptConfigsService.createPromptConfig({
        requestBody: {
          slug: generatedSlug,
          name: title,
          description:
            asTrimmedString(newPromptConfigDescription) ||
            "Created from Prompt Builder",
          payload: draft as any,
          commit_message: "Initial version",
        },
      })
    },
    onSuccess: async (created) => {
      setSelectedPromptConfigId(created.id)
      setNewPromptConfigSlug(created.slug)
      if (!asTrimmedString(newPromptConfigName)) {
        setNewPromptConfigName(created.name)
      }
      await queryClient.invalidateQueries({
        queryKey: ["prompt-builder", "prompt-configs"],
      })
      await queryClient.invalidateQueries({
        queryKey: ["prompt-builder", "working-copy", created.id],
      })
      showSuccessToast("Created PromptConfig.")
    },
    onError: (error: unknown) => {
      const detail = extractApiErrorDetail(error)
      showErrorToast(detail ?? "Failed to create PromptConfig.")
    },
  })
  const bindPromptConfigToAgentMutation = useMutation({
    mutationFn: async (input: {
      agentId: string
      promptConfigId: string | null
      versionPolicy: "latest" | "pinned"
      versionNumber: number | null
    }) => {
      const agent = await AgentsService.getAgent({ agentId: input.agentId })
      const name = asTrimmedString(agent.name)
      const slug = asTrimmedString(agent.slug)
      const providerType = asTrimmedString(agent.provider_type)
      if (!name || !slug || !providerType) {
        throw new Error("Selected agent is missing required identity fields.")
      }
      return AgentsService.updateAgent({
        agentId: input.agentId,
        requestBody: {
          name,
          slug,
          provider_type: providerType as any,
          description: agent.description ?? null,
          user_access_provider: agent.user_access_provider ?? null,
          model: agent.model ?? null,
          model_id: agent.model_id ?? null,
          model_name: agent.model_name ?? undefined,
          system_prompt: agent.system_prompt ?? null,
          custom_system_prompt: agent.custom_system_prompt ?? null,
          instructions: agent.instructions ?? null,
          tool_config: agent.tool_config ?? null,
          deps_config: agent.deps_config ?? null,
          prompt_config_id: input.promptConfigId,
          prompt_config_version_policy: input.promptConfigId
            ? input.versionPolicy
            : null,
          prompt_config_version_number: input.promptConfigId
            ? input.versionPolicy === "pinned"
              ? input.versionNumber
              : null
            : null,
          agent_metadata: agent.agent_metadata ?? null,
          agent_type: agent.agent_type ?? null,
          presentation: agent.presentation ?? null,
          is_enabled: agent.is_enabled ?? true,
          is_clonable: agent.is_clonable ?? false,
          is_visible: agent.is_visible ?? false,
          scope: agent.scope ?? "personal",
          participation_mode: agent.participation_mode ?? "on_mention",
          is_coordinator: agent.is_coordinator ?? false,
          max_tool_iterations: agent.max_tool_iterations ?? 10,
          capabilities: agent.capabilities ?? [],
        } as any,
      })
    },
    onSuccess: async (_, variables) => {
      await queryClient.invalidateQueries({
        queryKey: ["prompt-builder", "agents"],
      })
      const label =
        variables.promptConfigId == null
          ? "Removed PromptConfig binding."
          : "Bound PromptConfig to agent."
      showSuccessToast(label)
    },
    onError: (error: unknown) => {
      const detail = extractApiErrorDetail(error)
      showErrorToast(detail ?? "Failed to update agent PromptConfig binding.")
    },
  })
  const saveWorkingCopyMutation = useMutation({
    mutationFn: async () => {
      if (!selectedPromptConfigId) throw new Error("No prompt config selected.")
      return PromptConfigsService.putPromptConfigWorkingCopy({
        promptConfigId: selectedPromptConfigId,
        requestBody: {
          payload: draft as any,
          base_version: activeWorkingCopy?.base_version ?? null,
          has_uncommitted_changes: true,
        },
      })
    },
    onSuccess: async (saved) => {
      setBaselineDraft(saved.payload as PromptConfigDraft)
      setLastSavedAt(new Date().toISOString())
      await queryClient.invalidateQueries({
        queryKey: ["prompt-builder", "working-copy", selectedPromptConfigId],
      })
      showSuccessToast("Saved working copy.")
    },
    onError: (error: unknown) => {
      const detail = extractApiErrorDetail(error)
      showErrorToast(detail ?? "Failed to save working copy.")
    },
  })
  const commitVersionMutation = useMutation({
    mutationFn: async () => {
      if (!selectedPromptConfigId) throw new Error("No prompt config selected.")
      return PromptConfigsService.commitPromptConfigVersion({
        promptConfigId: selectedPromptConfigId,
        requestBody: {
          commit_message: "Commit from Prompt Builder",
        },
      })
    },
    onSuccess: async () => {
      setLastSavedAt(new Date().toISOString())
      await queryClient.invalidateQueries({
        queryKey: ["prompt-builder", "working-copy", selectedPromptConfigId],
      })
      await queryClient.invalidateQueries({
        queryKey: ["prompt-builder", "prompt-configs"],
      })
      showSuccessToast("Committed prompt version.")
    },
    onError: (error: unknown) => {
      const detail = extractApiErrorDetail(error)
      showErrorToast(detail ?? "Failed to commit prompt version.")
    },
  })
  const resetWorkingCopyMutation = useMutation({
    mutationFn: async () => {
      if (!selectedPromptConfigId) throw new Error("No prompt config selected.")
      return PromptConfigsService.resetPromptConfigWorkingCopy({
        promptConfigId: selectedPromptConfigId,
        requestBody: {},
      })
    },
    onSuccess: (reset) => {
      const next = reset.payload as PromptConfigDraft
      setDraft(next)
      setBaselineDraft(next)
      setRawJsonDraft(JSON.stringify(next, null, 2))
      setRawJsonError(null)
      showSuccessToast("Reset working copy to latest committed version.")
    },
    onError: () => showErrorToast("Failed to reset working copy."),
  })

  useEffect(() => {
    if (!activeWorkingCopy) return
    const next = activeWorkingCopy.payload as PromptConfigDraft
    setDraft(next)
    setBaselineDraft(next)
    setRawJsonDraft(JSON.stringify(next, null, 2))
    setRawJsonError(null)
    setFieldErrors({})
  }, [activeWorkingCopy])

  useEffect(() => {
    if (selectedPromptConfigId) {
      setPersistencePath("resume_prompt_config")
      return
    }
    if (selectedAgentId) {
      setPersistencePath("start_from_agent")
    }
  }, [selectedPromptConfigId, selectedAgentId])

  useEffect(() => {
    if (selectedPromptConfig) {
      setNewPromptConfigSlug(selectedPromptConfig.slug)
      setNewPromptConfigName(selectedPromptConfig.name)
      setNewPromptConfigDescription(selectedPromptConfig.description ?? "")
      return
    }
    if (!newPromptConfigName) {
      setNewPromptConfigName("")
    }
  }, [selectedPromptConfig, newPromptConfigName])

  useEffect(() => {
    if (!selectedAgent) {
      setBindingVersionPolicy("latest")
      setBindingVersionNumber("")
      return
    }
    const nextPolicy =
      selectedAgent.prompt_config_version_policy === "pinned"
        ? "pinned"
        : "latest"
    setBindingVersionPolicy(nextPolicy)
    setBindingVersionNumber(
      selectedAgent.prompt_config_version_number != null
        ? String(selectedAgent.prompt_config_version_number)
        : "",
    )
  }, [
    selectedAgent?.id,
    selectedAgent?.prompt_config_version_policy,
    selectedAgent?.prompt_config_version_number,
    selectedAgent,
  ])

  useEffect(() => {
    if (typeof window === "undefined") return
    window.localStorage.setItem(
      SECTION_VISIBILITY_STORAGE_KEY,
      JSON.stringify(sectionVisibility),
    )
  }, [sectionVisibility])

  function onDraftChange(next: PromptConfigDraft) {
    setDraft(next)
    setRawJsonDraft(JSON.stringify(next, null, 2))
    setRawJsonError(null)
  }

  function resetRawJsonFromCurrentDraft() {
    setRawJsonDraft(JSON.stringify(draft, null, 2))
    setRawJsonError(null)
  }

  function applyRawJsonToDraft() {
    try {
      const parsed = JSON.parse(rawJsonDraft) as Partial<PromptConfigDraft>
      const normalized = normalizePromptDraft(parsed)
      setDraft(normalized)
      setRawJsonDraft(JSON.stringify(normalized, null, 2))
      setRawJsonError(null)
      showSuccessToast("Applied raw JSON to Prompt Builder.")
    } catch {
      setRawJsonError("Invalid prompt draft JSON.")
    }
  }

  function onSaveDraftLocal() {
    setBaselineDraft(draft)
    showSuccessToast("Local prompt draft snapshot saved.")
  }

  function onRevertToSaved() {
    setDraft(baselineDraft)
    setRawJsonDraft(JSON.stringify(baselineDraft, null, 2))
    setRawJsonError(null)
  }

  function resetFromAgent() {
    if (!selectedAgentId) {
      showErrorToast("Select an agent before reset.")
      return
    }
    if (!selectedPromptConfigId) {
      showErrorToast("Select a PromptConfig before reset.")
      return
    }
    setIsResetFromAgentConfirmOpen(true)
  }

  function confirmResetFromAgent() {
    if (!selectedAgentId || !selectedPromptConfigId) {
      showErrorToast("Select both PromptConfig and source agent before reset.")
      return
    }
    resetFromAgentMutation.mutate({
      promptConfigId: selectedPromptConfigId,
      agentId: selectedAgentId,
    })
  }

  function saveToPromptConfig() {
    if (!selectedPromptConfigId) {
      showErrorToast("Select a PromptConfig to save.")
      return
    }
    saveWorkingCopyMutation.mutate()
  }

  async function populateNewPromptConfigSlug() {
    const slug = await generateSharedSlugValue()
    if (!slug) {
      showErrorToast("Failed to generate slug.")
      return
    }
    setNewPromptConfigSlug(slug)
    if (!asTrimmedString(newPromptConfigName)) {
      setNewPromptConfigName(slug)
    }
  }

  function bindSelectedPromptConfigToAgent() {
    if (!selectedAgentId) {
      showErrorToast("Select an agent to bind.")
      return
    }
    if (!selectedPromptConfigId) {
      showErrorToast("Select a PromptConfig to bind.")
      return
    }
    const parsedVersionNumber =
      bindingVersionPolicy === "pinned"
        ? Number.parseInt(bindingVersionNumber, 10)
        : null
    if (
      bindingVersionPolicy === "pinned" &&
      (!Number.isFinite(parsedVersionNumber) ||
        parsedVersionNumber == null ||
        parsedVersionNumber <= 0)
    ) {
      showErrorToast(
        "Pinned version policy requires a positive version number.",
      )
      return
    }
    bindPromptConfigToAgentMutation.mutate({
      agentId: selectedAgentId,
      promptConfigId: selectedPromptConfigId,
      versionPolicy: bindingVersionPolicy,
      versionNumber: parsedVersionNumber,
    })
  }

  function unbindPromptConfigFromAgent() {
    if (!selectedAgentId) {
      showErrorToast("Select an agent to unbind.")
      return
    }
    bindPromptConfigToAgentMutation.mutate({
      agentId: selectedAgentId,
      promptConfigId: null,
      versionPolicy: "latest",
      versionNumber: null,
    })
  }

  function commitPromptConfigVersion() {
    if (!selectedPromptConfigId) {
      showErrorToast("Select a PromptConfig to commit.")
      return
    }
    commitVersionMutation.mutate()
  }

  function saveWorkingCopyToBrowser() {
    try {
      window.localStorage.setItem(workingCopyStorageKey, JSON.stringify(draft))
      showSuccessToast("Saved browser working copy.")
    } catch {
      showErrorToast("Failed to save browser working copy.")
    }
  }

  function loadWorkingCopyFromBrowser() {
    try {
      const raw = window.localStorage.getItem(workingCopyStorageKey)
      if (!raw) {
        showErrorToast("No browser working copy found for selected scope.")
        return
      }
      const parsed = JSON.parse(raw) as Partial<PromptConfigDraft>
      const normalized = normalizePromptDraft(parsed)
      setDraft(normalized)
      setRawJsonDraft(JSON.stringify(normalized, null, 2))
      setRawJsonError(null)
      showSuccessToast("Loaded browser working copy.")
    } catch {
      showErrorToast("Failed to parse browser working copy.")
    }
  }

  return (
    <div className="space-y-4 p-4 pb-24">
      <Card>
        <Collapsible
          open={sectionVisibility.persistence}
          onOpenChange={(open) =>
            setSectionVisibility((current) => ({
              ...current,
              persistence: open,
            }))
          }
        >
          <CardHeader>
            <div className="flex items-center justify-between gap-2">
              <div>
                <CardTitle>PromptConfig Persistence</CardTitle>
                <CardDescription>
                  A PromptConfig is the saved prompt recipe for one run profile
                  (provider/model/input/params/tools), with API-backed
                  working-copy + version history.
                </CardDescription>
              </div>
              <CollapsibleTrigger asChild>
                <Button variant="outline" size="sm">
                  {sectionVisibility.persistence ? (
                    <ChevronDown className="h-4 w-4 mr-1" />
                  ) : (
                    <ChevronRight className="h-4 w-4 mr-1" />
                  )}
                  {sectionVisibility.persistence ? "Collapse" : "Expand"}
                </Button>
              </CollapsibleTrigger>
            </div>
          </CardHeader>
          <CollapsibleContent>
            <CardContent className="space-y-3">
              <div className="rounded-md border bg-muted/40 p-3 text-xs text-muted-foreground">
                First choose your starting path: resume an existing
                PromptConfig, or start from a Source Agent template. Both paths
                edit the same draft model, but they represent different
                workflows for how prompt state is sourced.
              </div>
              <Tabs
                value={persistencePath}
                onValueChange={(value) =>
                  setPersistencePath(
                    value as "resume_prompt_config" | "start_from_agent",
                  )
                }
              >
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="resume_prompt_config">
                    Resume PromptConfig
                  </TabsTrigger>
                  <TabsTrigger value="start_from_agent">
                    Start From SourceAgent
                  </TabsTrigger>
                </TabsList>
                <TabsContent
                  value="resume_prompt_config"
                  className="mt-3 space-y-3"
                >
                  <div className="rounded-md border bg-muted/40 p-3 text-xs text-muted-foreground">
                    Choose this when you already have a PromptConfig to
                    continue, review, or version.
                  </div>
                  <div className="space-y-1">
                    <Label>Prompt Config</Label>
                    <Select
                      value={selectedPromptConfigId || "__none"}
                      onValueChange={(value) =>
                        setSelectedPromptConfigId(
                          value === "__none" ? "" : value,
                        )
                      }
                    >
                      <SelectTrigger>
                        <SelectValue
                          placeholder={
                            isLoadingPromptConfigs
                              ? "Loading prompt configs..."
                              : "Select a prompt config"
                          }
                        />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__none">None</SelectItem>
                        {promptConfigs.map((config) => (
                          <SelectItem key={config.id} value={config.id}>
                            {config.slug} · {config.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-3 md:grid-cols-3">
                    <div className="space-y-1">
                      <Label>New PromptConfig Slug</Label>
                      <Input
                        placeholder="generated-slug"
                        value={newPromptConfigSlug}
                        onChange={(event) =>
                          setNewPromptConfigSlug(event.target.value)
                        }
                      />
                    </div>
                    <div className="space-y-1">
                      <Label>New PromptConfig Name</Label>
                      <Input
                        placeholder="Prompt Config name"
                        value={newPromptConfigName}
                        onChange={(event) =>
                          setNewPromptConfigName(event.target.value)
                        }
                      />
                    </div>
                    <div className="space-y-1">
                      <Label>New PromptConfig Description</Label>
                      <Input
                        placeholder="Optional description"
                        value={newPromptConfigDescription}
                        onChange={(event) =>
                          setNewPromptConfigDescription(event.target.value)
                        }
                      />
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      variant="outline"
                      onClick={() => void populateNewPromptConfigSlug()}
                    >
                      Generate Slug
                    </Button>
                    <Button
                      variant="outline"
                      disabled={createPromptConfigMutation.isPending}
                      onClick={() => createPromptConfigMutation.mutate()}
                    >
                      Create Prompt Config
                    </Button>
                    <Button
                      variant="outline"
                      disabled={
                        !selectedPromptConfigId ||
                        resetWorkingCopyMutation.isPending ||
                        isLoadingWorkingCopy
                      }
                      onClick={() => resetWorkingCopyMutation.mutate()}
                    >
                      Reset To Latest Commit
                    </Button>
                  </div>
                  <div className="rounded-md border bg-muted/40 p-3 text-xs text-muted-foreground">
                    Optional: load a Source Agent into your local draft to
                    compare or re-baseline behavior. This does not overwrite
                    PromptConfig history unless you explicitly save/commit.
                  </div>
                  <div className="space-y-1">
                    <Label>Source Agent (Optional)</Label>
                    <Select
                      value={selectedAgentId || "__none"}
                      onValueChange={(value) =>
                        setSelectedAgentId(value === "__none" ? "" : value)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue
                          placeholder={
                            isLoadingAgents
                              ? "Loading agents..."
                              : "Select an agent"
                          }
                        />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__none">None</SelectItem>
                        {agents.map((agent) => (
                          <SelectItem key={agent.id} value={agent.id}>
                            {agent.name ?? agent.slug ?? agent.id}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      variant="outline"
                      disabled={
                        !selectedAgentId ||
                        loadFromAgentMutation.isPending ||
                        resetFromAgentMutation.isPending
                      }
                      onClick={() =>
                        loadFromAgentMutation.mutate(selectedAgentId)
                      }
                    >
                      Load From Agent
                    </Button>
                    <Button
                      variant="destructive"
                      disabled={
                        !selectedAgentId ||
                        !selectedPromptConfigId ||
                        loadFromAgentMutation.isPending ||
                        resetFromAgentMutation.isPending
                      }
                      onClick={resetFromAgent}
                    >
                      Reset From Agent
                    </Button>
                  </div>
                  <div className="space-y-3 rounded-md border p-3">
                    <div>
                      <Label>Agent Binding</Label>
                      <p className="text-xs text-muted-foreground">
                        Bind the selected PromptConfig to the selected agent so
                        runtime resolves this recipe by default.
                      </p>
                    </div>
                    <div className="grid gap-3 md:grid-cols-3">
                      <div className="space-y-1">
                        <Label>Version Policy</Label>
                        <Select
                          value={bindingVersionPolicy}
                          onValueChange={(value) =>
                            setBindingVersionPolicy(
                              value as "latest" | "pinned",
                            )
                          }
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="latest">Latest</SelectItem>
                            <SelectItem value="pinned">Pinned</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-1">
                        <Label>Pinned Version</Label>
                        <Input
                          type="number"
                          min={1}
                          disabled={bindingVersionPolicy !== "pinned"}
                          placeholder="e.g. 3"
                          value={bindingVersionNumber}
                          onChange={(event) =>
                            setBindingVersionNumber(event.target.value)
                          }
                        />
                      </div>
                      <div className="space-y-1">
                        <Label>Current Agent Binding</Label>
                        <div className="rounded-md border bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
                          {selectedAgent?.prompt_config_id
                            ? selectedAgentBoundPromptConfig
                              ? `${selectedAgentBoundPromptConfig.slug} · ${selectedAgentBoundPromptConfig.name}`
                              : selectedAgent.prompt_config_id
                            : "No PromptConfig bound."}
                        </div>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button
                        variant="secondary"
                        disabled={
                          !selectedAgentId ||
                          !selectedPromptConfigId ||
                          bindPromptConfigToAgentMutation.isPending
                        }
                        onClick={bindSelectedPromptConfigToAgent}
                      >
                        Bind To Agent
                      </Button>
                      <Button
                        variant="outline"
                        disabled={
                          !selectedAgentId ||
                          !selectedAgent?.prompt_config_id ||
                          bindPromptConfigToAgentMutation.isPending
                        }
                        onClick={unbindPromptConfigFromAgent}
                      >
                        Unbind From Agent
                      </Button>
                    </div>
                  </div>
                </TabsContent>
                <TabsContent
                  value="start_from_agent"
                  className="mt-3 space-y-3"
                >
                  <div className="rounded-md border bg-muted/40 p-3 text-xs text-muted-foreground">
                    Choose this when you want to bootstrap from an existing
                    agent config. Load from agent first, then create a
                    PromptConfig when you are ready to persist and version.
                  </div>
                  <div className="space-y-1">
                    <Label>Source Agent</Label>
                    <Select
                      value={selectedAgentId || "__none"}
                      onValueChange={(value) =>
                        setSelectedAgentId(value === "__none" ? "" : value)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue
                          placeholder={
                            isLoadingAgents
                              ? "Loading agents..."
                              : "Select an agent"
                          }
                        />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__none">None</SelectItem>
                        {agents.map((agent) => (
                          <SelectItem key={agent.id} value={agent.id}>
                            {agent.name ?? agent.slug ?? agent.id}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      variant="outline"
                      disabled={
                        !selectedAgentId ||
                        loadFromAgentMutation.isPending ||
                        resetFromAgentMutation.isPending
                      }
                      onClick={() =>
                        loadFromAgentMutation.mutate(selectedAgentId)
                      }
                    >
                      Load From Agent
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => void populateNewPromptConfigSlug()}
                    >
                      Generate Slug
                    </Button>
                    <Button
                      disabled={createPromptConfigMutation.isPending}
                      onClick={() => createPromptConfigMutation.mutate()}
                    >
                      Create Prompt Config From Current Draft
                    </Button>
                  </div>
                  <div className="grid gap-3 md:grid-cols-3">
                    <div className="space-y-1">
                      <Label>New PromptConfig Slug</Label>
                      <Input
                        placeholder="generated-slug"
                        value={newPromptConfigSlug}
                        onChange={(event) =>
                          setNewPromptConfigSlug(event.target.value)
                        }
                      />
                    </div>
                    <div className="space-y-1">
                      <Label>New PromptConfig Name</Label>
                      <Input
                        placeholder="Prompt Config name"
                        value={newPromptConfigName}
                        onChange={(event) =>
                          setNewPromptConfigName(event.target.value)
                        }
                      />
                    </div>
                    <div className="space-y-1">
                      <Label>New PromptConfig Description</Label>
                      <Input
                        placeholder="Optional description"
                        value={newPromptConfigDescription}
                        onChange={(event) =>
                          setNewPromptConfigDescription(event.target.value)
                        }
                      />
                    </div>
                  </div>
                </TabsContent>
              </Tabs>

              <div className="space-y-2 pt-1">
                <Label>Browser Checkpoints</Label>
                <div className="flex flex-wrap gap-2">
                  <Button variant="outline" onClick={saveWorkingCopyToBrowser}>
                    Save Working Copy (Browser)
                  </Button>
                  <Button
                    variant="outline"
                    onClick={loadWorkingCopyFromBrowser}
                  >
                    Load Working Copy (Browser)
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Use browser checkpoints for fast local recovery during
                  experimentation. Use PromptConfig save/commit for shared
                  API-backed history.
                </p>
              </div>
              <p className="text-xs text-muted-foreground">
                {selectedPromptConfig
                  ? `PromptConfig: ${selectedPromptConfig.slug} · ${selectedPromptConfig.name}`
                  : "No PromptConfig selected."}{" "}
                {selectedAgent
                  ? `Selected: ${selectedAgent.name ?? selectedAgent.slug ?? selectedAgent.id}`
                  : "No source agent selected."}
                {lastSavedAt
                  ? ` Last persisted: ${new Date(lastSavedAt).toLocaleString()}.`
                  : ""}{" "}
                {activeWorkingCopy?.base_version != null
                  ? `Base version: ${activeWorkingCopy.base_version}.`
                  : ""}
              </p>
              <AlertDialog
                open={isResetFromAgentConfirmOpen}
                onOpenChange={setIsResetFromAgentConfirmOpen}
              >
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>
                      Reset From Agent (Destructive)
                    </AlertDialogTitle>
                    <AlertDialogDescription>
                      This will delete PromptConfig "
                      {selectedPromptConfig?.name ?? "selected config"}" and its
                      full version history, then load a new local draft from the
                      selected source agent. This action cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel
                      disabled={resetFromAgentMutation.isPending}
                    >
                      Cancel
                    </AlertDialogCancel>
                    <AlertDialogAction
                      onClick={confirmResetFromAgent}
                      disabled={resetFromAgentMutation.isPending}
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                    >
                      {resetFromAgentMutation.isPending
                        ? "Resetting..."
                        : "Delete And Reset"}
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </CardContent>
          </CollapsibleContent>
        </Collapsible>
      </Card>

      <PromptTopLevelEditor
        draft={hydration.draft}
        fieldErrors={fieldErrors}
        onFieldErrorsChange={setFieldErrors}
        onDraftChange={onDraftChange}
        capabilityOptions={capabilityOptions}
        loadingCapabilityOptions={{
          "provider.user_access_provider_id": isLoadingProviders,
          "model.model_id": isLoadingModels,
        }}
        isOpen={sectionVisibility.top_level}
        onOpenChange={(open) =>
          setSectionVisibility((current) => ({ ...current, top_level: open }))
        }
      />

      <Card>
        <Collapsible
          open={sectionVisibility.planned_integrations}
          onOpenChange={(open) =>
            setSectionVisibility((current) => ({
              ...current,
              planned_integrations: open,
            }))
          }
        >
          <CardHeader>
            <div className="flex items-center justify-between gap-2">
              <div>
                <CardTitle>Planned Integration Points</CardTitle>
                <CardDescription>
                  Early/beta placeholder surfaces for required capabilities that
                  are not wired yet.
                </CardDescription>
              </div>
              <CollapsibleTrigger asChild>
                <Button variant="outline" size="sm">
                  {sectionVisibility.planned_integrations ? (
                    <ChevronDown className="h-4 w-4 mr-1" />
                  ) : (
                    <ChevronRight className="h-4 w-4 mr-1" />
                  )}
                  {sectionVisibility.planned_integrations
                    ? "Collapse"
                    : "Expand"}
                </Button>
              </CollapsibleTrigger>
            </div>
          </CardHeader>
          <CollapsibleContent>
            <CardContent className="space-y-4">
              <div className="rounded-md border bg-muted/40 p-3 text-xs text-muted-foreground">
                These controls are intentionally disabled for now. They are
                visible to communicate roadmap direction and ensure integration
                points remain explicit during implementation.
              </div>

              <div className="space-y-3 rounded-md border p-3">
                <h3 className="text-sm font-medium">
                  Execution & Integration (Planned)
                </h3>
                <p className="text-xs text-muted-foreground">
                  Planned integrations for source synchronization, orchestration
                  strategy, and runtime tool contract selection.
                </p>
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="space-y-1">
                    <Label>Git Repo URL</Label>
                    <Input disabled placeholder="Add or view linked git repo" />
                  </div>
                  <div className="space-y-1">
                    <Label>Orchestration Pattern</Label>
                    <Select
                      disabled
                      value="__none"
                      onValueChange={() => undefined}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select orchestration pattern" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__none">None</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button disabled variant="outline">
                    View Repo
                  </Button>
                  <Button disabled variant="outline">
                    Push
                  </Button>
                  <Button disabled variant="outline">
                    Pull
                  </Button>
                  <Button disabled variant="outline">
                    Select Tools From Library
                  </Button>
                </div>
              </div>

              <div className="space-y-3 rounded-md border p-3">
                <h3 className="text-sm font-medium">Presentation (Planned)</h3>
                <p className="text-xs text-muted-foreground">
                  Planned controls for configuring how this prompt/workflow is
                  presented in platform UI and downstream surfaces.
                </p>
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="space-y-1">
                    <Label>Presentation Profile</Label>
                    <Select
                      disabled
                      value="__none"
                      onValueChange={() => undefined}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select presentation profile" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__none">None</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <Label>Presentation Notes</Label>
                    <Input
                      disabled
                      placeholder="Author-facing guidance for presentation behavior"
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-3 rounded-md border p-3">
                <h3 className="text-sm font-medium">
                  Governance & Distribution (Planned)
                </h3>
                <p className="text-xs text-muted-foreground">
                  Planned controls for visibility, reuse, traceability, and
                  policy-based locking.
                </p>
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="space-y-1">
                    <Label>Visibility</Label>
                    <Select
                      disabled
                      value="__none"
                      onValueChange={() => undefined}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Shared or private" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__none">None</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <Label>Locked Categories</Label>
                    <Input
                      disabled
                      placeholder="Define categories that are locked from editing"
                    />
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button disabled variant="outline">
                    Cloneable
                  </Button>
                  <Button disabled variant="outline">
                    Inspectable
                  </Button>
                </div>
              </div>
            </CardContent>
          </CollapsibleContent>
        </Collapsible>
      </Card>

      <Card>
        <Collapsible
          open={sectionVisibility.raw_json}
          onOpenChange={(open) =>
            setSectionVisibility((current) => ({ ...current, raw_json: open }))
          }
        >
          <CardHeader>
            <div className="flex items-center justify-between gap-2">
              <div>
                <CardTitle>Raw JSON Editor</CardTitle>
                <CardDescription>
                  Advanced fallback for full-draft editing. Apply writes
                  normalized values back into editor state.
                </CardDescription>
              </div>
              <CollapsibleTrigger asChild>
                <Button variant="outline" size="sm">
                  {sectionVisibility.raw_json ? (
                    <ChevronDown className="h-4 w-4 mr-1" />
                  ) : (
                    <ChevronRight className="h-4 w-4 mr-1" />
                  )}
                  {sectionVisibility.raw_json ? "Collapse" : "Expand"}
                </Button>
              </CollapsibleTrigger>
            </div>
          </CardHeader>
          <CollapsibleContent>
            <CardContent className="space-y-3">
              <Textarea
                className="min-h-[220px] font-mono text-xs"
                value={rawJsonDraft}
                onChange={(event) => {
                  setRawJsonDraft(event.target.value)
                  if (rawJsonError) setRawJsonError(null)
                }}
              />
              {rawJsonError && (
                <p className="text-sm text-destructive">{rawJsonError}</p>
              )}
              <div className="flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  onClick={resetRawJsonFromCurrentDraft}
                >
                  Reset From Current Draft
                </Button>
                <Button variant="secondary" onClick={applyRawJsonToDraft}>
                  Apply Raw JSON
                </Button>
              </div>
            </CardContent>
          </CollapsibleContent>
        </Collapsible>
      </Card>

      <Card>
        <Collapsible
          open={sectionVisibility.validation}
          onOpenChange={(open) =>
            setSectionVisibility((current) => ({
              ...current,
              validation: open,
            }))
          }
        >
          <CardHeader>
            <div className="flex items-center justify-between gap-2">
              <div>
                <CardTitle>Semantic Validation</CardTitle>
                <CardDescription>
                  Combined base semantic rules + capability hook validators.
                </CardDescription>
              </div>
              <CollapsibleTrigger asChild>
                <Button variant="outline" size="sm">
                  {sectionVisibility.validation ? (
                    <ChevronDown className="h-4 w-4 mr-1" />
                  ) : (
                    <ChevronRight className="h-4 w-4 mr-1" />
                  )}
                  {sectionVisibility.validation ? "Collapse" : "Expand"}
                </Button>
              </CollapsibleTrigger>
            </div>
          </CardHeader>
          <CollapsibleContent>
            <CardContent className="space-y-2">
              {semanticIssues.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No semantic issues.
                </p>
              ) : (
                semanticIssues.map((issue, index) => (
                  <div key={`${issue.code}-${index}`} className="text-sm">
                    <span
                      className={
                        issue.severity === "error"
                          ? "text-destructive"
                          : "text-amber-600"
                      }
                    >
                      [{issue.severity}]
                    </span>{" "}
                    <span>{issue.message}</span>
                    {issue.path && (
                      <span className="text-xs text-muted-foreground">
                        {" "}
                        ({issue.path})
                      </span>
                    )}
                  </div>
                ))
              )}

              <div className="pt-2">
                <Button
                  disabled={
                    blockingIssues.length > 0 ||
                    Object.keys(fieldErrors).length > 0
                  }
                  onClick={() =>
                    showSuccessToast(
                      "Prompt draft is semantically valid for save flow.",
                    )
                  }
                >
                  Validate Draft
                </Button>
              </div>
            </CardContent>
          </CollapsibleContent>
        </Collapsible>
      </Card>

      <div className="sticky bottom-0 z-20 border rounded-md bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 p-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-muted-foreground">
            {isDirty ? "Unsaved local changes" : "All local changes saved"}
          </p>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              disabled={!isDirty}
              onClick={onRevertToSaved}
            >
              Revert To Saved
            </Button>
            <Button
              disabled={!isDirty || !canSaveOrCommit}
              onClick={onSaveDraftLocal}
            >
              Save Draft (Local)
            </Button>
            <Button
              disabled={
                !selectedPromptConfigId ||
                !isDirty ||
                !canSaveOrCommit ||
                saveWorkingCopyMutation.isPending
              }
              onClick={saveToPromptConfig}
            >
              Save Working Copy
            </Button>
            <Button
              variant="secondary"
              disabled={
                !selectedPromptConfigId ||
                !canSaveOrCommit ||
                commitVersionMutation.isPending
              }
              onClick={commitPromptConfigVersion}
            >
              Commit Version
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
