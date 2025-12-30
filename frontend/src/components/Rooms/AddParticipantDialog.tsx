   import { type SubmitHandler, useForm } from "react-hook-form";
   import { useState } from "react";
   import { FaPlus } from "react-icons/fa";

   import type { ApiError } from "@/client/core/ApiError";
   import useCustomToast from "@/hooks/useCustomToast";
   import { handleError } from "@/utils";
   import {
     Button,
     DialogActionTrigger,
     DialogTitle,
     NativeSelectField,
     NativeSelectRoot,
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

   // Available agents from backend
   const AVAILABLE_AGENTS = [
     { value: "StoryAdvisor", label: "Story Advisor" },
     { value: "SymbolWeaver", label: "Symbol Weaver" },
     { value: "CharacterForge", label: "Character Forge" },
     { value: "PlotTwistArchitect", label: "Plot Twist Architect" },
     { value: "DialogueCoach", label: "Dialogue Coach" },
   ];

   interface AddParticipantForm {
     participant_type: 'agent' | 'user';
     participant_id: string;
   }

   interface AddParticipantDialogProps {
     roomId: string;
     currentParticipants: string[]; // Array of participant IDs already in room
     onAdd: (participantId: string, type: 'user' | 'agent') => Promise<void>;
   }

   const AddParticipantDialog = ({
     currentParticipants,
     onAdd,
   }: AddParticipantDialogProps) => {
     const [isOpen, setIsOpen] = useState(false);
     const { showSuccessToast } = useCustomToast();

     const {
       register,
       handleSubmit,
       reset,
       formState: { errors, isValid, isSubmitting },
     } = useForm<AddParticipantForm>({
       mode: "onChange",
       defaultValues: {
         participant_type: "agent",
         participant_id: "",
       },
     });

     // Filter out agents already in the room
     const availableAgents = AVAILABLE_AGENTS.filter(
       (agent) => !currentParticipants.includes(agent.value)
     );

     const onSubmit: SubmitHandler<AddParticipantForm> = async (data) => {
       try {
         await onAdd(data.participant_id, data.participant_type);
         showSuccessToast("Participant added successfully.");
         reset();
         setIsOpen(false);
       } catch (err) {
         handleError(err as ApiError);
       }
     };

     return (
       <DialogRoot
         size={{ base: "xs", md: "md" }}
         placement="center"
         open={isOpen}
         onOpenChange={({ open }) => setIsOpen(open)}
       >
         <DialogTrigger asChild>
           <Button size="sm" variant="outline">
             <FaPlus fontSize="12px" />
             Add Participant
           </Button>
         </DialogTrigger>
         <DialogContent>
           <form onSubmit={handleSubmit(onSubmit)}>
             <DialogHeader>
               <DialogTitle>Add Participant to Room</DialogTitle>
             </DialogHeader>
             <DialogBody>
               <Text mb={4}>
                 Select an agent to add to this collaborative room.
               </Text>
               <VStack gap={4}>
                 <Field
                   required
                   invalid={!!errors.participant_id}
                   errorText={errors.participant_id?.message}
                   label="Agent"
                 >
                   <NativeSelectRoot>
                     <NativeSelectField
                       {...register("participant_id", {
                         required: "Please select an agent",
                       })}
                       placeholder="Select an agent"
                     >
                       <option value="" disabled>
                         Select an agent
                       </option>
                       {availableAgents.map((agent) => (
                         <option key={agent.value} value={agent.value}>
                           {agent.label}
                         </option>
                       ))}
                     </NativeSelectField>
                   </NativeSelectRoot>
                 </Field>

                 {availableAgents.length === 0 && (
                   <Text fontSize="sm" color="gray.500">
                     All available agents are already in this room.
                   </Text>
                 )}
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
                 disabled={!isValid || availableAgents.length === 0}
                 loading={isSubmitting}
               >
                 Add Agent
               </Button>
             </DialogFooter>
           </form>
           <DialogCloseTrigger />
         </DialogContent>
       </DialogRoot>
     );
   };

   export default AddParticipantDialog;