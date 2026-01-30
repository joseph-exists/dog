/**
 * Agent Validation Utilities
 *
 * Validation functions for agent configuration data.
 * Ensures the three-way binding is correctly configured before submission.
 *
 * Three-Way Binding Validation:
 * ============================
 * UserAgentConfig requires three aligned components:
 *   1. user_access_provider (UUID) → WHERE + WITH WHAT (credentials)
 *   2. provider_type (string)      → HOW (API format, derived from model_name)
 *   3. model_name (string)         → WHAT (model identifier)
 *
 * These validations ensure:
 * - model_name is present and properly formatted
 * - provider_type can be derived from model_name
 * - user_access_provider (if provided) is a valid UUID
 * - required fields are not empty
 */

import type { AgentFormData } from "@/components/Agents/Forms/AgentForm"
import { isValidModelName } from "./modelParsing"

// ============================================================================
// Type Definitions
// ============================================================================

export interface ValidationResult {
  isValid: boolean
  errors: string[]
  warnings: string[]
}

// ============================================================================
// UUID Validation
// ============================================================================

/**
 * UUID v4 regex pattern
 */
const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

/**
 * Validates that a string is a valid UUID v4
 */
function isValidUUID(value: string): boolean {
  return UUID_PATTERN.test(value)
}

// ============================================================================
// Field Validators
// ============================================================================

/**
 * Validates agent name field
 */
function validateName(name: string): string | null {
  if (!name || name.trim() === "") {
    return "Agent name is required"
  }
  if (name.length > 100) {
    return "Agent name must be 100 characters or less"
  }
  return null
}

/**
 * Validates agent slug field
 */
function validateSlug(slug: string): string | null {
  if (!slug || slug.trim() === "") {
    return "Agent slug is required"
  }
  // Basic slug validation (alphanumeric, hyphens, underscores)
  if (!/^[a-z0-9_-]+$/.test(slug)) {
    return "Slug must contain only lowercase letters, numbers, hyphens, and underscores"
  }
  return null
}

/**
 * Validates description field
 */
function validateDescription(description: string): string | null {
  if (description.length > 500) {
    return "Description must be 500 characters or less"
  }
  return null
}

/**
 * Validates model_name field
 *
 * Three-Way Binding Note:
 * The model_name MUST have a valid provider prefix (e.g., "openai:gpt-4")
 * because provider_type is derived from it.
 */
function validateModelName(modelName: string): string | null {
  if (!modelName || modelName.trim() === "") {
    return "Model is required"
  }

  if (!isValidModelName(modelName, true)) {
    return 'Model name must be in format "provider:model" (e.g., "openai:gpt-4")'
  }

  return null
}

/**
 * Validates user_access_provider field
 *
 * Three-Way Binding Note:
 * UserAccessProvider is optional. If not provided, system default credentials
 * will be used. If provided, it must be a valid UUID.
 */
function validateUserAccessProvider(
  userAccessProvider: string | null,
): string | null {
  if (!userAccessProvider) return null // Optional field

  if (!isValidUUID(userAccessProvider)) {
    return "User access provider must be a valid UUID"
  }

  return null
}

/**
 * Validates system_prompt field
 */
function validateSystemPrompt(_systemPrompt: string): string | null {
  // System prompt is optional, so empty is valid
  // Could add max length validation if backend has limits
  return null
}

/**
 * Validates participation_mode field
 */
function validateParticipationMode(
  participationMode: string,
): string | null {
  const validModes = ["on_mention", "always", "manual"]
  if (!validModes.includes(participationMode)) {
    return `Participation mode must be one of: ${validModes.join(", ")}`
  }
  return null
}

// ============================================================================
// Three-Way Binding Validation
// ============================================================================

/**
 * Validates the three-way binding consistency.
 *
 * Three-Way Binding Rules:
 * 1. model_name must have a valid provider prefix (provider_type is derived from it)
 * 2. user_access_provider is optional (if null, system credentials are used)
 * 3. The user is responsible for ensuring their credentials work with the selected model
 *
 * @deprecated This validation is no longer needed with the new architecture.
 * The three-way binding is validated by checking model_name format only.
 * User credentials and model selection are independent.
 */
export function validateThreeWayBinding(
  formData: AgentFormData,
): string | null {
  // With the new architecture, we don't enforce provider/model consistency
  // because UserAccessProvider doesn't have a provider_type field.
  // Users are responsible for ensuring their credentials work with their model.

  const modelError = validateModelName(formData.model_name)
  if (modelError) return modelError

  return null // Valid
}

