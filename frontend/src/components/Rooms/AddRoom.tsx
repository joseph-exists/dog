   import { useMutation, useQueryClient } from "@tanstack/react-query";
   import { type SubmitHandler, useForm } from "react-hook-form";
   import { useState } from "react";
   import { FaPlus } from "react-icons/fa";
   import { useNavigate } from "@tanstack/react-router";

   import { RoomService, type CreateRoomInput } from "@/services/roomService";
   import type { ApiError } from "@/client/core/ApiError";
   import useCustomToast from "@/hooks/useCustomToast";
   import { handleError } from "@/utils";
   import {
     Button,
     DialogActionTrigger,
     DialogTitle,
     Input,
     Text,
     VStack,
   } from "@chakra-ui/react";
   import {
     DialogBody,
     DialogCloseTrigger,
     DialogContent,
     DialogFooter,
     DialogHeader,
     DialogRoot,
     DialogTrigger,
   } from "../ui/dialog";
   import { Field } from "../ui/field";

   const AddRoom = () => {
     const [isOpen, setIsOpen] = useState(false);
     const queryClient = useQueryClient();
     const navigate = useNavigate();
     const { showSuccessToast } = useCustomToast();

     const {
       register,
       handleSubmit,
       reset,
       formState: { errors, isValid, isSubmitting },
     } = useForm<CreateRoomInput>({
       mode: "onBlur",
       defaultValues: {
         title: "",
         story_id: null,
       },
     });

     const mutation = useMutation({
       mutationFn: (data: CreateRoomInput) =>
         RoomService.createRoom(data),
       onSuccess: (room) => {
         showSuccessToast("Room created successfully.");
         reset();
         setIsOpen(false);
         // Navigate to the new room
         navigate({ to: '/room/$roomId', params: { roomId: room.room_id } });
       },
       onError: (err: ApiError) => {
         handleError(err);
       },
       onSettled: () => {
         queryClient.invalidateQueries({ queryKey: ["rooms"] });
       },
     });

     const onSubmit: SubmitHandler<CreateRoomInput> = (data) => {
       mutation.mutate(data);
     };

     return (
       <DialogRoot
         size={{ base: "xs", md: "md" }}
         placement="center"
         open={isOpen}
         onOpenChange={({ open }) => setIsOpen(open)}
       >
         <DialogTrigger asChild>
           <Button value="add-room" my={4}>
             <FaPlus fontSize="16px" />
             Create Room
           </Button>
         </DialogTrigger>
         <DialogContent>
           <form onSubmit={handleSubmit(onSubmit)}>
             <DialogHeader>
               <DialogTitle>Create New Room</DialogTitle>
             </DialogHeader>
             <DialogBody>
               <Text mb={4}>
                 Create a collaborative space for story creation.
               </Text>
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
                     placeholder="e.g., My Story Workshop"
                     type="text"
                   />
                 </Field>

                 {/* Story ID is optional for now, can be added later */}
               </VStack>
             </DialogBody>

             <DialogFooter gap={2}>
               <DialogActionTrigger asChild>
                 <Button
                   variant="subtle"
                   colorPalette="gray"
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
                 Create Room
               </Button>
             </DialogFooter>
           </form>
           <DialogCloseTrigger />
         </DialogContent>
       </DialogRoot>
     );
   };

   export default AddRoom;