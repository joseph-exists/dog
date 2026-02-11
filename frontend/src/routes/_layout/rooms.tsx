/**
 * Room List Route
 *
 * Displays all rooms accessible to the current user.
 * Uses RoomList component with RoomCard grid layout.
 */

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { AlertCircle, Loader2 } from "lucide-react"

import AddRoom from "@/components/Room/Dialogs/AddRoom"
import RoomList from "@/components/Room/RoomList"
import { RoomService } from "@/services/roomService"

export const Route = createFileRoute("/_layout/rooms")({
  component: Rooms,
})

function Rooms() {
  const navigate = useNavigate()

  // Fetch rooms using RoomService (returns RoomViewModel[] directly)
  const {
    data: rooms,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["rooms"],
    queryFn: () => RoomService.listRooms(),
  })

  // Handle room selection - navigate to room detail view
  const handleRoomSelect = (roomId: string) => {
    navigate({ to: "/r/$roomId", params: { roomId } })
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-destructive/10 p-4 mb-4">
          <AlertCircle className="h-8 w-8 text-destructive" />
        </div>
        <h3 className="text-lg font-semibold">Error loading rooms</h3>
        <p className="text-muted-foreground">
          {error instanceof Error ? error.message : "Unknown error occurred"}
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header with title and add button */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Rooms</h1>
          <p className="text-muted-foreground">
            Collaborative spaces for conversations
          </p>
        </div>
        <AddRoom />
      </div>

      {/* Room list with card grid */}
      <RoomList
        rooms={rooms || []}
        onRoomSelect={handleRoomSelect}
        isLoading={isLoading}
      />
    </div>
  )
}
