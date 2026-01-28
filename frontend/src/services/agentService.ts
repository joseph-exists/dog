/**
 * Agent Service - Data Integration Layer
 *
 * Purpose: Provide a clean, type-safe abstraction over the OpenAPI client
 * for agent-related operations. Transforms backend response models to
 * frontend ViewModels optimized for UI consumption.
 *
 * Architecture:
 * - Wraps OpenAPI client methods
 * - Transforms backend types to ViewModels
 * - Computes derived fields (e.g., display_model from model_name)
 * - Centralizes API endpoint usage
 * - Provides type-safe interfaces
 *
 * Dependencies:
 * - OpenAPI auto-generated client (@/client)
 */

import {
  type AgentConfigCreate,
  type AgentConfigPublic,
  type AgentConfigsPublic,
  type AgentConfigUpdate,
  AgentsService,
  OpenAPI,
} from "@/client"
import type { ApiRequestOptions } from "@/client/core/ApiRequestOptions"
import { request as __request } from "@/client/core/request"
import type { LLMProviderType } from "@/services/llmCatalogService"

// ============================================================================
// Type Definitions - ViewModels
// ============================================================================

/**
 * Agent scope - determines visibility and ownership
 */
export type AgentScope = "system" | "personal"

/**
 * Agent participation mode - how the agent engages in rooms by default
 * - "always": Agent responds to all messages
 * - "on_mention": Agent responds when mentioned
 * - "manual": Agent only responds when explicitly invoked
 */
export type ParticipationMode = "always" | "on_mention" | "manual"

/**
 * AgentViewModel - Optimized for UI display
 *
 * Transformations from backend AgentConfigPublic:
 * - Parses ISO timestamps to Date objects
 * - Computes display_model from model_name (e.g., "openai:gpt-4o-mini" → "GPT 4o Mini")
 * - Provides strict union types for scope and participation_mode
 * - Normalizes nullable fields
 */
export interface AgentViewModel {
  id: string
  name: string
  slug: string
  description: string | null
  model_name: string
  display_model: string
  provider_type: LLMProviderType
  user_provider: string | null
  system_prompt: string | null
  tool_config: Record<string, unknown> | null
  deps_config: Record<string, unknown> | null
  agent_metadata: Record<string, unknown> | null
  is_enabled: boolean
  scope: AgentScope
  participation_mode: ParticipationMode
  is_coordinator: boolean
  capabilities: string[]
  owner_id: string | null
  created_at: Date
  updated_at: Date | null
  version: number
}

/**
 * Agent creation input
 */
export interface CreateAgentInput {
  name: string
  slug: string
  description?: string | null
  model_name?: string
  provider_type?: LLMProviderType
  user_provider?: string | null
  system_prompt?: string | null
  participation_mode?: ParticipationMode
  scope?: AgentScope
  is_enabled?: boolean
}

/**
 * Agent update input
 */
export interface UpdateAgentInput {
  name?: string | null
  description?: string | null
  model_name?: string | null
  provider_type?: LLMProviderType | null
  user_provider?: string | null
  system_prompt?: string | null
  participation_mode?: ParticipationMode | null
  is_enabled?: boolean | null
}

/**
 * Paginated agents response
 */
export interface PaginatedAgents {
  agents: AgentViewModel[]
  total_count: number
}

interface GeneratedSlugResponse {
  slug: string
}

// ============================================================================
// Transformation Functions
// ============================================================================

/**
 * Format model name for display
 *
 * Transforms provider:model format to human-readable display name.
 * Examples:
 * - "openai:gpt-4o-mini" → "GPT 4o Mini"
 * - "anthropic:claude-3-sonnet" → "Claude 3 Sonnet"
 * - null/undefined → "Default"
 *
 * @param modelName - Raw model name from backend
 * @returns Formatted display name
 */
