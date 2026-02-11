// import { EllipsisVertical, Loader2Icon, TrashIcon } from "lucide-react"
// import { useState } from "react"

// import {
//   AlertDialog,
//   AlertDialogAction,
//   AlertDialogCancel,
//   AlertDialogContent,
//   AlertDialogDescription,
//   AlertDialogFooter,
//   AlertDialogHeader,
//   AlertDialogTitle,
// } from "@/components/ui/alert-dialog"
// import {
//   DropdownMenu,
//   DropdownMenuContent,
//   DropdownMenuItem,
//   DropdownMenuSeparator,
//   DropdownMenuTrigger,
// } from "@/components/ui/dropdown-menu"
// import type { RoomViewModel } from "@/services/roomService"
// import { Button } from "../ui/button"
// import EditRoomDialog from "./EditRoomDialog"

// interface RoomActionsMenuProps {
//   room: RoomViewModel
//   onUpdate: (data: { title: string }) => Promise<void>
//   onDelete?: () => Promise<void>
// }

// /**
//  * RoomActionsMenu - Dropdown menu for room management actions
//  *
//  * Provides edit and delete (soft-delete) options for room owners.
//  */
// export const RoomActionsMenu = ({
//   room,
//   onUpdate,
//   onDelete,
// }: RoomActionsMenuProps) => {
//   const [open, setOpen] = useState(false)
//   const [confirmOpen, setConfirmOpen] = useState(false)
//   const [isDeleting, setIsDeleting] = useState(false)

//   const handleDelete = async () => {
//     if (!onDelete) return
//     setIsDeleting(true)
//     try {
//       await onDelete()
//       setConfirmOpen(false)
//       setOpen(false)
//     } finally {
//       setIsDeleting(false)
//     }
//   }

//   return (
//     <>
//       <DropdownMenu open={open} onOpenChange={setOpen}>
//         <DropdownMenuTrigger asChild>
//           <Button variant="ghost" size="sm" color="inherit">
//             <EllipsisVertical />
//           </Button>
//         </DropdownMenuTrigger>
//         <DropdownMenuContent>
//           <EditRoomDialog room={room} onUpdate={onUpdate} />
//           {onDelete && (
//             <>
//               <DropdownMenuSeparator />
//               <DropdownMenuItem
//                 className="text-destructive focus:text-destructive"
//                 onSelect={(e) => {
//                   e.preventDefault()
//                   setConfirmOpen(true)
//                 }}
//               >
//                 <TrashIcon className="size-4" />
//                 Delete Room
//               </DropdownMenuItem>
//             </>
//           )}
//         </DropdownMenuContent>
//       </DropdownMenu>

//       <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
//         <AlertDialogContent>
//           <AlertDialogHeader>
//             <AlertDialogTitle>Delete Room</AlertDialogTitle>
//             <AlertDialogDescription>
//               Permanently delete &quot;{room.title || "Untitled Room"}
//               &quot;? All messages and history will be hidden. This action
//               cannot be undone.
//             </AlertDialogDescription>
//           </AlertDialogHeader>
//           <AlertDialogFooter>
//             <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
//             <AlertDialogAction
//               onClick={handleDelete}
//               disabled={isDeleting}
//               className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
//             >
//               {isDeleting && <Loader2Icon className="size-4 animate-spin" />}
//               Delete
//             </AlertDialogAction>
//           </AlertDialogFooter>
//         </AlertDialogContent>
//       </AlertDialog>
//     </>
//   )
// }
