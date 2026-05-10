import { useQuery } from "@tanstack/react-query"

import { ApiError } from "@/client/core/ApiError"
import { WorkspaceService } from "@/services/workspaceService"
import { workspaceKeys } from "./useWorkspaces"

export type WorkspaceTerminalEndpointState =
  | "idle"
  | "loading"
  | "available"
  | "expired"
  | "unavailable"
  | "not_allowed"
  | "error"

function classifyTerminalEndpointState(
  error: unknown,
  hasTerminalDescriptor: boolean,
  isLoading: boolean,
  enabled: boolean,
): { state: WorkspaceTerminalEndpointState; message: string | null } {
  if (!enabled) {
    return {
      state: "idle",
      message: "Terminal endpoint has not been requested yet.",
    }
  }

  if (isLoading) {
    return {
      state: "loading",
      message: "Requesting terminal endpoint descriptor.",
    }
  }

  if (hasTerminalDescriptor) {
    return {
      state: "available",
      message: "Terminal endpoint descriptor is active.",
    }
  }

  if (error instanceof ApiError) {
    if (error.status === 401 || error.status === 403) {
      return {
        state: "not_allowed",
        message: "Terminal access is not allowed for this workspace/account.",
      }
    }
    if (error.status === 410 || error.status === 412) {
      return {
        state: "expired",
        message:
          "Terminal endpoint expired. Request a fresh endpoint descriptor.",
      }
    }
    if (error.status === 404) {
      return {
        state: "unavailable",
        message:
          "Terminal endpoint is unavailable. Request a fresh endpoint descriptor.",
      }
    }
    return {
      state: "error",
      message: `Terminal endpoint request failed (${error.status}).`,
    }
  }

  if (error instanceof Error) {
    return { state: "error", message: error.message }
  }

  return {
    state: "unavailable",
    message: "Terminal endpoint is unavailable right now.",
  }
}

export function useWorkspaceTerminal(
  workspaceId: string,
  options?: { enabled?: boolean },
) {
  const enabled = (options?.enabled ?? false) && !!workspaceId
  const query = useQuery({
    queryKey: workspaceKeys.terminal(workspaceId),
    queryFn: () => WorkspaceService.getTerminalDescriptor(workspaceId),
    enabled,
    retry: false,
    staleTime: 30_000,
  })
  const endpoint = classifyTerminalEndpointState(
    query.error,
    Boolean(query.data),
    query.isLoading || query.isFetching,
    enabled,
  )
  const descriptorFetchedAt =
    query.dataUpdatedAt > 0 ? new Date(query.dataUpdatedAt) : null

  return {
    terminal: query.data ?? null,
    isLoading: query.isLoading || query.isFetching,
    error: query.error,
    endpointState: endpoint.state,
    endpointStateMessage: endpoint.message,
    descriptorFetchedAt,
    requestTerminal: query.refetch,
  }
}
