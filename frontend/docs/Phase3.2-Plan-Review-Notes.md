# Phase 3.2 Implementation Plan Review

**Date:** 2025-12-28
**Reviewers:** Code Analysis
**Files Reviewed:**
- `frontend/src/hooks/useRoom.ts`
- `frontend/src/hooks/useRoomMessages.ts`
- `frontend/src/services/roomService.ts`
- `frontend/src/client/sdk.gen.ts`
- `frontend/docs/Phase3.2-Implementation-Plan.md`

---

## Summary

Overall, the implementation plan is **very accurate** and well-aligned with the existing code. However, there are **two architectural issues** that need addressing before implementation begins.

---

## ✅ Correctly Identified in Plan

### 1. **Task 1: User Lookup** ✅
- **Plan says:** Need to add user lookup to display names instead of UUIDs
- **Actual code:** Utility functions `enrichMessagesWithUserNames()` and `enrichParticipantsWithUserProfiles()` exist but aren't being called
- **Verdict:** CORRECT - Task 1 accurately describes what needs to be done

### 2. **Task 2: Missing Mutations** ✅
- **Plan says:** Need to add `updateRoom` and `deleteRoom` mutations to `useRoom` hook
- **Actual code:**
  - `useRoom.ts` lines 37-70: `UseRoomResult` interface has NO `updateRoom` or `deleteRoom` fields
  - Only has `addParticipant` and `removeParticipant` (lines 169-204)
- **Verdict:** CORRECT - These mutations are missing and need to be added

### 3. **Backend Delete Endpoint Missing** ✅
- **Plan says:** Backend doesn't have delete endpoint yet
- **Actual code:**
  - Backend routes: No DELETE endpoint found for rooms
  - `RoomsService` in SDK: Has `createNewRoom`, `updateRoom`, but NO `deleteRoom`
- **Verdict:** CORRECT - Delete endpoint doesn't exist in backend

### 4. **Service Methods Exist** ✅
- **Plan says:** RoomService has `updateRoom()` method ready to use
- **Actual code:** `roomService.ts` has `updateRoom()` method (lines 320-334)
- **Verdict:** CORRECT - Service layer is ready

### 5. **Participant Management Complete** ✅
- **Plan says:** `addParticipant` and `removeParticipant` already exist in useRoom
- **Actual code:** Both mutations exist in `useRoom.ts` (lines 169-204)
- **Verdict:** CORRECT - No changes needed for participant management

---

## ⚠️ Issues Found - Require Plan Updates

### Issue 1: Navigation in Hook (Architectural Concern)

**Location:** Task 2, Step 3

**Current Plan:**
```typescript
// Inside useRoom function:
const navigate = useNavigate();

const deleteRoomMutation = useMutation({
  onSuccess: () => {
    // Navigate to rooms list after successful deletion
    navigate({ to: '/rooms' });
    queryClient.invalidateQueries({ queryKey: ['rooms'] });
  },
});
```

