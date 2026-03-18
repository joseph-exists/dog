import { createFileRoute } from "@tanstack/react-router"

import {
  WorkspacesShell,
  type PanelConfig,
  WorkspaceControlsPanel,
  WorkspaceDetailsPanel,
  WorkspaceTerminalPanel,
} from "@/components/Workspaces"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useWorkspace } from "@/hooks/useWorkspace"
import { useWorkspaceTerminal } from "@/hooks/useWorkspaceTerminal"
import { useDestroyWorkspace, useStopWorkspace } from "@/hooks/useWorkspaces"
import { usePageThemes } from "@/hooks/useThemeBinding"
import { useAvailableThemes, useUserThemeBindings } from "@/hooks/useThemeRegistry"

export const Route = createFileRoute("/_layout/workspace/$workspaceId")({
  component: WorkspaceDetailPage,
  head: () => ({
    meta: [{ title: "Workspace" }],
  }),
})

function WorkspaceDetailPage() {
  const { workspaceId } = Route.useParams()
  const workspaceQuery = useWorkspace(workspaceId)
  const terminalQuery = useWorkspaceTerminal(workspaceId, { enabled: false })
  const stopWorkspace = useStopWorkspace()
  const destroyWorkspace = useDestroyWorkspace()

  const contextPath = ["page:workspace"]
  const { themes } = usePageThemes(contextPath)
  const { setBinding } = useUserThemeBindings("page:workspace")
  const { themes: availablePageThemes } = useAvailableThemes("page")
  const { themes: availableCardThemes } = useAvailableThemes("card")

  if (workspaceQuery.isLoading || !workspaceQuery.data) {
    return (
      <div className="p-6">
        <Card>
          <CardHeader>
            <CardTitle>Loading workspace</CardTitle>
            <CardDescription>Preparing the workspace detail view.</CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  if (workspaceQuery.error) {
    return (
      <div className="p-6">
        <Card>
          <CardHeader>
            <CardTitle>Failed to load workspace</CardTitle>
            <CardDescription>{workspaceQuery.error.message}</CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  const workspace = workspaceQuery.data

  const panels: PanelConfig[] = [
    {
      id: "workspace-terminal",
      kind: "workspace-terminal",
      prominence: "primary",
      title: "Terminal",
      render: () => (
        <WorkspaceTerminalPanel
          workspace={workspace}
          terminal={terminalQuery.terminal}
          isLoadingTerminal={terminalQuery.isLoading}
          terminalError={terminalQuery.error}
          onRequestTerminal={() => terminalQuery.requestTerminal()}
        />
      ),
    },
    {
      id: "workspace-details",
      kind: "workspace-details",
      prominence: "auxiliary",
      title: "Details",
      render: () => <WorkspaceDetailsPanel workspace={workspace} />,
    },
    {
      id: "workspace-controls",
      kind: "workspace-controls",
      prominence: "auxiliary",
      title: "Controls",
      render: () => (
        <WorkspaceControlsPanel
          workspace={workspace}
          isStopping={stopWorkspace.isPending}
          isDestroying={destroyWorkspace.isPending}
          onStop={() => stopWorkspace.mutateAsync(workspace.id)}
          onDestroy={() => destroyWorkspace.mutateAsync(workspace.id)}
        />
      ),
    },
  ]

  return (
    <WorkspacesShell
      title={workspace.name}
      description="Operate a single kennel-backed environment and request its direct terminal endpoint."
      panels={panels}
      pageTheme={themes.page?.theme ?? null}
      cardsTheme={themes.cards?.theme ?? null}
      availablePageThemes={availablePageThemes}
      availableCardThemes={availableCardThemes}
      onPageThemeChange={(themeId) =>
        setBinding({ contextKey: "page:workspace", slot: "page", themeId })
      }
      onCardsThemeChange={(themeId) =>
        setBinding({ contextKey: "page:workspace", slot: "cards", themeId })
      }
      backHref="/workspaces"
    />
  )
}
