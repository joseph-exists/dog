/**
 * ParticipantPanel
 *
 * Combined participants panel showing users and agents.
 * Replicates V1 sidebar functionality for "classic" layout.
 */

import { Loader2 } from "lucide-react"
import AgentToggle from "@/components/Rooms/AgentToggle"
import RemoveParticipantButton from "@/components/Rooms/RemoveParticipantButton"
import type { ParticipantViewModel } from "@/services/roomService"
import { PanelContainer } from "../primitives/PanelContainer"

interface ParticipantPanelProps {
  activeUsers: ParticipantViewModel[]
  activeAgents: ParticipantViewModel[]
  isLoading?: boolean
  currentUserRole: "owner" | "member" | null
  onRemoveParticipant?: (participantId: string) => Promise<void>
  onToggleAgent?: (agentId: string, activate: boolean) => Promise<void>
}

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
  activeAgents,
  isLoading,
  currentUserRole,
  onRemoveParticipant,
  onToggleAgent,
}: ParticipantPanelProps) {
  const canManage = currentUserRole === "owner"

  if (isLoading) {
    return (
      <PanelContainer title="Participants">
        <div className="flex items-center justify-center p-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      </PanelContainer>
    )
  }

  return (
    <PanelContainer title="Participants">
      <div className="flex flex-col h-full overflow-y-auto">
        {/* Users Section */}
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
                <div className="size-8 rounded-full bg-primary/10 flex items-center justify-center text-xs font-medium">
                  {getInitials(user.display_name)}
                </div>
                <span className="flex-1 text-sm truncate">
                  {user.display_name}
                </span>
                {canManage && user.role !== "owner" && onRemoveParticipant && (
                  <RemoveParticipantButton
                    participantId={user.participant_id}
                    participantName={user.display_name}
                    participantType="user"
                    onRemove={onRemoveParticipant}
                  />
                )}
              </div>
            ))}
            {activeUsers.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-2">
                No users
              </p>
            )}
          </div>
        </div>

        {/* Agents Section */}
        <div className="p-3 flex-1">
          <h3 className="text-xs font-medium text-muted-foreground mb-2">
            Agents ({activeAgents.length})
          </h3>
          <div className="space-y-1">
            {activeAgents.map((agent) => (
              <div
                key={agent.participant_id}
                className="flex items-center gap-2 p-2 rounded-md hover:bg-muted/50"
              >
                <div className="size-8 rounded-full bg-accent flex items-center justify-center text-xs">
                  🤖
                </div>
                <span className="flex-1 text-sm truncate">
                  {agent.display_name}
                </span>
                {canManage && onToggleAgent && (
                  <AgentToggle
                    agentId={agent.participant_id}
                    agentName={agent.display_name}
                    isActive={agent.is_active}
                    onToggle={onToggleAgent}
                  />
                )}
              </div>
            ))}
            {activeAgents.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-2">
                No agents
              </p>
            )}
          </div>
        </div>
      </div>
    </PanelContainer>
  )
}
