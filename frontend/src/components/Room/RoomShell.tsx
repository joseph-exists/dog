/**
 * RoomShell
 *
 * Outer container for the room.
 * Manages room-level state and composes header + layout.
 */

import * as React from "react"
import { cn } from "@/lib/utils"
import type { Participant } from "./primitives/ParticipantStack"
import { RoomHeader, type RoomType } from "./RoomHeader"
import { type PanelConfig, RoomLayout } from "./RoomLayout"

interface RoomShellProps {
  /** Room ID for panel layout dialog */
  roomId?: string
  /** Room title */
  title: string
  /** Room type */
  type: RoomType
  /** Participants */
  participants: Participant[]
  /** Panel configurations */
  panels: PanelConfig[]
  /** Whether user can edit room */
  canEdit: boolean
  /** Add panel callback */
  onAddPanel?: () => void
  /** Room settings callback */
  onSettings?: () => void
  /** Copy link callback */
  onCopyLink?: () => void
  /** Delete room callback */
  onDelete?: () => void
  /** Participant click callback */
  onParticipantClick?: (participant: Participant) => void
  /** Whether debug panel is shown */
  showDebugPanel?: boolean
  /** Toggle debug panel callback */
  onToggleDebugPanel?: () => void
  /** Show dev mode indicator when internal messages are enabled. */
  devModeEnabled?: boolean
  /** Additional className */
  className?: string
}

export function RoomShell({
  roomId,
  title,
  type,
  participants,
  panels,
  canEdit,
  onAddPanel,
  onSettings,
  onCopyLink,
  onDelete,
  onParticipantClick,
  showDebugPanel,
  onToggleDebugPanel,
  devModeEnabled,
  className,
}: RoomShellProps) {
  const [layoutMode, setLayoutMode] = React.useState<"panels" | "tabs">(
    "panels",
  )

  return (
    <div className={cn("flex flex-col h-full", className)}>
      <RoomHeader
        roomId={roomId}
        title={title}
        type={type}
        participants={participants}
        layoutMode={layoutMode}
        onLayoutModeChange={setLayoutMode}
        canEdit={canEdit}
        onAddPanel={type === "workspace" ? onAddPanel : undefined}
        onSettings={onSettings}
        onCopyLink={onCopyLink}
        onDelete={onDelete}
        onParticipantClick={onParticipantClick}
        showDebugPanel={showDebugPanel}
        onToggleDebugPanel={onToggleDebugPanel}
        devModeEnabled={devModeEnabled}
      />
      <div className="flex-1 min-h-0">
        <RoomLayout panels={panels} mode={layoutMode} />
      </div>
    </div>
  )
}
