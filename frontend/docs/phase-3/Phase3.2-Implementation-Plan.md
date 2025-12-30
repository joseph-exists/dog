# Phase 3.2 Implementation Plan: Room Management Features

**Version:** 1.2
**Status:** Ready for Implementation
**Last Updated:** 2025-12-28
**Revision:** Updated based on thorough plan review, 5 patches
**Dependencies:** Phase 3.1 (Complete), Phase 2 Backend (Complete)

---

## Executive Summary

This document provides a detailed, step-by-step implementation plan for Phase 3.2 Room Management features. Each task builds incrementally on previous work and follows established patterns from the existing codebase.

**Target:** Minimal viable implementation to enable iteration based on UX feedback.

**Key Deliverables:**
1. ✅ Room creation with form validation
2. ✅ Participant management (add/remove users and agents)
3. ✅ Agent activation toggle
4. ✅ Room metadata editing (title)
5. ✅ Room deletion with confirmation
6. ✅ Display usernames and agent names in messages
7. ✅ Consolidated room actions menu

---

## Existing Implementation Analysis

### ✅ What Already Works (Phase 3.1)

#### **Hooks**
- **`useRoom`** (`frontend/src/hooks/useRoom.ts`)
  - Aggregates room metadata, messages, participants
  - Provides `addParticipant` and `removeParticipant` mutations
  - Computes derived state: `currentUserRole`, `activeAgents`, `activeUsers`
  - Polling enabled (3s for messages, 5s for participants)
  - **NOTE:** Already has participant management mutations implemented!

- **`useRoomMessages`** (`frontend/src/hooks/useRoomMessages.ts`)
  - Message fetching with pagination
  - `sendMessage` mutation with optimistic updates
  - Polling for new messages
  - Auto-scroll handling

#### **Service Layer**
- **`RoomService`** (`frontend/src/services/roomService.ts`)
  - ✅ `listRooms()` - Get all user's rooms
  - ✅ `getRoom()` - Get single room
  - ✅ `createRoom()` - Create new room
  - ✅ `updateRoom()` - Update room metadata (title)
  - ✅ `getMessages()` - Paginated messages
  - ✅ `sendMessage()` - Send message
  - ✅ `getParticipants()` - Get room participants
  - ✅ `addParticipant()` - Add user or agent
  - ✅ `removeParticipant()` - Remove participant
  - ✅ `changeParticipantRole()` - Change participant role
  - **All service methods are complete!**

#### **Components**
- ✅ `MessageList` - Displays messages chronologically
- ✅ `Message` - Individual message with sender name
- ✅ `MessageInput` - Send message form
- ✅ `ParticipantList` - Displays users and agents
- ✅ `RoomHeader` - Room title and metadata
- ✅ `RoomList` - List of all rooms
- ⚠️ `AddRoom` - **Incomplete** (has TODO comments)

#### **Routes**
- ✅ `/_layout/room.$roomId.tsx` - Room view with all components integrated
- ✅ `/_layout/rooms.tsx` - Room list view

#### **Available Agents (Backend)**
From `backend/app/agents/__init__.py`:
1. `StoryAdvisor`
2. `SymbolWeaver`
3. `CharacterForge`
4. `PlotTwistArchitect`
5. `DialogueCoach`

### ❌ What Needs to Be Built

1. ❌ Complete `AddRoom` component (room creation)
2. ❌ `AddParticipantDialog` component (select and add agents/users)
3. ❌ `EditRoomDialog` component (edit room title)
4. ❌ `DeleteRoomDialog` component (delete room with confirmation)
5. ❌ `RoomActionsMenu` component (consolidate edit/delete actions)
6. ❌ Agent toggle UI in `ParticipantList`
7. ❌ Display user/agent names in messages (enhance existing transformations)
8. ❌ Hook mutations for room update and delete in `useRoom`

---

## Implementation Tasks

### Task 1: Enhance RoomService User Lookup (Foundation)