**Problem:**
- Couples the hook to navigation behavior
- Reduces hook reusability
- Makes testing harder (need to mock navigation)
- Violates separation of concerns (data hooks shouldn't control navigation)

**Better Pattern:**
Let the component handle navigation by accepting an optional callback:

```typescript
// Hook interface
export interface UseRoomOptions {
  enablePolling?: boolean;
  pollingInterval?: number;
  autoScrollToBottom?: boolean;
  onDeleteSuccess?: () => void;  // NEW
}

// Hook implementation
const deleteRoomMutation = useMutation({
  mutationFn: async () => {
    await RoomService.deleteRoom(roomId);
  },
  onSuccess: () => {
    // Invalidate queries
    queryClient.invalidateQueries({ queryKey: ['rooms'] });
    queryClient.invalidateQueries({ queryKey: roomQueryKey });

    // Call optional callback (component can provide navigation)
    options?.onDeleteSuccess?.();
  },
  onError: (err: ApiError) => {
    handleError(err);
  },
});
```

**Component Usage:**
```typescript
// In room.$roomId.tsx
const navigate = useNavigate();

const { deleteRoom, ... } = useRoom(roomId, {
  enablePolling: true,
  onDeleteSuccess: () => {
    navigate({ to: '/rooms' });
  },
});
```

**Benefits:**
- Hook remains pure and reusable
- Component controls navigation
- Easier to test
- More flexible (can do other things on delete success)

---

### Issue 2: Backend Delete Endpoint Needs Creation

**Location:** Task 2, Step 6 (and RoomService)

**Current Plan:**
```typescript
// Step 6 says "Add deleteRoom to RoomService (if not exists)"
async deleteRoom(roomId: string): Promise<void> {
  await RoomsService.deleteRoom({ roomId });
}
```

**Problem:**
- `RoomsService.deleteRoom()` doesn't exist in the generated SDK
- This will cause TypeScript errors
- Backend endpoint needs to be created first

**Better Approach:**

**Option A: Stub it out temporarily**
```typescript
// In roomService.ts
async deleteRoom(roomId: string): Promise<void> {
  // TODO: Backend endpoint doesn't exist yet
  // File backend ticket: Add DELETE /api/v1/rooms/{room_id} endpoint
  throw new Error('Room deletion not yet supported by backend');

  // Uncomment when backend endpoint is ready:
  // await RoomsService.deleteRoom({ roomId });
}
```

**Option B: Skip delete functionality for now**
- Implement all other features (Tasks 3-7, 9)
- Skip Task 8 (DeleteRoomDialog)
- Add to Phase 3.3 or 4 when backend is ready

**Recommendation:** Use **Option A** (stub with error) so the hook interface is complete, and update Task 8 to note it's blocked on backend.

---

### Issue 3: Missing Success Toasts in Hook

**Location:** Task 2 mutations

**Current Plan:**
Mutations in useRoom don't show success toasts

**Actual Code Pattern:**
Looking at `AddUser.tsx`, success toasts are shown in components, not hooks.

**Question:**
Should the hook show toasts or should components?

**Analysis:**
- **Current pattern:** Components show toasts (see `AddUser.tsx` line 63)
- **Hooks:** Only show error toasts via `handleError()` (see `useRoom.ts` line 188, 201)

**Recommendation:**
Keep toasts in components for consistency. Update plan to show toasts in dialog components, not hooks.

---

## 📊 Comparison Matrix

| Plan Item | Actual Code | Status | Action |
|-----------|-------------|--------|--------|
| Task 1: Add user lookup | Utility functions exist, not called | ✅ Correct | Implement as planned |
| Task 2: updateRoom mutation | Missing from hook | ✅ Correct | Add to hook |
| Task 2: deleteRoom mutation | Missing from hook | ✅ Correct | Add to hook WITH callback pattern |
| Task 2: Navigation in hook | N/A | ⚠️ Issue | Change to callback pattern |
| Task 2: Backend delete endpoint | Doesn't exist | ✅ Correct | Stub with error message |
| Task 3: AddRoom component | Incomplete | ✅ Correct | Complete as planned |
| Task 4-9: Component creation | Components don't exist | ✅ Correct | Create as planned |
| Participant mutations | Already exist | ✅ Correct | No changes needed |
| Service layer | Complete | ✅ Correct | No changes needed |

---

## 🔧 Required Plan Updates

### Update 1: Task 2 - Step 3 (Delete Mutation)

**Replace:**
```typescript
3. **Add room delete mutation with navigation**
   ```typescript
   import { useNavigate } from '@tanstack/react-router';

   // Inside useRoom function:
   const navigate = useNavigate();

   // Delete room mutation
   const deleteRoomMutation = useMutation({
     mutationFn: async () => {
       throw new Error('Delete functionality not yet implemented in backend');
     },
     onSuccess: () => {
       navigate({ to: '/rooms' });
       queryClient.invalidateQueries({ queryKey: ['rooms'] });
     },
     onError: (err: ApiError) => {
       handleError(err);
     },
   });
```

**With:**

3. **Add room delete mutation (without navigation)**
   ```typescript

   ```


### Update 2: Task 2 - Step 1 (Interface)

**Add to UseRoomOptions:**
```typescript
export interface UseRoomOptions {
  enablePolling?: boolean;
  pollingInterval?: number;
  autoScrollToBottom?: boolean;
  onDeleteSuccess?: () => void;  // NEW: Callback after successful deletion
}
```

### Update 3: Task 2 - Step 6 (RoomService)

**Update the deleteRoom service method:**
```typescript
/**
 * Delete a room (owner-only)
 *
 * @param roomId - Room UUID
 * @returns Promise that resolves when deletion is complete
 * @throws Error if backend endpoint not implemented yet
 * @throws ApiError - 403 if not room owner, 404 if room not found
 */
async deleteRoom(roomId: string): Promise<void> {
  // TODO: Backend DELETE endpoint doesn't exist yet
  // Backend ticket: Add DELETE /api/v1/rooms/{room_id} endpoint
  // For now, throw error to prevent usage
  throw new Error(
    'Room deletion not yet supported. Backend endpoint needs to be created.'
  );

  // Uncomment when backend endpoint is ready:
  // await RoomsService.deleteRoom({ roomId });
}
```

### Update 4: Task 8 - Add Note

**Add to Task 8 Context:**
```markdown
#### Context
Room owners need ability to delete rooms with strong confirmation (destructive action).

**⚠️ BLOCKED:** This feature is currently blocked on backend implementation. The dialog
can be implemented and integrated, but the actual deletion will throw an error until
the backend DELETE endpoint is created.

**Backend Ticket Needed:**
- Add `DELETE /api/v1/rooms/{room_id}` endpoint
- Regenerate OpenAPI client
- Update RoomService.deleteRoom() to use the endpoint
```

### Update 5: Task 9 - Component Integration

**Update room route integration:**
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

---

## ✅ Recommendations

1. **Update Plan Document**
   - Apply Updates 1-5 above
   - Bump version to 1.2
   - Add "Navigation Pattern" to Appendix

2. **Implementation Order**
   - Proceed with Task 1 immediately (no blockers)
   - Implement Task 2 with updated navigation pattern
   - Task 2 completion enables all other tasks
   - Tasks 3-7, 9 can proceed in parallel
   - Task 8 (Delete) can be UI-complete but will error until backend ready

3. **Backend Coordination**
   - File backend ticket for DELETE endpoint
   - Clearly communicate this blocks Task 8 testing
   - When backend ready: Update RoomService, regenerate SDK, test

4. **Testing Strategy**
   - Tasks 1-7, 9: Fully testable with current backend
   - Task 8: Test dialog UI, but deletion will error (expected)
   - Add integration test for Task 8 once backend ready

---

## 📝 Conclusion

The implementation plan is **well-researched and accurate**. The two main issues are:

1. **Architectural:** Navigation should be in component, not hook (easy fix)
2. **Backend Dependency:** Delete endpoint doesn't exist (expected, plan accounts for it)

With the recommended updates, the plan will be production-ready and follow best practices.

**Next Steps:**
1. Apply updates to Phase3.2-Implementation-Plan.md
2. Begin implementation starting with Task 1
3. File backend ticket for DELETE endpoint
