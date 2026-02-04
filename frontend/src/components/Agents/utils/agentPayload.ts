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