**Priority:** HIGH
**Estimated Time:** 30 minutes
**Dependencies:** None

#### Context
Currently, `transformMessage()` and `transformParticipant()` use placeholder names for users (just shows UUID). The `roomService.ts` file already has utility functions `enrichMessagesWithUserNames()` and `enrichParticipantsWithUserProfiles()` designed for this exact purpose. We just need to implement the user lookup logic and call these functions.

#### Implementation Steps

1. [X]  **Add UsersService import to roomService.ts**


2. [X] **Create a user cache helper (add before the RoomService object)**

3. [X] **Update `getMessages()` to use the existing `enrichMessagesWithUserNames()` utility** DONE
   

4. [X] **Update `getParticipants()` to use the existing `enrichParticipantsWithUserProfiles()` utility**
 

#### Verification
- Messages show "John Doe" instead of UUID for user messages
- Agent messages still show agent names correctly (e.g., "Story Advisor")
- Participant list shows user full names instead of UUIDs
- Participant list shows agent names correctly
- No performance regression (caching prevents redundant fetches)
- Multiple messages from same user only fetch user details once

#### Builds On
- Existing service layer architecture
- Existing utility functions (`enrichMessagesWithUserNames`, `enrichParticipantsWithUserProfiles`)
- Existing transformation functions (keep them pure, no modifications needed)

#### Enables
- Phase 3.2 deliverable #6 (usernames and agent names displayed with messages)
- Better UX for participant list

---

### Task 2: Add Room Update and Delete Mutations to useRoom Hook

**Priority:** HIGH
**Estimated Time:** 45 minutes
**Dependencies:** Task 1

#### Context
The `useRoom` hook needs `updateRoom` and `deleteRoom` mutations to support editing and deletion. RoomService already has these methods; we just need to wire them into the hook.

#### Implementation Steps

1. [x] **Update `UseRoomResult` interface in `useRoom.ts`**
   -- delete functionalities

2. [x] **Add room update mutation**
   ```typescript
   // After removeParticipantMutation, add:

   // Update room mutation
   const updateRoomMutation = useMutation({
     mutationFn: async (data: { title?: string | null }) => {
       return await RoomService.updateRoom(roomId, data);
     },
     onSuccess: () => {
       // Invalidate room metadata to refetch
       queryClient.invalidateQueries({ queryKey: roomQueryKey });
     },
     onError: (err: ApiError) => {
       handleError(err);
     },
   });
   ```

3. [x] **Add room delete mutation with navigation**
   ```typescript
   // Delete room mutation
   const deleteRoomMutation = useMutation({
     mutationFn: async () => {
       // Call service method (will throw error if backend not ready)
       await RoomService.deleteRoom(roomId);
     },
     onSuccess: () => {
       // Invalidate queries
       queryClient.invalidateQueries({ queryKey: ['rooms'] });
       queryClient.invalidateQueries({ queryKey: roomQueryKey });

       // Call optional callback (component provides navigation)
       options?.onDeleteSuccess?.();
     },
     onError: (err: ApiError) => {
       handleError(err);
     },
   });
   ```

4. [x] **Add action wrappers**
   ```typescript
   const updateRoom = useCallback(
     async (data: { title?: string | null }) => {
       await updateRoomMutation.mutateAsync(data);
     },
     [updateRoomMutation]
   );

   const deleteRoom = useCallback(
     async () => {
       await deleteRoomMutation.mutateAsync();
     },
     [deleteRoomMutation]
   );
   ```

5. [x] **Update return value**
   ```typescript
   return {
     // ... existing fields ...

     // Room Management
     updateRoom,
     deleteRoom,
     isUpdatingRoom: updateRoomMutation.isPending,
     isDeletingRoom: deleteRoomMutation.isPending,
   };
   ```

