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
import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { AgentsService, LlmProvidersService } from "@/client/sdk.gen"
import type {
  UserAccessProviderPublic,
  UserAgentConfigCreate,
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
  user_access_provider: z.string().nullable().optional(),
  provider_type_id: z.string().min(1, "Provider type is required"),
  model_name: z.string().optional(),
  system_prompt: z.string().optional(),
  participation_mode: z.string().optional(),
})

type AgentFormValues = z.infer<typeof agentFormSchema>

// ============================================================================
// Component Props
// ============================================================================

interface AgentFormProps {
  /** Whether this is editing an existing agent or creating a new one */
  isEditMode?: boolean
  /** Initial values for edit mode */
  initialValues?: Partial<UserAgentConfigCreate>
  /** Callback when form values change */
  onChange: (values: Partial<UserAgentConfigCreate>) => void
  /** Optional className for styling */
  className?: string
}

// ============================================================================
// Component
// ============================================================================

export default function AgentForm({
  isEditMode = false,
  initialValues,
  onChange,
  className,
}: AgentFormProps) {
  // ==========================================================================
  // Form Setup
  // ==========================================================================

  const form = useForm<AgentFormValues>({
    resolver: zodResolver(agentFormSchema),
    mode: "onChange",
    defaultValues: {
      name: initialValues?.name || "",
      slug: initialValues?.slug || "",
      description: initialValues?.description || "",
      user_access_provider: initialValues?.user_access_provider || undefined,
      provider_type_id: initialValues?.provider_type_id || "",
      model_name: initialValues?.model_name || "",
      system_prompt: initialValues?.system_prompt || "",
      participation_mode: initialValues?.participation_mode || "on_mention",
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
  const selectedProvider =
    providers.find((p) => p.id === selectedProviderId) ?? null

  // ==========================================================================
  // Auto-Generate Slug (Create Mode Only)
  // ==========================================================================

  useEffect(() => {
    if (isEditMode || form.getValues("slug")) return

    let isActive = true
    AgentsService.generateAgentSlug()
      .then((generatedSlug) => {
        if (isActive && typeof generatedSlug === "string") {
          form.setValue("slug", generatedSlug, { shouldValidate: true })
        }
      })
      .catch((error) => {
        console.error("Failed to generate slug:", error)
        // TODO: Add retry mechanism or user notification
      })

    return () => {
      isActive = false
    }
  }, [isEditMode, form])

  // ==========================================================================
  // Notify Parent of Changes
  // ==========================================================================

  useEffect(() => {
    const subscription = form.watch((values) => {
      // Only notify if we have all required values
      if (!values.name || !values.slug || !values.provider_type_id) return

      // Get provider_type_id from selected provider or use existing value
      const providerTypeId =
        selectedProvider?.alpha_provider_type_id || values.provider_type_id

      onChange({
        name: values.name,
        slug: values.slug,
        description: values.description || "",
        model_name: values.model_name || "",
        system_prompt: values.system_prompt || "",
        participation_mode: values.participation_mode || "on_mention",
        user_access_provider: values.user_access_provider,
        provider_type_id: providerTypeId,
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

    // Update provider_type_id when provider changes
    if (provider?.alpha_provider_type_id) {
      form.setValue("provider_type_id", provider.alpha_provider_type_id, {
        shouldValidate: true,
      })
    }
  }

  const handleModelChange = (newModelName: string) => {
    form.setValue("model_name", newModelName, { shouldValidate: true })
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
          <Label>Slug</Label>
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
          name="model_name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>
                Model <span className="text-destructive">*</span>
              </FormLabel>
              <FormControl>
                <ModelCombobox
                  value={field.value ?? ""}
                  onChange={handleModelChange}
                  providerType={undefined}
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
