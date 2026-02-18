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
 * Themes are resolved by the route and passed as ThemeViewModel objects.
 */

import {
  BookOpen,
  Bug,
  Layout,
  LayoutGrid,
  LayoutList,
  Link,
  MessageSquareHeart,
  MoreVertical,
  PianoIcon,
  Pickaxe,
  Plus,
  RockingChair,
  Settings,
  Trash2,
} from "lucide-react"
import type React from "react"
import { useState } from "react"
import CreateAgentDialog from "@/components/Agents/Dialogs/CreateAgentDialog"
import CreateAgentusDialog from "@/components/Agents/Dialogs/CreateAgentusDialog"
import { PanelLayoutDialog } from "@/components/Page/Dialogs/PanelLayoutDialog"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import type { ThemeViewModel } from "@/services/themeService"

export type AgentType = "work" | "boss" | "think" | "be" | "make"

export interface AgentsHeaderProps {
  /** Page title */
  title: string
  type: AgentType
  agentId?: string
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
  /** Current layout mode */
  layoutMode: "panels" | "tabs"
  /** Layout mode change callback */
  onLayoutModeChange: (mode: "panels" | "tabs") => void
  canEdit: boolean
  onAddPanel?: () => void
  /** Room settings callback */
  onSettings?: () => void
  /** Copy link callback */
  onCopyLink?: () => void
  /** Delete room callback */
  onDelete?: () => void
  /** Whether debug panel is shown */
  showDebugPanel?: boolean
  /** Toggle debug panel callback */
  onToggleDebugPanel?: () => void
  /** Show dev mode indicator when internal messages are enabled. */
  devModeEnabled?: boolean
  /** Additional className */
  className?: string
}

const agentTypeIcons: Record<AgentType, React.ElementType> = {
  work: MessageSquareHeart,
  boss: RockingChair,
  think: BookOpen,
  be: Pickaxe,
  make: PianoIcon,
}

export function AgentsHeader({
  title,
  type,
  pageTheme,
  cardsTheme,
  availablePageThemes,
  availableCardThemes,
  onPageThemeChange,
  onCardsThemeChange,
  layoutMode,
  canEdit,
  onLayoutModeChange,
  onAddPanel,
  onSettings,
  onCopyLink,
  onDelete,
  showDebugPanel,
  onToggleDebugPanel,
}: AgentsHeaderProps) {
  const TypeIcon = agentTypeIcons[type]
  const [layoutDialogOpen, setLayoutDialogOpen] = useState(false)

  // Get current theme IDs for select value (fallback to empty string if not resolved)
  const pageThemeId = pageTheme?.id ?? ""
  const cardsThemeId = cardsTheme?.id ?? ""

  return (
    <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0 bg-background text-foreground">
      {/* Left: Sidebar trigger + Title */}
      <div className="flex items-center gap-2">
        <TypeIcon className="h-5 w-5 text-muted-foreground" />
        <SidebarTrigger className="-ml-1 text-muted-foreground" />
        <Separator orientation="vertical" className="h-4" />
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-3">
        {/* Page theme selector */}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Select value={pageThemeId} onValueChange={onPageThemeChange}>
                <SelectTrigger className="w-[160px] h-8 text-xs">
                  <SelectValue>
                    Page: {pageTheme?.name ?? "Loading..."}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {availablePageThemes.map((theme) => (
                    <SelectItem key={theme.id} value={theme.id}>
                      {theme.name}
                      {theme.isSystem && (
                        <span className="ml-2 text-muted-foreground text-xs">
                          (system)
                        </span>
                      )}
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
                  <SelectValue>
                    Cards: {cardsTheme?.name ?? "Loading..."}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {availableCardThemes.map((theme) => (
                    <SelectItem key={theme.id} value={theme.id}>
                      {theme.name}
                      {theme.isSystem && (
                        <span className="ml-2 text-muted-foreground text-xs">
                          (system)
                        </span>
                      )}
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
          className="hidden md:flex"
        >
          <ToggleGroupItem value="panels" aria-label="Panel layout">
            <LayoutGrid className="h-4 w-4" />
          </ToggleGroupItem>
          <ToggleGroupItem value="tabs" aria-label="Tab layout">
            <LayoutList className="h-4 w-4" />
          </ToggleGroupItem>
        </ToggleGroup>

        {/* Create actions */}
        <CreateAgentDialog />
        <CreateAgentusDialog />

        {/* Room menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {type === "boss" && onAddPanel && (
              <DropdownMenuItem onClick={onAddPanel}>
                <Plus className="h-4 w-4 mr-2" />
                Add Panel
              </DropdownMenuItem>
            )}
            {onCopyLink && (
              <DropdownMenuItem onClick={onCopyLink}>
                <Link className="h-4 w-4 mr-2" />
                Copy Link
              </DropdownMenuItem>
            )}
            {onToggleDebugPanel && (
              <DropdownMenuItem onClick={onToggleDebugPanel}>
                <Bug className="h-4 w-4 mr-2" />
                {showDebugPanel ? "Hide Debug Panel" : "Show Debug Panel"}
              </DropdownMenuItem>
            )}
            <DropdownMenuItem onClick={() => setLayoutDialogOpen(true)}>
              <Layout className="h-4 w-4 mr-2" />
              Panel Layout
            </DropdownMenuItem>
            {canEdit && onSettings && (
              <DropdownMenuItem onClick={onSettings}>
                <Settings className="h-4 w-4 mr-2" />
                Room Settings
              </DropdownMenuItem>
            )}
            {canEdit && onDelete && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={onDelete}
                  className="text-destructive focus:text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Room
                </DropdownMenuItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Panel layout dialog */}
      <PanelLayoutDialog
        open={layoutDialogOpen}
        onOpenChange={setLayoutDialogOpen}
        entityId={null}
        context="room"
      />
    </div>
  )
}
