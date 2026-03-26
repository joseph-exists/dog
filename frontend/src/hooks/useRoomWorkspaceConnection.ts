import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback } from "react"
import type { RoomWorkspaceConnectionPurpose } from "@/client"
import type { RoomWorkspaceCandidateViewModel } from "@/services/roomService"
import {
  RoomService,
  type RoomWorkspaceCurrentConnectionViewModel,
} from "@/services/roomService"

export interface RoomWorkspaceCurrentConnectionState {
  connectionId: string
  roomId: string
  workspaceId: string
  workspaceName: string
  purpose: RoomWorkspaceConnectionPurpose
  relationship: RoomWorkspaceCandidateViewModel["relationship"]
  accessLevel: RoomWorkspaceCandidateViewModel["access_level"]
  state: "active" | "unavailable"
  stateReason: string | null
  descriptorId: string
  descriptorStatus: RoomWorkspaceCurrentConnectionViewModel["descriptor"]["status"]
  descriptorIssuedAt: string
  descriptorExpiresAt: string | null
  reason: string | null
  capabilities: string[]
  endpoints: RoomWorkspaceCurrentConnectionViewModel["descriptor"]["endpoints"]
  serviceCount: number
  readyServiceCount: number
  selectedAt: string
}

function roomWorkspaceConnectionKey(roomId: string) {
  return ["rooms", roomId, "workspace-connection", "current"] as const
}

function toState(
  current: RoomWorkspaceCurrentConnectionViewModel | null,
): RoomWorkspaceCurrentConnectionState | null {
  if (!current) return null
  return {
    connectionId: current.connection_id,
    roomId: current.room_id,
    workspaceId: current.workspace_id,
    workspaceName: current.workspace_name,
    purpose: current.purpose,
    relationship: current.relationship,
    accessLevel: current.access_level,
    state: current.state,
    stateReason: current.state_reason,
    descriptorId: current.descriptor.descriptor_id,
    descriptorStatus: current.descriptor.status,
    descriptorIssuedAt: current.descriptor.issued_at.toISOString(),
    descriptorExpiresAt: current.descriptor.expires_at
      ? current.descriptor.expires_at.toISOString()
      : null,
    reason: current.descriptor.reason,
    capabilities: current.descriptor.capabilities,
    endpoints: current.descriptor.endpoints,
    serviceCount: current.service_count,
    readyServiceCount: current.ready_service_count,
    selectedAt: current.selected_at.toISOString(),
  }
}

export function useRoomWorkspaceConnection(roomId: string) {
  const queryClient = useQueryClient()
  const queryKey = roomWorkspaceConnectionKey(roomId)

  const query = useQuery<RoomWorkspaceCurrentConnectionViewModel | null>({
    queryKey,
    queryFn: () => RoomService.getCurrentWorkspaceConnection(roomId),
    staleTime: 1_000,
    refetchInterval: (queryState) => {
      const current = queryState.state.data
      if (!current) return false
      if (current.state === "unavailable") return 15_000
      if (current.descriptor.status === "pending") return 3_000
      if (
        current.descriptor.expires_at &&
        current.descriptor.expires_at.getTime() - Date.now() <= 60_000
      ) {
        return 15_000
      }
      return false
    },
  })

  const setCurrentConnection = useCallback(
    async (params: {
      candidate: RoomWorkspaceCandidateViewModel
      purpose: RoomWorkspaceConnectionPurpose
    }) => {
      const nextState = await RoomService.setCurrentWorkspaceConnection(
        roomId,
        {
          workspace_id: params.candidate.workspace_id,
          purpose: params.purpose,
        },
      )
      queryClient.setQueryData(queryKey, nextState)
      return nextState
    },
    [queryClient, queryKey, roomId],
  )

  const clearCurrentConnection = useCallback(async () => {
    await RoomService.clearCurrentWorkspaceConnection(roomId)
    queryClient.setQueryData(queryKey, null)
  }, [queryClient, queryKey, roomId])

  const refetchCurrentConnection = useCallback(async () => {
    await query.refetch()
  }, [query])

  return {
    currentConnection: toState(query.data ?? null),
    isLoadingCurrentConnection: query.isLoading,
    setCurrentConnection,
    clearCurrentConnection,
    refetchCurrentConnection,
  }
}
