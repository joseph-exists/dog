import { cn } from "@/lib/utils"
import type { ThemeViewModel } from "@/services/themeService"
import { themeTokensToStyle } from "@/services/themeService"
import { WorkspacesHeader } from "./WorkspacesHeader"
import { WorkspacesLayout, type PanelConfig } from "./WorkspacesLayout"

export interface WorkspacesShellProps {
  title: string
  description: string
  panels: PanelConfig[]
  pageTheme: ThemeViewModel | null
  cardsTheme: ThemeViewModel | null
  availablePageThemes: ThemeViewModel[]
  availableCardThemes: ThemeViewModel[]
  onPageThemeChange: (themeId: string) => void
  onCardsThemeChange: (themeId: string) => void
  backHref?: string
  className?: string
}

export function WorkspacesShell({
  title,
  description,
  panels,
  pageTheme,
  cardsTheme,
  availablePageThemes,
  availableCardThemes,
  onPageThemeChange,
  onCardsThemeChange,
  backHref,
  className,
}: WorkspacesShellProps) {
  const pageThemeStyle = themeTokensToStyle(pageTheme?.tokens)
  const cardsThemeStyle = themeTokensToStyle(cardsTheme?.tokens)

  return (
    <div style={pageThemeStyle} className={cn("flex h-full min-h-0 flex-col", className)}>
      <WorkspacesHeader
        title={title}
        description={description}
        pageTheme={pageTheme}
        cardsTheme={cardsTheme}
        availablePageThemes={availablePageThemes}
        availableCardThemes={availableCardThemes}
        onPageThemeChange={onPageThemeChange}
        onCardsThemeChange={onCardsThemeChange}
        backHref={backHref}
      />
      <div style={cardsThemeStyle} className="flex-1 min-h-0 overflow-y-auto p-4 md:p-6">
        <WorkspacesLayout panels={panels} />
      </div>
    </div>
  )
}
