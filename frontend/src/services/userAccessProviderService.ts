/**
 * User Access Provider Service - User's API Access Configuration Layer
 *
 * Purpose: Manage user's personal API access credentials and endpoints for LLM providers.
 * This service handles the "WHERE and WITH WHAT" of the three-way binding:
 *   - WHERE: base_url (the API endpoint)
 *   - WITH WHAT: api_key (user's credentials, encrypted at rest and over the wire)
 *
 * This is NOT the API specification (see llmCatalogService for LLMProviderType).
 * This is NOT the model catalog (see llmCatalogService for models).
 * This is NOT the agent configuration (see agentService for UserAgentConfig).
 *
 * Architecture:
 * - Wraps OpenAPI client methods for /llm-providers endpoints
 * - Transforms UserAccessProviderPublic to UserAccessProviderViewModel
 * - Computes derived fields (status, is_usable)
 * - Provides filtering and utility functions
 *
 * Three-Way Binding Context:
 * UserAgentConfig requires three aligned components:
 *   1. user_access_provider (UUID) → UserAccessProvider (THIS SERVICE)
 *   2. provider_type (string)      → LLMProviderType (llmCatalogService)
 *   3. model_name (string)         → Model identifier
 *
 * Dependencies:
 * - OpenAPI auto-generated client (@/client)
 * - UserAccessProvidersService from generated client (CRUD operations)
 */

import {
  UserAccessProviderCreate,
  UserAccessProviderPublic,
  UserAccessProvidersPublic,
  UserAccessProviderUpdate,
  LlmProvidersService
} from "@/client"



// ============================================================================
// Type Definitions - ViewModels
// ============================================================================

/**
 * UserAccessProvider verification status
 */

export type UserAccessProviderStatus = "verified" | "failed" | "unknown"

export interface UserAccessProviderViewModel {
  id: string
  user_id: string
  name: string
  base_url: string | null
  is_enabled: boolean
  is_validated: boolean
  is_default: boolean
  description: string | null
  created_at: Date
  updated_at: Date
  last_tested_at: Date | null
  last_test_success: boolean | null

  // Computed fields
  status: UserAccessProviderStatus  // "verified" | "failed" | "unknown"
  is_usable: boolean                // is_enabled && status !== "failed"
}

/**
 * Transform backend UserAccessProviderPublic to UserAccessProviderViewModel
 *
 * Transformations:
 * - Parses ISO timestamp strings to Date objects
 * - Computes status from last_test_success
 * - Computes is_usable from is_enabled and status
 *
 * @param user_access_provider - Backend UserAccessProviderPublic
 * @returns Transformed UserAccessProviderViewModel
 */
function transformUserAccessProvider(
  user_access_provider: UserAccessProviderPublic
): UserAccessProviderViewModel {
  const status = computeStatus(
    user_access_provider.last_test_success ?? null,
    user_access_provider.last_tested_at ?? null
  )

  return {
    id: user_access_provider.id,
    user_id: user_access_provider.user_id,
    name: user_access_provider.name,
    base_url: user_access_provider.base_url ?? null,
    is_enabled: user_access_provider.is_enabled ?? true,
    is_validated: user_access_provider.is_validated ?? false,
    is_default: user_access_provider.is_default ?? false,
    description: user_access_provider.description ?? null,
    created_at: new Date(user_access_provider.created_at),
    updated_at: new Date(user_access_provider.updated_at),
    last_tested_at: user_access_provider.last_tested_at
      ? new Date(user_access_provider.last_tested_at)
      : null,
    last_test_success: user_access_provider.last_test_success ?? null,

    // Computed fields
    status,
    is_usable: (user_access_provider.is_enabled ?? true) && status !== "failed",
  }
}

/**
 * Compute user_access_provider status from test results
 */
function computeStatus(
  lastTestSuccess: boolean | null,
  lastTestedAt: string | null
): UserAccessProviderStatus {
  if (lastTestedAt === null) return "unknown"
  return lastTestSuccess ? "verified" : "failed"
}

/**
 * Paginated providers response
 */
export interface PaginatedUserAccessProviders {
  providers: UserAccessProviderViewModel[]
  total_count: number
}

/**
 * Create user_access_provider input (wraps backend type)
 */
export type CreateUserAccessProviderInput = UserAccessProviderCreate

/**
 * Update UserAccessProvider input (wraps backend type)
 */
export type UpdateUserAccessProviderInput = UserAccessProviderUpdate

/**
 * Test result from UserAccessProvider test endpoint
 */
export interface TestResult {
  success: boolean
  message: string
  tested_at?: Date
}

/**
 * Validation result
 */
export interface ValidationResult {
  is_valid: boolean
  errors: string[]
  warnings: string[]
}


