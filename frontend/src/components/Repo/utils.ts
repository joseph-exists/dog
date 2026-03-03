import type { UserRepoImportStatus, UserRepoPublic } from "@/client/types.gen"

export const repoStatusLabel: Record<UserRepoImportStatus, string> = {
  pending: "Pending",
  importing: "Importing",
  ready: "Ready",
  failed: "Failed",
}

export function getRepoStatus(repo: Pick<UserRepoPublic, "import_status">) {
  return repo.import_status ?? "pending"
}

export function isRepoTerminalStatus(status: UserRepoImportStatus | undefined) {
  return status === "ready" || status === "failed"
}

export function formatRepoDate(value?: string | null) {
  if (!value) return "Not available"

  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return "Not available"

  return parsed.toLocaleString()
}

export function formatRepoShortDate(value?: string | null) {
  if (!value) return "Not available"

  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return "Not available"

  return parsed.toLocaleDateString()
}

export function getRepoInitial(name: string) {
  return name.trim().charAt(0).toUpperCase() || "R"
}
