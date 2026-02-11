// /**
//  * EditRoomDialog Component
//  *
//  * Dialog for editing room details, triggered from a dropdown menu.
//  */

// import { Loader2 } from "lucide-react"
// import { useState } from "react"
// import { type SubmitHandler, useForm } from "react-hook-form"

// import type { ApiError } from "@/client/core/ApiError"
// import { Button } from "@/components/ui/button"
// import {
//   Dialog,
//   DialogClose,
//   DialogContent,
//   DialogFooter,
//   DialogHeader,
//   DialogTitle,
// } from "@/components/ui/dialog"
// import { DropdownMenuItem } from "@/components/ui/dropdown-menu"
// import { Input } from "@/components/ui/input"
// import { Label } from "@/components/ui/label"
// import { showSuccessToast, showErrorToast } from "@/hooks/useCustomToast"
// import { cn } from "@/lib/utils"
// import type { RoomViewModel } from "@/services/roomService"
// import { handleError } from "@/utils"

// interface EditRoomForm {
//   title: string
// }

// interface EditRoomDialogProps {
//   room: RoomViewModel
//   onUpdate: (data: { title: string }) => Promise<void>
// }

// export default function EditRoomDialog({
//   room,
//   onUpdate,
// }: EditRoomDialogProps) {
//   const [isOpen, setIsOpen] = useState(false)
  

//   const {
//     register,
//     handleSubmit,
//     reset,
//     formState: { errors, isValid, isSubmitting },
//   } = useForm<EditRoomForm>({
//     mode: "onBlur",
//     defaultValues: {
//       title: room.title || "",
//     },
//   })

//   const onSubmit: SubmitHandler<EditRoomForm> = async (data) => {
//     try {
//       await onUpdate({ title: data.title })
//       showSuccessToast("Room updated successfully.")
//       setIsOpen(false)
//     } catch (err) {
//       handleError.call(showErrorToast, err as ApiError)
//     }
//   }

//   const handleOpenChange = (open: boolean) => {
//     setIsOpen(open)
//     if (!open) reset()
//   }

//   return (
//     <Dialog open={isOpen} onOpenChange={handleOpenChange}>
//       {/* Trigger as DropdownMenuItem for ActionsMenu */}
//       <DropdownMenuItem
//         onSelect={(e) => {
//           e.preventDefault()
//           // Use setTimeout to allow menu to close before opening dialog
//           setTimeout(() => setIsOpen(true), 0)
//         }}
//       >
//         Edit Room
//       </DropdownMenuItem>

//       <DialogContent>
//         <form onSubmit={handleSubmit(onSubmit)}>
//           <DialogHeader>
//             <DialogTitle>Edit Room</DialogTitle>
//           </DialogHeader>

//           <div className="flex flex-col gap-4 py-4">
//             <div className="space-y-2">
//               <Label htmlFor="edit-title">
//                 Room Title <span className="text-destructive">*</span>
//               </Label>
//               <Input
//                 id="edit-title"
//                 {...register("title", {
//                   required: "Room title is required",
//                   minLength: {
//                     value: 3,
//                     message: "Title must be at least 3 characters",
//                   },
//                   maxLength: {
//                     value: 100,
//                     message: "Title must be less than 100 characters",
//                   },
//                 })}
//                 placeholder="Room title"
//                 type="text"
//                 className={cn(errors.title && "border-destructive")}
//               />
//               {errors.title && (
//                 <p className="text-sm text-destructive">
//                   {errors.title.message}
//                 </p>
//               )}
//             </div>
//           </div>

//           <DialogFooter>
//             <DialogClose asChild>
//               <Button type="button" variant="outline" disabled={isSubmitting}>
//                 Cancel
//               </Button>
//             </DialogClose>
//             <Button type="submit" disabled={!isValid || isSubmitting}>
//               {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
//               Save Changes
//             </Button>
//           </DialogFooter>
//         </form>
//       </DialogContent>
//     </Dialog>
//   )
// }
