/**
 * useAgentSettings Hook
 *
 * Manages user's personal settings for an agent (my_settings endpoint).
 *
 * Purpose:
 * - Fetch user's override settings for any agent (personal or system)
 * - Update provider/model overrides
 * - Delete overrides (revert to agent defaults)
 *
 * Use Cases:
 * - Personal agents: Customize your own agent configuration
 * - System agents: Use your own API key without affecting other users
 *
 * Three-Way Binding Context:
 * ==========================
 * User settings can override:
 *   1. user_access_provider → Use your own API credentials instead of system default
 *   2. model_name → Use a different model than the agent's default
 *
 * The provider_type is still derived from model_name, maintaining the three-way binding.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { UserAgentConfigPublic, UserAgentConfigUpdate } from "@/client"
import { AgentsService } from "@/client"
import type { AgentViewModel } from "@/services/agentService"
import { useLlmProviders } from "@/hooks/useLlmProviders"
import type { UserAccessProviderViewModel } from "@/services/userAccessProviderService"
import { parseProviderFromModelName } from "@/components/Agents/utils/modelParsing"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"

// ============================================================================
// Query Keys
// ============================================================================

export const AGENT_SETTINGS_QUERY_KEYS = {
  all: ["agent-settings"] as const,
  byAgent: (agentId: string) => ["agent-settings", agentId] as const,
}

// ============================================================================
// Types
// ============================================================================

export interface UseAgentSettingsParams {
  /** The agent to get settings for */
  agent: AgentViewModel
}

export interface AgentSettingsUpdateInput {
  /** User's access provider UUID (null = use system default) */
  user_access_provider?: string | null
  /** Model name override (null = use agent default) */
  model_name?: string | null
  /** Custom system prompt override */
  custom_system_prompt?: string | null
}

// ============================================================================
// Hook
// ============================================================================

/**
 * Hook for managing user's personal settings for an agent.
 *
 * @param params - Hook parameters
 * @returns Agent settings state and mutations
 *
 * @example
 * ```tsx
 * const {
 *   settings,
 *   isUsingSystemDefault,
 *   effectiveModel,
 *   provider,
 *   updateSettings,
 *   deleteSettings,
 *   isLoading,
 *   isUpdating,
 * } = useAgentSettings({ agent })
 * ```
 */
export function useAgentSettings({ agent }: UseAgentSettingsParams) {
  const queryClient = useQueryClient()
  const { providers } = useLlmProviders()

  // ==========================================================================
  // Fetch User Settings
  // ==========================================================================

  const {
    data: settings,
    isLoading,
    error,
  } = useQuery<UserAgentConfigPublic | null>({
    queryKey: AGENT_SETTINGS_QUERY_KEYS.byAgent(agent.id),
    queryFn: async () => {
      const response = await AgentsService.getMyAgentSettings({
        agentId: agent.id,
      })
      return response || null
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // ==========================================================================
  // Update Settings Mutation
  // ==========================================================================

  const updateMutation = useMutation({
    mutationFn: async (input: AgentSettingsUpdateInput) => {
      const updateData: UserAgentConfigUpdate = {
        user_access_provider: input.user_access_provider,
        model_name: input.model_name,
        custom_system_prompt: input.custom_system_prompt,
      }

      return await AgentsService.updateMyAgentSettings({
        agentId: agent.id,
        requestBody: updateData,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: AGENT_SETTINGS_QUERY_KEYS.byAgent(agent.id),
      })
      showSuccessToast("Settings updated successfully")
    },
    onError: (error: Error) => {
      showErrorToast(`Failed to update settings: ${error.message}`)
    },
  })

  // ==========================================================================
  // Delete Settings Mutation
  // ==========================================================================

  const deleteMutation = useMutation({
    mutationFn: async () => {
      return await AgentsService.deleteMyAgentSettings({
        agentId: agent.id,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: AGENT_SETTINGS_QUERY_KEYS.byAgent(agent.id),
      })
      showSuccessToast("Settings reset to defaults")
    },
    onError: (error: Error) => {
      showErrorToast(`Failed to reset settings: ${error.message}`)
    },
  })

  // ==========================================================================
  // Computed Values
  // ==========================================================================

  /**
   * Check if user is using system default (no custom settings)
   */
  const isUsingSystemDefault = !settings || !settings.user_access_provider

  /**
   * Get the effective model (user override or agent default)
   */
  const effectiveModel = settings?.model_name || agent.model_name

  /**
   * Get the effective provider type (derived from effective model)
   */
  const effectiveProviderType = parseProviderFromModelName(effectiveModel)

  /**
   * Find the user's selected provider (if any)
   */
  const provider: UserAccessProviderViewModel | null = settings?.user_access_provider
    ? providers.find((p) => p.id === settings.user_access_provider) ?? null
    : null

  /**
   * Format model name for display
   */
  const effectiveModelDisplay = effectiveModel
    ? effectiveModel.includes(":")
      ? effectiveModel.split(":")[1] // Show just the model part
      : effectiveModel
    : "No model"

  /**
   * Get effective system prompt (user override or agent default)
   */
  const effectiveSystemPrompt =
    settings?.custom_system_prompt || agent.system_prompt

  // ==========================================================================
  // Mutation Helpers
  // ==========================================================================

  const updateSettings = async (input: AgentSettingsUpdateInput) => {
    return updateMutation.mutateAsync(input)
  }

  const deleteSettings = async () => {
    return deleteMutation.mutateAsync()
  }

  // ==========================================================================
  // Return
  // ==========================================================================

  return {
    // Data
    settings,
    isLoading,
    error,

    // Computed values
    isUsingSystemDefault,
    effectiveModel,
    effectiveModelDisplay,
    effectiveProviderType,
    effectiveSystemPrompt,
    provider,

    // Mutations
    updateSettings,
    deleteSettings,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  }
}
