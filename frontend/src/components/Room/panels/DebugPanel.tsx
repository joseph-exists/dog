/**
 * DebugPanel
 *
 * Debug sidebar panel for room/agent debugging.
 * Wraps RoomDebugPanelContent with PanelContainer.
 */

import { RoomDebugPanelContent } from "@/components/Rooms/RoomDebugPanel"
import { cn } from "@/lib/utils"
import type {
  MessageViewModel,
  ParticipantViewModel,
} from "@/services/roomService"
import { PanelContainer } from "../primitives/PanelContainer"

interface DebugPanelProps {
  /** Messages to analyze */
  messages: MessageViewModel[]
  /** Current streaming message from agent */
  streamingMessage: { agent_name: string; content: string } | null
  /** WebSocket connection status */
  isConnected: boolean
  /** Active agents in room */
  activeAgents: ParticipantViewModel[]
  /** Hide panel header (when page provides its own) */
  hideHeader?: boolean
  /** Additional className */
  className?: string
}

export function DebugPanel({
  messages,
  streamingMessage,
  isConnected,
  activeAgents,
  hideHeader = false,
  className,
}: DebugPanelProps) {
  const content = (
    <div className="p-4">
      <RoomDebugPanelContent
        messages={messages}
        streamingMessage={streamingMessage}
        isConnected={isConnected}
        activeAgents={activeAgents}
      />
    </div>
  )

  if (hideHeader) {
    return (
      <div className={cn("h-full overflow-y-auto", className)}>{content}</div>
    )
  }

  return (
    <PanelContainer title="Debug" className={className}>
      {content}
    </PanelContainer>
  )
}
