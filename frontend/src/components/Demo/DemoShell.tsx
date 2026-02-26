import React from "react"
import { cn } from "@/lib/utils"
import type { DemoConfigViewModel } from "@/services/demoService"
import {
  type ThemeViewModel,
  themeTokensToStyle,
} from "@/services/themeService"
import { DemoHeader } from "./DemoHeader"
import { DemoLayout, type PanelConfig } from "./DemoLayout"

export interface DemoShellBlockRenderItem {
  id: string
  content: React.ReactNode
  visibilityMode: "visible" | "hidden_mounted"
  style?: React.CSSProperties
}

export interface DemoShellProps {
  demoConfig: DemoConfigViewModel
  /** Panel configurations */
  panels: PanelConfig[]
  /** Blocks rendered above panel layout */
  topBlocks?: DemoShellBlockRenderItem[]
  /** Blocks rendered in primary support region */
  primaryBlocks?: DemoShellBlockRenderItem[]
  /** Blocks rendered in auxiliary support region */
  auxiliaryBlocks?: DemoShellBlockRenderItem[]
  /** Blocks rendered below panel layout */
  footerBlocks?: DemoShellBlockRenderItem[]
  /** Auto-respond toggle state */
  autoRespond: boolean
  /** Auto-respond toggle handler */
  onAutoRespondChange: (value: boolean) => void
  /** Room socket status */
  isConnected: boolean
  /** Resolved page theme (from usePageThemes hook) */
  pageTheme: ThemeViewModel | null
  /** Resolved cards theme (from usePageThemes hook) */
  cardsTheme: ThemeViewModel | null
  /** Available page themes for picker */
  availablePageThemes: ThemeViewModel[]
  /** Available card themes for picker */
  availableCardThemes: ThemeViewModel[]
  /** Page theme change callback */
  onPageThemeChange: (themeId: string) => void
  /** Cards theme change callback */
  onCardsThemeChange: (themeId: string) => void
  /** Additional className */
  className?: string
}

export function getDemoBlockContainerClassName(
  visibilityMode: DemoShellBlockRenderItem["visibilityMode"],
): string {
  return cn(
    "rounded-md border bg-card/50",
    visibilityMode === "hidden_mounted" && "hidden",
  )
}

export function DemoShell({
  demoConfig,
  panels,
  topBlocks = [],
  primaryBlocks = [],
  auxiliaryBlocks = [],
  footerBlocks = [],
  autoRespond,
  onAutoRespondChange,
  isConnected,
  pageTheme,
  cardsTheme,
  availablePageThemes,
  availableCardThemes,
  onPageThemeChange,
  onCardsThemeChange,
  className,
}: DemoShellProps) {
  const [layoutMode] = React.useState<"panels" | "tabs">("panels")

  // Convert theme tokens to CSS style objects.
  const pageThemeStyle = themeTokensToStyle(pageTheme?.tokens)
  const cardsThemeStyle = themeTokensToStyle(cardsTheme?.tokens)

  return (
    // Outermost: Page theme scope (affects header + content)
    // Transparent wrapper — only sets CSS variables, does not render a surface
    // Downstream components (Header, PanelContainer) render with inherited variables
    <div
      style={pageThemeStyle}
      className={cn("demo-shell flex flex-col h-full min-h-0", className)}
    >
      <DemoHeader
        title={demoConfig.title}
        description={demoConfig.description ?? ""}
        autoRespond={autoRespond}
        onAutoRespondChange={onAutoRespondChange}
        isConnected={isConnected}
        pageTheme={pageTheme}
        cardsTheme={cardsTheme}
        availablePageThemes={availablePageThemes}
        availableCardThemes={availableCardThemes}
        onPageThemeChange={onPageThemeChange}
        onCardsThemeChange={onCardsThemeChange}
      />

      {/* Inner: Cards theme scope (overrides page theme for card areas) */}
      {/* Transparent wrapper — only sets CSS variables, does not render a surface */}
      <div
        style={cardsThemeStyle}
        className="flex-1 min-h-0 flex flex-col gap-2 p-2 overflow-y-auto overflow-x-hidden"
      >
        {topBlocks.length > 0 && (
          <div className="space-y-2">
            {topBlocks.map((block) => (
              <div
                key={`top-block-${block.id}`}
                className={getDemoBlockContainerClassName(block.visibilityMode)}
                style={block.style}
              >
                {block.content}
              </div>
            ))}
          </div>
        )}

        {(primaryBlocks.length > 0 || auxiliaryBlocks.length > 0) && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
            <div className="space-y-2">
              {primaryBlocks.map((block) => (
                <div
                  key={`primary-block-${block.id}`}
                  className={getDemoBlockContainerClassName(
                    block.visibilityMode,
                  )}
                  style={block.style}
                >
                  {block.content}
                </div>
              ))}
            </div>
            <div className="space-y-2">
              {auxiliaryBlocks.map((block) => (
                <div
                  key={`aux-block-${block.id}`}
                  className={getDemoBlockContainerClassName(
                    block.visibilityMode,
                  )}
                  style={block.style}
                >
                  {block.content}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex-1 min-h-0">
          <DemoLayout panels={panels} mode={layoutMode} />
        </div>

        {footerBlocks.length > 0 && (
          <div className="space-y-2">
            {footerBlocks.map((block) => (
              <div
                key={`footer-block-${block.id}`}
                className={getDemoBlockContainerClassName(block.visibilityMode)}
                style={block.style}
              >
                {block.content}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
