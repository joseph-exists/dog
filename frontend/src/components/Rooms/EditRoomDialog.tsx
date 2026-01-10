   import { useState } from "react";
   import { type SubmitHandler, useForm } from "react-hook-form";
   import {
     Button,
     DialogActionTrigger,
     DialogTitle,
     Input,
     VStack,
   } from "@chakra-ui/react";
  import {
    DialogBody,
    DialogCloseTrigger,
    DialogContent,
    DialogFooter,
    DialogHeader,
    DialogRoot,
  } from "../ui/dialog";
   import { Field } from "../ui/field";
   import { MenuItem } from "../ui/menu";
   import type { RoomViewModel } from "@/services/roomService";
   import type { ApiError } from "@/client/core/ApiError";
   import useCustomToast from "@/hooks/useCustomToast";
   import { handleError } from "@/utils";

   interface EditRoomForm {
     title: string;
   }

   interface EditRoomDialogProps {
     room: RoomViewModel;
     onUpdate: (data: { title: string }) => Promise<void>;
   }

   const EditRoomDialog = ({ room, onUpdate }: EditRoomDialogProps) => {
     const [isOpen, setIsOpen] = useState(false);
     const { showSuccessToast } = useCustomToast();

     const {
       register,
       handleSubmit,
       reset,
       formState: { errors, isValid, isSubmitting },
     } = useForm<EditRoomForm>({
       mode: "onBlur",
       defaultValues: {
         title: room.title || "",
       },
     });

     const onSubmit: SubmitHandler<EditRoomForm> = async (data) => {
       try {
         await onUpdate({ title: data.title });
         showSuccessToast("Room updated successfully.");
         setIsOpen(false);
       } catch (err) {
         handleError(err as ApiError);
       }
     };

     return (
       <DialogRoot
         size={{ base: "xl", md: "md" }}
         placement="center"
         open={isOpen}
         onOpenChange={({ open }) => {
           setIsOpen(open);
           if (!open) reset(); // Reset form when closing
         }}
      >
        {/* Trigger as MenuItem for ActionsMenu */}
        <MenuItem 
          value="edit" 
          onClick={(e) => {
            e.stopPropagation();
            // Use setTimeout to allow menu to close before opening dialog
            setTimeout(() => {
              setIsOpen(true);
            }, 0);
          }}
        >
          Edit Room
        </MenuItem>

        <DialogContent>
           <form onSubmit={handleSubmit(onSubmit)}>
             <DialogHeader>
               <DialogTitle>Edit Room</DialogTitle>
             </DialogHeader>
             <DialogBody>
               <VStack gap={4}>
                 <Field
                   required
                   invalid={!!errors.title}
                   errorText={errors.title?.message}
                   label="Room Title"
                 >
                   <Input
                     id="title"
                     {...register("title", {
                       required: "Room title is required",
                       minLength: {
                         value: 3,
                         message: "Title must be at least 3 characters",
                       },
                       maxLength: {
                         value: 100,
                         message: "Title must be less than 100 characters",
                       },
                     })}
                     placeholder="Room title"
                     type="text"
                   />
                 </Field>
               </VStack>
             </DialogBody>

             <DialogFooter gap={2}>
               <DialogActionTrigger asChild>
                 <Button
                   disabled={isSubmitting}
                 >
                   Cancel
                 </Button>
               </DialogActionTrigger>
               <Button
                 variant="solid"
                 type="submit"
                 disabled={!isValid}
                 loading={isSubmitting}
               >
                 Save Changes
               </Button>
             </DialogFooter>
           </form>
           <DialogCloseTrigger />
         </DialogContent>
       </DialogRoot>
     );
   };

   export default EditRoomDialog;