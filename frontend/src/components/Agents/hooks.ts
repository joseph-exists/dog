import { useQuery } from "@tanstack/react-query"
import { LlmCatalogService } from "@/client/sdk.gen"

export function useProviderTypeName(providerTypeId: string | null | undefined) {
  return useQuery({
    queryKey: ["providerType", providerTypeId],
    queryFn: () => LlmCatalogService.getProviderType({ providerTypeId: providerTypeId! }),
    enabled: !!providerTypeId,
    staleTime: Infinity, // provider types don't change often
    select: (data) => data.name,
  })
}