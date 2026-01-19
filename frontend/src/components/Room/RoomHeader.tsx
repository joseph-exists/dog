/**
 * RoomHeader
 *
 * Room header with title, participants, and actions.
 * Consistent across all room types.
 */

import {
  BookOpen,
  Grid3X3,
  LayoutGrid,
  LayoutList,
  Link,
  MessageSquare,
  MoreVertical,
  Plus,
  Settings,
  Trash2,
} from "lucide-react"
import type * as React from "react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { cn } from "@/lib/utils"
import {
  type Participant,
  ParticipantStack,
} from "./primitives/ParticipantStack"

export type RoomType = "chat" | "story" | "workspace"

interface RoomHeaderProps {
  /** Room title */
  title: string
  /** Room type */
  type: RoomType
  /** Participants in the room */
  participants: Participant[]
  /** Current layout mode */
  layoutMode: "panels" | "tabs"
  /** Layout mode change callback */
  onLayoutModeChange: (mode: "panels" | "tabs") => void
  /** Whether user can edit room */
  canEdit: boolean
  /** Add panel callback (workspace only) */
  onAddPanel?: () => void
  /** Room settings callback */
  onSettings?: () => void
  /** Copy link callback */
  onCopyLink?: () => void
  /** Delete room callback */
  onDelete?: () => void
  /** Participant click callback */
  onParticipantClick?: (participant: Participant) => void
  /** Additional className */
  className?: string
}

const roomTypeIcons: Record<RoomType, React.ElementType> = {
  chat: MessageSquare,
  story: BookOpen,
  workspace: Grid3X3,
}

export function RoomHeader({
  title,
  type,
  participants,
  layoutMode,
  onLayoutModeChange,
  canEdit,
  onAddPanel,
  onSettings,
  onCopyLink,
  onDelete,
  onParticipantClick,
  className,
}: RoomHeaderProps) {
  const TypeIcon = roomTypeIcons[type]

  return (
    <header
      className={cn(
        "flex items-center justify-between px-4 py-3 border-b border-border bg-background shrink-0",
        className,
      )}
    >
      {/* Left: Room identity */}
      <div className="flex items-center gap-3">
        <TypeIcon className="h-5 w-5 text-muted-foreground" />
        <div>
          <h1 className="text-base font-semibold">{title}</h1>
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        {/* Participants */}
        <ParticipantStack
          participants={participants}
          onParticipantClick={onParticipantClick}
        />

        {/* Layout toggle (desktop only) */}
        <ToggleGroup
          type="single"
          value={layoutMode}
          onValueChange={(value) =>
            value && onLayoutModeChange(value as "panels" | "tabs")
          }
          className="hidden md:flex"
        >
          <ToggleGroupItem value="panels" aria-label="Panel layout">
            <LayoutGrid className="h-4 w-4" />
          </ToggleGroupItem>
          <ToggleGroupItem value="tabs" aria-label="Tab layout">
            <LayoutList className="h-4 w-4" />
          </ToggleGroupItem>
        </ToggleGroup>

        {/* Room menu */}
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
    </header>
  )
}
