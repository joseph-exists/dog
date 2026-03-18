import { useQuery } from "@tanstack/react-query"

import { WorkspaceService } from "@/services/workspaceService"
import { workspaceKeys } from "./useWorkspaces"

export function useWorkspaceTerminal(
  workspaceId: string,
  options?: { enabled?: boolean },
) {
  const query = useQuery({
    queryKey: workspaceKeys.terminal(workspaceId),
    queryFn: () => WorkspaceService.getTerminalDescriptor(workspaceId),
    enabled: (options?.enabled ?? false) && !!workspaceId,
    retry: false,
    staleTime: 30_000,
  })

  return {
    terminal: query.data ?? null,
    isLoading: query.isLoading || query.isFetching,
    error: query.error,
    requestTerminal: query.refetch,
  }
}
