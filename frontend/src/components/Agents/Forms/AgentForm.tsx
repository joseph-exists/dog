/**
 * AgentForm Component
 *
 * Shared form for creating and editing agents using React Hook Form + Zod.
 *
 * Features:
 * - Name and slug inputs (slug auto-generated on create)
 * - Description textarea with character count
 * - Provider selector (UserAccessProvider for credentials)
 * - Model selector (from LLM catalog)
 * - System prompt textarea with preview
 * - Participation mode selector
 *
 * Three-Way Binding Architecture:
 * ================================
 * UserAgentConfig requires three aligned components:
 *   1. user_access_provider (UUID) → WHERE + WITH WHAT (endpoint + credentials)
 *   2. provider_type (string)      → HOW (API format - necessary)
 *   3. model_name (string)         → WHAT (model identifier)
 *
 * This form manages all three, deriving provider_type from model_name.
 */

import { zodResolver } from "@hookform/resolvers/zod"
import { ChevronDownIcon } from "lucide-react"
import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import type { LLMProviderType } from "@/services/llmCatalogService"
import { parseProviderFromModelName } from "@/components/Agents/utils/modelParsing"
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

import {
  AgentService,
  type AgentViewModel,
  type ParticipationMode,
} from "@/services/agentService"
import { useLlmProviders } from "@/hooks/useLlmProviders"
import type { UserAccessProviderViewModel } from "@/services/userAccessProviderService"

// ============================================================================
// Constants
// ============================================================================

const PARTICIPATION_MODES = [
  {
    value: "on_mention",
    label: "say my name, sucker",
    description: "responds when @mentioned, this makes naming agents an interesting pain in the ass and this mechanic sucks",
  },
  {
    value: "always",
    label: "always talks",
    description: "responds to everything",
  },
  {
    value: "manual",
    label: "manual intervention required",
    description: "this might not work yet, but give it a shot and let me know",
  },
] as const

// ============================================================================
// Form Schema
// ============================================================================

/**
 * Zod validation schema for AgentForm
 *
 * Validation rules:
 * - name: Required, 1-100 characters
 * - slug: Required (auto-generated in create mode)
 * - description: Optional, max 500 characters
 * - model_name: Required (format: "provider:model" or just "model")
 * - system_prompt: Optional
 * - participation_mode: Required, one of the defined modes
 * - user_access_provider: Optional UUID
 *
 * Note: provider_type is derived from model_name, not a user input
 */
const agentFormSchema = z.object({
  name: z
    .string()
    .min(1, "gimme a name, pal")
    .max(100, "you're going to have to type this, you know."),
  slug: z.string().min(1, "Slug is required"),
  description: z.string().max(500, "Description must be 500 characters or less, you should complain about it, please"),
  model_name: z.string().min(1, "Model IS REQUIRED???"),
  system_prompt: z.string(),
  participation_mode: z.enum(["on_mention", "always", "manual"]),
  user_access_provider: z.string().nullable(),
})

type AgentFormValues = z.infer<typeof agentFormSchema>

// ============================================================================
// Exported Types
// ============================================================================

export interface AgentFormData {
  name: string
  slug: string
  description: string
  model_name: string
  system_prompt: string
  participation_mode: ParticipationMode
  provider_type: LLMProviderType
  user_access_provider: string | null
}

interface AgentFormProps {
  /** Initial values (for edit mode) */
  initialData?: Partial<AgentViewModel>
  /** Called when form data changes */
  onChange: (data: AgentFormData) => void
  /** Whether this is edit mode (affects slug editability) */
  isEditMode?: boolean
  /** Additional classes */
  className?: string
}

// ============================================================================
// Component
// ============================================================================

export default function AgentForm({
  initialData,
  onChange,
  isEditMode = false,
  className,
}: AgentFormProps) {
  // ==========================================================================
  // Form Setup
  // ==========================================================================

  const form = useForm<AgentFormValues>({
    resolver: zodResolver(agentFormSchema),
    mode: "onChange",
    defaultValues: {
      name: initialData?.name || "",
      slug: initialData?.slug || "",
      description: initialData?.description || "",
      model_name: initialData?.model_name || "gpt-4o-mini",
      system_prompt: initialData?.system_prompt || "",
      participation_mode: initialData?.participation_mode || "on_mention",
      user_access_provider: initialData?.user_access_provider ?? null,
    },
  })

  // ==========================================================================
  // Data Fetching
  // ==========================================================================

  const { providers, isLoading: providersLoading } = useLlmProviders()

  // ==========================================================================
  // Derived Values
  // ==========================================================================

  const selectedProviderId = form.watch("user_access_provider")
  const modelName = form.watch("model_name")
  const systemPrompt = form.watch("system_prompt")
  const description = form.watch("description")

  const selectedProvider =
    providers.find((p) => p.id === selectedProviderId) ?? null

  /**
   * Derive provider_type from ??? 
   *
   * Three-Way Binding Note:
   * The provider_type "openai"
   * It does NOT come from UserAccessProvider, which only stores credentials.
   */
  const derivedProviderType: LLMProviderType =
    parseProviderFromModelName(modelName) ?? "empty"

  // ==========================================================================
  // Auto-Generate Slug (Create Mode Only)
  // ==========================================================================

  useEffect(() => {
    if (isEditMode || form.getValues("slug")) return

    let isActive = true
    AgentService.generateSlug()
      .then((generatedSlug) => {
        if (isActive) {
          form.setValue("slug", generatedSlug, { shouldValidate: true })
        }
      })
      .catch(() => {
        // Silently fail - user can manually enter slug if needed
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
      if (!values.name || !values.slug) return

      onChange({
        name: values.name,
        slug: values.slug,
        description: values.description || "",
        model_name: values.model_name || "",
        system_prompt: values.system_prompt || "",
        participation_mode: values.participation_mode || "on_mention",
        provider_type: derivedProviderType,
        user_access_provider: values.user_access_provider ?? null,
      })
    })

    return () => subscription.unsubscribe()
  }, [form, onChange, derivedProviderType])

  // ==========================================================================
  // Handlers
  // ==========================================================================

  const handleProviderChange = (
    providerId: string | null,
    _provider: UserAccessProviderViewModel | null,
  ) => {
    form.setValue("user_access_provider", providerId, { shouldValidate: true })
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
                  {description.length}/500
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
            value={selectedProviderId}
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
                  value={field.value}
                  onChange={handleModelChange}
                  providerType={undefined}
                  placeholder="Select a model..."
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
                these are important later. but you can change them later, too.  don't sweat it too much. unless you want. if you understand them better than i do, you should write me a letter that tells me how smart you are.
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
