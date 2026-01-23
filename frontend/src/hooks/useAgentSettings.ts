/**
 * useAgentSettings Hook
 *
 * Provides access to user's settings for a specific agent.
 * Handles provider/model resolution with computed helpers.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback } from "react"

import type { AgentViewModel } from "@/services/agentService"
import {
  LLM_PROVIDER_QUERY_KEYS,
  LlmProviderService,
  type ProviderResolution,
  type ProviderViewModel,
  type UpdateAgentSettingsInput,
  type UserAgentSettingsViewModel,
} from "@/services/llmProviderService"
import { handleError } from "@/utils"
import { showErrorToast, showSuccessToast } from "./useCustomToast"
import { useLlmProviders } from "./useLlmProviders"

export interface UseAgentSettingsReturn {
  /** User's settings for this agent (null if none configured) */
  settings: UserAgentSettingsViewModel | null
  /** Loading state */
  isLoading: boolean
  /** Error state */
  error: Error | null
  /** Effective model being used (override or agent default) */
  effectiveModel: string
  /** Display name for effective model */
  effectiveModelDisplay: string
  /** Whether using system default (no user provider) */
  isUsingSystemDefault: boolean
  /** The resolved provider (null if system default) */
  provider: ProviderViewModel | null
  /** Full resolution info */
  resolution: ProviderResolution | null
  /** Update settings */
  updateSettings: (data: Partial<UpdateAgentSettingsInput>) => Promise<void>
  /** Reset to defaults (delete settings) */
  resetToDefaults: () => Promise<void>
  /** Toggle favorite status */
  toggleFavorite: () => Promise<void>
  /** Mutation states */
  isUpdating: boolean
  isResetting: boolean
}

interface UseAgentSettingsOptions {
  /** The agent to get settings for */
  agent: AgentViewModel | null
  /** Whether to enable the query */
  enabled?: boolean
}

/**
 * Hook for managing user's settings for a specific agent
 */
export function useAgentSettings({
  agent,
  enabled = true,
}: UseAgentSettingsOptions): UseAgentSettingsReturn {
  const queryClient = useQueryClient()

  const { providers } = useLlmProviders()

  const agentId = agent?.id ?? ""

  // Query for agent settings
  const {
    data: settings,
    isLoading,
    error,
  } = useQuery({
    queryKey: LLM_PROVIDER_QUERY_KEYS.agentSettings(agentId),
    queryFn: () => LlmProviderService.getAgentSettings(agentId),
    enabled: enabled && !!agentId,
    staleTime: 30000, // 30 seconds
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: UpdateAgentSettingsInput) =>
      LlmProviderService.updateAgentSettings(agentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: LLM_PROVIDER_QUERY_KEYS.agentSettings(agentId),
      })
      showSuccessToast("Settings updated")
    },
    onError: handleError.bind(showErrorToast),
  })

  // Delete/reset mutation
  const resetMutation = useMutation({
    mutationFn: () => LlmProviderService.deleteAgentSettings(agentId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: LLM_PROVIDER_QUERY_KEYS.agentSettings(agentId),
      })
      showSuccessToast("Settings reset to defaults")
    },
    onError: handleError.bind(showErrorToast),
  })

  // Compute resolution if we have an agent
  const resolution = agent
    ? LlmProviderService.resolveProviderForAgent(
        agent,
        settings ?? null,
        providers,
      )
    : null

  // Compute derived values
  const effectiveModel =
    resolution?.model || agent?.model_name || "openai:gpt-4o-mini"
  const effectiveModelDisplay =
    resolution?.model_display ||
    LlmProviderService.formatModelName(effectiveModel)
  const isUsingSystemDefault = settings?.is_using_system_default ?? true
  const provider = resolution?.provider ?? null

  // Stable function references
  const updateSettings = useCallback(
    async (data: Partial<UpdateAgentSettingsInput>) => {
      await updateMutation.mutateAsync(data)
    },
    [updateMutation],
  )

  const resetToDefaults = useCallback(async () => {
    await resetMutation.mutateAsync()
  }, [resetMutation])

  const toggleFavorite = useCallback(async () => {
    const currentFavorite = settings?.is_favorite ?? false
    await updateMutation.mutateAsync({ is_favorite: !currentFavorite })
  }, [settings, updateMutation])

  return {
    settings: settings ?? null,
    isLoading,
    error: error as Error | null,
    effectiveModel,
    effectiveModelDisplay,
    isUsingSystemDefault,
    provider,
    resolution,
    updateSettings,
    resetToDefaults,
    toggleFavorite,
    isUpdating: updateMutation.isPending,
    isResetting: resetMutation.isPending,
  }
}

export default useAgentSettings
