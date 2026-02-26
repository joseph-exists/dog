/**
 * AgentForm Component
 *
 * Complete form for creating and editing agent configurations.
 * Uses react-hook-form + zod for validation, ProviderModelSelector
 * for the compound provider+model selection concern.
 *
 * Sections:
 *   1. Identity — name, slug, description
 *   2. Provider & Model — ProviderModelSelector
 *   3. Prompts — system_prompt, custom_system_prompt, instructions
 *   4. Behavior — participation_mode, scope
 *   5. Settings — is_enabled, is_visible, is_clonable, is_coordinator, max_tool_iterations
 *   6. Advanced — capabilities, tool_config, presentation, deps_config, agent_metadata
 *
 * The parent component receives validated AgentFormData on submit and
 * is responsible for calling the API (create or update).
 */

import { zodResolver } from "@hookform/resolvers/zod"
import { ChevronDownIcon, Loader2 } from "lucide-react"
import { useCallback, useEffect, useRef, useState } from "react"
import { useForm } from "react-hook-form"

import { z } from "zod/v4"

import { AgentsService } from "@/client/sdk.gen"
import type {
  LLMModelPublic,
  UserAccessProviderPublic,
  UserAgentConfigPublic,
} from "@/client/types.gen"
import { Button } from "@/components/ui/button"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
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
import { Textarea } from "@/components/ui/textarea"
import { useAvailableThemes } from "@/hooks/useThemeRegistry"
import { cn } from "@/lib/utils"
import { ProviderModelSelector } from "./FormSelectors/ProviderModelSelector"

// ── Types ─────────────────────────────────────────────────────────────────

/**
 * What the form emits on submit.
 * Structurally compatible with Type1Create / Type3Create —
 * the parent casts provider_type to the literal UUID as needed.
 */
export type AgentFormData = {
  name: string
  slug: string
  description: string
  user_access_provider?: string | null
  provider_type: string
  model?: string | null
  model_id?: string | null
  model_name?: string
  system_prompt: string
  custom_system_prompt?: string | null
  agent_type: string
  instructions?: string | null
  is_enabled: boolean
  is_clonable: boolean
  is_visible: boolean
  scope: string
  participation_mode: string
  is_coordinator: boolean
  max_tool_iterations: number
  capabilities: string[]
  tool_config?: Record<string, unknown> | null
  deps_config?: Record<string, unknown> | null
  agent_metadata?: Record<string, unknown> | null
  presentation?: Record<string, unknown> | null
}

// ── Constants ─────────────────────────────────────────────────────────────

const PARTICIPATION_MODES = [
  {
    value: "on_mention",
    label: "On Mention",
    description: "Responds when @mentioned",
  },
  {
    value: "always",
    label: "Always",
    description: "Responds to every message",
  },
  {
    value: "manual",
    label: "Manual",
    description: "Only responds when explicitly invoked",
  },
] as const

const SCOPE_OPTIONS = [
  {
    value: "personal",
    label: "Personal",
    description: "Only you can use this agent",
  },
  {
    value: "system",
    label: "System",
    description: "Available to all users",
  },
] as const

const AGENT_TYPE_PRESENTATIONS = [
  {
    value: "advisor",
    label: "advisor",
    description: "advises with advisories",
  },
  {
    value: "creative",
    label: "creative",
    description: "creatively",
  },
  {
    value: "analyst",
    label: "analyst",
    description: "analytic analysis and analyses",
  },
  {
    value: "guardian",
    label: "guardian",
    description: "guarder that guards",
  },
  {
    value: "oracle",
    label: "oracle",
    description: "orally oracular",
  },
  {
    value: "engineer",
    label: "engineer",
    description: "engines the eers",
  },
] as const

// ── Schema ────────────────────────────────────────────────────────────────

const agentFormSchema = z.object({
  // Identity
  name: z.string().min(1, "Name is required").max(100, "Max 100 characters"),
  slug: z.string().min(1, "Slug is required"),
  description: z.string().max(500, "Max 500 characters"),

  // Provider & Model (managed outside zod, stored as hidden fields)
  user_access_provider: z.string().nullable(),
  provider_type: z.string().min(1, "Provider type is required"),
  model: z.string().nullable(),
  model_id: z.string().nullable(),
  model_name: z.string(),

  // Prompts
  system_prompt: z.string(),
  custom_system_prompt: z.string().nullable(),
  agent_type: z.string(),
  instructions: z.string().nullable(),

  // Behavior
  participation_mode: z.string(),
  scope: z.string(),

  // Settings
  is_enabled: z.boolean(),
  is_clonable: z.boolean(),
  is_visible: z.boolean(),
  is_coordinator: z.boolean(),
  max_tool_iterations: z.coerce.number().int().min(0).max(100),

  // Advanced (JSON strings — parsed via safeJsonParse in submit handler)
  capabilities_raw: z.string(),
  tool_config_raw: z.string(),
  deps_config_raw: z.string(),
  agent_metadata_raw: z.string(),
  presentation_raw: z.string(),
})

