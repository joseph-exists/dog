import { useQuery } from "@tanstack/react-query"
import { AgentInvocationsService } from "@/client"

export const agentInvocationKeys = {
  all: ["agent-invocations"] as const,
  list: (roomId: string, limit: number) =>
    [...agentInvocationKeys.all, "list", roomId, limit] as const,
  detail: (roomId: string, invocationId: string) =>
    [...agentInvocationKeys.all, "detail", roomId, invocationId] as const,
}

export function useAgentInvocations({
  roomId,
  limit = 20,
  enabled = true,
  live = false,
}: {
  roomId: string | null | undefined
  limit?: number
  enabled?: boolean
  live?: boolean
}) {
  return useQuery({
    queryKey: roomId
      ? agentInvocationKeys.list(roomId, limit)
      : [...agentInvocationKeys.all, "list", "none", limit],
    queryFn: () =>
      AgentInvocationsService.listAgentInvocations({
        roomId: roomId!,
        limit,
      }),
    enabled: enabled && Boolean(roomId),
    refetchInterval: live ? 3000 : false,
  })
}

export function useAgentInvocationDetail({
  roomId,
  invocationId,
  enabled = true,
}: {
  roomId: string | null | undefined
  invocationId: string | null | undefined
  enabled?: boolean
}) {
  return useQuery({
    queryKey:
      roomId && invocationId
        ? agentInvocationKeys.detail(roomId, invocationId)
        : [...agentInvocationKeys.all, "detail", "none", "none"],
    queryFn: () =>
      AgentInvocationsService.getAgentInvocation({
        roomId: roomId!,
        invocationId: invocationId!,
      }),
    enabled: enabled && Boolean(roomId) && Boolean(invocationId),
  })
}
