/**
 * AgentsHeader
 *
 * Page header for the agents listing. Contains:
 * - Title
 * - Theme selector (reads from stub themes, does not own state)
 * - Create agent triggers (both simple and wizard)
 * - Layout mode toggle (panels/tabs)
 *
 * Simpler than RoomHeader — no participants, no debug toggle.
 * Same structural role: top bar with title and actions.
 */

import { LayoutGridIcon, PanelLeftIcon } from "lucide-react"

import CreateAgentDialog from "@/components/Agents/Dialogs/CreateAgentDialog"
import CreateAgentusDialog from "@/components/Agents/Dialogs/CreateAgentusDialog"

// import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  ToggleGroup,
  ToggleGroupItem,
} from "@/components/ui/toggle-group"

import { AMBIENT_THEMES } from "./themes"

export interface AgentsHeaderProps {
  /** Page title */
  title: string
  /** Currently selected theme ID */
  selectedThemeId: string
  /** Theme change callback */
  onThemeChange: (themeId: string) => void
  /** Current layout mode */
  layoutMode: "panels" | "tabs"
  /** Layout mode change callback */
  onLayoutModeChange: (mode: "panels" | "tabs") => void
}

export function AgentsHeader({
  title,
  selectedThemeId,
  onThemeChange,
  layoutMode,
  onLayoutModeChange,
}: AgentsHeaderProps) {
  return (
    <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
      {/* Left: Title */}
      <h1 className="text-xl font-semibold tracking-tight">{title}</h1>

      {/* Right: Actions */}
      <div className="flex items-center gap-3">
        {/* Theme selector */}
        <Select value={selectedThemeId} onValueChange={onThemeChange}>
          <SelectTrigger className="w-[140px] h-8 text-xs">
            <SelectValue placeholder="Theme" />
          </SelectTrigger>
          <SelectContent>
            {AMBIENT_THEMES.map((theme) => (
              <SelectItem key={theme.id} value={theme.id}>
                {theme.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Layout toggle */}
        <ToggleGroup
          type="single"
          value={layoutMode}
          onValueChange={(v) => {
            if (v === "panels" || v === "tabs") onLayoutModeChange(v)
          }}
          className="h-8"
        >
          <ToggleGroupItem value="panels" aria-label="Panel layout" className="h-8 w-8 p-0">
            <PanelLeftIcon className="size-4" />
          </ToggleGroupItem>
          <ToggleGroupItem value="tabs" aria-label="Tab layout" className="h-8 w-8 p-0">
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
