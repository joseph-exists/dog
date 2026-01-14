/**
 * RoomHeader Component
 *
 * Displays room metadata:
 * - Room title
 * - Participant count
 * - Agent count
 * - User role badge
 */

import { RoomActionsMenu } from "@/components/Rooms/RoomsActionsMenu"
import { cn } from "@/lib/utils"
import type {
  ParticipantViewModel,
  RoomViewModel,
} from "@/services/roomService"
import AddParticipantDialog from "./AddParticipantDialog"

interface RoomHeaderProps {
  room: RoomViewModel | null | undefined
  participants: ParticipantViewModel[]
  activeAgents: ParticipantViewModel[]
  currentUserRole: string | null
  onAddParticipant: (
    participantId: string,
    type: "user" | "agent",
  ) => Promise<void>
  onUpdateRoom?: (data: { title: string }) => Promise<void>
  onDeleteRoom?: () => Promise<void>
}

export default function RoomHeader({
  room,
  participants,
  activeAgents,
  currentUserRole,
  onAddParticipant,
  onUpdateRoom,
  onDeleteRoom,
}: RoomHeaderProps) {
  return (
    <div className="p-4 border-b border-border bg-background">
      <div className="flex justify-between items-center">
        <div className="flex flex-col items-start gap-1">
          {/* Room title */}
          <span className="text-lg font-bold">
            {room?.title || "Untitled Room"}
          </span>

          {/* Participant and agent counts */}
          <span className="text-sm text-muted-foreground">
            {participants.length} participant
            {participants.length !== 1 ? "s" : ""}
            {activeAgents.length > 0 &&
              ` • ${activeAgents.length} agent${
                activeAgents.length !== 1 ? "s" : ""
              }`}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Owner actions */}
          {currentUserRole === "owner" && room && (
            <>
              <AddParticipantDialog
                roomId={room.room_id}
                currentParticipants={participants.map((p) => p.participant_id)}
                onAdd={onAddParticipant}
              />
              {onUpdateRoom && (
                <RoomActionsMenu
                  room={room}
                  onUpdate={onUpdateRoom}
                  onDelete={onDeleteRoom}
                />
              )}
            </>
          )}

          {/* User role badge */}
          {currentUserRole && (
            <span
              className={cn(
                "text-xs px-2 py-1 rounded-md font-medium",
                currentUserRole === "owner"
                  ? "bg-primary/10 text-primary"
                  : "bg-muted text-muted-foreground",
              )}
            >
              {currentUserRole.toUpperCase()}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
