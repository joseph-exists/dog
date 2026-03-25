import { useQuery } from "@tanstack/react-query"

import { WorkspaceService } from "@/services/workspaceService"
import { workspaceKeys } from "./useWorkspaces"

export function useWorkspace(workspaceId: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: workspaceKeys.detail(workspaceId),
    queryFn: () => WorkspaceService.getWorkspace(workspaceId),
    enabled: (options?.enabled ?? true) && !!workspaceId,
    refetchInterval: (query) => {
      const workspace = query.state.data
      if (!workspace) return false
      if (workspace.status === "requested" || workspace.status === "provisioning" || workspace.status === "starting") {
        return 2500
      }
      if (
        workspace.bootstrapProgress &&
        workspace.bootstrapProgress.phase !== "complete" &&
        workspace.bootstrapProgress.phase !== "failed"
      ) {
        return 2500
      }
      if (
        workspace.connectivitySummary &&
        workspace.connectivitySummary.serviceCount !== null &&
        workspace.connectivitySummary.serviceCount > 0 &&
        !workspace.connectivitySummary.servicesReady
      ) {
        return 2500
      }
      if (workspace.services.some((service) => service.status === "pending")) {
        return 2500
      }
      return false
    },
    staleTime: 1_000,
  })
}