6. [x] **Add deleteRoom to RoomService** (if not exists)
   ```typescript
   // In roomService.ts, add to RoomService object:

   /**
    * Delete a room (owner-only, hard delete)
    *
    * @param roomId - Room UUID
    * @returns Promise that resolves when deletion is complete
    * @throws ApiError - 403 if not room owner, 404 if room not found
    */
   async deleteRoom(roomId: string): Promise<void> {
    throw new Error(
      'Room deletion not yet supported. Backend endpoint needs to be created.'
    ); 
     // uncomment once we figure out this endpoint
     // await RoomsService.deleteRoom({ roomId });
   },
   ```

#### Verification
- `updateRoom({ title: 'New Title' })` updates room title
- `deleteRoom()` navigates to `/rooms` after deletion
- Loading states (`isUpdatingRoom`, `isDeletingRoom`) work correctly
- Errors handled gracefully with toast notifications

#### Builds On
- Task 1 (service layer is ready)
- Existing mutation pattern in useRoom

#### Enables
- Task 8 (EditRoomDialog can use `updateRoom`)
- Task 10 (DeleteRoomDialog can use `deleteRoom`)

---

### Task 3: Complete AddRoom Component (Room Creation)

**Priority:** HIGH
**Estimated Time:** 1 hour
**Dependencies:** Task 2

#### Context
`AddRoom.tsx` exists but is incomplete (has TODO comments). We need to complete it following the pattern from `AddUser.tsx`.

#### Implementation Steps

1. [x] **Review existing AddRoom.tsx** - It has basic dialog structure, needs form logic

2. [x] **Implement form with React Hook Form**
   ```typescript
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
   ```

3. [x] **Update `/rooms` route to include AddRoom button**
   - Verify it's already included in `/_layout/rooms.tsx`
   - If not, add it to the top of the room list

#### Verification
- Click "Create Room" opens dialog
- Form validation works (title required, min 3 chars)
- Submitting form creates room and navigates to it
- Errors display as toasts
- Success shows toast and navigates

#### Builds On
- Task 2 (RoomService.createRoom already exists)
- AddUser component pattern

