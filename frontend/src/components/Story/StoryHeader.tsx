// src/components/Story/StoryHeader.tsx

import {
  BookOpen,
  Bug,
  Grid3X3,
  Layout,
  PanelLeftIcon,
  LayoutGridIcon,
  LayoutList,
  Link,
  LayoutPanelLeft,
  MoreVertical,
  Plus,
  Settings,
  Trash2,
  MessageSquare,
  Grid2X2PlusIcon,
  Gamepad2Icon,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import CreateStoryModal from "@/components/Story/Display/CreateStoryModal"
import type * as React from "react"
import { useState } from "react"
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { PanelLayoutDialog } from "@/components/Page/Dialogs/PanelLayoutDialog"

import { PAGE_THEMES, getPageThemeById } from "@/components/Common/Themes/page_themes"
import { CARD_THEMES, getCardThemeById } from "@/components/Common/Themes/card_themes" 

export type StoryType = "process" | "workspace" | "play"

export interface StoryHeaderProps {
  storyId?: string
  /** Page title */
  title: string
  type: StoryType 
  /* not sure if this is the way i want to go or not */
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

const storyTypeIcons: Record<StoryType, React.ElementType>={
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
  pageThemeId,
  cardsThemeId,
  onPageThemeChange,
  onCardsThemeChange,
  layoutMode,
  onLayoutModeChange,
  canEdit,
  onAddPanel,
  onSettings,
  onCopyLink,
  showDebugPanel,
  onToggleDebugPanel,
  devModeEnabled,
  className,
}: StoryHeaderProps) {
  const TypeIcon = storyTypeIcons[type]
  const [layoutDialogOpen, setLayoutDialogOpen] = useState(false)
  const pageTheme = getPageThemeById(pageThemeId)
  const cardsTheme = getCardThemeById(cardsThemeId)

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
        {/* TODO: change to DropdownMenu Page theme selector */}
        
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Select value={pageThemeId} onValueChange={onPageThemeChange}>
                <SelectTrigger className="w-[160px] h-8 text-xs">
                  <SelectValue>Page: {pageTheme.name}</SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {PAGE_THEMES.map((theme) => (
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

        {/* Cards theme selector TODO: DropdownMenu */}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Select value={cardsThemeId} onValueChange={onCardsThemeChange}>
                <SelectTrigger className="w-[160px] h-8 text-xs">
                  <SelectValue>Cards: {cardsTheme.name}</SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {CARD_THEMES.map((theme) => (
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
            {/* {canEdit && onDelete && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={onDelete}
                  className="text-destructive focus:text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Story
                </DropdownMenuItem>
              </>
            )} */}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Panel layout dialog */}
        <PanelLayoutDialog
          open={layoutDialogOpen}
          onOpenChange={setLayoutDialogOpen}
        />


        {/* Create actions   <StoryPlayer /> */}
         <CreateStoryModal />

      </div>

  )
}
