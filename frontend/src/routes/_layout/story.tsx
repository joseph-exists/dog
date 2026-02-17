/**
 * Story Page — Route Orchestrator
 *
 * Builds panel configuration and manages page-level state.
 * Delegates all rendering to StoryShell.
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
import { StoryGridPanel } from "@/components/Story/panels"

export const Route = createFileRoute("/_layout/story")({
  component: StoryPage,
  head: () => ({
    meta: [{ title: "Library" }],
  }),
})

// localStorage keys for theme persistence
const STORAGE_KEYS = {
  pageTheme: "story-page-theme",
  cardsTheme: "story-cards-theme",
} as const

function StoryPage() {
  // ─────────────────────────────────────────────────────────────────────────
  // Theme Persistence (localStorage)
  //
  // TODO: Replace with useUserPagePrefs("story") when backend user preferences
  // are implemented. The hook should:
  //   1. Fetch user preferences from backend on mount
  //   2. Return { pageTheme, cardsTheme } with defaults if not set
  //   3. Provide updatePrefs(key, value) that persists to backend
  //   4. Use optimistic updates for responsive UX
  //
  // When migrating, replace the useState + handlers below with:
  //   const { prefs, updatePageTheme, updateCardsTheme } = useUserPagePrefs("story")
  // ─────────────────────────────────────────────────────────────────────────

  // Theme selection with localStorage persistence
  const [pageThemeId, setPageThemeId] = useState(() =>
    localStorage.getItem(STORAGE_KEYS.pageTheme) ?? "default"
  )
  const [cardsThemeId, setCardsThemeId] = useState(() =>
    localStorage.getItem(STORAGE_KEYS.cardsTheme) ?? "default"
  )

  // Handlers that persist to localStorage
  const handlePageThemeChange = (themeId: string) => {
    setPageThemeId(themeId)
    localStorage.setItem(STORAGE_KEYS.pageTheme, themeId)
  }

  const handleCardsThemeChange = (themeId: string) => {
    setCardsThemeId(themeId)
    localStorage.setItem(STORAGE_KEYS.cardsTheme, themeId)
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

  return (
    <StoryShell
      title="Library"
      type="workspace"
      canEdit={false}
      panels={panels}
      pageThemeId={pageThemeId}
      cardsThemeId={cardsThemeId}
      onPageThemeChange={handlePageThemeChange}
      onCardsThemeChange={handleCardsThemeChange}
    />
  )
}
