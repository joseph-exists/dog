import type { RoomViewModel } from "@/services/roomService"
// see *ActionsMenu.tsx in this directory for examples
import { IconButton } from "@chakra-ui/react"
import { BsThreeDotsVertical } from "react-icons/bs"
import EditRoomDialog from "../Rooms/EditRoomDialog"
import { MenuContent, MenuRoot, MenuTrigger } from "../ui/menu"

interface RoomActionsMenuProps {
  room: RoomViewModel
  onUpdate: (data: { title: string }) => Promise<void>
  // onDelete is optional since DeleteRoomDialog is blocked (backend endpoint doesn't exist)
  onDelete?: () => Promise<void>
}

export const RoomActionsMenu = ({ room, onUpdate }: RoomActionsMenuProps) => {
  return (
    <MenuRoot>
      <MenuTrigger asChild>
        <IconButton variant="ghost" size="sm" color="inherit">
          <BsThreeDotsVertical />
        </IconButton>
      </MenuTrigger>
      <MenuContent>
        <EditRoomDialog room={room} onUpdate={onUpdate} />
        {/* DeleteRoomDialog temporarily removed - blocked on backend DELETE endpoint */}
      </MenuContent>
    </MenuRoot>
  )
}
