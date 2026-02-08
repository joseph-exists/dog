/**
 * ParticipantPanel
 *
 * Unified panel showing all room participants (users and agents).
 * Agents display real metadata badges and support toggle/add/remove.
 */

// mixed case problem here again - camel fights the snake and they both wrestle pascal.
// we need to understand how this panel interacts with the presentation design we're moving towards.
// posthaste.


import { Loader2 } from "lucide-react"

// PRI ZERO:is this the best place for components/panels pulling UserAgentConfigData from?
import type { UserAgentConfigData as AgentData } from "@/components/Agents/types"

// ok now we have to review AgentQuickAdd
import AgentQuickAdd from "@/components/Agents/RoomManagers/AgentQuickAdd"

import {  AgentCoordinatorBadge, AgentModeBadge } from "@/components/Agents/Display/AgentBadge"

import AgentAvatar from "@/components/Agents/Display/AgentAvatar"

// PRI0 yuck we have to review Rooms
import AgentToggle from "@/components/Rooms/AgentToggle"

import RemoveParticipantButton from "@/components/Rooms/RemoveParticipantButton"
import type { ParticipantViewModel } from "@/services/roomService"
import { PanelContainer } from "../primitives/PanelContainer"

interface ParticipantPanelProps {
  /** Human users in the room */
  activeUsers: ParticipantViewModel[]
  /** Enriched agent data (with real mode, scope, coordinator) */
  roomAgents: AgentData[]
  /** All available agents for quick-add */
  availableAgents: AgentData[]
  /** IDs of agents already in room */
  existingAgentIds: string[]
  /** Add agent callback */
  onAddAgent: (agent: AgentData) => Promise<void>
  /** Remove agent callback */
  onRemoveAgent: (agent: AgentData) => Promise<void>
  /** Toggle agent activate/deactivate callback */
  onToggleAgent: (agentId: string, activate: boolean) => Promise<void>
  /** Remove user participant callback */
  onRemoveParticipant?: (participantId: string) => Promise<void>
  /** Whether current user can manage participants */
  canManage: boolean
  /** Whether loading */
  isLoading: boolean
}

// we have better functionality in Agents utils - and more of it.
// lets' think about what our capabilities are for this Panel.
function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)
}

export function ParticipantPanel({
  activeUsers,
  roomAgents,
  availableAgents,
  existingAgentIds,
  onAddAgent,
  onRemoveAgent,
  onToggleAgent,
  onRemoveParticipant,
  canManage,
  isLoading,
}: ParticipantPanelProps) {
  if (isLoading) {
    return (
      <PanelContainer title="Participants">
        <div className="flex items-center justify-center p-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      </PanelContainer>
    )
  }

  const headerActions = canManage ? (
    <AgentQuickAdd
      availableAgents={availableAgents}
      existingAgentIds={existingAgentIds}
      onAdd={onAddAgent}
      buttonSize="sm"
    />
  ) : undefined

  const totalCount = activeUsers.length + roomAgents.length

  return (
    <PanelContainer
      title={`Participants (${totalCount})`}
      headerActions={headerActions}
    >
      <div className="flex flex-col">
        {/* Users Section */}
        {activeUsers.length > 0 && (
          <div className="p-3 border-b">
            <h3 className="text-xs font-medium text-muted-foreground mb-2">
              Users ({activeUsers.length})
            </h3>
            <div className="space-y-1">
              {activeUsers.map((user) => (
                <div
                  key={user.participant_id}
                  className="flex items-center gap-2 p-2 rounded-md hover:bg-muted/50"
                >
                  <div className="size-7 rounded-full bg-primary/10 flex items-center justify-center text-xs font-medium shrink-0">
                    {getInitials(user.display_name)}
                  </div>
                  <span className="flex-1 text-xl truncate">
                    {user.display_name}
                  </span>
                  {canManage &&
                    user.role !== "owner" &&
                    onRemoveParticipant && (
                      <RemoveParticipantButton
                        participantId={user.participant_id}
                        participantName={user.display_name}
                        participantType="user"
                        onRemove={onRemoveParticipant}
                      />
                    )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Agents Section */}
        <div className="p-3">
          <h3 className="text-xs font-medium text-muted-foreground mb-2">
            Agents ({roomAgents.length})
          </h3>
          {roomAgents.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              No agents in this room
            </p>
          ) : (
            <div className="space-y-1">
              {roomAgents.map((agent) => {
                const isInactive = agent.is_enabled === false
                return (
                  <div
                    key={agent.id}
                    className={`flex items-center gap-2 p-2 rounded-md hover:bg-muted/50 ${isInactive ? "opacity-50" : ""}`}
                  >
                    <AgentAvatar name={agent.name} size="sm" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-sm font-medium truncate">
                          {agent.name}
                        </span>
                        {agent.is_coordinator && (
                          <AgentCoordinatorBadge className="text-[10px] px-1.5 py-0 h-4 scale-90" />
                        )}
                        {agent.participation_mode && (
                          <AgentModeBadge
                            mode={agent.participation_mode}
                            className="text-[10px] px-1.5 py-0 h-4 scale-90"
                          />
                        )}
                      </div>
                    </div>
                    {canManage && (
                      <div className="flex items-center gap-1 shrink-0">
                        <AgentToggle
                          agentId={agent.id}
                          agentName={agent.name}
                          isActive={agent.is_enabled ?? true}
                          onToggle={onToggleAgent}
                        />
                        <RemoveParticipantButton
                          participantId={agent.id}
                          participantName={agent.name}
                          participantType="agent"
                          onRemove={async (id) => {
                            const agentData = roomAgents.find(
                              (a) => a.id === id,
                            )
                            if (agentData) await onRemoveAgent(agentData)
                          }}
                        />
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </PanelContainer>
  )
}
