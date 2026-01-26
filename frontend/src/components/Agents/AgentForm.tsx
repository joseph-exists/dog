/**
 * AgentForm Component
 *
 * Shared form for creating and editing agents.
 * Features:
 * - Name and slug inputs (slug auto-generated on create)
 * - Description textarea
 * - Model selector dropdown (populated from LLM catalog)
 * - System prompt textarea with character count
 * - Participation mode selector
 */

import { useQuery } from "@tanstack/react-query"
import { ChevronDownIcon } from "lucide-react"
import { useCallback, useEffect, useState } from "react"

import {
  AgentProviderBadge,
  parseProviderFromModelName,
  type LLMProviderType as AgentBadgeLLMProviderType,
} from "@/components/Agents/AgentBadge"
import { ProviderSelect } from "./ProviderSelect"
import ModelCombobox from "@/components/Agents/providers/ModelCombobox"
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
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import type { LLMProviderType } from "@/client"
import {
  AgentService,
  type AgentViewModel,
  type ParticipationMode,
} from "@/services/agentService"
import {
  LlmProviderService,
  LLM_PROVIDER_QUERY_KEYS,
  type ProviderViewModel,
} from "@/services/llmProviderService"

// Participation modes
const PARTICIPATION_MODES = [
  {
    value: "on_mention",
    label: "On Mention",
    description: "Responds when @mentioned",
  },
  {
    value: "always",
    label: "Always Active",
    description: "Responds to all messages",
  },
  {
    value: "manual",
    label: "Manual",
    description: "Only responds when explicitly triggered",
  },
] as const

export interface AgentFormData {
  name: string
  slug: string
  description: string
  model_name: string
  system_prompt: string
  participation_mode: ParticipationMode
  // Provider selection fields
  provider_type: LLMProviderType // "openai" | "anthropic" | "google" | "openai_compatible" | "empty"
  user_provider: string | null // UUID of user's provider, or null
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

export default function AgentForm({
  initialData,
  onChange,
  isEditMode = false,
  className,
}: AgentFormProps) {
  const [name, setName] = useState(initialData?.name || "")
  const [slug, setSlug] = useState(initialData?.slug || "")
  const [description, setDescription] = useState(initialData?.description || "")
  const [modelName, setModelName] = useState(
    initialData?.model_name || "openai:gpt-4o-mini",
  )
  const [systemPrompt, setSystemPrompt] = useState(
    initialData?.system_prompt || "",
  )
  const [participationMode, setParticipationMode] = useState<ParticipationMode>(
    initialData?.participation_mode || "on_mention",
  )

  // Provider selection state
  const [selectedProviderId, setSelectedProviderId] = useState<string | null>(
    initialData?.user_provider ?? null
  )

  // Fetch user's configured providers
  const { data: providersData, isLoading: providersLoading } = useQuery({
    queryKey: LLM_PROVIDER_QUERY_KEYS.providers,
    queryFn: () => LlmProviderService.listProviders(),
  })

  const providers = providersData?.providers ?? []

  // Find selected provider object for derived values
  const selectedProvider = providers.find((p) => p.id === selectedProviderId) ?? null

  // Derive provider_type from selection (or "empty" if none)
  const derivedProviderType: LLMProviderType = selectedProvider?.provider_type ?? "empty"

  /**
   * Handle provider selection change.
   * Resets model if incompatible with new provider type.
   */
  const handleProviderChange = useCallback(
    (providerId: string | null, provider: ProviderViewModel | null) => {
      setSelectedProviderId(providerId)

      // Reset model if incompatible with new provider
      if (provider) {
        const currentModelProviderType = parseProviderFromModelName(modelName)
        if (currentModelProviderType && currentModelProviderType !== provider.provider_type) {
          setModelName("") // Reset - user must re-select
        }
      }
      // If provider cleared (null), keep model (aspirational selection)
    },
    [modelName]
  )

  // Auto-generate slug from backend (only in create mode)
  useEffect(() => {
    if (isEditMode || slug) return

    let isActive = true
    AgentService.generateSlug()
      .then((generatedSlug) => {
        if (isActive) setSlug(generatedSlug)
      })
      .catch(() => {})

    return () => {
      isActive = false
    }
  }, [isEditMode, slug])

  // Notify parent of changes
  useEffect(() => {
    onChange({
      name,
      slug,
      description,
      model_name: modelName,
      system_prompt: systemPrompt,
      participation_mode: participationMode,
      provider_type: derivedProviderType,
      user_provider: selectedProviderId,
    })
  }, [
    name,
    slug,
    description,
    modelName,
    systemPrompt,
    participationMode,
    derivedProviderType,
    selectedProviderId,
    onChange,
  ])

  return (
    <div className={cn("space-y-6", className)}>
      {/* Name */}
      <div className="space-y-2">
        <Label htmlFor="agent-name">
          Name <span className="text-destructive">*</span>
        </Label>
        <Input
          id="agent-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="My Helpful Agent"
          maxLength={100}
        />
        <p className="text-xs text-muted-foreground">
          Display name for your agent
        </p>
      </div>

      {/* Slug (read-only, auto-generated by backend) */}
      <div className="space-y-2">
        <Label>Slug</Label>
        <p className="text-sm font-mono text-muted-foreground px-3 py-2 rounded-md bg-muted">
          {slug ? `@${slug}` : "Generating..."}
        </p>
      </div>

      {/* Description */}
      <div className="space-y-2">
        <Label htmlFor="agent-description">Description</Label>
        <Textarea
          id="agent-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe what this agent does..."
          maxLength={500}
          className="min-h-[80px]"
        />
        <p className="text-xs text-muted-foreground text-right">
          {description.length}/500
        </p>
      </div>

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
      <div className="space-y-2">
        <Label htmlFor="agent-model">Model</Label>
        {selectedProvider && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Filtered to:</span>
            <AgentProviderBadge providerType={selectedProvider.provider_type as AgentBadgeLLMProviderType} />
          </div>
        )}
        <ModelCombobox
          value={modelName}
          onChange={setModelName}
          providerType={selectedProvider?.provider_type}
          placeholder="Select a model..."
        />
        <p className="text-xs text-muted-foreground">
          {selectedProvider
            ? `Models compatible with ${selectedProvider.display_type}`
            : "All catalog models (select a provider to filter)"}
        </p>
      </div>

      {/* System Prompt */}
      <div className="space-y-2">
        <Label htmlFor="agent-prompt">System Prompt</Label>
        <Textarea
          id="agent-prompt"
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
          placeholder="You are a helpful assistant that..."
          className="min-h-[150px] font-mono text-sm"
        />

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

        <p className="text-xs text-muted-foreground">
          Instructions that define your agent's personality and behavior
        </p>
      </div>

      {/* Participation Mode */}
      <div className="space-y-2">
        <Label htmlFor="agent-mode">Participation Mode</Label>
        <Select
          value={participationMode}
          onValueChange={(v) => setParticipationMode(v as ParticipationMode)}
        >
          <SelectTrigger id="agent-mode" className="w-full">
            <SelectValue placeholder="Select mode" />
          </SelectTrigger>
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
      </div>
    </div>
  )
}

// Export constants for reuse
export { PARTICIPATION_MODES }
