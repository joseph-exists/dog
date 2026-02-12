/**
 * AgentsHeader
 *
 * Page header for the agents listing. Contains:
 * - Title
 * - Page theme selector (affects entire page surface including header)
 * - Cards theme selector (ambient theme for cards without individual presentation)
 * - Create agent triggers (both simple and wizard)
 * - Layout mode toggle (panels/tabs)
 *
 * Simpler than RoomHeader — no participants, no debug toggle.
 * Same structural role: top bar with title and actions.
 */

import { LayoutGridIcon, PanelLeftIcon } from "lucide-react"

import CreateAgentDialog from "@/components/Agents/Dialogs/CreateAgentDialog"
import CreateAgentusDialog from "@/components/Agents/Dialogs/CreateAgentusDialog"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

import { AMBIENT_THEMES, getThemeById } from "./themes"

export interface AgentsHeaderProps {
  /** Page title */
  title: string
  /** Currently selected page theme ID */
  pageThemeId: string
  /** Currently selected cards theme ID */
  cardsThemeId: string
  /** Page theme change callback */
  onPageThemeChange: (themeId: string) => void
  /** Cards theme change callback */
  onCardsThemeChange: (themeId: string) => void
  /** Current layout mode */
  layoutMode: "panels" | "tabs"
  /** Layout mode change callback */
  onLayoutModeChange: (mode: "panels" | "tabs") => void
}

export function AgentsHeader({
  title,
  pageThemeId,
  cardsThemeId,
  onPageThemeChange,
  onCardsThemeChange,
  layoutMode,
  onLayoutModeChange,
}: AgentsHeaderProps) {
  const pageTheme = getThemeById(pageThemeId)
  const cardsTheme = getThemeById(cardsThemeId)

  return (
    <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0 bg-background text-foreground">
      {/* Left: Title */}
      <h1 className="text-xl font-semibold tracking-tight">{title}</h1>

      {/* Right: Actions */}
      <div className="flex items-center gap-3">
        {/* Page theme selector */}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Select value={pageThemeId} onValueChange={onPageThemeChange}>
                <SelectTrigger className="w-[160px] h-8 text-xs">
                  <SelectValue>Page: {pageTheme.name}</SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {AMBIENT_THEMES.map((theme) => (
                    <SelectItem key={theme.id} value={theme.id}>
                      {theme.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </TooltipTrigger>
            <TooltipContent>Theme for page surface</TooltipContent>
          </Tooltip>
        </TooltipProvider>

        {/* Cards theme selector */}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Select value={cardsThemeId} onValueChange={onCardsThemeChange}>
                <SelectTrigger className="w-[160px] h-8 text-xs">
                  <SelectValue>Cards: {cardsTheme.name}</SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {AMBIENT_THEMES.map((theme) => (
                    <SelectItem key={theme.id} value={theme.id}>
                      {theme.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </TooltipTrigger>
            <TooltipContent>
              Ambient theme for cards without presentation
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        {/* Layout toggle */}
        <ToggleGroup
          type="single"
          value={layoutMode}
          onValueChange={(v) => {
            if (v === "panels" || v === "tabs") onLayoutModeChange(v)
          }}
          className="h-8"
        >
          <ToggleGroupItem
            value="panels"
            aria-label="Panel layout"
            className="h-8 w-8 p-0"
          >
            <PanelLeftIcon className="size-4" />
          </ToggleGroupItem>
          <ToggleGroupItem
            value="tabs"
            aria-label="Tab layout"
            className="h-8 w-8 p-0"
          >
            <LayoutGridIcon className="size-4" />
          </ToggleGroupItem>
        </ToggleGroup>

        {/* Create actions */}
        <CreateAgentDialog />
        <CreateAgentusDialog />
      </div>
    </div>
  )
}
