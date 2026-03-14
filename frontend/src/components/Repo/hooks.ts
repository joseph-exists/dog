import { UserReposService } from "@/client/sdk.gen"
import type { UserRepoPublic } from "@/client/types.gen"
import { isRepoTerminalStatus } from "./utils"

export const repoQueryKeys = {
  all: ["user-repos"] as const,
  detail: (repoId: string) => ["user-repo", repoId] as const,
  head: (repoId: string, ref?: string | null) =>
    ["user-repo-head", repoId, ref?.trim() || "__default__"] as const,
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

export function getUserRepoHeadQueryOptions(
  repoId: string,
  ref?: string | null,
) {
  const normalizedRef = ref?.trim() || null
  return {
    queryKey: repoQueryKeys.head(repoId, normalizedRef),
    queryFn: async () => {
      const view = await UserReposService.getUserRepoTree({
        repoId,
        ref: normalizedRef || undefined,
        commitLimit: 1,
      })
      return {
        ref: view.ref,
        expectedHeadSha: view.summary.latest_commit_sha || null,
      }
    },
    enabled: !!repoId,
    staleTime: 10_000,
    refetchOnWindowFocus: false,
  }
}
