/**
 * RoomList Component
 *
 * Displays a list of rooms with responsive grid layout and empty state.
 */

import { MessageSquare } from "lucide-react"
import type { RoomViewModel } from "@/services/roomService"
import RoomCard from "./RoomCard"

interface RoomListProps {
  rooms: RoomViewModel[]
  onRoomSelect: (roomId: string) => void
  isLoading?: boolean
  activeRoomId?: string
}

export default function RoomList({
  rooms,
  onRoomSelect,
  isLoading = false,
  activeRoomId,
}: RoomListProps) {
  if (!isLoading && (!rooms || rooms.length === 0)) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <MessageSquare className="h-12 w-12 text-muted-foreground mb-4" />
        <h3 className="text-lg font-medium">No rooms available</h3>
        <p className="text-sm text-muted-foreground">
          You don't have access to any rooms yet.
        </p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {rooms.map((room) => (
        <RoomCard
          key={room.room_id}
          room={room}
          onClick={() => onRoomSelect(room.room_id)}
          isActive={activeRoomId === room.room_id}
        />
      ))}
    </div>
  )
}
