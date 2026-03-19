import { createFileRoute } from "@tanstack/react-router"

import {
  WorkspacesShell,
  type PanelConfig,
  WorkspaceCreatePanel,
  WorkspaceListPanel,
} from "@/components/Workspaces"
import { useCreateWorkspace, useWorkspaces } from "@/hooks/useWorkspaces"
import { usePageThemes } from "@/hooks/useThemeBinding"
import { useAvailableThemes, useUserThemeBindings } from "@/hooks/useThemeRegistry"

export const Route = createFileRoute("/_layout/workspaces")({
  component: WorkspacesPage,
  head: () => ({
    meta: [{ title: "Workspaces" }],
  }),
})

function WorkspacesPage() {
  const { data: workspaces = [], isLoading, error } = useWorkspaces()
  const createWorkspace = useCreateWorkspace()

  const contextPath = ["page:workspaces"]
  const { themes } = usePageThemes(contextPath)
  const { setBinding } = useUserThemeBindings("page:workspaces")
  const { themes: availablePageThemes } = useAvailableThemes("page")
  const { themes: availableCardThemes } = useAvailableThemes("card")

  const panels: PanelConfig[] = [
    {
      id: "workspace-list",
      kind: "workspace-list",
      prominence: "primary",
      title: "Workspace Fleet",
      render: () => (
        <WorkspaceListPanel
          workspaces={workspaces}
          isLoading={isLoading}
          error={error}
        />
      ),
    },
    {
      id: "workspace-create",
      kind: "workspace-create",
      prominence: "auxiliary",
      title: "Provision a Workspace",
      render: () => (
        <WorkspaceCreatePanel
          isSubmitting={createWorkspace.isPending}
          onCreate={async (input) => {
            await createWorkspace.mutateAsync(input)
          }}
        />
      ),
    },
  ]

  return (
    <WorkspacesShell
      title="Workspaces"
      description="Provision, monitor, and enter kennel-backed environments."
      panels={panels}
      pageTheme={themes.page?.theme ?? null}
      cardsTheme={themes.cards?.theme ?? null}
      availablePageThemes={availablePageThemes}
      availableCardThemes={availableCardThemes}
      onPageThemeChange={(themeId) =>
        setBinding({ contextKey: "page:workspaces", slot: "page", themeId })
      }
      onCardsThemeChange={(themeId) =>
        setBinding({ contextKey: "page:workspaces", slot: "cards", themeId })
      }
    />
  )
}
