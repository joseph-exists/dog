import { useQuery } from "@tanstack/react-query"

import { WorkspaceService } from "@/services/workspaceService"
import { workspaceKeys } from "./useWorkspaces"

export function useWorkspace(workspaceId: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: workspaceKeys.detail(workspaceId),
    queryFn: () => WorkspaceService.getWorkspace(workspaceId),
    enabled: (options?.enabled ?? true) && !!workspaceId,
    refetchInterval: (query) =>
      query.state.data?.status === "provisioning" ? 2500 : false,
    staleTime: 1_000,
  })
}
