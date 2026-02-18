/**
 * Story Page — Route Orchestrator
 *
 * Builds panel configuration and manages page-level state.
 * Delegates all rendering to StoryShell.
 *
 * Follows the orchestrator pattern from r.$roomId.tsx:
 * route owns state + panel registry, shell owns structure + rendering.
 *
 * Theme state uses backend bindings via useUserThemeBindings hook.
 */

import { createFileRoute } from "@tanstack/react-router"
import { StoryGridPanel } from "@/components/Story/panels"
import type { PanelConfig } from "@/components/Story/StoryLayout"
import { StoryShell } from "@/components/Story/StoryShell"
import { usePageThemes } from "@/hooks/useThemeBinding"
import {
  useAvailableThemes,
  useUserThemeBindings,
} from "@/hooks/useThemeRegistry"

export const Route = createFileRoute("/_layout/story")({
  component: StoryPage,
  head: () => ({
    meta: [{ title: "Library" }],
  }),
})

// Context path for theme resolution
const CONTEXT_PATH = ["page:story"]

function StoryPage() {
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
  const { setBinding } = useUserThemeBindings("page:story")

  // Available themes for pickers
  const { themes: availablePageThemes } = useAvailableThemes("page")
  const { themes: availableCardThemes } = useAvailableThemes("card")

  // Theme change handlers
  const handlePageThemeChange = (themeId: string) => {
    setBinding({
      contextKey: "page:story",
      slot: "page",
      themeId,
    })
  }

  const handleCardsThemeChange = (themeId: string) => {
    setBinding({
      contextKey: "page:story",
      slot: "cards",
      themeId,
    })
  }

  // Panel component registry
  const panelComponents: Record<string, () => React.ReactNode> = {
    "story-grid": () => <StoryGridPanel />,
  }

  // Panel configurations — static for now, future: backend-driven
  const panels: PanelConfig[] = [
    {
      id: "story-grid",
      kind: "story-grid",
      prominence: "primary",
      title: "Library",
      render: panelComponents["story-grid"],
    },
  ]

  // Extract resolved theme data
  const pageTheme = themes.page?.theme ?? null
  const cardsTheme = themes.cards?.theme ?? null

  return (
    <StoryShell
      title="Library"
      type="workspace"
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
