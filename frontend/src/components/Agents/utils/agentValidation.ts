import type { AgentFormData } from "../Forms/AgentForm"

export type AgentValidationResult = {
  isValid: boolean
  errors: string[]
  warnings: string[]
}

export function validateAgentFormData(
  data: AgentFormData,
): AgentValidationResult {
  const errors: string[] = []
  const warnings: string[] = []

  if (!data.name.trim()) {
    errors.push("Agent name is required")
  }

  if (!data.slug.trim()) {
    errors.push("Agent slug is required")
  }

  if (!data.provider_type.trim()) {
    errors.push("Select a provider type before continuing")
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  }
}
