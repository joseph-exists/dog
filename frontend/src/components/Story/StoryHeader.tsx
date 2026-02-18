// src/components/Story/StoryHeader.tsx

import {
  Bug,
  Gamepad2Icon,
  Grid2X2PlusIcon,
  Layout,
  Link,
  MessageSquare,
  MoreVertical,
  Plus,
  Settings,
} from "lucide-react"
import type * as React from "react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import type { ThemeViewModel } from "@/services/themeService"
import { PanelLayoutDialog } from "./Dialogs/PanelLayoutDialog"

export type StoryType = "process" | "workspace" | "play"

export interface StoryHeaderProps {
  storyId?: string
  /** Page title */
  title: string
  type: StoryType
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
  /** Add panel callback (workspace only) */
  onAddPanel?: () => void
  /** Room settings callback */
  onSettings?: () => void
  /** Copy link callback */
  onCopyLink?: () => void
  /** Delete room callback */
  onDelete?: () => void

  showDebugPanel?: boolean
  /** Toggle debug panel callback */
  onToggleDebugPanel?: () => void
  /** Show dev mode indicator when internal messages are enabled. */
  devModeEnabled?: boolean
  /** Additional className */
  className?: string
}

const storyTypeIcons: Record<StoryType, React.ElementType> = {
  process: MessageSquare,
  workspace: Grid2X2PlusIcon,
  play: Gamepad2Icon,
}

/**
 * PageHeader - Header component for entity pages
 *
 * Displays breadcrumb navigation, timestamps, and action buttons.
 * Actions vary based on whether the current user is the owner.
 */
export function StoryHeader({
  storyId,
  type,
  title,
  pageTheme,
  cardsTheme,
  availablePageThemes,
  availableCardThemes,
  onPageThemeChange,
  onCardsThemeChange,
  layoutMode: _layoutMode,
  onLayoutModeChange: _onLayoutModeChange,
  canEdit,
  onAddPanel,
  onSettings,
  onCopyLink,
  showDebugPanel,
  onToggleDebugPanel,
}: StoryHeaderProps) {
  const TypeIcon = storyTypeIcons[type]
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
                <SelectTrigger className="w-40 h-8 text-xs">
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
                <SelectTrigger className="w-40 h-8 text-xs">
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

        {/* StoryMenu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {type === "workspace" && onAddPanel && (
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
                Story Settings
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Panel layout dialog */}
      <PanelLayoutDialog
        open={layoutDialogOpen}
        onOpenChange={setLayoutDialogOpen}
        storyId={storyId ?? null}
        isOwner={canEdit}
        userPermission={canEdit ? "owner" : "none"}
      />
    </div>
  )
}
