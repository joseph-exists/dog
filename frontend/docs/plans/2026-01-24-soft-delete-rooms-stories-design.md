# Soft-Delete for Rooms & Stories

## Problem

Deleting a story or room via the UI causes `IntegrityError: ForeignKeyViolation` because:
- `rooms.story_id` references `story.id` without `ondelete` behavior
- No `DELETE /rooms/{room_id}` endpoint exists at all

## Solution: Soft-Delete

Add `deleted_at: datetime | None` to both models. NULL = active, timestamp = deleted.

## Backend Changes

### 1. Model Changes (`models.py`)
- Add `deleted_at` to `Story` and `Room` models
- No changes to Public response models (deleted items won't be returned)

### 2. Migration
- Single migration adding `deleted_at` column to `story` and `rooms` tables

### 3. Story Delete (`crud.py`)
- Change `delete_story` from `session.delete()` to `story.deleted_at = utcnow()`
- Nullify `story_id` on any rooms referencing this story (detach, don't cascade-delete)

### 4. Room Delete (new endpoint in `rooms.py`)
- `DELETE /rooms/{room_id}` — sets `deleted_at`, owner-only
- Child entities (messages, events, participants) stay in DB but are unreachable

### 5. Query Filters
- `read_stories` list: add `.where(Story.deleted_at == None)`
- `read_story` single: return 404 if `deleted_at` is set
- `list_rooms_for_user`: add `.where(Room.deleted_at == None)`
- `get_room_for_user`: return 404 if `deleted_at` is set

## Frontend Changes

### 1. `roomService.ts`
- Uncomment `deleteRoom` call, remove thrown error

### 2. `RoomsActionsMenu.tsx`
- Re-enable the delete menu item

## Implementation Order

1. Add `deleted_at` to models
2. Create Alembic migration (user runs)
3. Update `delete_story` in crud.py
4. Add `DELETE /rooms/{room_id}` endpoint
5. Add query filters to story/room list and get operations
6. Frontend: enable room delete
7. Regenerate client (user runs)
8. Verify build