export function formatModelName(modelName: string | undefined | null): string {
  if (!modelName) return "Default"

  // Extract model part after provider prefix
  const modelPart = modelName.split(":").pop() || modelName

  // Convert kebab-case to Title Case
  return modelPart
    .replace(/-/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

/**
 * Transform backend AgentConfigPublic to AgentViewModel
 *
 * @param agent - Backend agent object
 * @returns Transformed AgentViewModel
 */
function transformAgent(agent: AgentConfigPublic): AgentViewModel {
  return {
    id: agent.id,
    name: agent.name,
    slug: agent.slug ?? "",
    description: agent.description ?? null,
    model_name: agent.model_name ?? "openai:gpt-4o-mini",
    display_model: formatModelName(agent.model_name),
    provider_type: agent.provider_type ?? "openai",
    user_provider: agent.user_provider ?? null,
    system_prompt: agent.system_prompt ?? null,
    tool_config: agent.tool_config ?? null,
    deps_config: agent.deps_config ?? null,
    agent_metadata: agent.agent_metadata ?? null,
    is_enabled: agent.is_enabled ?? true,
    scope: (agent.scope as AgentScope) ?? "personal",
    participation_mode:
      (agent.participation_mode as ParticipationMode) ?? "on_mention",
    is_coordinator: agent.is_coordinator ?? false,
    capabilities: agent.capabilities ?? [],
    owner_id: agent.owner_id ?? null,
    created_at: new Date(agent.created_at),
    updated_at: agent.updated_at ? new Date(agent.updated_at) : null,
    version: agent.version,
  }
}

// ============================================================================
// Agent Service - Public API
// ============================================================================

/**
 * Agent Service
 *
 * Provides all agent-related data operations with clean, type-safe interfaces.
 * All methods return ViewModels optimized for UI consumption.
 *
 * Error Handling:
 * - All methods can throw ApiError from the OpenAPI client
 * - Callers should handle errors appropriately (see handleError utility)
 *
 * Authentication:
 * - All methods require valid JWT token (handled by OpenAPI client)
 * - 401 errors indicate authentication failure
 * - 403 errors indicate authorization failure
 */
export const AgentService = {
  // ==========================================================================
  // Agent Operations
  // ==========================================================================

  /**
   * List all agents accessible to the current user
   *
   * Returns both personal agents owned by the user and system agents.
   *
   * @param options - Pagination options
   * @returns Paginated agents response
   * @throws ApiError on network or server errors
   */
  async listAgents(options?: {
    skip?: number
    limit?: number
  }): Promise<PaginatedAgents> {
    const response: AgentConfigsPublic = await AgentsService.listAgents({
      skip: options?.skip ?? 0,
      limit: options?.limit ?? 100,
    })

    return {
      agents: response.data.map(transformAgent),
      total_count: response.count,
    }
  },

  /**
   * List available agents for room participation
   *
   * Returns agents that can be added to rooms (enabled agents only).
   *
   * @param options - Pagination options
   * @returns Paginated agents response
   * @throws ApiError on network or server errors
   */
  async listAvailableAgents(options?: {
    skip?: number
    limit?: number
  }): Promise<PaginatedAgents> {
    const response: AgentConfigsPublic =
      await AgentsService.listAvailableAgents({
        skip: options?.skip ?? 0,
        limit: options?.limit ?? 100,
      })

    return {
      agents: response.data.map(transformAgent),
      total_count: response.count,
    }
  },

  /**
   * Get a single agent by ID
   *
   * @param agentId - Agent UUID
   * @returns AgentViewModel
   * @throws ApiError - 404 if agent not found
   */
  async getAgent(agentId: string): Promise<AgentViewModel> {
    const agent: AgentConfigPublic = await AgentsService.getAgent({ agentId })
    return transformAgent(agent)
  },

  /**
   * Get a single agent by slug
   *
   * @param slug - Agent slug
   * @returns AgentViewModel
   * @throws ApiError - 404 if agent not found
   */
  async getAgentBySlug(slug: string): Promise<AgentViewModel> {
    const options: ApiRequestOptions<AgentConfigPublic> = {
      method: "GET",
      url: `/api/v1/agents/slug/${slug}`,
    }
    const agent = await __request(OpenAPI, options)
    return transformAgent(agent)
  },

  /**
   * Generate a unique agent slug
   *
   * @returns Generated slug
   * @throws ApiError on network or server errors
   */
  async generateSlug(): Promise<string> {
    const options: ApiRequestOptions<GeneratedSlugResponse> = {
      method: "GET",
      url: "/api/v1/agents/generate-slug",
    }
    const response = await __request(OpenAPI, options)
    return response.slug
  },

  /**
   * Create a new personal agent
   *
   * System agents can only be created by superusers via backend.
   * Personal agents are owned by the creating user.
   *
   * @param data - Agent creation parameters
   * @returns Newly created AgentViewModel
   * @throws ApiError on validation or server errors
   */
  async createAgent(data: CreateAgentInput): Promise<AgentViewModel> {
    const createData: AgentConfigCreate = {
      name: data.name,
      slug: data.slug,
      description: data.description,
      model_name: data.model_name,
      provider_type: data.provider_type,
      user_provider: data.user_provider,
      system_prompt: data.system_prompt,
      participation_mode: data.participation_mode,
      scope: data.scope ?? "personal",
      is_enabled: data.is_enabled ?? true,
    }

    const agent: AgentConfigPublic = await AgentsService.createAgent({
      requestBody: createData,
    })

    return transformAgent(agent)
  },

  /**
   * Update an existing agent
   *
   * Only the agent owner or superusers can update agents.
   * System agents can only be updated by superusers.
   *
   * @param agentId - Agent UUID
   * @param data - Fields to update
   * @returns Updated AgentViewModel
   * @throws ApiError - 403 if not authorized, 404 if agent not found
   */
  async updateAgent(
    agentId: string,
    data: UpdateAgentInput,
  ): Promise<AgentViewModel> {
    const updateData: AgentConfigUpdate = {
      name: data.name,
      description: data.description,
      model_name: data.model_name,
      provider_type: data.provider_type,
      user_provider: data.user_provider,
      system_prompt: data.system_prompt,
      participation_mode: data.participation_mode,
      is_enabled: data.is_enabled,
    }

    const agent: AgentConfigPublic = await AgentsService.updateAgent({
      agentId,
      requestBody: updateData,
    })

    return transformAgent(agent)
  },

  /**
   * Delete an agent
   *
   * Only the agent owner or superusers can delete agents.
   * System agents can only be deleted by superusers.
   *
   * @param agentId - Agent UUID
   * @returns Promise that resolves when deletion is complete
   * @throws ApiError - 403 if not authorized, 404 if agent not found
   */
  async deleteAgent(agentId: string): Promise<void> {
    await AgentsService.deleteAgent({ agentId })
  },

  // ==========================================================================
  // Filtering Utilities
  // ==========================================================================

  /**
   * Filter agents by scope
   *
   * @param agents - Array of agents to filter
   * @param scope - Scope to filter by
   * @returns Filtered agents
   */
  filterByScope(agents: AgentViewModel[], scope: AgentScope): AgentViewModel[] {
    return agents.filter((agent) => agent.scope === scope)
  },

  /**
   * Filter agents by enabled status
   *
   * @param agents - Array of agents to filter
   * @param enabled - Enabled status to filter by
   * @returns Filtered agents
   */
  filterByEnabled(
    agents: AgentViewModel[],
    enabled: boolean,
  ): AgentViewModel[] {
    return agents.filter((agent) => agent.is_enabled === enabled)
  },

  /**
   * Separate agents into personal and system groups
   *
   * @param agents - Array of agents to group
   * @returns Object with personal and system agent arrays
   */
  groupByScope(agents: AgentViewModel[]): {
    personal: AgentViewModel[]
    system: AgentViewModel[]
  } {
    return {
      personal: agents.filter((a) => a.scope === "personal"),
      system: agents.filter((a) => a.scope === "system"),
    }
  },
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Check if an agent can be edited by the current user
 *
 * Personal agents can be edited by their owner.
 * System agents can only be edited by superusers.
 *
 * @param agent - Agent to check
 * @param currentUserId - Current user's ID
 * @param isSuperuser - Whether current user is a superuser
 * @returns Whether the agent can be edited
 */
export function canEditAgent(
  agent: AgentViewModel,
  currentUserId: string | null,
  isSuperuser: boolean,
): boolean {
  if (isSuperuser) return true
  if (agent.scope === "system") return false
  return agent.owner_id === currentUserId
}

/**
 * Check if an agent can be deleted by the current user
 *
 * Same rules as editing.
 *
 * @param agent - Agent to check
 * @param currentUserId - Current user's ID
 * @param isSuperuser - Whether current user is a superuser
 * @returns Whether the agent can be deleted
 */
export function canDeleteAgent(
  agent: AgentViewModel,
  currentUserId: string | null,
  isSuperuser: boolean,
): boolean {
  return canEditAgent(agent, currentUserId, isSuperuser)
}
