/**
 * RoomAgentList Component
 *
 * Displays the list of agents currently in a room.
 * Features:
 * - Shows agent avatars and names
 * - Remove button for each agent
 * - Empty state with prompt to add agents
 * - Compact or expanded views
 */

import { BotIcon, Loader2Icon, XIcon } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"
import AgentAvatar from "./Display/AgentAvatar"
import { AgentModeBadge } from "./Display/AgentBadge"
import type { AgentData } from "./AgentCarousel"

interface RoomAgentListProps {
  /** Agents currently in the room */
  agents: AgentData[]
  /** Called when remove button is clicked */
  onRemove?: (agent: AgentData) => Promise<void> | void
  /** Whether the current user can remove agents */
  canRemove?: boolean
  /** Display variant */
  variant?: "list" | "compact" | "avatars-only"
  /** Empty state action (typically an Add button) */
  emptyAction?: React.ReactNode
  /** Additional classes */
  className?: string
}

export default function RoomAgentList({
  agents,
  onRemove,
  canRemove = true,
  variant = "list",
  emptyAction,
  className,
}: RoomAgentListProps) {
  const [removingId, setRemovingId] = useState<string | null>(null)

  const handleRemove = async (agent: AgentData) => {
    if (!onRemove) return
    setRemovingId(agent.id)
    try {
      await onRemove(agent)
    } finally {
      setRemovingId(null)
    }
  }

  // Empty state
  if (agents.length === 0) {
    return (
      <div
        className={cn(
          "flex flex-col items-center justify-center gap-3 p-6 text-center border border-dashed rounded-lg",
          className,
        )}
      >
        <BotIcon className="size-8 text-muted-foreground" />
        <div>
          <p className="font-medium">No agents in this room</p>
          <p className="text-sm text-muted-foreground">
            Add agents to get AI assistance
          </p>
        </div>
        {emptyAction}
      </div>
    )
  }

  // Avatars-only view (for tight spaces like headers)
  if (variant === "avatars-only") {
    return (
      <div className={cn("flex -space-x-2", className)}>
        {agents.slice(0, 5).map((agent) => (
          <Tooltip key={agent.id}>
            <TooltipTrigger asChild>
              <div className="ring-2 ring-background rounded-full">
                <AgentAvatar name={agent.name} size="sm" />
              </div>
            </TooltipTrigger>
            <TooltipContent>{agent.name}</TooltipContent>
          </Tooltip>
        ))}
        {agents.length > 5 && (
          <div className="flex items-center justify-center size-6 rounded-full bg-muted text-xs font-medium ring-2 ring-background">
            +{agents.length - 5}
          </div>
        )}
      </div>
    )
  }

  // Compact view (horizontal with smaller items)
  if (variant === "compact") {
    return (
      <div className={cn("flex flex-wrap gap-2", className)}>
        {agents.map((agent) => (
          <div
            key={agent.id}
            className="flex items-center gap-2 px-2 py-1 rounded-full bg-muted"
          >
            <AgentAvatar name={agent.name} size="sm" />
            <span className="text-sm font-medium">{agent.name}</span>
            {canRemove && onRemove && (
              <Button
                variant="ghost"
                size="icon"
                className="size-5 rounded-full hover:bg-destructive/20"
                onClick={() => handleRemove(agent)}
                disabled={removingId === agent.id}
              >
                {removingId === agent.id ? (
                  <Loader2Icon className="size-3 animate-spin" />
                ) : (
                  <XIcon className="size-3" />
                )}
              </Button>
            )}
          </div>
        ))}
      </div>
    )
  }

  // Full list view (default)
  return (
    <div className={cn("space-y-2", className)}>
      {agents.map((agent) => (
        <div
          key={agent.id}
          className="flex items-center gap-3 p-3 rounded-lg border bg-card"
        >
          <AgentAvatar name={agent.name} size="md" />

          <div className="flex-1 min-w-0">
            <div className="font-medium truncate">{agent.name}</div>
            {agent.description && (
              <p className="text-sm text-muted-foreground truncate">
                {agent.description}
              </p>
            )}
          </div>

          {agent.participationMode && (
            <AgentModeBadge mode={agent.participationMode} />
          )}

          {canRemove && onRemove && (
            <Button
              variant="ghost"
              size="icon"
              className="shrink-0 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
              onClick={() => handleRemove(agent)}
              disabled={removingId === agent.id}
            >
              {removingId === agent.id ? (
                <Loader2Icon className="size-4 animate-spin" />
              ) : (
                <XIcon className="size-4" />
              )}
            </Button>
          )}
        </div>
      ))}
    </div>
  )
}
