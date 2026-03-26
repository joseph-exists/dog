import type { UserRepoPublic } from "@/client/types.gen"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { getRepoStatus, repoStatusLabel } from "../utils"

const statusClassName: Record<string, string> = {
  pending:
    "border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-300",
  importing: "border-sky-500/40 bg-sky-500/10 text-sky-700 dark:text-sky-300",
  ready:
    "border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
  failed: "border-red-500/40 bg-red-500/10 text-red-700 dark:text-red-300",
}

export function RepoStatusBadge({
  repo,
  className,
}: {
  repo: Pick<UserRepoPublic, "import_status">
  className?: string
}) {
  const status = getRepoStatus(repo)

  return (
    <Badge
      variant="outline"
      className={cn("capitalize", statusClassName[status], className)}
    >
      {repoStatusLabel[status]}
    </Badge>
  )
}
