import { useQuery } from "@tanstack/react-query"
import { TesserService } from "@/services/tesserService"
import { tesserQueryKeys } from "./useTesser"

const TERMINAL_JOB_STATUSES = new Set(["completed", "ok", "error", "failed", "not_found"])

export function isTerminalTesserJobStatus(status: string | null | undefined): boolean {
  return status ? TERMINAL_JOB_STATUSES.has(status) : false
}

export function useTesserJob(
  jobId: string,
  options?: {
    enabled?: boolean
    refetchIntervalMs?: number
  },
) {
  const enabled = (options?.enabled ?? true) && Boolean(jobId)

  return useQuery({
    queryKey: tesserQueryKeys.job(jobId),
    queryFn: () => TesserService.getJobStatus(jobId),
    enabled,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (!enabled || isTerminalTesserJobStatus(status)) {
        return false
      }
      return options?.refetchIntervalMs ?? 2000
    },
  })
}
