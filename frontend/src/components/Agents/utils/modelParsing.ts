/**
 * Model Name Parsing Utilities
 *
 * Utilities for parsing and manipulating model name strings in the format "provider:model".
 *
 * Three-Way Binding Context:
 * ==========================
 * Model names in this application use the format "provider:model" (e.g., "openai:gpt-4").
 * The provider prefix determines the API format (HOW) while the model suffix specifies
 * which model to invoke (WHAT). This is separate from UserAccessProvider (WHERE + WITH WHAT).
 *
 * Format: "provider:model"
 * - provider: LLMProviderType ("openai" | "anthropic" | "google" | "openai_compatible")
 * - model: Model identifier (e.g., "gpt-4", "claude-3-opus")
 *
 * Examples:
 * - "openai:gpt-4" → provider: "openai", model: "gpt-4"
 * - "anthropic:claude-3-opus" → provider: "anthropic", model: "claude-3-opus"
 * - "google:gemini-pro" → provider: "google", model: "gemini-pro"
 */

import type { LLMProviderType } from "@/services/llmCatalogService"

// ============================================================================
// Constants
// ============================================================================

/**
 * Valid LLM provider types.
 * Used for validation when parsing model names.
 */
const VALID_PROVIDERS: readonly LLMProviderType[] = [
  "openai",
  "anthropic",
  "google",
  "openai_compatible",
  "empty",
] as const

/**
 * Model name format separator
 */
const MODEL_NAME_SEPARATOR = ":"

// ============================================================================
// Type Guards
// ============================================================================

/**
 * Type guard to check if a string is a valid LLMProviderType
 */
function isValidProviderType(value: string): value is LLMProviderType {
  return VALID_PROVIDERS.includes(value as LLMProviderType)
}

// ============================================================================
// Parsing Functions
// ============================================================================

/**
 * Extracts the provider type from a model name string.
 *
 * @param modelName - Model name in "provider:model" format or plain model name
 * @returns The provider type, or null if invalid/not found
 *
 * @example
 * parseProviderFromModelName("openai:gpt-4") // "openai"
 * parseProviderFromModelName("gpt-4") // null (no provider prefix)
 * parseProviderFromModelName("invalid:model") // null (unknown provider)
 * parseProviderFromModelName(null) // null
 */
export function parseProviderFromModelName(
  modelName: string | undefined | null,
): LLMProviderType | null {
  if (!modelName) return null

  const parts = modelName.split(MODEL_NAME_SEPARATOR)
  if (parts.length < 2) return null // No separator found

  const provider = parts[0]
  return isValidProviderType(provider) ? provider : null
}

/**
 * Alias for parseProviderFromModelName for consistency with naming conventions.
 * Some code may prefer "extract" terminology over "parse".
 */
export const extractProviderType = parseProviderFromModelName

/**
 * Extracts the model identifier from a model name string.
 *
 * @param modelName - Model name in "provider:model" format or plain model name
 * @returns The model identifier, or the original string if no provider prefix
 *
 * @example
 * extractModelId("openai:gpt-4") // "gpt-4"
 * extractModelId("anthropic:claude-3-opus-20240229") // "claude-3-opus-20240229"
 * extractModelId("gpt-4") // "gpt-4" (no provider prefix, returns as-is)
 * extractModelId("openai:") // "" (edge case: empty model id)
 */
export function extractModelId(modelName: string | undefined | null): string {
  if (!modelName) return ""

  const parts = modelName.split(MODEL_NAME_SEPARATOR)
  if (parts.length < 2) return modelName // No separator, return original

  // Join remaining parts (in case model ID contains colons)
  return parts.slice(1).join(MODEL_NAME_SEPARATOR)
}

/**
 * Constructs a fully qualified model name from provider and model components.
 *
 * @param provider - The LLM provider type
 * @param modelId - The model identifier
 * @returns Formatted model name as "provider:model"
 *
 * @example
 * constructModelName("openai", "gpt-4") // "openai:gpt-4"
 * constructModelName("anthropic", "claude-3-opus") // "anthropic:claude-3-opus"
 */
export function constructModelName(
  provider: LLMProviderType,
  modelId: string,
): string {
  return `${provider}${MODEL_NAME_SEPARATOR}${modelId}`
}

/**
 * Validates that a model name string follows the expected format.
 *
 * @param modelName - Model name to validate
 * @param requireProvider - Whether to require a provider prefix (default: true)
 * @returns True if valid, false otherwise
 *
 * @example
 * isValidModelName("openai:gpt-4") // true
 * isValidModelName("gpt-4", false) // true (provider not required)
 * isValidModelName("gpt-4", true) // false (provider required but missing)
 * isValidModelName("invalid:model") // false (unknown provider)
 * isValidModelName("") // false (empty string)
 */
export function isValidModelName(
  modelName: string | undefined | null,
  requireProvider = true,
): boolean {
  if (!modelName || modelName.trim() === "") return false

  const parts = modelName.split(MODEL_NAME_SEPARATOR)

  // If provider not required, any non-empty string is valid
  if (!requireProvider) return true

  // Provider required: must have separator and valid provider
  if (parts.length < 2) return false

  const provider = parts[0]
  const model = parts.slice(1).join(MODEL_NAME_SEPARATOR)

  return isValidProviderType(provider) && model.trim() !== ""
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Normalizes a model name by ensuring it has a provider prefix.
 * If no provider is specified, uses the fallback provider.
 *
 * @param modelName - Model name (with or without provider)
 * @param fallbackProvider - Provider to use if none specified
 * @returns Normalized model name with provider prefix
 *
 * @example
 * normalizeModelName("gpt-4", "openai") // "openai:gpt-4"
 * normalizeModelName("openai:gpt-4", "anthropic") // "openai:gpt-4" (already has provider)
 */
export function normalizeModelName(
  modelName: string,
  fallbackProvider: LLMProviderType,
): string {
  const existingProvider = parseProviderFromModelName(modelName)
  if (existingProvider) {
    return modelName // Already has a valid provider prefix
  }

  // No provider prefix, add the fallback
  return constructModelName(fallbackProvider, modelName)
}

/**
 * Checks if a model name matches a specific provider type.
 *
 * @param modelName - Model name to check
 * @param providerType - Provider type to match against
 * @returns True if the model name's provider matches the given type
 *
 * @example
 * isModelOfProvider("openai:gpt-4", "openai") // true
 * isModelOfProvider("anthropic:claude-3", "openai") // false
 * isModelOfProvider("gpt-4", "openai") // false (no provider prefix)
 */
export function isModelOfProvider(
  modelName: string | undefined | null,
  providerType: LLMProviderType,
): boolean {
  const modelProvider = parseProviderFromModelName(modelName)
  return modelProvider === providerType
}

/**
 * Extracts both provider and model ID from a model name.
 *
 * @param modelName - Model name in "provider:model" format
 * @returns Object with provider and modelId, or null if invalid
 *
 * @example
 * parseModelName("openai:gpt-4") // { provider: "openai", modelId: "gpt-4" }
 * parseModelName("gpt-4") // null (no provider)
 * parseModelName("invalid:model") // null (unknown provider)
 */
export function parseModelName(
  modelName: string | undefined | null,
): { provider: LLMProviderType; modelId: string } | null {
  const provider = parseProviderFromModelName(modelName)
  if (!provider) return null

  const modelId = extractModelId(modelName)
  if (!modelId) return null

  return { provider, modelId }
}