// type FormValues = z.infer<typeof agentFormSchema>
// we don't need to do this because we're using zodresolver

// ── Props ─────────────────────────────────────────────────────────────────

interface AgentFormProps {
  mode: "create" | "edit"
  /** Pre-populate for edit mode */
  defaultValues?: UserAgentConfigPublic
  /** Called with validated form data */
  onSubmit: (data: AgentFormData) => void | Promise<void>
  /** Disable form and show spinner on submit button */
  isSubmitting?: boolean
  /** Custom submit button text */
  submitLabel?: string
  className?: string
}

// ── Helpers ───────────────────────────────────────────────────────────────

function safeJsonStringify(val: unknown): string {
  if (val === null || val === undefined) return ""
  try {
    return JSON.stringify(val, null, 2)
  } catch {
    return ""
  }
}

function safeJsonParse(val: string | null): Record<string, unknown> | null {
  if (!val || val.trim() === "") return null
  try {
    return JSON.parse(val) as Record<string, unknown>
  } catch {
    return null
  }
}

// ── Presentation Section ──────────────────────────────────────────────────

interface PresentationSectionProps {
  presentationRaw: string
  onPresentationChange: (value: string) => void
  defaultPresentation?: Record<string, unknown>
}

function PresentationSection({
  presentationRaw,
  onPresentationChange,
  defaultPresentation,
}: PresentationSectionProps) {
  const { themes: cardThemes, isLoading } = useAvailableThemes("card")

  // Parse current presentation to get selected theme
  const currentPresentation = presentationRaw
    ? safeJsonParse(presentationRaw)
    : defaultPresentation

  const selectedCardThemeId = currentPresentation?.card_theme_id as
    | string
    | undefined

  const handleCardThemeChange = (themeId: string) => {
    // Merge with existing presentation data, preserving non-token fields
    const existing = presentationRaw
      ? (safeJsonParse(presentationRaw) ?? {})
      : {}

    if (themeId === "none") {
      // Clear theme: remove card_theme_id and all token overrides
      const { card_theme_id, tokens, ...rest } = existing as Record<
        string,
        unknown
      >
      onPresentationChange(
        Object.keys(rest).length > 0 ? JSON.stringify(rest, null, 2) : "",
      )
      return
    }

    // Find the selected theme and copy its tokens into presentation
    const selectedTheme = cardThemes.find((t) => t.id === themeId)
    if (!selectedTheme) return

    // Build updated presentation with theme tokens embedded
    const updated: Record<string, unknown> = {
      ...existing,
      card_theme_id: themeId,
      tokens: selectedTheme.tokens ?? {},
    }

    onPresentationChange(JSON.stringify(updated, null, 2))
  }

  return (
    <fieldset className="space-y-4">
      <legend className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
        Presentation
      </legend>

      <div className="space-y-2">
        <Label>Card Theme</Label>
        <Select
          value={selectedCardThemeId ?? "none"}
          onValueChange={handleCardThemeChange}
          disabled={isLoading}
        >
          <SelectTrigger>
            <SelectValue
              placeholder={
                isLoading ? "Loading themes..." : "Select card theme..."
              }
            />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">
              <div className="flex flex-col">
                <span>Default</span>
                <span className="text-xs text-muted-foreground">
                  Inherit from context
                </span>
              </div>
            </SelectItem>
            {cardThemes.map((theme) => (
              <SelectItem key={theme.id} value={theme.id}>
                <div className="flex flex-col">
                  <span>{theme.name}</span>
                  {theme.description && (
                    <span className="text-xs text-muted-foreground">
                      {theme.description}
                    </span>
                  )}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground">
          Visual theme applied to this agent's card appearance
        </p>
      </div>
    </fieldset>
  )
}

// ── Component ─────────────────────────────────────────────────────────────

export default function AgentForm({
  mode,
  defaultValues,
  onSubmit,
  isSubmitting = false,
  submitLabel,
  className,
}: AgentFormProps) {
  const isEdit = mode === "edit"
  const dv = defaultValues

  // ── Form Setup ──────────────────────────────────────────────────────────

  const form = useForm({
    resolver: zodResolver(agentFormSchema),
    mode: "onBlur",
    defaultValues: {
      name: dv?.name ?? "",
      slug: dv?.slug ?? "",
      description: dv?.description ?? "",
      user_access_provider: dv?.user_access_provider ?? null,
      provider_type: dv?.provider_type ?? "",
      model: dv?.model ?? null,
      model_id: dv?.model_id ?? null,
      model_name: dv?.model_name ?? "",
      system_prompt: dv?.system_prompt ?? "",
      custom_system_prompt: dv?.custom_system_prompt ?? null,
      agent_type: dv?.agent_type ?? "advisor",
      instructions: dv?.instructions ?? null,
      participation_mode: dv?.participation_mode ?? "on_mention",
      scope: dv?.scope ?? "personal",
      is_enabled: dv?.is_enabled ?? true,
      is_clonable: dv?.is_clonable ?? false,
      is_visible: dv?.is_visible ?? true,
      is_coordinator: dv?.is_coordinator ?? false,
      max_tool_iterations: dv?.max_tool_iterations ?? 10,
      capabilities_raw: dv?.capabilities?.join(", ") ?? "",
      tool_config_raw: safeJsonStringify(dv?.tool_config),
      deps_config_raw: safeJsonStringify(dv?.deps_config),
      agent_metadata_raw: safeJsonStringify(dv?.agent_metadata),
      presentation_raw: safeJsonStringify(dv?.presentation),
    },
  })

  // ── Slug Auto-Generation ────────────────────────────────────────────────

  const [isSlugLoading, setIsSlugLoading] = useState(false)
  const slugFetched = useRef(false)

  const fetchSlug = useCallback(async () => {
    if (isSlugLoading) return
    setIsSlugLoading(true)
    try {
      const generated = await AgentsService.generateAgentSlug()
      const slug =
        typeof generated === "string"
          ? generated
          : (generated as { slug?: string })?.slug
      if (slug) {
        form.setValue("slug", slug, { shouldValidate: true })
      }
    } catch (error) {
      console.error("Failed to generate slug:", error)
    } finally {
      setIsSlugLoading(false)
    }
  }, [form, isSlugLoading])

  useEffect(() => {
    if (isEdit || slugFetched.current || form.getValues("slug")) return
    slugFetched.current = true
    void fetchSlug()
  }, [isEdit, form, fetchSlug])

  // ── Provider/Model Callbacks ────────────────────────────────────────────

  const handleProviderChange = (providerId: string | null) => {
    form.setValue("user_access_provider", providerId, { shouldValidate: true })
  }

  const handleProviderResolved = (
    provider: UserAccessProviderPublic | null,
  ) => {
    if (provider?.alpha_provider_type_id) {
      form.setValue("provider_type", provider.alpha_provider_type_id, {
        shouldValidate: true,
      })
    }
  }

  const handleModelChange = (modelValue: string | null) => {
    // ModelCombobox onChange fires with model UUID
    form.setValue("model_id", modelValue, { shouldValidate: true })
  }

  const handleModelSelected = (model: LLMModelPublic | null) => {
    if (model) {
      form.setValue("model_name", model.model_id ?? model.display_name ?? "")
      form.setValue("model", model.model_id ?? null)
      form.setValue("model_id", model.id, { shouldValidate: true })
    } else {
      form.setValue("model_name", "")
      form.setValue("model", null)
      form.setValue("model_id", null)
    }
  }

  // ── Submit ──────────────────────────────────────────────────────────────

  const handleSubmit = form.handleSubmit(async (values) => {
    const capabilities = values.capabilities_raw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)

    const data: AgentFormData = {
      name: values.name,
      slug: values.slug,
      description: values.description,
      user_access_provider: values.user_access_provider || null,
      provider_type: values.provider_type,
      model: values.model || null,
      model_id: values.model_id || null,
      model_name: values.model_name || undefined,
      system_prompt: values.system_prompt,
      custom_system_prompt: values.custom_system_prompt || null,
      instructions: values.instructions || null,
      agent_type: values.agent_type,
      participation_mode: values.participation_mode,
      scope: values.scope,
      is_enabled: values.is_enabled,
      is_clonable: values.is_clonable,
      is_visible: values.is_visible,
      is_coordinator: values.is_coordinator,
      max_tool_iterations: values.max_tool_iterations,
      capabilities,
      tool_config: safeJsonParse(values.tool_config_raw),
      deps_config: safeJsonParse(values.deps_config_raw),
      agent_metadata: safeJsonParse(values.agent_metadata_raw),
      presentation: safeJsonParse(values.presentation_raw),
    }

    await onSubmit(data)
  })

  // ── Watched Values ──────────────────────────────────────────────────────

  const description = form.watch("description")
  const systemPrompt = form.watch("system_prompt")
  const customSystemPrompt = form.watch("custom_system_prompt")
  const instructions = form.watch("instructions")

  // ── Render ──────────────────────────────────────────────────────────────

  return (
    <Form {...form}>
      <form onSubmit={handleSubmit} className={cn("space-y-8", className)}>
        {/* ════════════════════════════════════════════════════════════════
            Section 1: Identity
            ════════════════════════════════════════════════════════════════ */}
        <fieldset className="space-y-4">
          <legend className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
            Identity
          </legend>

          {/* Name */}
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>
                  Name <span className="text-destructive">*</span>
                </FormLabel>
                <FormControl>
                  <Input {...field} placeholder="Agent name" maxLength={100} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {/* Slug */}
          <div className="space-y-2">
            <div className="flex items-center justify-between gap-3">
              <Label className="flex items-center gap-2">
                Slug
                <span className="text-xs text-muted-foreground">(auto)</span>
              </Label>
              {!isEdit && (
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => void fetchSlug()}
                  disabled={isSlugLoading}
                >
                  {isSlugLoading ? "Regenerating..." : "Regenerate"}
                </Button>
              )}
            </div>
            <p className="text-sm font-mono text-muted-foreground px-3 py-2 rounded-md bg-muted">
              {form.watch("slug") ? `@${form.watch("slug")}` : "Generating..."}
            </p>
          </div>

          {/* Description */}
          <FormField
            control={form.control}
            name="description"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Description</FormLabel>
                <FormControl>
                  <Textarea
                    {...field}
                    placeholder="What does this agent do?"
                    maxLength={500}
                    className="min-h-[80px]"
                  />
                </FormControl>
                <div className="flex justify-end">
                  <span className="text-xs text-muted-foreground">
                    {description?.length ?? 0}/500
                  </span>
                </div>
                <FormMessage />
              </FormItem>
            )}
          />
        </fieldset>

        {/* ════════════════════════════════════════════════════════════════
            Section 2: Provider & Model
            ════════════════════════════════════════════════════════════════ */}
        <fieldset className="space-y-4">
          <legend className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
            Provider &amp; Model
          </legend>

          <ProviderModelSelector
            providerId={form.watch("user_access_provider")}
            modelName={form.watch("model_id")}
            agentDefaultModel={dv?.model_name ?? ""}
            onProviderChange={handleProviderChange}
            onModelChange={handleModelChange}
            onModelSelected={handleModelSelected}
            onProviderResolved={handleProviderResolved}
          />

          {/* Hidden provider_type validation error */}
          <FormField
            control={form.control}
            name="provider_type"
            render={() => (
              <FormItem className="hidden">
                <FormMessage />
              </FormItem>
            )}
          />
        </fieldset>

        {/* ════════════════════════════════════════════════════════════════
            Section 3: Prompts
            ════════════════════════════════════════════════════════════════ */}
        <fieldset className="space-y-4">
          <legend className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
            Prompts
          </legend>

          {/* System Prompt */}
          <FormField
            control={form.control}
            name="system_prompt"
            render={({ field }) => (
              <FormItem>
                <FormLabel>System Prompt</FormLabel>
                <FormControl>
                  <Textarea
                    {...field}
                    placeholder="You are a helpful assistant..."
                    className="min-h-[150px] font-mono text-sm"
                  />
                </FormControl>
                {systemPrompt && (
                  <Collapsible>
                    <CollapsibleTrigger className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors">
                      <ChevronDownIcon className="size-3" />
                      Preview ({systemPrompt.length} chars)
                    </CollapsibleTrigger>
                    <CollapsibleContent>
                      <div className="mt-2 p-3 rounded-md bg-muted text-sm whitespace-pre-wrap max-h-[200px] overflow-y-auto">
                        {systemPrompt}
                      </div>
                    </CollapsibleContent>
                  </Collapsible>
                )}
                <FormMessage />
              </FormItem>
            )}
          />

          {/* Custom System Prompt Override */}
          <FormField
            control={form.control}
            name="custom_system_prompt"
            render={({ field }) => (
              <FormItem>
                <Collapsible>
                  <CollapsibleTrigger className="flex items-center gap-1 text-sm font-medium hover:text-foreground transition-colors">
                    <ChevronDownIcon className="size-3" />
                    Custom System Prompt Override
                    {customSystemPrompt && (
                      <span className="text-xs text-muted-foreground ml-1">
                        ({customSystemPrompt.length} chars)
                      </span>
                    )}
                  </CollapsibleTrigger>
                  <CollapsibleContent className="pt-2">
                    <FormControl>
                      <Textarea
                        {...field}
                        value={field.value ?? ""}
                        placeholder="Override the system prompt for this agent instance..."
                        className="min-h-[100px] font-mono text-sm"
                      />
                    </FormControl>
                    <FormDescription>
                      If set, replaces the system prompt entirely for this
                      agent.
                    </FormDescription>
                  </CollapsibleContent>
                </Collapsible>
                <FormMessage />
              </FormItem>
            )}
          />

          {/* Instructions */}
          <FormField
            control={form.control}
            name="instructions"
            render={({ field }) => (
              <FormItem>
                <Collapsible>
                  <CollapsibleTrigger className="flex items-center gap-1 text-sm font-medium hover:text-foreground transition-colors">
                    <ChevronDownIcon className="size-3" />
                    Instructions
                    {instructions && (
                      <span className="text-xs text-muted-foreground ml-1">
                        ({instructions.length} chars)
                      </span>
                    )}
                  </CollapsibleTrigger>
                  <CollapsibleContent className="pt-2">
                    <FormControl>
                      <Textarea
                        {...field}
                        value={field.value ?? ""}
                        placeholder="Additional instructions appended to context..."
                        className="min-h-[120px] font-mono text-sm"
                      />
                    </FormControl>
                    <FormDescription>
                      Supplementary context or rules. Does not replace the
                      system prompt.
                    </FormDescription>
                  </CollapsibleContent>
                </Collapsible>
                <FormMessage />
              </FormItem>
            )}
          />
        </fieldset>

        {/* ════════════════════════════════════════════════════════════════
            Section 4: Behavior
            ════════════════════════════════════════════════════════════════ */}
        <fieldset className="space-y-4">
          <legend className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
            Behavior
          </legend>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Participation Mode */}
            <FormField
              control={form.control}
              name="participation_mode"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Participation Mode</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select mode..." />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {PARTICIPATION_MODES.map((mode) => (
                        <SelectItem key={mode.value} value={mode.value}>
                          <div className="flex flex-col">
                            <span>{mode.label}</span>
                            <span className="text-xs text-muted-foreground">
                              {mode.description}
                            </span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            {/* Agent Type */}
            <FormField
              control={form.control}
              name="agent_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Agent Type</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select agent type..." />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {AGENT_TYPE_PRESENTATIONS.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          <div className="flex flex-col">
                            <span>{opt.label}</span>
                            <span className="text-xs text-muted-foreground">
                              {opt.description}
                            </span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            {/* Scope */}
            <FormField
              control={form.control}
              name="scope"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Scope</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select scope..." />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {SCOPE_OPTIONS.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          <div className="flex flex-col">
                            <span>{opt.label}</span>
                            <span className="text-xs text-muted-foreground">
                              {opt.description}
                            </span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
        </fieldset>

        {/* ════════════════════════════════════════════════════════════════
            Section 5: Presentation
            ════════════════════════════════════════════════════════════════ */}
        <PresentationSection
          presentationRaw={form.watch("presentation_raw")}
          onPresentationChange={(value) =>
            form.setValue("presentation_raw", value, { shouldValidate: true })
          }
          defaultPresentation={
            dv?.presentation as Record<string, unknown> | undefined
          }
        />

        {/* ════════════════════════════════════════════════════════════════
            Section 6: Settings
            ════════════════════════════════════════════════════════════════ */}
        <fieldset className="space-y-4">
          <legend className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
            Settings
          </legend>

          <div className="space-y-3">
            {/* is_enabled */}
            <FormField
              control={form.control}
              name="is_enabled"
              render={({ field }) => (
                <FormItem className="flex items-center justify-between rounded-lg border p-3">
                  <div className="space-y-0.5">
                    <FormLabel className="text-sm">Enabled</FormLabel>
                    <FormDescription className="text-xs">
                      Agent is active and can participate in rooms
                    </FormDescription>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            {/* is_visible */}
            <FormField
              control={form.control}
              name="is_visible"
              render={({ field }) => (
                <FormItem className="flex items-center justify-between rounded-lg border p-3">
                  <div className="space-y-0.5">
                    <FormLabel className="text-sm">Visible</FormLabel>
                    <FormDescription className="text-xs">
                      Appears in agent lists and search
                    </FormDescription>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            {/* is_clonable */}
            <FormField
              control={form.control}
              name="is_clonable"
              render={({ field }) => (
                <FormItem className="flex items-center justify-between rounded-lg border p-3">
                  <div className="space-y-0.5">
                    <FormLabel className="text-sm">Clonable</FormLabel>
                    <FormDescription className="text-xs">
                      Other users can clone this agent's configuration
                    </FormDescription>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            {/* is_coordinator */}
            <FormField
              control={form.control}
              name="is_coordinator"
              render={({ field }) => (
                <FormItem className="flex items-center justify-between rounded-lg border p-3">
                  <div className="space-y-0.5">
                    <FormLabel className="text-sm">Coordinator</FormLabel>
                    <FormDescription className="text-xs">
                      Can orchestrate other agents in multi-agent rooms
                    </FormDescription>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            {/* max_tool_iterations */}
            <FormField
              control={form.control}
              name="max_tool_iterations"
              render={({ field }) => (
                <FormItem className="flex items-center justify-between rounded-lg border p-3">
                  <div className="space-y-0.5">
                    <FormLabel className="text-sm">
                      Max Tool Iterations
                    </FormLabel>
                    <FormDescription className="text-xs">
                      Maximum tool call loops per turn (0–100)
                    </FormDescription>
                  </div>
                  <FormControl>
                    <Input
                      type="number"
                      min={0}
                      max={100}
                      className="w-20 text-center"
                      {...field}
                      value={Number(field.value)}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
        </fieldset>

        {/* ════════════════════════════════════════════════════════════════
            Section 7: Advanced
            ════════════════════════════════════════════════════════════════ */}
        <Collapsible>
          <CollapsibleTrigger className="flex items-center gap-2 text-sm font-medium text-muted-foreground uppercase tracking-wider hover:text-foreground transition-colors">
            <ChevronDownIcon className="size-4" />
            Advanced Configuration
          </CollapsibleTrigger>

          <CollapsibleContent className="pt-4 space-y-4">
            {/* Capabilities */}
            <FormField
              control={form.control}
              name="capabilities_raw"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Capabilities</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      placeholder="web_search, code_execution, file_upload"
                    />
                  </FormControl>
                  <FormDescription>
                    Comma-separated list of capability identifiers
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Tool Config */}
            <FormField
              control={form.control}
              name="tool_config_raw"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tool Config</FormLabel>
                  <FormControl>
                    <Textarea
                      {...field}
                      placeholder='{"tools": []}'
                      className="min-h-[100px] font-mono text-sm"
                    />
                  </FormControl>
                  <FormDescription>
                    JSON object for tool configuration
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            {/* Presentation Config */}
            <FormField
              control={form.control}
              name="presentation_raw"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Presentation Config</FormLabel>
                  <FormControl>
                    <Textarea
                      {...field}
                      placeholder='{"presentation": []}'
                      className="min-h-[100px] font-mono text-sm"
                    />
                  </FormControl>
                  <FormDescription>
                    JSON object for presentation configuration
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Deps Config */}
            <FormField
              control={form.control}
              name="deps_config_raw"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Dependencies Config</FormLabel>
                  <FormControl>
                    <Textarea
                      {...field}
                      placeholder='{"dependencies": {}}'
                      className="min-h-[100px] font-mono text-sm"
                    />
                  </FormControl>
                  <FormDescription>
                    JSON object for dependency injection configuration
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Agent Metadata */}
            <FormField
              control={form.control}
              name="agent_metadata_raw"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Agent Metadata</FormLabel>
                  <FormControl>
                    <Textarea
                      {...field}
                      placeholder='{"key": "value"}'
                      className="min-h-[100px] font-mono text-sm"
                    />
                  </FormControl>
                  <FormDescription>
                    Arbitrary JSON metadata stored with the agent
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CollapsibleContent>
        </Collapsible>

        {/* ════════════════════════════════════════════════════════════════
            Submit
            ════════════════════════════════════════════════════════════════ */}
        <Button
          type="submit"
          disabled={isSubmitting}
          className="w-full sm:w-auto"
        >
          {isSubmitting && <Loader2 className="size-4 animate-spin mr-2" />}
          {submitLabel ?? (isEdit ? "Save Changes" : "Create Agent")}
        </Button>
      </form>
    </Form>
  )
}
