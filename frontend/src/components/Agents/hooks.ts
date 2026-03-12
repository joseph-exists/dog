import { useQuery } from "@tanstack/react-query"
import { LlmCatalogService } from "@/client/sdk.gen"

function isUuid(value: string | null | undefined): value is string {
  if (!value) return false
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
    value,
  )
}

export function useProviderTypeName(providerTypeId: string | null | undefined) {
  const canQuery = isUuid(providerTypeId)

  return useQuery({
    queryKey: ["providerType", providerTypeId],
    queryFn: () =>
      LlmCatalogService.getProviderType({ providerTypeId: providerTypeId! }),
    enabled: canQuery,
    staleTime: Infinity, // provider types don't change often
    select: (data) => data.name,
  })
}