export const UserAccessProviderService = {
  // ==========================================================================
  // UserAccessProvider CRUD Operations
  // ==========================================================================

  /**
   * List user's UserAccessProviders
   */
  async listUserAccessProviders(options?: {
    skip?: number
    limit?: number
  }): Promise<PaginatedUserAccessProviders> {
    const response: UserAccessProvidersPublic =
      await LlmProvidersService.listProviders({
        skip: options?.skip ?? 0,
        limit: options?.limit ?? 100,
      })

    return {
      providers: response.data.map(transformUserAccessProvider),
      total_count: response.count,
    }
  },

  /**
   * Get a single UserAccessProvider by ID
   */
  async getProvider(providerId: string): Promise<UserAccessProviderViewModel> {
    const user_access_provider = await LlmProvidersService.getProvider({ providerId })
    return transformUserAccessProvider(user_access_provider)
  },
  /**
   * Create a new provider
   */
  async createProvider(
    data: CreateUserAccessProviderInput
  ): Promise<UserAccessProviderViewModel> {
    const provider = await LlmProvidersService.createProvider({
      requestBody: data,
    })
    return transformUserAccessProvider(provider)
  },

  /**
   * Update an existing provider
   */
  async updateProvider(
    providerId: string,
    data: UpdateUserAccessProviderInput
  ): Promise<UserAccessProviderViewModel> {
    const provider = await LlmProvidersService.updateProvider({
      providerId,
      requestBody: data,
    })
    return transformUserAccessProvider(provider)
  },

  /**
   * Delete a provider
   */
  async deleteProvider(providerId: string): Promise<void> {
    await LlmProvidersService.deleteProvider({ providerId })
  },

  // ==========================================================================
  // Testing & Validation Operations (TODO: Backend endpoints needed)
  // ==========================================================================

  /**
   * Test a provider connection
   * TODO: Backend endpoint needed - /api/v1/llm-providers/{provider_id}/test
   */
  async testProvider(_providerId: string): Promise<TestResult> {
    // NOTE: This endpoint doesn't exist yet in the generated client
    // When implemented, it should:
    // 1. Make a test request to the provider's base_url with _providerId
    // 2. Update last_tested_at and last_test_success
    // 3. Return success status and message
    throw new Error("testProvider not yet implemented - backend endpoint needed")
  },

  /**
   * Validate provider configuration
   * Client-side validation before API call
   */
  validateProviderConfig(data: CreateUserAccessProviderInput | UpdateUserAccessProviderInput): ValidationResult {
    const errors: string[] = []
    const warnings: string[] = []

    // Required fields for create
    if ('name' in data && !data.name) {
      errors.push("Provider name is required")
    }

    // Validate base_url format if provided
    if (data.base_url) {
      try {
        new URL(data.base_url)
      } catch {
        errors.push("base_url must be a valid URL")
      }
    } else if ('name' in data) {
      // Creating without base_url - might be system default
      warnings.push("No base_url provided - will use system default endpoint")
    }

    // Warn if api_key not provided (for create)
    if ('api_key' in data && !data.api_key && 'name' in data) {
      warnings.push("No API key provided - provider may not be functional")
    }

    return {
      is_valid: errors.length === 0,
      errors,
      warnings
    }
  },

  // ==========================================================================
  // Utility Methods
  // ==========================================================================

  /**
   * Filter to only enabled providers
   */
  filterEnabled(
    providers: UserAccessProviderViewModel[]
  ): UserAccessProviderViewModel[] {
    return providers.filter((p) => p.is_enabled)
  },

  /**
   * Filter to only usable providers (enabled and not failed)
   */
  filterUsable(
    providers: UserAccessProviderViewModel[]
  ): UserAccessProviderViewModel[] {
    return providers.filter((p) => p.is_usable)
  },

  /**
   * Filter to only validated providers
   */
  filterValidated(
    providers: UserAccessProviderViewModel[]
  ): UserAccessProviderViewModel[]  {
    return providers.filter((p) => p.is_validated)
  },

  /**
   * Get the default provider for the user
   */
  getDefaultProvider(
    providers: UserAccessProviderViewModel[]
  ): UserAccessProviderViewModel | null {
    return providers.find((p) => p.is_default) || null
  },

  /**
   * Set a provider as the default
   * Updates the provider's is_default flag and un-sets others
   */
  async setDefault(
    providerId: string
  ): Promise<UserAccessProviderViewModel> {
    return await this.updateProvider(providerId, { is_default: true })
  },
}

// ============================================================================
// Query Keys for TanStack Query
// ============================================================================

export const USER_ACCESS_PROVIDER_QUERY_KEYS = {
  providers: ["user-access-providers"] as const,
  provider: (id: string) => ["user-access-providers", id] as const,
  default: () => ["user-access-providers", "default"] as const,
}