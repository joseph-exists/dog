/**
 * AgentPanel
 *
 * Auxiliary panel for managing room agents.
 * Adapts existing agent management components.
 */

import { Users, Loader2 } from "lucide-react"
import { PanelContainer } from "../primitives/PanelContainer"
import {
  type AgentData,
  AgentQuickAdd,
  AgentPartyPicker,
  RoomAgentList,
} from "@/components/Agents"
import { Button } from "@/components/ui/button"

interface AgentPanelProps {
  /** Agents currently in the room */
  roomAgents: AgentData[]
  /** All available agents */
  availableAgents: AgentData[]
  /** IDs of agents already in room */
  existingAgentIds: string[]
  /** Add single agent callback */
  onAddAgent: (agent: AgentData) => Promise<void>
  /** Add multiple agents callback */
  onAddMultipleAgents: (agents: AgentData[]) => Promise<void>
  /** Remove agent callback */
  onRemoveAgent: (agent: AgentData) => Promise<void>
  /** Whether user can manage agents */
  canManage: boolean
  /** Whether loading */
  isLoading: boolean
}

export function AgentPanel({
  roomAgents,
  availableAgents,
  existingAgentIds,
  onAddAgent,
  onAddMultipleAgents,
  onRemoveAgent,
  canManage,
  isLoading,
}: AgentPanelProps) {
  if (isLoading) {
    return (
      <PanelContainer title="Agents">
        <div className="flex items-center justify-center p-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      </PanelContainer>
    )
  }

  const headerActions = canManage ? (
    <div className="flex items-center gap-1">
      <AgentQuickAdd
        availableAgents={availableAgents}
        existingAgentIds={existingAgentIds}
        onAdd={onAddAgent}
        buttonSize="sm"
      />
      <AgentPartyPicker
        availableAgents={availableAgents}
        existingAgentIds={existingAgentIds}
        onConfirm={onAddMultipleAgents}
        title="Add Agents to Room"
        description="Select multiple agents to add at once"
        trigger={
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <Users className="h-4 w-4" />
          </Button>
        }
      />
    </div>
  ) : undefined

  return (
    <PanelContainer
      title={`Agents (${roomAgents.length})`}
      headerActions={headerActions}
    >
      <div className="p-3">
        {roomAgents.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">
            No agents in this room
          </p>
        ) : (
          <RoomAgentList
            agents={roomAgents}
            onRemove={canManage ? onRemoveAgent : undefined}
            canRemove={canManage}
            variant="list"
          />
        )}
      </div>
    </PanelContainer>
  )
}
