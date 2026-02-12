// src/components/Page/PageShell.tsx
import * as React from 'react'
import { cn } from "@/lib/utils"
import { StoryHeader } from "./StoryHeader"
import { StoryLayout, type PanelConfig } from "./StoryLayout"
import { getPageThemeById, getPageThemeStyle } from "@/components/Common/Themes/page_themes"
import { getCardThemeById, getCardThemeStyle } from "@/components/Common/Themes/card_themes"


export interface StoryShellProps {
  /** Page title */
  title: string
  /** Panel configurations */
  panels: PanelConfig[]
  /** Currently selected page theme ID */
  pageThemeId: string
  /** Currently selected cards theme ID */
  cardsThemeId: string
  /** Page theme change callback */
  onPageThemeChange: (themeId: string) => void
  /** Cards theme change callback */
  onCardsThemeChange: (themeId: string) => void
  /** Additional className */
  className?: string
  // entityType: string
  // entityId: string
  // isOwner: boolean
  // onDelete?: () => void
}

/**
 * StoryShell - Main container that orchestrates the page layout
 *
 * Uses usePageEditor hook to manage layout state and editing.
 * Renders the PageHeader, PageLayout with blocks, and editor components.
 */
export function StoryShell({
  title,
  panels,
  pageThemeId,
  cardsThemeId,
  onPageThemeChange,
  onCardsThemeChange,
  className,
}: StoryShellProps) {
  const [layoutMode, setLayoutMode] = React.useState<"panels" | "tabs">("panels",)
  // const [paletteOpen, setPaletteOpen] = useState(true)
  // const [targetColumn, setTargetColumn] = useState<"primary" | "auxiliary">(
  //   "primary",
  // )

  const pageTheme = getPageThemeById(pageThemeId)
  const cardsTheme = getCardThemeById(cardsThemeId)
  
  return (
  // outermost: page theme scope (affects header and content)
  // transparent wrapper - only sets CSS variables does not render a surface
  // downstream components render with inherited variables
    <div
      style={getPageThemeStyle(pageTheme)}
      className={cn("flex flex-col h-full", className)}
    >
      <StoryHeader
        title={title}
        pageThemeId={pageThemeId}
        cardsThemeId={cardsThemeId}
        onPageThemeChange={onPageThemeChange}
        onCardsThemeChange={onCardsThemeChange}
        layoutMode={layoutMode}
        onLayoutModeChange={setLayoutMode}
      />

      {/* Inner: Cards theme scope (overrides page theme for card areas) */}
      {/* Transparent wrapper — only sets CSS variables, does not render a surface */}
      <div style={getCardThemeStyle(cardsTheme)} className="flex-1 min-h-0">
        <StoryLayout panels={panels} mode={layoutMode} />
      </div>
    </div>
  )
}
