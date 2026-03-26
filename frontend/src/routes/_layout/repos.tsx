import { createFileRoute } from "@tanstack/react-router"
import {
  ImportRepoDialog,
  type RepoPanelConfig,
  RepoShell,
} from "@/components/Repo"
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
      kind: "repoOverview",
      prominence: "primary",
      title: "Repositories",
      render: panelComponents["repos-grid"],
    },
  ]

  return (
    <RepoShell
      title="Repositories"
      description="View, import, and browse the platform-managed repositories available to you, including shared public repos and viewer-ready imports."
      panels={panels}
      actions={<ImportRepoDialog />}
    />
  )
}
