import { EllipsisVertical } from "lucide-react"
// see *ActionsMenu.tsx in this directory for examples
import { useState } from "react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import type { RoomViewModel } from "@/services/roomService"
import { Button } from "../ui/button"
import EditRoomDialog from "./EditRoomDialog"

interface RoomActionsMenuProps {
  room: RoomViewModel
  onUpdate: (data: { title: string }) => Promise<void>
  // onDelete is optional since DeleteRoomDialog is blocked (backend endpoint doesn't exist)
  onDelete?: () => Promise<void>
}

export const RoomActionsMenu = ({ room, onUpdate }: RoomActionsMenuProps) => {
  const [open, setOpen] = useState(false)

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" color="inherit">
          <EllipsisVertical />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <EditRoomDialog room={room} onUpdate={onUpdate} />
        {/* DeleteRoomDialog temporarily removed - blocked on backend DELETE endpoint */}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
