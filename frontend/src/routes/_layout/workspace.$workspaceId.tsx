import { useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  type PanelConfig,
  WorkspaceControlsPanel,
  WorkspaceDetailsPanel,
  WorkspaceProjectPanel,
  WorkspacesShell,
  WorkspaceTerminalPanel,
} from "@/components/Workspaces"
import useAuth from "@/hooks/useAuth"
import {
  useAttachProjectResource,
  useDetachProjectResource,
  useProjectsList,
} from "@/hooks/useProjects"
import { usePageThemes } from "@/hooks/useThemeBinding"
import {
  useAvailableThemes,
  useUserThemeBindings,
} from "@/hooks/useThemeRegistry"
import { useWorkspace } from "@/hooks/useWorkspace"
import {
  useDestroyWorkspace,
  useStartWorkspace,
  useStopWorkspace,
  workspaceKeys,
} from "@/hooks/useWorkspaces"
import { useWorkspaceTerminal } from "@/hooks/useWorkspaceTerminal"

export const Route = createFileRoute("/_layout/workspace/$workspaceId")({
  component: WorkspaceDetailPage,
  head: () => ({
    meta: [{ title: "Workspace" }],
  }),
})

function WorkspaceDetailPage() {
  const { workspaceId } = Route.useParams()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const workspaceQuery = useWorkspace(workspaceId)
  const terminalQuery = useWorkspaceTerminal(workspaceId, { enabled: false })
  const projectsQuery = useProjectsList()
  const startWorkspace = useStartWorkspace()
  const stopWorkspace = useStopWorkspace()
  const destroyWorkspace = useDestroyWorkspace()
  const attachProjectResource = useAttachProjectResource()
  const detachProjectResource = useDetachProjectResource()

  const contextPath = ["page:workspace"]
  const { themes } = usePageThemes(contextPath)
  const { setBinding } = useUserThemeBindings("page:workspace")
  const { themes: availablePageThemes } = useAvailableThemes("page")
  const { themes: availableCardThemes } = useAvailableThemes("card")

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

  if (workspaceQuery.isLoading || !workspaceQuery.data) {
    return (
      <div className="p-6">
        <Card>
          <CardHeader>
            <CardTitle>Loading workspace</CardTitle>
            <CardDescription>
              Preparing the workspace detail view.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  const workspace = workspaceQuery.data
  const canManageProjectAssignment = user?.id === workspace.ownerId

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
          endpointState={terminalQuery.endpointState}
          endpointStateMessage={terminalQuery.endpointStateMessage}
          endpointFetchedAt={terminalQuery.descriptorFetchedAt}
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
      id: "workspace-project",
      kind: "workspace-project",
      prominence: "auxiliary",
      title: "Project Assignment",
      render: () => (
        <WorkspaceProjectPanel
          workspace={workspace}
          projects={projectsQuery.data ?? []}
          isAssigning={attachProjectResource.isPending}
          isDetaching={detachProjectResource.isPending}
          canManageAssignment={canManageProjectAssignment}
          onAssign={async (projectId) => {
            await attachProjectResource.mutateAsync({
              projectId,
              input: {
                resource_type: "workspace",
                resource_id: workspace.id,
              },
            })
            await queryClient.invalidateQueries({ queryKey: workspaceKeys.all })
          }}
          onDetach={async () => {
            if (!workspace.projectId) return
            await detachProjectResource.mutateAsync({
              projectId: workspace.projectId,
              input: {
                resource_type: "workspace",
                resource_id: workspace.id,
              },
            })
            await queryClient.invalidateQueries({ queryKey: workspaceKeys.all })
          }}
        />
      ),
    },
    {
      id: "workspace-controls",
      kind: "workspace-controls",
      prominence: "auxiliary",
      title: "Controls",
      render: () => (
        <WorkspaceControlsPanel
          workspace={workspace}
          isStarting={startWorkspace.isPending}
          isStopping={stopWorkspace.isPending}
          isDestroying={destroyWorkspace.isPending}
          onStart={() => startWorkspace.mutateAsync(workspace.id)}
          onStop={() => stopWorkspace.mutateAsync(workspace.id)}
          onDestroy={() => destroyWorkspace.mutateAsync(workspace.id)}
        />
      ),
    },
  ]

  return (
    <WorkspacesShell
      title={workspace.name}
      description={
        workspace.accessLevel === "manage"
          ? "Operate a single kennel-backed environment and manage its runtime directly."
          : workspace.accessLevel === "use"
            ? "Use a project-shared kennel-backed environment through the capabilities exposed to your account."
            : "Inspect a project-visible kennel-backed environment and its current operational state."
      }
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
      defaultLayoutMode="tabs"
    />
  )
}
