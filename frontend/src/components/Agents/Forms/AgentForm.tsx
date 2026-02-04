/**
 * AgentForm Component
 *
 * Shared form for creating and editing agents using React Hook Form + Zod.
 *
 * Features:
 * - Name input, slug display with auto-generation
 * - Description textarea
 * - UserAccessProvider selector (for credentials)
 * - Model selector
 * - System prompt textarea with preview
 * - Participation mode selector
 */

import { zodResolver } from "@hookform/resolvers/zod"
import { useQuery } from "@tanstack/react-query"
import { ChevronDownIcon } from "lucide-react"
import { useCallback, useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { AgentsService, LlmProvidersService } from "@/client/sdk.gen"
import type {
  UserAccessProviderPublic,
  Type3Create,
  // Type3 is openai_compatible creation model - this allows us faster proof of concept and less munging about
  // TODO: add Type1Create (and others) as exported from "@/client/types.gen"
  // this is the switch between types (openai, anthropic, openai_compatible that enables creating user agent config forms tailored specifically to those models with field validators)
} from "@/client/types.gen"
import ModelCombobox from "@/components/Agents/Selectors/ModelCombobox"
import { ProviderSelect } from "../Selectors/ProviderSelect"

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
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

// ============================================================================
// Constants
// ============================================================================

const PARTICIPATION_MODES = [
  {
    value: "on_mention",
    label: "say my name, sucker",
    description:
      "responds when @mentioned, this makes naming agents an interesting pain in the ass and this mechanic sucks",
  },
  {
    value: "always",
    label: "always talks",
    description: "responds to everything",
  },
  {
    value: "manual",
    label: "manual intervention required",
    description:
      "this might not work yet, but give it a shot and let me know",
  },
] as const

// ============================================================================
// Form Schema
// ============================================================================

/**
 * Zod validation schema for AgentForm
 *
 * Based on UserAgentConfigCreate from the exported client types
 */
const agentFormSchema = z.object({
  name: z
    .string()
    .min(1, "Name is required")
    .max(100, "Name must be 100 characters or less"),
  slug: z.string().min(1, "Slug is required"),
  description: z
    .string()
    .max(500, "Description must be 500 characters or less")
    .optional(),
  model_id: z.string().optional(),
  user_access_provider: z.string().nullable().optional(),
  provider_type: z.string().min(1, "Provider type is required"),
  model_name: z.string().optional(),
  system_prompt: z.string().optional(),
  participation_mode: z.string().optional(),
})

type AgentFormValues = z.infer<typeof agentFormSchema>

export type AgentFormData = {
  name: string
  slug: string
  description: string
  model_id: string
  model_name: string
  system_prompt: string
  participation_mode: string
  provider_type: string
  user_access_provider?: string | null
}

// ============================================================================
// Component Props
// ============================================================================

interface AgentFormProps {
  /** Whether this is editing an existing agent or creating a new one */
  isEditMode?: boolean
  /** Initial values for edit mode */
  initialValues?: Partial<Type3Create>
  /** Legacy prop name kept for compatibility */
  initialData?: Partial<Type3Create>
  /** Callback when form values change */
  onChange: (values: AgentFormData) => void
  /** Optional className for styling */
  className?: string
}

// ============================================================================
// Component
// ============================================================================

export default function AgentForm({
  isEditMode = false,
  initialValues,
  initialData,
  onChange,
  className,
}: AgentFormProps) {
  // ==========================================================================
  // Form Setup
  // ==========================================================================

  const defaults = initialValues ?? initialData

  const form = useForm<AgentFormValues>({
    resolver: zodResolver(agentFormSchema),
    mode: "onChange",
    defaultValues: {
      name: defaults?.name || "",
      slug: defaults?.slug || "",
      description: defaults?.description || "",
      user_access_provider: defaults?.user_access_provider || undefined,
      provider_type: defaults?.provider_type || "",
      model_id: defaults?.model_id || "",
      model_name: defaults?.model_name || "",
      system_prompt: defaults?.system_prompt || "",
      participation_mode: defaults?.participation_mode || "on_mention",
    },
  })

  // ==========================================================================
  // Data Fetching
  // ==========================================================================

  const { data: providersResponse, isLoading: providersLoading } = useQuery({
    queryKey: ["llm-providers"],
    queryFn: () => LlmProvidersService.listProviders(),
  })

  const providers: UserAccessProviderPublic[] =
    providersResponse?.data || []

  // ==========================================================================
  // Derived Values
  // ==========================================================================

  const selectedProviderId = form.watch("user_access_provider")
  const systemPrompt = form.watch("system_prompt")
  const description = form.watch("description")
  const providerTypeWatch = form.watch("provider_type")
  const selectedProvider =
    providers.find((p) => p.id === selectedProviderId) ?? null
  // ModelCombobox filters on provider type (not provider id), so pass alpha_provider_type_id when available.
  const providerTypeFilter =
    selectedProvider?.alpha_provider_type_id || providerTypeWatch || undefined

  // ==========================================================================
  // Auto-Generate Slug (Create Mode Only)
  // ==========================================================================

  const [isSlugLoading, setIsSlugLoading] = useState(false)

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
    if (isEditMode || form.getValues("slug")) return
    void fetchSlug()
  }, [isEditMode, form, fetchSlug])

  // ==========================================================================
  // Notify Parent of Changes
  // ==========================================================================

  useEffect(() => {
    const subscription = form.watch((values) => {
      // Only notify if we have all required values
      if (!values.name || !values.slug || !values.provider_type) return

      // Get provider_type from selected provider or use existing value
      const providerType =
        selectedProvider?.alpha_provider_type_id || values.provider_type

      onChange({
        name: values.name,
        slug: values.slug,
        description: values.description || "",
        model_id: values.model_id || "",
        model_name: values.model_name || "",
        system_prompt: values.system_prompt || "",
        participation_mode: values.participation_mode || "on_mention",
        user_access_provider: values.user_access_provider,
        provider_type: providerType,
      })
    })

    return () => subscription.unsubscribe()
  }, [form, onChange, selectedProvider])

  // ==========================================================================
  // Handlers
  // ==========================================================================

  const handleProviderChange = (
    providerId: string | null,
    provider: UserAccessProviderPublic | null,
  ) => {
    form.setValue("user_access_provider", providerId ?? undefined, {
      shouldValidate: true,
    })

    // Update provider_type when provider changes
    if (provider?.alpha_provider_type_id) {
      form.setValue("provider_type", provider.alpha_provider_type_id, {
        shouldValidate: true,
      })
    }
  }

  const handleModelChange = (modelId: string, modelName?: string) => {
    form.setValue("model_id", modelId, { shouldValidate: true })
    if (modelName) {
      form.setValue("model_name", modelName, { shouldValidate: true })
    }
  }

  // ==========================================================================
  // Render
  // ==========================================================================

  return (
    <Form {...form}>
      <div className={cn("space-y-6", className)}>
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
                <Input
                  {...field}
                  placeholder="Crankypants"
                  maxLength={100}
                />
              </FormControl>
              <FormDescription>display Name</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Slug (read-only, auto-generated) */}
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-3">
            <Label className="flex items-center gap-2">
              Slug
              <span className="text-xs text-muted-foreground">(auto)</span>
            </Label>
            {!isEditMode && (
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
          <p className="text-xs text-muted-foreground">
            Auto-generated unique identifier
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
                  placeholder="this is mostly display at this point, you can use this for notes... might change."
                  maxLength={500}
                  className="min-h-[80px]"
                />
              </FormControl>
              <div className="flex justify-end">
                <p className="text-xs text-muted-foreground">
                  {description?.length || 0}/500
                </p>
              </div>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Provider Selector */}
        <div className="space-y-2">
          <Label htmlFor="agent-provider">Provider</Label>
          <ProviderSelect
            value={selectedProviderId ?? null}
            providers={providers}
            isLoading={providersLoading}
            onChange={handleProviderChange}
          />
          <p className="text-xs text-muted-foreground">
            {selectedProvider
              ? `Using your "${selectedProvider.name}" credentials`
              : "Select a provider to use your own API credentials"}
          </p>
        </div>

        {/* Model Selector */}
        <FormField
          control={form.control}
          name="model_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>
                Model <span className="text-destructive">*</span>
              </FormLabel>
          <FormControl>
            <ModelCombobox
              value={field.value ?? ""}
              onChange={(id) => handleModelChange(id)}
              onModelSelected={(model) =>
                handleModelChange(
                  // agents endpoint expects UUID from models.id
                  (model as any)?.id || model?.model_id || "",
                  model?.model_id || model?.display_name || "",
                )
              }
              providerType={providerTypeFilter}
            />
          </FormControl>
              <FormDescription>
                {selectedProvider
                  ? `Using credentials from "${selectedProvider.name}"`
                  : "All catalog models (default credentials will be used)"}
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

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
                  placeholder="You are a thing that things things.  Enjoy your existence, you thing-thinging thing."
                  className="min-h-[150px] font-mono text-sm"
                />
              </FormControl>

              {/* Collapsible Preview */}
              {systemPrompt && (
                <Collapsible>
                  <CollapsibleTrigger className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors">
                    <ChevronDownIcon className="size-3" />
                    Preview rendered prompt ({systemPrompt.length} chars)
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    <div className="mt-2 p-3 rounded-md bg-muted text-sm whitespace-pre-wrap max-h-[200px] overflow-y-auto">
                      {systemPrompt}
                    </div>
                  </CollapsibleContent>
                </Collapsible>
              )}

              <FormDescription>
                these are important later. but you can change them later, too.
                don't sweat it too much. unless you want. if you understand them
                better than i do, you should write me a letter that tells me how
                smart you are.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

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
                    <SelectValue placeholder="MODUS OPERANDI (default state for your little buddy. you can change it later.)" />
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
      </div>
    </Form>
  )
}

// Export constants for reuse
export { PARTICIPATION_MODES }
