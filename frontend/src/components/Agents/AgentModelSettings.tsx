/**
 * Agent Model Settings
 *
 * Allows users to customize which model and provider an agent uses.
 * Users can override the agent's default model and select their own API key.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Bot, Key, Loader2, RotateCcw } from "lucide-react"

import { AgentsService, LlmProvidersService } from "@/client"
import type { UserLLMProviderPublic } from "@/client/types.gen"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import useCustomToast from "@/hooks/useCustomToast"
import { cn } from "@/lib/utils"

// Supported models organized by provider type
// Must match backend SUPPORTED_MODELS in models.py
const SUPPORTED_MODELS = {
  openai: [
    { value: "openai:gpt-4o", label: "GPT-4o", description: "Latest multimodal flagship" },
    { value: "openai:gpt-4o-mini", label: "GPT-4o Mini", description: "Fast and affordable" },
    { value: "openai:gpt-4-turbo", label: "GPT-4 Turbo", description: "Previous generation flagship" },
    { value: "openai:gpt-3.5-turbo", label: "GPT-3.5 Turbo", description: "Fast, economical" },
    { value: "openai:o1", label: "o1", description: "Advanced reasoning" },
    { value: "openai:o1-mini", label: "o1 Mini", description: "Faster reasoning" },
  ],
  anthropic: [
    { value: "anthropic:claude-sonnet-4-20250514", label: "Claude Sonnet 4", description: "Latest balanced model" },
    { value: "anthropic:claude-3-5-sonnet-latest", label: "Claude 3.5 Sonnet", description: "Previous Sonnet" },
    { value: "anthropic:claude-3-5-haiku-latest", label: "Claude 3.5 Haiku", description: "Fast and affordable" },
    { value: "anthropic:claude-3-opus-latest", label: "Claude 3 Opus", description: "Most capable" },
  ],
  google: [
    { value: "google:gemini-2.0-flash", label: "Gemini 2.0 Flash", description: "Latest fast model" },
    { value: "google:gemini-1.5-pro", label: "Gemini 1.5 Pro", description: "Long context flagship" },
    { value: "google:gemini-1.5-flash", label: "Gemini 1.5 Flash", description: "Fast and capable" },
  ],
  openai_compatible: [
    { value: "openai:custom", label: "Custom Model", description: "Enter model name manually" },
  ],
} as const

// All models flattened for easy lookup
const ALL_MODELS = Object.values(SUPPORTED_MODELS).flat()

interface AgentModelSettingsProps {
  agentId: string
  defaultModelName: string  // Agent's default model from config
  className?: string
}

/**
 * Extract provider type from model name (e.g., "openai:gpt-4o-mini" -> "openai")
 */
function getProviderTypeFromModel(modelName: string): string {
  return modelName.split(":")[0] || "openai"
}

/**
 * Get display label for provider type
 */
function getProviderTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    openai: "OpenAI",
    anthropic: "Anthropic",
    google: "Google",
    openai_compatible: "OpenAI Compatible",
  }
  return labels[type] || type
}

/**
 * Find model info by value
 */
function getModelInfo(modelValue: string) {
  return ALL_MODELS.find((m) => m.value === modelValue)
}

