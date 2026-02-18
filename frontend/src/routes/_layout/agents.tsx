/**
 * Agents Page — Route Orchestrator
 *
 * Builds panel configuration and manages page-level state.
 * Delegates all rendering to AgentsShell.
 *
 * Follows the orchestrator pattern from r.$roomId.tsx:
 * route owns state + panel registry, shell owns structure + rendering.
 *
 * Theme state uses backend bindings via useUserThemeBindings hook.
 */

import { createFileRoute } from "@tanstack/react-router"

import { AgentsShell, type PanelConfig } from "@/components/Agents"
import { AgentsGridPanel } from "@/components/Agents/panels"
import { usePageThemes } from "@/hooks/useThemeBinding"
import {
  useAvailableThemes,
  useUserThemeBindings,
} from "@/hooks/useThemeRegistry"

export const Route = createFileRoute("/_layout/agents")({
  component: AgentsPage,
  head: () => ({
    meta: [{ title: "My Agents" }],
  }),
})

// Context path for theme resolution
const CONTEXT_PATH = ["page:agents"]

function AgentsPage() {
  // ─────────────────────────────────────────────────────────────────────────
  // Theme Resolution & Bindings
  //
  // Resolves effective themes from the cascade:
  //   1. Authored bindings (not applicable for listing page)
  //   2. User preference bindings
  //   3. System defaults
  // ─────────────────────────────────────────────────────────────────────────

  // Resolve current themes
  const { themes, isLoading: isResolvingThemes } = usePageThemes(CONTEXT_PATH)

  // User binding management
  const { setBinding } = useUserThemeBindings("page:agents")

  // Available themes for pickers
  const { themes: availablePageThemes } = useAvailableThemes("page")
  const { themes: availableCardThemes } = useAvailableThemes("card")

  // Theme change handlers
  const handlePageThemeChange = (themeId: string) => {
    setBinding({
      contextKey: "page:agents",
      slot: "page",
      themeId,
    })
  }

  const handleCardsThemeChange = (themeId: string) => {
    setBinding({
      contextKey: "page:agents",
      slot: "cards",
      themeId,
    })
  }

  // Panel component registry
  const panelComponents: Record<string, () => React.ReactNode> = {
    "agents-grid": () => <AgentsGridPanel />,
  }

  // Panel configurations — static for now, future: backend-driven
  const panels: PanelConfig[] = [
    {
      id: "agents-grid",
      kind: "agents-grid",
      prominence: "primary",
      title: "Agents",
      render: panelComponents["agents-grid"],
    },
  ]

  // Extract resolved theme data
  const pageTheme = themes.page?.theme ?? null
  const cardsTheme = themes.cards?.theme ?? null

  return (
    <AgentsShell
      title="Agents"
      type="work"
      canEdit={false}
      panels={panels}
      // New theme props
      pageTheme={pageTheme}
      cardsTheme={cardsTheme}
      availablePageThemes={availablePageThemes}
      availableCardThemes={availableCardThemes}
      onPageThemeChange={handlePageThemeChange}
      onCardsThemeChange={handleCardsThemeChange}
      isLoadingThemes={isResolvingThemes}
    />
  )
}
