/**
 * Agents Page — Route Orchestrator
 *
 * Builds panel configuration and manages page-level state.
 * Delegates all rendering to AgentsShell.
 *
 * Follows the orchestrator pattern from r.$roomId.tsx:
 * route owns state + panel registry, shell owns structure + rendering.
 */

import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"

import { AgentsShell, type PanelConfig } from "@/components/Agents/AgentsShell"
import { AgentsGridPanel } from "@/components/Agents/AgentsShell/panels"

export const Route = createFileRoute("/_layout/agents")({
  component: AgentsPage,
  head: () => ({
    meta: [{ title: "My Agents" }],
  }),
})

function AgentsPage() {
  // Theme selection — local state for now, future: persisted preference
  const [selectedThemeId, setSelectedThemeId] = useState("default")

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
      panels={panels}
      selectedThemeId={selectedThemeId}
      onThemeChange={setSelectedThemeId}
    />
  )
}
