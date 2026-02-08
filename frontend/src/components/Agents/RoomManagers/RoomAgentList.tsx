/**
 * RoomAgentList Component
 *
 * Room-specific agent list that composes AgentCard for rendering
 * and adds room concerns: remove handling, empty state, density variants.
 *
 * Variants:
 * - "list": AgentCard compact with remove action (default)
 * - "avatars-only": Stacked avatar circles for tight spaces (headers, toolbars)
 */

// currently not used - but healthy.  Can be imported.
// AvatarsOnly is neat.

import { BotIcon, Loader2Icon, XIcon } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"
import AgentAvatar from "../Display/AgentAvatar"
import AgentCard from "../Display/AgentCard"
import type { UserAgentConfigData } from "../types"

// ── Remove Button ─────────────────────────────────────────────────────────

function RemoveButton({
  agent,
  onRemove,
  removingId,
}: {
  agent: UserAgentConfigData
  onRemove: (agent: UserAgentConfigData) => Promise<void> | void
  removingId: string | null
}) {
  return (
    <Button
      variant="ghost"
      size="icon"
      className="shrink-0 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
      onClick={() => onRemove(agent)}
      disabled={removingId === agent.id}
    >
      {removingId === agent.id ? (
        <Loader2Icon className="size-4 animate-spin" />
      ) : (
        <XIcon className="size-4" />
      )}
    </Button>
  )
}

// ── Avatars-Only Variant ──────────────────────────────────────────────────

function AvatarsOnly({
  agents,
  className,
}: {
  agents: UserAgentConfigData[]
  className?: string
}) {
  return (
    <div className={cn("flex -space-x-2", className)}>
      {agents.slice(0, 5).map((agent) => (
        <Tooltip key={agent.id}>
          <TooltipTrigger asChild>
            <div className="ring-2 ring-background rounded-full">
              <AgentAvatar
                name={agent.name ?? "Agent"}
                size="sm"
                presentation={agent.presentation?.avatar}
              />
            </div>
          </TooltipTrigger>
          <TooltipContent>{agent.name ?? "Agent"}</TooltipContent>
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

// ── Main Component ────────────────────────────────────────────────────────

interface RoomAgentListProps {
  agents: UserAgentConfigData[]
  onRemove?: (agent: UserAgentConfigData) => Promise<void> | void
  canRemove?: boolean
  variant?: "list" | "avatars-only"
  emptyAction?: React.ReactNode
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

  const handleRemove = async (agent: UserAgentConfigData) => {
    if (!onRemove) return
    setRemovingId(agent.id)
    try {
      await onRemove(agent)
    } finally {
      setRemovingId(null)
    }
  }

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

  if (variant === "avatars-only") {
    return <AvatarsOnly agents={agents} className={className} />
  }

  return (
    <div className={cn("space-y-2", className)}>
      {agents.map((agent) => (
        <AgentCard
          key={agent.id}
          agent={agent}
          variant="compact"
          action={
            canRemove && onRemove ? (
              <RemoveButton
                agent={agent}
                onRemove={handleRemove}
                removingId={removingId}
              />
            ) : undefined
          }
        />
      ))}
    </div>
  )
}
