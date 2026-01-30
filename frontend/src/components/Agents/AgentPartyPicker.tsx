/**
 * AgentPartyPicker Component
 *
 * A dialog for selecting multiple agents to add to a room.
 * Features:
 * - Checkbox selection for multi-select
 * - Visual feedback for already-added agents
 * - Batch add with confirmation
 * - Search/filter capability
 */

import { Loader2Icon, SearchIcon, UsersIcon } from "lucide-react"
import { useMemo, useState } from "react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import AgentAvatar from "./Display/AgentAvatar"
import { AgentModeBadge, AgentScopeBadge } from "./AgentBadge"
import type { AgentData } from "./AgentCarousel"

interface AgentPartyPickerProps {
  /** Available agents to choose from */
  availableAgents: AgentData[]
  /** IDs of agents already in the room */
  existingAgentIds?: string[]
  /** Called when agents are confirmed */
  onConfirm: (agents: AgentData[]) => Promise<void> | void
  /** Custom trigger element */
  trigger?: React.ReactNode
  /** Dialog title */
  title?: string
  /** Dialog description */
  description?: string
  /** Confirm button text */
  confirmText?: string
  /** Additional classes */
  className?: string
}

export default function AgentPartyPicker({
  availableAgents,
  existingAgentIds = [],
  onConfirm,
  trigger,
  title = "Select Agents",
  description = "Choose which agents to add to this room",
  confirmText = "Add Selected",
  className,
}: AgentPartyPickerProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [searchQuery, setSearchQuery] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Filter agents based on search and existing
  const filteredAgents = useMemo(() => {
    return availableAgents.filter((agent) => {
      // Filter by search query
      const matchesSearch =
        searchQuery === "" ||
        agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.description?.toLowerCase().includes(searchQuery.toLowerCase())

      return matchesSearch
    })
  }, [availableAgents, searchQuery])

  // Separate into available and already-added
  const { available, alreadyAdded } = useMemo(() => {
    const available: AgentData[] = []
    const alreadyAdded: AgentData[] = []

    for (const agent of filteredAgents) {
      if (existingAgentIds.includes(agent.id)) {
        alreadyAdded.push(agent)
      } else {
        available.push(agent)
      }
    }

    return { available, alreadyAdded }
  }, [filteredAgents, existingAgentIds])

  const toggleAgent = (agentId: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(agentId)) {
        next.delete(agentId)
      } else {
        next.add(agentId)
      }
      return next
    })
  }

  const selectAll = () => {
    setSelectedIds(new Set(available.map((a) => a.id)))
  }

  const clearSelection = () => {
    setSelectedIds(new Set())
  }

  const handleConfirm = async () => {
    const selectedAgents = availableAgents.filter((a) => selectedIds.has(a.id))
    if (selectedAgents.length === 0) return

    setIsSubmitting(true)
    try {
      await onConfirm(selectedAgents)
      setIsOpen(false)
      setSelectedIds(new Set())
      setSearchQuery("")
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    if (!open) {
      // Reset state when closing
      setSelectedIds(new Set())
      setSearchQuery("")
    }
  }

  const defaultTrigger = (
    <Button variant="outline" className={className}>
      <UsersIcon className="size-4" />
      <span>Manage Agents</span>
    </Button>
  )

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>{trigger || defaultTrigger}</DialogTrigger>

      <DialogContent className="max-w-lg max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        {/* Search Input */}
        <div className="relative">
          <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input
            placeholder="Search agents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Selection Controls */}
        {available.length > 0 && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              {selectedIds.size} of {available.length} selected
            </span>
            <div className="flex gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={selectAll}
                disabled={selectedIds.size === available.length}
              >
                Select All
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearSelection}
                disabled={selectedIds.size === 0}
              >
                Clear
              </Button>
            </div>
          </div>
        )}

        {/* Agent List */}
        <div className="flex-1 overflow-y-auto space-y-1 min-h-[200px] max-h-[300px]">
          {/* Available Agents */}
          {available.map((agent) => (
            <AgentPickerItem
              key={agent.id}
              agent={agent}
              isSelected={selectedIds.has(agent.id)}
              onToggle={() => toggleAgent(agent.id)}
            />
          ))}

          {/* Already Added Agents */}
          {alreadyAdded.length > 0 && (
            <>
              <div className="pt-4 pb-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Already in Room
              </div>
              {alreadyAdded.map((agent) => (
                <AgentPickerItem
                  key={agent.id}
                  agent={agent}
                  isSelected={false}
                  disabled
                />
              ))}
            </>
          )}

          {/* Empty State */}
          {filteredAgents.length === 0 && (
            <div className="flex items-center justify-center h-32 text-muted-foreground">
              {searchQuery
                ? "No agents match your search"
                : "No agents available"}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setIsOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={selectedIds.size === 0 || isSubmitting}
          >
            {isSubmitting && <Loader2Icon className="size-4 animate-spin" />}
            {confirmText} ({selectedIds.size})
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

/**
 * Individual agent item in the picker list
 */
function AgentPickerItem({
  agent,
  isSelected,
  onToggle,
  disabled = false,
}: {
  agent: AgentData
  isSelected: boolean
  onToggle?: () => void
  disabled?: boolean
}) {
  return (
    <label
      className={cn(
        "flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors",
        isSelected && "bg-accent border-primary",
        disabled && "opacity-50 cursor-not-allowed bg-muted",
        !disabled && !isSelected && "hover:bg-accent/50",
      )}
    >
      <Checkbox
        checked={isSelected}
        onCheckedChange={onToggle}
        disabled={disabled}
      />

      <AgentAvatar name={agent.name} size="sm" />

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium truncate">{agent.name}</span>
          {agent.scope && (
            <AgentScopeBadge scope={agent.scope} className="scale-75" />
          )}
        </div>
        {agent.description && (
          <p className="text-xs text-muted-foreground truncate">
            {agent.description}
          </p>
        )}
      </div>

      {agent.participationMode && (
        <AgentModeBadge
          mode={agent.participationMode}
          className="hidden sm:flex scale-75"
        />
      )}
    </label>
  )
}
