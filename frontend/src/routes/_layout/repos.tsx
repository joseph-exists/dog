import { createFileRoute } from "@tanstack/react-router"
import { ImportRepoDialog, RepoShell, type RepoPanelConfig } from "@/components/Repo"
import { ReposGridPanel } from "@/components/Repo/panels"

export const Route = createFileRoute("/_layout/repos")({
  component: ReposPage,
  head: () => ({
    meta: [{ title: "My Repositories" }],
  }),
})

function ReposPage() {
  const panelComponents: Record<string, () => React.ReactNode> = {
    "repos-grid": () => <ReposGridPanel />,
  }

  const panels: RepoPanelConfig[] = [
    {
      id: "repos-grid",
      kind: "repos-grid",
      prominence: "primary",
      title: "Repositories",
      render: panelComponents["repos-grid"],
    },
  ]

  return (
    <RepoShell
      title="Repositories"
      description="View, import, and review the repositories this platform manages on your behalf."
      panels={panels}
      actions={<ImportRepoDialog />}
    />
  )
}
