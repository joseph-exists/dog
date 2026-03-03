import { UserReposService } from "@/client/sdk.gen"
import type { UserRepoPublic } from "@/client/types.gen"
import { isRepoTerminalStatus } from "./utils"

export const repoQueryKeys = {
  all: ["user-repos"] as const,
  detail: (repoId: string) => ["user-repo", repoId] as const,
}

export function getUserReposQueryOptions() {
  return {
    queryKey: repoQueryKeys.all,
    queryFn: () => UserReposService.listUserRepos(),
  }
}

export function getUserRepoQueryOptions(repoId: string) {
  return {
    queryKey: repoQueryKeys.detail(repoId),
    queryFn: () => UserReposService.getUserRepo({ repoId }),
    enabled: !!repoId,
    refetchInterval: (query: { state: { data?: UserRepoPublic } }) => {
      const status = query.state.data?.import_status
      return isRepoTerminalStatus(status) ? false : 3000
    },
  }
}
