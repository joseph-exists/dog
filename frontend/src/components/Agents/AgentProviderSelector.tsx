/**
 * Agent Provider Selector
 *
 * Allows users to select which of their LLM providers to use for a specific agent.
 * Supports system agents (use your own key) and personal agents (customize provider).
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Key, Loader2 } from "lucide-react"

import { AgentsService, LlmProvidersService } from "@/client"
import type { UserLLMProviderPublic } from "@/client/types.gen"
import { Badge } from "@/components/ui/badge"
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

interface AgentProviderSelectorProps {
  agentId: string
  modelName: string
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

export default function AgentProviderSelector({
  agentId,
  modelName,
  className,
}: AgentProviderSelectorProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const requiredProviderType = getProviderTypeFromModel(modelName)

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
    mutationFn: (providerId: string | null) =>
      AgentsService.updateMyAgentSettings({
        agentId,
        requestBody: { provider_id: providerId },
      }),
    onSuccess: () => {
      showSuccessToast("Provider updated")
      queryClient.invalidateQueries({ queryKey: ["agent-settings", agentId] })
    },
    onError: () => {
      showErrorToast("Failed to update provider")
    },
  })

  // Filter providers to only show compatible ones
  const compatibleProviders = (providersData?.data ?? []).filter(
    (p) => p.provider_type === requiredProviderType,
  )

  const selectedProviderId = currentSettings?.provider_id ?? "system-default"

  const selectedProvider = compatibleProviders.find(
    (p) => p.id === currentSettings?.provider_id,
  )

  const isLoading = isLoadingProviders || isLoadingSettings

  const handleValueChange = (value: string) => {
    const providerId = value === "system-default" ? null : value
    updateMutation.mutate(providerId)
  }

  if (isLoading) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        <span className="text-sm text-muted-foreground">Loading...</span>
      </div>
    )
  }

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex items-center gap-2">
        <Key className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium">LLM Provider</span>
        <Badge variant="outline" className="text-xs">
          {getProviderTypeLabel(requiredProviderType)}
        </Badge>
        {compatibleProviders.length > 0 && (
          <span className="text-xs text-muted-foreground">
            ({compatibleProviders.length} available)
          </span>
        )}
      </div>

      <Select
        value={selectedProviderId}
        onValueChange={handleValueChange}
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
          ? `Using your "${selectedProvider.name}" API key for this agent`
          : "This agent uses system environment variables"}
      </p>

      {compatibleProviders.length === 0 && (
        <div className="text-xs text-amber-600 space-y-1">
          <p>
            No {getProviderTypeLabel(requiredProviderType)} providers found.
          </p>
          <p>
            Add one in Settings → AI Providers with type "{getProviderTypeLabel(requiredProviderType)}".
          </p>
          {(providersData?.data?.length ?? 0) > 0 && (
            <div className="text-muted-foreground space-y-1 mt-2 border-t pt-2">
              <p>Your providers by type:</p>
              <ul className="list-disc list-inside">
                {Object.entries(
                  (providersData?.data ?? []).reduce(
                    (acc, p) => {
                      const type = p.provider_type
                      acc[type] = (acc[type] || 0) + 1
                      return acc
                    },
                    {} as Record<string, number>,
                  ),
                ).map(([type, count]) => (
                  <li key={type}>
                    {getProviderTypeLabel(type)}: {count}
                    {type === requiredProviderType && " ← needed"}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/**
 * Small status indicator for provider verification status
 */
function ProviderStatusBadge({
  provider,
}: {
  provider: UserLLMProviderPublic
}) {
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
