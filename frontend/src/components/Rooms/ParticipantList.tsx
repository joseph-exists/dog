/**
 * ParticipantList Component
 *
 * Displays active participants:
 * - Users section with count
 * - Agents section with count
 * - Visual distinction (agent icon)
 * - Loading state handling
 */

import { Loader2 } from "lucide-react"
import type { ParticipantViewModel } from "@/services/roomService"
import AgentToggle from "./AgentToggle"
import RemoveParticipantButton from "./RemoveParticipantButton"

interface ParticipantListProps {
  activeUsers: ParticipantViewModel[]
  activeAgents: ParticipantViewModel[]
  isLoading?: boolean
  currentUserRole: "owner" | "member" | null
  onRemoveParticipant?: (participantId: string) => Promise<void>
  onToggleAgent?: (agentId: string, activate: boolean) => Promise<void>
}

export default function ParticipantList({
  activeUsers,
  activeAgents,
  isLoading = false,
  currentUserRole,
  onRemoveParticipant,
  onToggleAgent,
}: ParticipantListProps) {
  if (isLoading) {
    return (
      <div className="p-4 border-t border-border">
        <Loader2 className="h-4 w-4 animate-spin" />
      </div>
    )
  }

  return (
    <div className="p-4 border-t border-border bg-background">
      <span className="text-sm font-bold mb-2 block">Participants</span>

      <div className="flex flex-col items-start gap-2 text-sm">
        {/* Users section */}
        {activeUsers.length > 0 && (
          <>
            <span className="text-xs text-muted-foreground">
              Users ({activeUsers.length})
            </span>
            {activeUsers.map((p) => (
              <div
                key={p.participant_id}
                className="flex justify-between w-full items-center"
              >
                <span>{p.display_name}</span>
                {currentUserRole === "owner" && onRemoveParticipant && (
                  <RemoveParticipantButton
                    participantId={p.participant_id}
                    participantName={p.display_name}
                    participantType="user"
                    onRemove={onRemoveParticipant}
                  />
                )}
              </div>
            ))}
          </>
        )}

        {/* Agents section */}
        {activeAgents.length > 0 && (
          <>
            <span className="text-xs text-muted-foreground mt-2">
              Agents ({activeAgents.length})
            </span>
            {activeAgents.map((p) =>
              currentUserRole === "owner" && onToggleAgent ? (
                <AgentToggle
                  key={p.participant_id}
                  agentId={p.participant_id}
                  agentName={p.display_name}
                  isActive={p.is_active}
                  onToggle={onToggleAgent}
                />
              ) : (
                <span key={p.participant_id} className="text-sm">
                  🤖 {p.display_name}
                </span>
              ),
            )}
          </>
        )}

        {/* Empty state */}
        {activeUsers.length === 0 && activeAgents.length === 0 && (
          <span className="text-xs text-muted-foreground">
            No active participants
          </span>
        )}
      </div>
    </div>
  )
}