#### Enables
- Users can create rooms (Phase 3.2 deliverable #1)

---

### Task 4: Create AddParticipantDialog Component

**Priority:** HIGH
**Estimated Time:** 1.5 hours
**Dependencies:** Task 3

#### Context
Users need to add agents (and eventually other users) to rooms. This requires a dialog with agent selection.

#### Implementation Steps

1. [x] **Create new file: `frontend/src/components/Rooms/AddParticipantDialog.tsx`**

2. [x] **Implement agent selection dropdown**


3. **Integrate into RoomHeader**
   ```typescript
   // In RoomHeader.tsx, add:
   import AddParticipantDialog from './AddParticipantDialog';

   // In component, get the addParticipant function from useRoom via props
   // Add to props interface:
   interface RoomHeaderProps {
     // ... existing props ...
     onAddParticipant: (participantId: string, type: 'user' | 'agent') => Promise<void>;
   }

   // In JSX, add button next to title (only if owner):
   {currentUserRole === 'owner' && (
     <AddParticipantDialog
       roomId={room.room_id}
       currentParticipants={participants.map(p => p.participant_id)}
       onAdd={onAddParticipant}
     />
   )}
   ```

4. **Update room route to pass addParticipant**
   ```typescript
   // In room.$roomId.tsx:
   <RoomHeader
     room={room}
     participants={participants}
     activeAgents={activeAgents}
     currentUserRole={currentUserRole}
     onAddParticipant={addParticipant}  // NEW
   />
   ```

#### Verification
- Only room owner sees "Add Participant" button
- Dialog shows available agents
- Already-added agents are filtered out
- Selecting agent and submitting adds them to room
- Participant list updates automatically (via polling/invalidation)
- Error handling works

#### Builds On
- Task 2 (useRoom hook has addParticipant)
- Task 3 (dialog pattern established)

#### Enables
- Phase 3.2 deliverable #2 (add participants)

---

### Task 5: Create RemoveParticipantButton Component

**Priority:** MEDIUM
**Estimated Time:** 45 minutes
**Dependencies:** Task 4

#### Context
Room owners need ability to remove participants (users or agents) from the room. This should be a simple inline button with confirmation.

#### Implementation Steps

1. **Create new file: `frontend/src/components/Rooms/RemoveParticipantButton.tsx`**

2. [x] **Implement with confirmation dialog**


3. [x] **Integrate into ParticipantList**
   ```typescript
   // Update ParticipantList.tsx to accept remove function and role
   import RemoveParticipantButton from './RemoveParticipantButton';

   interface ParticipantListProps {
     activeUsers: ParticipantViewModel[];
     activeAgents: ParticipantViewModel[];
     isLoading?: boolean;
     currentUserRole: 'owner' | 'member' | null; // NEW
     onRemoveParticipant?: (participantId: string) => Promise<void>; // NEW
   }

   // In the JSX, add remove button next to each participant (if owner):
   {activeUsers.map((p) => (
     <Flex key={p.participant_id} justify="space-between" w="full">
       <Text>{p.display_name}</Text>
       {currentUserRole === 'owner' && onRemoveParticipant && (
         <RemoveParticipantButton
           participantId={p.participant_id}
           participantName={p.display_name}
           participantType="user"
           onRemove={onRemoveParticipant}
         />
       )}
     </Flex>
   ))}

   // Same for agents
   ```

4. [x] **Update room route to pass props**
   ```typescript
   <ParticipantList
     activeUsers={activeUsers}
     activeAgents={activeAgents}
     isLoading={isLoadingParticipants}
     currentUserRole={currentUserRole}  // NEW
     onRemoveParticipant={removeParticipant}  // NEW
   />
   ```

#### Verification
- Remove button only visible to room owner
- Clicking remove shows confirmation dialog
- Confirming removes participant
- Participant list updates automatically
- Toast shows success message

#### Builds On
- Task 4 (participant management pattern)
- Existing useRoom.removeParticipant

#### Enables
- Phase 3.2 deliverable #3 (remove participants)

---

### Task 6: Add Agent Toggle Component

**Priority:** MEDIUM
**Estimated Time:** 1 hour
**Dependencies:** Task 5

#### Context
Agents in the participant list should have a toggle switch to activate/deactivate them without removing them. This uses the existing `addParticipant` and `removeParticipant` functionality.

#### Implementation Steps

1. [x] **Create new file: `frontend/src/components/Rooms/AgentToggle.tsx`**

2. [x] **Implement toggle switch**

3. [x] **Update ParticipantList to use AgentToggle**
   ```typescript
   import AgentToggle from './AgentToggle';

   interface ParticipantListProps {
     // ... existing props ...
     onToggleAgent?: (agentId: string, activate: boolean) => Promise<void>; // NEW
   }

   // Replace agent rendering with:
   {activeAgents.map((p) => (
     currentUserRole === 'owner' && onToggleAgent ? (
       <AgentToggle
         key={p.participant_id}
         agentId={p.participant_id}
         agentName={p.display_name}
         isActive={p.is_active}
         onToggle={onToggleAgent}
       />
     ) : (
       <Text key={p.participant_id}>🤖 {p.display_name}</Text>
     )
   ))}
   ```

4. [x] **Implement toggle handler in room route**
   ```typescript
   // In room.$roomId.tsx:
   const handleToggleAgent = async (agentId: string, activate: boolean) => {
     if (activate) {
       await addParticipant(agentId, 'agent');
     } else {
       await removeParticipant(agentId);
     }
   };

   // Pass to ParticipantList:
   <ParticipantList
     // ... existing props ...
     onToggleAgent={handleToggleAgent}
   />
   ```

#### Verification
- Toggle switch appears next to agents (owner only)
- Toggling off deactivates agent (stops responding)
- Toggling on reactivates agent
- Loading state shows during toggle
- Toast confirms action

#### Builds On
- Task 5 (participant management)
- Existing add/remove participant mutations

#### Enables
- Phase 3.2 deliverable #6 (toggle agents)

---

### Task 7: Create EditRoomDialog Component

**Priority:** MEDIUM
**Estimated Time:** 45 minutes
**Dependencies:** Task 2

#### Context
Room owners need ability to edit room metadata (primarily title). This is a simple form dialog.

#### Implementation Steps

1. [x] **Create new file: `frontend/src/components/Rooms/EditRoomDialog.tsx`**

2. [x] **Implement edit form**

  
#### Verification
- Clicking "Edit Room" opens dialog with current title pre-filled
- Form validation works
- Submitting updates room title
- Room header shows new title immediately
- Toast confirms success

#### Builds On
- Task 2 (useRoom.updateRoom mutation)
- Task 3 (dialog form pattern)

#### Enables
- Phase 3.2 deliverable #5 (edit room metadata)

---

### BLOCKED DO NOT IMPLEMENT Task 8: Create DeleteRoomDialog Component BLOCKED

**Priority:** MEDIUM
**Estimated Time:** 30 minutes
**Dependencies:** Task 7

#### Context
Room owners need ability to delete rooms with strong confirmation (destructive action).

**⚠️ BLOCKED:** This feature is currently blocked on backend implementation. The dialog
can be implemented and integrated, but the actual deletion will throw an error until
the backend DELETE endpoint is created.

**Backend Ticket Needed:**
- Add `DELETE /api/v1/rooms/{room_id}` endpoint
- Regenerate OpenAPI client
- Update RoomService.deleteRoom() to use the endpoint

#### Implementation Steps

1. **Create new file: `frontend/src/components/Rooms/DeleteRoomDialog.tsx`**

2. **Implement delete confirmation**
   ```typescript
   import { useState } from "react";
   import { Button, Text, VStack } from "@chakra-ui/react";
   import {
     DialogRoot,
     DialogContent,
     DialogHeader,
     DialogTitle,
     DialogBody,
     DialogFooter,
     DialogActionTrigger,
     DialogCloseTrigger,
   } from "../ui/dialog";
   import { MenuItem } from "../ui/menu";
   import type { ApiError } from "@/client/core/ApiError";
   import useCustomToast from "@/hooks/useCustomToast";
   import { handleError } from "@/utils";

   interface DeleteRoomDialogProps {
     roomTitle: string;
     onDelete: () => Promise<void>;
   }

   const DeleteRoomDialog = ({ roomTitle, onDelete }: DeleteRoomDialogProps) => {
     const [isOpen, setIsOpen] = useState(false);
     const [isDeleting, setIsDeleting] = useState(false);
     const { showSuccessToast } = useCustomToast();

     const handleDelete = async () => {
       setIsDeleting(true);
       try {
         await onDelete();
         showSuccessToast("Room deleted successfully.");
         // Navigation handled by onDelete (in useRoom mutation)
       } catch (err) {
         handleError(err as ApiError);
         setIsDeleting(false);
       }
     };

     return (
       <DialogRoot
         size="sm"
         open={isOpen}
         onOpenChange={({ open }) => setIsOpen(open)}
       >
         {/* Trigger as MenuItem for ActionsMenu */}
         <MenuItem
           value="delete"
           color="red.600"
           _dark={{ color: "red.400" }}
           onClick={() => setIsOpen(true)}
         >
           Delete Room
         </MenuItem>

         <DialogContent>
           <DialogHeader>
             <DialogTitle>Delete Room?</DialogTitle>
           </DialogHeader>
           <DialogBody>
             <VStack align="start" gap={2}>
               <Text>
                 Are you sure you want to delete <strong>{roomTitle}</strong>?
               </Text>
               <Text fontSize="sm" color="red.600" _dark={{ color: "red.400" }}>
                 This action cannot be undone. All messages and participant history will be permanently deleted.
               </Text>
             </VStack>
           </DialogBody>
           <DialogFooter gap={2}>
             <DialogActionTrigger asChild>
               <Button variant="subtle" colorPalette="gray">
                 Cancel
               </Button>
             </DialogActionTrigger>
             <Button
               colorPalette="red"
               onClick={handleDelete}
               loading={isDeleting}
             >
               Delete Room
             </Button>
           </DialogFooter>
           <DialogCloseTrigger />
         </DialogContent>
       </DialogRoot>
     );
   };

   export default DeleteRoomDialog;
   ```

#### Verification
- Clicking "Delete Room" shows warning dialog
- Confirmation required (strong warning text)
- Deleting navigates to /rooms
- Toast confirms deletion
- Error handling works

#### Builds On
- Task 2 (useRoom.deleteRoom mutation)
- Task 7 (dialog pattern)

#### Enables
- Phase 3.2 deliverable #4 (delete room)

---

### Task 9: Create RoomActionsMenu Component

**Priority:** MEDIUM
**Estimated Time:** 30 minutes
**Dependencies:** Tasks 7, 8

#### Context
Consolidate edit and delete actions into a dropdown menu in the room header (owner only).

#### Implementation Steps

1. [x] **Create new file: `frontend/src/components/Common/RoomActionsMenu.tsx`**

2. [x] **Implement menu component**

3. [x] **Integrate into RoomHeader**
   ```typescript
   // In RoomHeader.tsx:
   import { RoomActionsMenu } from '@/components/Common/RoomActionsMenu';

   interface RoomHeaderProps {
     room: RoomViewModel | undefined;
     // ... existing props ...
     onUpdateRoom?: (data: { title: string }) => Promise<void>; // NEW
     onDeleteRoom?: () => Promise<void>; // NEW
   }

   // In JSX, add next to title (owner only):
   {currentUserRole === 'owner' && room && onUpdateRoom && onDeleteRoom && (
     <RoomActionsMenu
       room={room}
       onUpdate={onUpdateRoom}
       onDelete={onDeleteRoom}
     />
   )}
   ```

4. [x] **Update room route to pass functions**
   ```typescript
   <RoomHeader
     room={room}
     participants={participants}
     activeAgents={activeAgents}
     currentUserRole={currentUserRole}
     onAddParticipant={addParticipant}
     onUpdateRoom={updateRoom}  // NEW
     onDeleteRoom={deleteRoom}  // NEW
   />
   ```

5. **Update room route integration:**
```typescript
// In room.$roomId.tsx:
const navigate = useNavigate();

const {
  room,
  messages,
  // ... other state
  updateRoom,
  deleteRoom,
  // ... rest
} = useRoom(roomId, {
  enablePolling: true,
  onDeleteSuccess: () => {
    // Component controls navigation after deletion
    navigate({ to: '/rooms' });
  },
});

// Pass to components:
<RoomHeader
  room={room}
  participants={participants}
  activeAgents={activeAgents}
  currentUserRole={currentUserRole}
  onAddParticipant={addParticipant}
  onUpdateRoom={updateRoom}
  onDeleteRoom={deleteRoom}  // Hook handles mutation, component handles navigation
/>
```


#### Verification
- Three-dot menu appears in room header (owner only)
- Menu contains "Edit Room" and "Delete Room"
- Clicking each opens respective dialog
- Actions work as expected

#### Builds On
- Tasks 7, 8 (dialog components)
- ItemActionsMenu pattern

#### Enables
- Phase 3.2 deliverable #7 (room actions menu)

---

### Task 10: Final Integration and Testing

**Priority:** HIGH
**Estimated Time:** 2 hours
**Dependencies:** All previous tasks

#### Context
Final integration of all components and comprehensive testing of the complete Phase 3.2 feature set.

#### Implementation Steps

1. **Verify all components are integrated in room view**
   - Check `room.$roomId.tsx` has all new props wired up
   - Verify `rooms.tsx` has AddRoom button
   - Test navigation flows

2. **Test CRUD operations end-to-end**
   - **Create Room**: Create room → should navigate to new room
   - **Read Room**: View room → should show messages, participants
   - **Update Room**: Edit title → should update immediately
   - **Delete Room**: Delete room → should navigate to /rooms

3. **Test Participant Management**
   - **Add Agent**: Add StoryAdvisor → should appear in participant list
   - **Toggle Agent**: Deactivate agent → should stop responding
   - **Toggle Agent**: Reactivate agent → should start responding
   - **Remove Participant**: Remove agent → should disappear from list
   - **Filter Agents**: Already-added agents shouldn't appear in "Add" dropdown

4. **Test Authorization**
   - **Member Role**: Verify members cannot see edit/delete/add buttons
   - **Owner Role**: Verify owner sees all management buttons
   - **403 Handling**: Non-participant accessing room → should redirect to /rooms

5. **Test Error Handling**
   - **Network Error**: Disconnect network → should show retry toast
   - **Validation Error**: Submit empty title → should show inline error
   - **Server Error**: Trigger 500 error → should show user-friendly message

6. **Test Loading States**
   - **Room Loading**: Initial load shows spinner
   - **Message Sending**: Shows loading on send button
   - **Participant Adding**: Shows loading during add
   - **Room Deleting**: Shows loading during delete

7. **Test Display Names**
   - **User Messages**: Should show user's full name (not UUID)
   - **Agent Messages**: Should show agent name
   - **Own Messages**: Should highlight user's own messages

8. **Performance Testing**
   - **Polling**: Verify polling works (3s messages, 5s participants)
   - **Cache**: Verify data cached correctly (no redundant fetches)
   - **Optimistic Updates**: User messages appear immediately

9. **Create test checklist document**
   ```markdown
   # Phase 3.2 Test Checklist

   ## Room Creation
   - [X] Click "Create Room" button
   - [X] Enter title (min 3 chars)
   - [X] Submit creates room
   - [X] Navigates to new room
   - [X] Toast shows success
   - [X] Validation errors show

   ## Participant Management
   - [X] Add agent (owner only)
   - [X] Agent appears in list
   - [X] Remove agent (owner only)
   - [X] Agent disappears
   - [X] Toggle agent off
   - [X] Toggle agent on
   - [X] Filter already-added agents

   ## Room Metadata
   - [ ] Edit room title (owner only)
   - [ ] Title updates immediately
   - [ ] Delete room (owner only)
   - [ ] Confirms before delete
   - [ ] Navigates to /rooms after delete

   ## Display
   - [X] User messages show full name
   - [X] Agent messages show agent name
   - [X] Own messages highlighted
   - [X] Timestamps display correctly

   ## Authorization
   - [ ] Members don't see owner actions
   - [ ] 403 redirects to /rooms

   ## Error Handling
   - [ ] Network errors show toast
   - [ ] Validation errors inline
   - [ ] Server errors user-friendly

   ## Performance
   - [ ] Polling works (3s/5s)
   - [ ] Optimistic updates
   - [ ] Cache prevents redundant fetches
   ```

#### Verification
- All items in test checklist pass
- No console errors
- No TypeScript errors
- No accessibility violations (basic check)
- Phase 3.2 success criteria all met

#### Builds On
- All previous tasks

#### Enables
- Phase 3.2 sign-off and handoff to Phase 4

---

## Implementation Order & Dependencies

### Critical Path (Must Be Done in Order)

1. **Task 1** (User Lookup) → Foundation for display names
2. **Task 2** (Hook Mutations) → Enables all room management
3. **Task 3** (AddRoom) → First user-facing feature
4. **Task 4** (AddParticipant) → Builds on Task 3 pattern
5. **Task 5** (RemoveParticipant) → Complements Task 4
6. **Task 6** (AgentToggle) → Uses Task 4 & 5 infrastructure
7. **Task 7** (EditRoom) → Uses Task 2 mutations
8. **Task 8** (DeleteRoom) → Uses Task 2 mutations
9. **Task 9** (ActionsMenu) → Consolidates Tasks 7 & 8
10. **Task 10** (Testing) → Validates everything

### Parallelization Opportunities

After completing Tasks 1-2, the following can be done in parallel:

- **Track A**: Tasks 3 → 4 → 5 → 6 (Participant management flow)
- **Track B**: Tasks 7 → 8 → 9 (Room metadata management flow)

Then both tracks merge at Task 10 (Testing).

---

## Success Criteria (from Phase3-TechnicalSpec.md §8)

| # | Criterion | Tasks |
|---|-----------|-------|
| 1 | ✅ User can view list of accessible rooms | Phase 3.1 |
| 2 | ✅ User can create a new room | Task 3 |
| 3 | ✅ User can select a room and view message history | Phase 3.1 |
| 4 | ✅ User can send a message and see it appear immediately | Phase 3.1 |
| 5 | ✅ User sees agent responses appear after backend processing | Phase 3.1 |
| 6 | ✅ User can view participant list (users and agents) | Phase 3.1 |
| 7 | ✅ User can add agents to the room | Task 4 |
| 8 | ✅ User with owner role can remove participants | Task 5 |
| 9 | ✅ Message history paginates correctly | Phase 3.1 |
| 10 | ✅ Polling updates messages every 3-5 seconds | Phase 3.1 |
| 11 | ✅ Authorization errors (403) redirect to room list | Phase 3.1 |
| 12 | ✅ Network errors show retry option | Phase 3.1 |
| 13 | ✅ All tests pass (unit + integration) | Task 10 |
| 14 | ✅ No regressions in existing frontend features | Task 10 |
| 15 | ✅ OpenAPI client remains synchronized with backend | Ongoing |

**Phase 3.2 Specific Additions:**
- ✅ Users can toggle agents active/inactive (Task 6)
- ✅ Usernames and agent names displayed with messages (Task 1)
- ✅ Room owners can edit room metadata (Task 7)
- ✅ Room owners can delete rooms (Task 8)

---

## Risk Mitigation



---

## Appendix: Code Patterns Reference

### Dialog Pattern
```typescript
const MyDialog = ({ onAction }: Props) => {
  const [isOpen, setIsOpen] = useState(false);
  const { register, handleSubmit, formState } = useForm();

  return (
    <DialogRoot open={isOpen} onOpenChange={({ open }) => setIsOpen(open)}>
      <DialogTrigger asChild>
        <Button>Open</Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader><DialogTitle>Title</DialogTitle></DialogHeader>
          <DialogBody>{/* Form fields */}</DialogBody>
          <DialogFooter>
            <DialogActionTrigger asChild>
              <Button variant="subtle">Cancel</Button>
            </DialogActionTrigger>
            <Button type="submit">Save</Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  );
};
```

### Mutation Pattern
```typescript
const mutation = useMutation({
  mutationFn: async (data) => Service.method(data),
  onSuccess: () => {
    showSuccessToast("Success message");
    queryClient.invalidateQueries({ queryKey: ["key"] });
  },
  onError: (err: ApiError) => {
    handleError(err);
  },
});
```

### Menu Pattern (from ItemActionsMenu)
```typescript
export const MyActionsMenu = ({ item, onEdit, onDelete }: Props) => (
  <MenuRoot>
    <MenuTrigger asChild>
      <IconButton variant="ghost">
        <BsThreeDotsVertical />
      </IconButton>
    </MenuTrigger>
    <MenuContent>
      <EditDialog item={item} onEdit={onEdit} />
      <DeleteDialog item={item} onDelete={onDelete} />
    </MenuContent>
  </MenuRoot>
);
```

---

**End of Implementation Plan**
