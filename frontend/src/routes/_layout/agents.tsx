/**
 * Agents Page — Route Orchestrator
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

import { AgentsShell, type PanelConfig } from "@/components/Agents"
import { AgentsGridPanel } from "@/components/Agents/panels"

export const Route = createFileRoute("/_layout/agents")({
  component: AgentsPage,
  head: () => ({
    meta: [{ title: "My Agents" }],
  }),
})

function AgentsPage() {
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

  return (
    <AgentsShell
      title="Agents"
      type="work"
      canEdit={false}
      panels={panels}
      pageThemeId={pageThemeId}
      cardsThemeId={cardsThemeId}
      onPageThemeChange={setPageThemeId}
      onCardsThemeChange={setCardsThemeId}
    />
  )
}