export default function AgentModelSettings({
  agentId,
  defaultModelName,
  className,
}: AgentModelSettingsProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  // Fetch user's LLM providers
  const { data: providersData, isLoading: isLoadingProviders } = useQuery({
    queryKey: ["llm-providers"],
    queryFn: () => LlmProvidersService.listProviders(),
  })

  // Fetch current agent settings
  const { data: currentSettings, isLoading: isLoadingSettings } = useQuery({
    queryKey: ["agent-settings", agentId],
    queryFn: () => AgentsService.getMyAgentSettings({ agentId }),
    enabled: !!agentId,
  })

  // Update settings mutation
  const updateMutation = useMutation({
    mutationFn: (updates: { model_name_override?: string | null; provider_id?: string | null }) =>
      AgentsService.updateMyAgentSettings({
        agentId,
        requestBody: updates,
      }),
    onSuccess: () => {
      showSuccessToast("Settings updated")
      queryClient.invalidateQueries({ queryKey: ["agent-settings", agentId] })
    },
    onError: () => {
      showErrorToast("Failed to update settings")
    },
  })

  // Determine effective model (override or default)
  const effectiveModel = currentSettings?.model_name_override || defaultModelName
  const effectiveProviderType = getProviderTypeFromModel(effectiveModel)
  const isUsingOverride = !!currentSettings?.model_name_override

  // Filter providers to show only compatible ones for the effective model
  const compatibleProviders = (providersData?.data ?? []).filter(
    (p) => p.provider_type === effectiveProviderType,
  )

  const selectedProviderId = currentSettings?.provider_id ?? "system-default"
  const selectedProvider = compatibleProviders.find(
    (p) => p.id === currentSettings?.provider_id,
  )

  const isLoading = isLoadingProviders || isLoadingSettings

  const handleModelChange = (value: string) => {
    const newModel = value === "agent-default" ? null : value
    const newProviderType = newModel ? getProviderTypeFromModel(newModel) : getProviderTypeFromModel(defaultModelName)
    const currentProviderType = getProviderTypeFromModel(effectiveModel)

    // If provider type changed, reset provider selection
    const updates: { model_name_override?: string | null; provider_id?: string | null } = {
      model_name_override: newModel,
    }

    if (newProviderType !== currentProviderType) {
      // Provider type changed - reset provider to system default
      updates.provider_id = null
    }

    updateMutation.mutate(updates)
  }

  const handleProviderChange = (value: string) => {
    const providerId = value === "system-default" ? null : value
    updateMutation.mutate({ provider_id: providerId })
  }

  const handleResetAll = () => {
    updateMutation.mutate({ model_name_override: null, provider_id: null })
  }

  if (isLoading) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        <span className="text-sm text-muted-foreground">Loading settings...</span>
      </div>
    )
  }

  const defaultModelInfo = getModelInfo(defaultModelName)

  return (
    <div className={cn("space-y-6", className)}>
      {/* Model Selection */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Model</span>
            {isUsingOverride && (
              <Badge variant="secondary" className="text-xs">
                Custom
              </Badge>
            )}
          </div>
          {(isUsingOverride || currentSettings?.provider_id) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleResetAll}
              disabled={updateMutation.isPending}
              className="h-7 text-xs"
            >
              <RotateCcw className="h-3 w-3 mr-1" />
              Reset to defaults
            </Button>
          )}
        </div>

        <Select
          value={isUsingOverride ? effectiveModel : "agent-default"}
          onValueChange={handleModelChange}
          disabled={updateMutation.isPending}
        >
          <SelectTrigger className="w-full">
            {updateMutation.isPending ? (
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Updating...</span>
              </div>
            ) : (
              <SelectValue placeholder="Select a model" />
            )}
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>Agent Default</SelectLabel>
              <SelectItem value="agent-default">
                <span className="flex items-center gap-2">
                  {defaultModelInfo?.label || defaultModelName}
                  <span className="text-xs text-muted-foreground">(default)</span>
                </span>
              </SelectItem>
            </SelectGroup>

            {Object.entries(SUPPORTED_MODELS).map(([providerType, models]) => (
              <SelectGroup key={providerType}>
                <SelectLabel>{getProviderTypeLabel(providerType)}</SelectLabel>
                {models.map((model) => (
                  <SelectItem key={model.value} value={model.value}>
                    <span className="flex flex-col">
                      <span>{model.label}</span>
                      <span className="text-xs text-muted-foreground">{model.description}</span>
                    </span>
                  </SelectItem>
                ))}
              </SelectGroup>
            ))}
          </SelectContent>
        </Select>

        <p className="text-xs text-muted-foreground">
          {isUsingOverride
            ? `Using ${getModelInfo(effectiveModel)?.label || effectiveModel} instead of agent's default (${defaultModelInfo?.label || defaultModelName})`
            : `Using agent's default model: ${defaultModelInfo?.label || defaultModelName}`}
        </p>
      </div>

      {/* Provider Selection */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Key className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">API Provider</span>
          <Badge variant="outline" className="text-xs">
            {getProviderTypeLabel(effectiveProviderType)}
          </Badge>
          {compatibleProviders.length > 0 && (
            <span className="text-xs text-muted-foreground">
              ({compatibleProviders.length} available)
            </span>
          )}
        </div>

        <Select
          value={selectedProviderId}
          onValueChange={handleProviderChange}
          disabled={updateMutation.isPending}
        >
          <SelectTrigger className="w-full">
            {updateMutation.isPending ? (
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Updating...</span>
              </div>
            ) : (
              <SelectValue placeholder="Select a provider" />
            )}
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>Your Providers</SelectLabel>
              <SelectItem value="system-default">Use system default</SelectItem>
              {compatibleProviders.map((provider) => (
                <SelectItem key={provider.id} value={provider.id}>
                  <span className="flex items-center gap-2">
                    {provider.name}
                    <ProviderStatusBadge provider={provider} />
                  </span>
                </SelectItem>
              ))}
            </SelectGroup>
          </SelectContent>
        </Select>

        <p className="text-xs text-muted-foreground">
          {selectedProvider
            ? `Using your "${selectedProvider.name}" API key`
            : "Using system environment variables"}
        </p>

        {compatibleProviders.length === 0 && (
          <ProviderTypeBreakdown
            providers={providersData?.data ?? []}
            requiredType={effectiveProviderType}
          />
        )}
      </div>
    </div>
  )
}

/**
 * Shows breakdown of user's providers when no compatible ones found
 */
function ProviderTypeBreakdown({
  providers,
  requiredType,
}: {
  providers: UserLLMProviderPublic[]
  requiredType: string
}) {
  if (providers.length === 0) {
    return (
      <div className="text-xs text-amber-600">
        <p>No providers configured. Add one in Settings → AI Providers.</p>
      </div>
    )
  }

  const byType = providers.reduce(
    (acc, p) => {
      acc[p.provider_type] = (acc[p.provider_type] || 0) + 1
      return acc
    },
    {} as Record<string, number>,
  )

  return (
    <div className="text-xs text-amber-600 space-y-1">
      <p>No {getProviderTypeLabel(requiredType)} providers found.</p>
      <div className="text-muted-foreground space-y-1 mt-2 border-t pt-2">
        <p>Your providers by type:</p>
        <ul className="list-disc list-inside">
          {Object.entries(byType).map(([type, count]) => (
            <li key={type}>
              {getProviderTypeLabel(type)}: {count}
              {type === requiredType && " ← needed"}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

/**
 * Small status indicator for provider verification status
 */
function ProviderStatusBadge({ provider }: { provider: UserLLMProviderPublic }) {
  if (provider.last_test_success === true) {
    return <span className="text-xs text-green-600">✓</span>
  }
  if (provider.last_test_success === false) {
    return <span className="text-xs text-red-600">✗</span>
  }
  if (provider.is_default) {
    return (
      <Badge variant="secondary" className="text-xs">
        Default
      </Badge>
    )
  }
  return null
}