/**
 * DEPRECATED: Old validation logic from before three-way binding refactor.
 * This validation is incorrect for the new architecture.
 *
 * @deprecated Use validateThreeWayBinding instead
 */
export function validateProviderModelConsistency_DEPRECATED(
  formData: AgentFormData,
): string | null {
  // Old logic (INCORRECT):
  // Rule: If provider_type is not "empty", user_access_provider must be set
  // Rule: If user_access_provider is set, provider_type must not be "empty"

  // This is wrong because:
  // 1. provider_type is derived from model_name, not from user_access_provider
  // 2. user_access_provider doesn't have a provider_type field
  // 3. The validation conflates credentials with API format

  return validateThreeWayBinding(formData)
}

// ============================================================================
// Comprehensive Validation
// ============================================================================

/**
 * Validates all fields in AgentFormData.
 *
 * Returns a ValidationResult with:
 * - isValid: true if no errors
 * - errors: array of error messages
 * - warnings: array of warning messages (non-blocking)
 *
 * @param formData - Agent form data to validate
 * @returns ValidationResult
 */
export function validateAgentFormData(
  formData: AgentFormData,
): ValidationResult {
  const errors: string[] = []
  const warnings: string[] = []

  // Validate required fields
  const nameError = validateName(formData.name)
  if (nameError) errors.push(nameError)

  const slugError = validateSlug(formData.slug)
  if (slugError) errors.push(slugError)

  const descriptionError = validateDescription(formData.description)
  if (descriptionError) errors.push(descriptionError)

  const modelError = validateModelName(formData.model_name)
  if (modelError) errors.push(modelError)

  const systemPromptError = validateSystemPrompt(formData.system_prompt)
  if (systemPromptError) errors.push(systemPromptError)

  const participationModeError = validateParticipationMode(
    formData.participation_mode,
  )
  if (participationModeError) errors.push(participationModeError)

  const userAccessProviderError = validateUserAccessProvider(
    formData.user_access_provider,
  )
  if (userAccessProviderError) errors.push(userAccessProviderError)

  // Validate three-way binding
  const bindingError = validateThreeWayBinding(formData)
  if (bindingError) errors.push(bindingError)

  // Warnings (non-blocking)
  if (!formData.user_access_provider) {
    warnings.push(
      "No API credentials selected. System default credentials will be used.",
    )
  }

  if (!formData.system_prompt || formData.system_prompt.trim() === "") {
    warnings.push("No system prompt provided. Agent will use default behavior.")
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  }
}

/**
 * Quick validation check: can the agent form be saved?
 *
 * This is a lightweight check for UI state (e.g., enabling/disabling save button).
 * For comprehensive validation before API submission, use validateAgentFormData().
 *
 * @param formData - Agent form data to check
 * @returns True if form has required fields and passes basic validation
 */
export function canSaveAgent(formData: AgentFormData | null): boolean {
  if (!formData) return false

  // Check required fields are present
  if (!formData.name || !formData.name.trim()) return false
  if (!formData.slug || !formData.slug.trim()) return false
  if (!formData.model_name || !formData.model_name.trim()) return false

  // Check model_name has valid format
  if (!isValidModelName(formData.model_name, true)) return false

  return true
}

/**
 * Validates and extracts submission data from form data.
 *
 * Performs full validation and transforms form data into the format
 * expected by the API.
 *
 * @param formData - Agent form data to validate and transform
 * @returns ValidationResult with transformed data, or errors
 */
export function prepareAgentForSubmission(formData: AgentFormData): {
  isValid: boolean
  errors: string[]
  data: {
    name: string
    slug: string
    description: string | null
    model_name: string
    provider_type: string
    user_access_provider: string | null
    system_prompt: string | null
    participation_mode: string
  } | null
} {
  const validation = validateAgentFormData(formData)

  if (!validation.isValid) {
    return {
      isValid: false,
      errors: validation.errors,
      data: null,
    }
  }

  // Transform form data for API submission
  const data = {
    name: formData.name.trim(),
    slug: formData.slug.trim(),
    description: formData.description.trim() || null,
    model_name: formData.model_name.trim(),
    provider_type: formData.provider_type,
    user_access_provider: formData.user_access_provider,
    system_prompt: formData.system_prompt.trim() || null,
    participation_mode: formData.participation_mode,
  }

  return {
    isValid: true,
    errors: [],
    data,
  }
}
