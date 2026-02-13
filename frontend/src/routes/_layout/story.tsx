/**
 * Story Page — Route Orchestrator
 *
 * Builds panel configuration and manages page-level state.
 * Delegates all rendering to AgentsShell.
 *
 * Follows the orchestrator pattern from r.$roomId.tsx:
 * route owns state + panel registry, shell owns structure + rendering.
 *
 * Theme state uses nullish coalescing for future user preference integration:
 * when prefs loading is implemented, savedPrefs?.pageTheme will provide the value.
 */

import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"

import { StoryShell } from "@/components/Story/StoryShell"
import type { PanelConfig } from "@/components/Story/StoryLayout"
//import { AgentsGridPanel } from "@/components/Agents/panels"
import { StoryList } from "@/components/Story/StoryList"

export const Route = createFileRoute("/_layout/story")({
  component: StoryPage,
  head: () => ({
    meta: [{ title: "Library" }],
  }),
})

function StoryPage() {
  // Future: useUserPagePrefs("agents") will provide saved preferences
  const savedPrefs = null as { pageTheme?: string; cardsTheme?: string } | null

  // Theme selection — nullish coalescing ready for future prefs integration
  const [pageThemeId, setPageThemeId] = useState(
    savedPrefs?.pageTheme ?? "default",
  )
  const [cardsThemeId, setCardsThemeId] = useState(
    savedPrefs?.cardsTheme ?? "default",
  )

  // Panel component registry
  const panelComponents: Record<string, () => React.ReactNode> = {
    "story-grid": () => <StoryList />,
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

  return (
    <StoryShell
      title="Library"
      type="workspace"
      canEdit={false}
      panels={panels}
      pageThemeId={pageThemeId}
      cardsThemeId={cardsThemeId}
      onPageThemeChange={setPageThemeId}
      onCardsThemeChange={setCardsThemeId}
    />
  )
}
