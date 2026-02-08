/**
 * AgentQuickAdd Component
 *
 * A dropdown menu for quickly adding a single agent to a room.
 * Shows available agents with their avatars and descriptions.
 * Filters out agents already in the room.
 */

// P0 refactor target for Room/Rooms. 
// used by ParticipantPanel

import { Loader2Icon, PlusIcon } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import AgentAvatar from "../Display/AgentAvatar"

// is this our canonical strategy?
// we do it almost everywhere - but not universally.
// we need a specific pattern defined - with reasons, constraints, and when
// to break it.
import type { UserAgentConfigData as AgentData } from "../types"

interface AgentQuickAddProps {
  /** Available agents to add */
  availableAgents: AgentData[]
  /** IDs of agents already in the room (to filter out) */
  existingAgentIds?: string[]
  /** Called when an agent is selected to add */
  onAdd: (agent: AgentData) => Promise<void> | void
  /** Button variant */
  buttonVariant?: "default" | "outline" | "ghost"
  /** Button size */
  buttonSize?: "default" | "sm" | "icon"
  /** Custom trigger content */
  trigger?: React.ReactNode
  /** Disabled state */
  disabled?: boolean
  /** Additional classes for the trigger */
  className?: string
}

export default function AgentQuickAdd({
  availableAgents,
  existingAgentIds = [],
  onAdd,
  buttonVariant = "outline",
  buttonSize = "sm",
  trigger,
  disabled = false,
  className,
}: AgentQuickAddProps) {
  const [isAdding, setIsAdding] = useState<string | null>(null)
  const [isOpen, setIsOpen] = useState(false)

  // Filter out agents already in the room
  const agentsToShow = availableAgents.filter(
    (agent) => !existingAgentIds.includes(agent.id),
  )

  const handleAdd = async (agent: AgentData) => {
    setIsAdding(agent.id)
    try {
      await onAdd(agent)
      setIsOpen(false)
    } finally {
      setIsAdding(null)
    }
  }

  const defaultTrigger = (
    <Button
      variant={buttonVariant}
      size={buttonSize}
      disabled={disabled || agentsToShow.length === 0}
      className={className}
    >
      <PlusIcon className="size-4" />
      {buttonSize !== "icon" && <span>Add Agent</span>}
    </Button>
  )

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        {trigger || defaultTrigger}
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-72">
        <DropdownMenuLabel>Add Agent to Room</DropdownMenuLabel>
        <DropdownMenuSeparator />

        {agentsToShow.length === 0 ? (
          <div className="px-2 py-4 text-sm text-muted-foreground text-center">
            All available agents are already in this room
          </div>
        ) : (
          agentsToShow.map((agent) => (
            <DropdownMenuItem
              key={agent.id}
              onClick={() => handleAdd(agent)}
              disabled={isAdding !== null}
              className="flex items-center gap-3 py-2 cursor-pointer"
            >
              <AgentAvatar name={agent.name as string} size="sm" />
              <div className="flex-1 min-w-0">
                <div className="font-medium truncate">{agent.name}</div>
                {/* added type guard w const assertion here
                todo: review UserAgentConfigData.description 
                 proper typing =  string | undefined (not string | null | undefined) */}
                {(agent.description as string | undefined) && (
                  <div className="text-xs text-muted-foreground truncate">
                    {agent.description}
                  </div>
                )}
              </div>
              {isAdding === agent.id && (
                <Loader2Icon className="size-4 animate-spin" />
              )}
            </DropdownMenuItem>
          ))
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
