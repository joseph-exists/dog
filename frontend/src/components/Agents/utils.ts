// Curated palette of distinct, accessible colors for agent avatars
export const AVATAR_COLORS = [
  "bg-rose-500",
  "bg-pink-500",
  "bg-fuchsia-500",
  "bg-purple-500",
  "bg-violet-500",
  "bg-indigo-500",
  "bg-blue-500",
  "bg-sky-500",
  "bg-cyan-500",
  "bg-teal-500",
  "bg-emerald-500",
  "bg-green-500",
  "bg-lime-500",
  "bg-amber-500",
  "bg-orange-500",
  "bg-red-500",
] 
/**
 * Generate a consistent hash from a string.
 * Same input always produces same output.
 */
function hashString(str: string): number {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = (hash << 5) - hash + char
    hash = hash & hash // Convert to 32-bit integer
  }
  return Math.abs(hash)
}

/**
 * Get initials from a name (up to 2 characters).
 * "Story Advisor" -> "SA"
 * "slug-beans" -> "SB"
 * "CharacterForge" -> "CF"
 */
function getInitials(name: string): string {
  // Handle kebab-case (slug-beans -> SB)
  if (name.includes("-")) {
    return name
      .split("-")
      .map((part) => part[0]?.toUpperCase() || "")
      .slice(0, 2)
      .join("")
  }

  // Handle PascalCase (CharacterForge -> CF)
  const pascalMatch = name.match(/[A-Z][a-z]*/g)
  if (pascalMatch && pascalMatch.length >= 2) {
    return pascalMatch
      .map((part) => part[0])
      .slice(0, 2)
      .join("")
  }

  // Handle space-separated (Story Advisor -> SA)
  const words = name.split(" ").filter(Boolean)
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase()
  }

  // Fallback: first two characters
  return name.slice(0, 2).toUpperCase()
}

/**
 * Get a deterministic color class for an agent name.
 */
function getColorForName(name: string): string {
  const hash = hashString(name.toLowerCase())
  return AVATAR_COLORS[hash % AVATAR_COLORS.length]
}


export type AvatarSize = "sm" | "md" | "lg" | "xl"

export const sizeClasses: Record<AvatarSize, string> = {
  sm: "size-6 text-xs",
  md: "size-8 text-sm",
  lg: "size-10 text-base",
  xl: "size-14 text-lg",
}

// Export utilities for use in other components
export { getInitials, getColorForName, hashString }

/**
 * Helpers for shaping agent update payloads to satisfy the discriminated
 * union exported by `AgentsUpdateAgentData['requestBody']`.
 *
 * Why this exists:
 * - The backend uses `provider_type` to pick the correct TypeNUpdate schema.
 * - Frontend callers typically build "sparse" payloads that include only
 *   changed fields. Forgetting `provider_type` breaks the discriminator and
 *   yields 422s. Centralizing the shape keeps future TypeN additions safe.
 *
 * Usage:
 * ```
 * const requestBody = sparseAgentUpdate(agent, {
 *   ...(name && { name }),
 *   ...(model_id && { model_id }),
 * })
 * await mutateAsync(requestBody)
 * ```
 */

import type {
  AgentsUpdateAgentData,
  UserAgentConfigPublic,
} from "@/client/types.gen"

type RequestBody = AgentsUpdateAgentData["requestBody"]
// Extracts the union of literal provider types from the discriminated union.
type ProviderType = RequestBody extends { provider_type: infer P }
  ? P
  : never

/**
 * Builds a minimal agent update payload that always includes the discriminator
 * (`provider_type`) plus any provided field overrides.
 *
 * - `agent` should come from a GET response so it already has provider_type.
 * - `changes` can be any subset of fields from the TypeN update types.
 */
export const sparseAgentUpdate = (
  agent: Pick<UserAgentConfigPublic, "provider_type">,
  changes: Partial<RequestBody> = {},
): RequestBody => {
  const providerType = agent.provider_type as ProviderType | undefined

  if (!providerType) {
    // Failing fast here keeps errors close to the UI layer instead of surfacing
    // as API 422s that are harder to trace.
    throw new Error(
      "provider_type is required to build a discriminated agent update payload",
    )
  }

  return {
    provider_type: providerType,
    ...changes,
  } as RequestBody
}

