# Phase 5 Frontend Implementation Plan
## Message Management Features - UI Components

**Status:** Backend Complete ✅ | Core Hooks Complete ✅ | UI Components Pending 🔴

---

## Executive Summary

### What's Been Completed

#### ✅ Backend (100% Complete)
- Database schema with `edited_at`, `edited_by`, `is_pinned`, `pinned_at`, `pinned_by` fields
- Event-sourced architecture with 5 new event types
- API endpoints with authorization
- Redis pub/sub for real-time updates
- All CRUD operations tested

#### ✅ Frontend Core Infrastructure (100% Complete)
1. **`useRoomStream` hook** (`frontend/src/hooks/useRoomStream.ts`)
   - WebSocket connection to `/api/v1/ws/rooms/{room_id}`
   - Sequence tracking for reconnection
   - Token streaming for agent responses
   - **Phase 5 event handlers ALREADY IMPLEMENTED** (lines 122-131):
     - `message.edited`
     - `message.pinned`
     - `message.unpinned`
     - `message.context_toggled`
     - `message.deleted`

2. **`useRoomMessages` hook** (`frontend/src/hooks/useRoomMessages.ts`)
   - **All Phase 5 mutations ALREADY IMPLEMENTED** (lines 186-328):
     - `editMessage` mutation + wrapper
     - `pinMessage` mutation + wrapper
     - `unpinMessage` mutation + wrapper
     - `toggleContext` mutation + wrapper
     - `deleteMessage` mutation + wrapper

3. **`RoomService`** (`frontend/src/services/roomService.ts`)
   - **All Phase 5 service methods ALREADY IMPLEMENTED** (lines 478-603):
     - `editMessage()`
     - `pinMessage()`
     - `unpinMessage()`
     - `toggleMessageContext()`
     - `deleteMessage()`

### What Remains: UI Components Only

**Scope:** 8 frontend components following strict frontend rules

**Estimated Time:** 2-3 days

---

## Implementation Status Reconciliation

### ❌ Original Plan Issue: AG-UI Session Hook

The original `phase-5-full.md` document proposed creating:
- `useAGUISession.ts` - WebSocket hook connecting to `/ui/session`
- `useRoomEvents.ts` - Event handling hook

**✅ ACTUAL REALITY:**
- The backend implements `/ws/rooms/{room_id}` (NOT `/ui/session`)
- The frontend uses `useRoomStream.ts` (NOT `useAGUISession.ts`)
- Event handling is ALREADY in `useRoomStream.ts` (lines 122-131)
- This is **the correct implementation** - simpler and more RESTful

**Decision:** Original plan was based on outdated spec. Current implementation is superior.

---

## Remaining Work: UI Components Implementation

### Component Organization (Following FrontendRULES.md)

```
frontend/src/
├── components/
│   ├── ui/                          # Design system primitives
│   │   └── message-badge.tsx        # 🔴 NEW: Status badges
│   ├── Common/                      # Reusable app components
│   │   └── EditDrawer.tsx           # 🔴 NEW: Generic slide-out panel
│   └── Rooms/                       # Feature-specific components
│       ├── Message.tsx              # ⚠️ UPDATE: Add badges & menu
│       ├── MessageList.tsx          # ⚠️ UPDATE: Add filters & pinned section
│       ├── MessageActionMenu.tsx   # 🔴 NEW: Action dropdown
│       ├── MessageFilters.tsx      # 🔴 NEW: Filter controls
│       └── PinnedMessagesSection.tsx # 🔴 NEW: Pinned display
└── hooks/
    ├── useRoomMessages.ts           # ✅ COMPLETE (has mutations)
    ├── useRoomStream.ts             # ✅ COMPLETE (has event handlers)
    └── useRoomPermissions.ts        # 🔴 NEW: Permission checks
```

---

## Phase 1: UI Primitives & Permissions (Day 1)

### Task 1.1: Create `ui/message-badge.tsx` Component

**Location:** `frontend/src/components/ui/message-badge.tsx`

**Purpose:** Reusable design system component for message status indicators

**Requirements from FrontendRULES.md:**
- Use kebab-case filename ✓
- Export component (not default) ✓
- Extend Chakra UI components ✓
- Type-safe props ✓

**Implementation:**

```tsx
// frontend/src/components/ui/message-badge.tsx
import { Badge, Icon, type BadgeProps } from "@chakra-ui/react"
import { FaEdit, FaThumbtack, FaCheckCircle, FaCircle } from "react-icons/fa"
import { Tooltip } from "@/components/ui/tooltip"

export type MessageBadgeVariant =
  | "edited"
  | "pinned"
  | "active"
  | "inactive"

export interface MessageBadgeProps extends Omit<BadgeProps, "variant"> {
  variant: MessageBadgeVariant
  timestamp?: string
}

const badgeConfig: Record<
  MessageBadgeVariant,
  { icon: any; colorScheme: string; label: string }
> = {
  edited: {
    icon: FaEdit,
    colorScheme: "gray",
    label: "Edited"
  },
  pinned: {
    icon: FaThumbtack,
    colorScheme: "yellow",
    label: "Pinned"
  },
  active: {
    icon: FaCheckCircle,
    colorScheme: "green",
    label: "Active for Context"
  },
  inactive: {
    icon: FaCircle,
    colorScheme: "gray",
    label: "Inactive"
  },
}

export const MessageBadge = ({
  variant,
  timestamp,
  ...props
}: MessageBadgeProps) => {
  const config = badgeConfig[variant]
  const tooltipLabel = timestamp
    ? `${config.label} - ${timestamp}`
    : config.label

  return (
    <Tooltip content={tooltipLabel}>
      <Badge
        colorScheme={config.colorScheme}
        variant="subtle"
        display="inline-flex"
        alignItems="center"
        gap={1}
        fontSize="xs"
        px={2}
        py={0.5}
        borderRadius="full"
        {...props}
      >
        <Icon as={config.icon} boxSize={3} />
        {config.label}
      </Badge>
    </Tooltip>
  )
}
```

**Acceptance Criteria:**
- [ ] Component follows kebab-case naming
- [ ] Exports as named export (not default)
- [ ] Uses TypeScript with strict types
- [ ] Extends Chakra Badge component
- [ ] Supports 4 variants: edited, pinned, active, inactive
- [ ] Shows tooltips with timestamps
- [ ] Accessible (aria labels via tooltip)

---

### Task 1.2: Create `useRoomPermissions` Hook

**Location:** `frontend/src/hooks/useRoomPermissions.ts`

**Purpose:** Centralized permission checking logic

**Requirements from FrontendRULES.md:**
- Custom hooks in `src/hooks` ✓
- Extract complex logic from components ✓
- Type-safe interfaces ✓

**Implementation:**

```tsx
// frontend/src/hooks/useRoomPermissions.ts
import { useMemo } from "react"
import type { RoomViewModel } from "@/services/roomService"
import type { MessageViewModel } from "@/services/roomService"
import useAuth from "./useAuth"

export interface RoomPermissions {
  isOwner: boolean
  canEditMessage: (message: MessageViewModel) => boolean
  canDeleteMessage: () => boolean
  canPinMessage: () => boolean
  canToggleContext: () => boolean
}

/**
 * Hook for computing room-level permissions
 *
 * @param room - Current room data
 * @returns Permission flags and checker functions
 */
export function useRoomPermissions(
  room: RoomViewModel | null | undefined
): RoomPermissions {
  const { user } = useAuth()

  return useMemo(() => {
    const isOwner = room?.creator_id === user?.id

    return {
      isOwner,

      // User messages: author OR owner can edit
      // Agent messages: owner only
      canEditMessage: (message: MessageViewModel) => {
        if (!user) return false
        if (message.sender_type === "agent") {
          return isOwner
        }
        return message.sender_id === user.id || isOwner
      },

      // Only room owner can delete messages
      canDeleteMessage: () => isOwner,

      // Only room owner can pin messages
      canPinMessage: () => isOwner,

      // Any participant can toggle context
      canToggleContext: () => Boolean(user),
    }
  }, [room?.creator_id, user])
}
```

**Acceptance Criteria:**
- [ ] Hook follows naming convention (use* prefix)
- [ ] Memoizes permission checks for performance
- [ ] Handles null/undefined room gracefully
- [ ] Returns consistent permission interface
- [ ] Type-safe with explicit return type

---

## Phase 2: Action Components (Day 2)

### Task 2.1: Create `Rooms/MessageActionMenu.tsx` Component

**Location:** `frontend/src/components/Rooms/MessageActionMenu.tsx`

**Purpose:** Dropdown menu with message actions (edit, pin, delete, toggle context)

**Requirements from FrontendRULES.md:**
- Feature-specific component in `Rooms/` ✓
- PascalCase filename ✓
- Default export ✓
- Use Chakra UI components ✓

**Implementation:**

```tsx
// frontend/src/components/Rooms/MessageActionMenu.tsx
import { useState } from "react"
import {
  MenuRoot,
  MenuTrigger,
  MenuContent,
  MenuItem,
  IconButton,
} from "@chakra-ui/react"
import {
  FaEdit,
  FaThumbtack,
  FaTrash,
  FaEye,
  FaEyeSlash,
  FaEllipsisV
} from "react-icons/fa"
import type { MessageViewModel } from "@/services/roomService"
import { useRoomPermissions } from "@/hooks/useRoomPermissions"
import type { RoomViewModel } from "@/services/roomService"

interface MessageActionMenuProps {
  message: MessageViewModel
  room: RoomViewModel
  onEdit: () => void
  onPin: () => void
  onUnpin: () => void
  onToggleContext: (active: boolean) => void
  onDelete: () => void
  isPinned: boolean
  isActiveForContext: boolean
}

const MessageActionMenu = ({
  message,
  room,
  onEdit,
  onPin,
  onUnpin,
  onToggleContext,
  onDelete,
  isPinned,
  isActiveForContext,
}: MessageActionMenuProps) => {
  const permissions = useRoomPermissions(room)
  const [isOpen, setIsOpen] = useState(false)

  return (
    <MenuRoot open={isOpen} onOpenChange={({ open }) => setIsOpen(open)}>
      <MenuTrigger asChild>
        <IconButton
          aria-label="Message actions"
          icon={<FaEllipsisV />}
          variant="ghost"
          size="xs"
          opacity={0.6}
          _hover={{ opacity: 1 }}
        />
      </MenuTrigger>
      <MenuContent>
        {/* Edit action - author or owner for user messages, owner for agent */}
        {permissions.canEditMessage(message) && (
          <MenuItem value="edit" onClick={onEdit}>
            <FaEdit />
            Edit
          </MenuItem>
        )}

        {/* Pin/Unpin - owner only */}
        {permissions.canPinMessage() && (
          <MenuItem
            value={isPinned ? "unpin" : "pin"}
            onClick={isPinned ? onUnpin : onPin}
          >
            <FaThumbtack />
            {isPinned ? "Unpin" : "Pin"}
          </MenuItem>
        )}

        {/* Toggle context - any participant */}
        {permissions.canToggleContext() && (
          <MenuItem
            value="toggle-context"
            onClick={() => onToggleContext(!isActiveForContext)}
          >
            {isActiveForContext ? <FaEyeSlash /> : <FaEye />}
            {isActiveForContext
              ? "Remove from Context"
              : "Add to Context"}
          </MenuItem>
        )}

        {/* Delete - owner only */}
        {permissions.canDeleteMessage() && (
          <MenuItem
            value="delete"
            onClick={onDelete}
            color="red.600"
            _hover={{ bg: "red.50" }}
          >
            <FaTrash />
            Delete
          </MenuItem>
        )}
      </MenuContent>
    </MenuRoot>
  )
}

export default MessageActionMenu
```

**Acceptance Criteria:**
- [ ] Component in `Rooms/` directory
- [ ] Default export
- [ ] Shows only permitted actions
- [ ] Uses permission hook for authorization
- [ ] Chakra UI Menu components
- [ ] Icon for each action
- [ ] Delete action styled in red

---

### Task 2.2: Create `Common/EditDrawer.tsx` Component

**Location:** `frontend/src/components/Common/EditDrawer.tsx`

**Purpose:** Reusable slide-out panel for editing messages

**Requirements from FrontendRULES.md:**
- Reusable component in `Common/` ✓
- PascalCase filename ✓
- Default export ✓
- Use React Hook Form ✓

**Implementation:**

```tsx
// frontend/src/components/Common/EditDrawer.tsx
import { useEffect } from "react"
import { useForm } from "react-hook-form"
import {
  DrawerRoot,
  DrawerBackdrop,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerBody,
  DrawerFooter,
  DrawerCloseTrigger,
  Button,
  Textarea,
  VStack,
  Text,
} from "@chakra-ui/react"
import { Field } from "@/components/ui/field"

interface EditDrawerProps {
  isOpen: boolean
  onClose: () => void
  onSave: (content: string) => Promise<void>
  initialContent: string
  title?: string
  description?: string
  isSaving?: boolean
}

interface EditForm {
  content: string
}

const EditDrawer = ({
  isOpen,
  onClose,
  onSave,
  initialContent,
  title = "Edit Message",
  description,
  isSaving = false,
}: EditDrawerProps) => {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty, isValid },
  } = useForm<EditForm>({
    mode: "onChange",
    defaultValues: {
      content: initialContent,
    },
  })

  // Reset form when drawer opens with new content
  useEffect(() => {
    if (isOpen) {
      reset({ content: initialContent })
    }
  }, [isOpen, initialContent, reset])

  const onSubmit = async (data: EditForm) => {
    await onSave(data.content)
    onClose()
  }

  return (
    <DrawerRoot open={isOpen} onOpenChange={({ open }) => !open && onClose()} size="md" placement="right">
      <DrawerBackdrop />
      <DrawerContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DrawerHeader>
            <DrawerTitle>{title}</DrawerTitle>
          </DrawerHeader>
          <DrawerCloseTrigger />

          <DrawerBody>
            <VStack gap={4} align="stretch">
              {description && (
                <Text fontSize="sm" color="gray.600">
                  {description}
                </Text>
              )}

              <Field
                label="Message Content"
                required
                invalid={!!errors.content}
                errorText={errors.content?.message}
              >
                <Textarea
                  {...register("content", {
                    required: "Message content is required",
                    minLength: {
                      value: 1,
                      message: "Message cannot be empty",
                    },
                  })}
                  rows={10}
                  placeholder="Edit message content..."
                />
              </Field>
            </VStack>
          </DrawerBody>

          <DrawerFooter gap={2}>
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              colorScheme="blue"
              loading={isSaving}
              disabled={!isDirty || !isValid}
            >
              Save Changes
            </Button>
          </DrawerFooter>
        </form>
      </DrawerContent>
    </DrawerRoot>
  )
}

export default EditDrawer
```

**Acceptance Criteria:**
- [ ] Component in `Common/` directory
- [ ] Default export
- [ ] Uses React Hook Form
- [ ] Validates required field
- [ ] Disables save if unchanged or invalid
- [ ] Shows loading state while saving
- [ ] Resets form on open
- [ ] Closes on successful save

---

## Phase 3: Display Components (Day 3)

### Task 3.1: Create `Rooms/MessageFilters.tsx` Component

**Location:** `frontend/src/components/Rooms/MessageFilters.tsx`

**Purpose:** Filter controls for messages (active/inactive, pinned, sender type)

**Implementation:**

```tsx
// frontend/src/components/Rooms/MessageFilters.tsx
import {
  HStack,
  Select,
  IconButton,
  Text,
} from "@chakra-ui/react"
import { FaTimes } from "react-icons/fa"

interface MessageFilters {
  activeForContext: boolean | null  // null = all, true = active, false = inactive
  isPinned: boolean | null          // null = all, true = pinned only
  senderType: "all" | "user" | "agent"
}

interface MessageFiltersProps {
  filters: MessageFilters
  onFilterChange: <K extends keyof MessageFilters>(
    key: K,
    value: MessageFilters[K]
  ) => void
  onClearFilters: () => void
}

const MessageFilters = ({
  filters,
  onFilterChange,
  onClearFilters,
}: MessageFiltersProps) => {
  return (
    <HStack gap={4} p={4} bg="gray.50" borderRadius="md" flexWrap="wrap">
      <Text fontWeight="medium" fontSize="sm">
        Filters:
      </Text>

      {/* Active/Inactive Filter */}
      <Select
        size="sm"
        maxW="200px"
        value={
          filters.activeForContext === null
            ? "all"
            : filters.activeForContext.toString()
        }
        onChange={(e) => {
          const val = e.target.value
          onFilterChange(
            "activeForContext",
            val === "all" ? null : val === "true"
          )
        }}
      >
        <option value="all">All Messages</option>
        <option value="true">Active for Context</option>
        <option value="false">Inactive for Context</option>
      </Select>

      {/* Pinned Filter */}
      <Select
        size="sm"
        maxW="180px"
        value={
          filters.isPinned === null ? "all" : filters.isPinned.toString()
        }
        onChange={(e) => {
          const val = e.target.value
          onFilterChange("isPinned", val === "all" ? null : val === "true")
        }}
      >
        <option value="all">All / Pinned</option>
        <option value="true">Pinned Only</option>
        <option value="false">Unpinned Only</option>
      </Select>

      {/* Sender Type Filter */}
      <Select
        size="sm"
        maxW="150px"
        value={filters.senderType}
        onChange={(e) =>
          onFilterChange("senderType", e.target.value as any)
        }
      >
        <option value="all">All Senders</option>
        <option value="user">Users Only</option>
        <option value="agent">Agents Only</option>
      </Select>

      {/* Clear Filters Button */}
      <IconButton
        size="sm"
        aria-label="Clear filters"
        onClick={onClearFilters}
        variant="ghost"
      >
        <FaTimes />
      </IconButton>
    </HStack>
  )
}

export default MessageFilters
```

**Acceptance Criteria:**
- [ ] Component in `Rooms/` directory
- [ ] Default export
- [ ] Three filter controls (active, pinned, sender type)
- [ ] Clear filters button
- [ ] Responsive layout with flexWrap
- [ ] Chakra UI Select components
- [ ] Type-safe filter interface

---

### Task 3.2: Create `Rooms/PinnedMessagesSection.tsx` Component

**Location:** `frontend/src/components/Rooms/PinnedMessagesSection.tsx`

**Purpose:** Dedicated section showing pinned messages at top of list

**Implementation:**

```tsx
// frontend/src/components/Rooms/PinnedMessagesSection.tsx
import { Box, HStack, Icon, Text, VStack } from "@chakra-ui/react"
import { FaThumbtack } from "react-icons/fa"
import Message from "./Message"
import type { MessageViewModel } from "@/services/roomService"

interface PinnedMessagesSectionProps {
  messages: MessageViewModel[]
  roomId: string
}

const PinnedMessagesSection = ({
  messages,
  roomId,
}: PinnedMessagesSectionProps) => {
  if (messages.length === 0) return null

  return (
    <Box
      bg="yellow.50"
      borderLeft="4px solid"
      borderColor="yellow.400"
      p={4}
      borderRadius="md"
      _dark={{
        bg: "yellow.900",
        borderColor: "yellow.600",
      }}
    >
      <HStack mb={3}>
        <Icon as={FaThumbtack} color="yellow.600" />
        <Text fontWeight="bold" color="yellow.800" _dark={{ color: "yellow.200" }}>
          Pinned Messages ({messages.length})
        </Text>
      </HStack>

      <VStack align="stretch" gap={2}>
        {messages.map((message) => (
          <Message key={message.message_id} message={message} />
        ))}
      </VStack>
    </Box>
  )
}

export default PinnedMessagesSection
```

**Acceptance Criteria:**
- [ ] Component in `Rooms/` directory
- [ ] Default export
- [ ] Shows count of pinned messages
- [ ] Yellow theme for visual distinction
- [ ] Dark mode support
- [ ] Returns null if no pinned messages
- [ ] Reuses Message component

---

### Task 3.3: Update `Rooms/Message.tsx` Component

**Purpose:** Add badges and action menu to existing Message component

**Changes Required:**

```tsx
// frontend/src/components/Rooms/Message.tsx
// Add new imports:
import { HStack } from "@chakra-ui/react"
import { MessageBadge } from "@/components/ui/message-badge"
import MessageActionMenu from "./MessageActionMenu"
import type { RoomViewModel } from "@/services/roomService"

// Update interface:
interface MessageProps {
  message: MessageViewModel
  isStreaming?: boolean
  room?: RoomViewModel  // For permissions
  // Phase 5: Message management props
  isPinned?: boolean
  isActiveForContext?: boolean
  editedAt?: string | null
  onEdit?: () => void
  onPin?: () => void
  onUnpin?: () => void
  onToggleContext?: (active: boolean) => void
  onDelete?: () => void
}

// Add badges section after sender name, before content:
{/* Phase 5: Status badges */}
{editedAt && (
  <MessageBadge variant="edited" timestamp={editedAt} />
)}
{isPinned && (
  <MessageBadge variant="pinned" />
)}
{isActiveForContext !== undefined && (
  <MessageBadge
    variant={isActiveForContext ? "active" : "inactive"}
  />
)}

// Add action menu at top-right:
{room && onEdit && (
  <Box position="absolute" top={2} right={2}>
    <MessageActionMenu
      message={message}
      room={room}
      onEdit={onEdit}
      onPin={onPin}
      onUnpin={onUnpin}
      onToggleContext={onToggleContext}
      onDelete={onDelete}
      isPinned={isPinned || false}
      isActiveForContext={isActiveForContext || false}
    />
  </Box>
)}
```

**Acceptance Criteria:**
- [ ] Shows edited badge when message was edited
- [ ] Shows pinned badge when message is pinned
- [ ] Shows active/inactive context badge
- [ ] Action menu appears on hover (top-right)
- [ ] Action menu only shows if callbacks provided
- [ ] Maintains existing streaming functionality
- [ ] Maintains existing styling

---

### Task 3.4: Update `Rooms/MessageList.tsx` Component

**Purpose:** Add filters and pinned messages section

**Changes Required:**

```tsx
// frontend/src/components/Rooms/MessageList.tsx
// Add new imports:
import MessageFilters from "./MessageFilters"
import PinnedMessagesSection from "./PinnedMessagesSection"
import { useState, useCallback } from "react"

// Add filter state:
const [filters, setFilters] = useState<MessageFilters>({
  activeForContext: null,
  isPinned: null,
  senderType: "all",
})

const updateFilter = useCallback(<K extends keyof MessageFilters>(
  key: K,
  value: MessageFilters[K]
) => {
  setFilters(prev => ({ ...prev, [key]: value }))
}, [])

const clearFilters = useCallback(() => {
  setFilters({
    activeForContext: null,
    isPinned: null,
    senderType: "all",
  })
}, [])

// Filter messages:
const filteredMessages = messages.filter(msg => {
  // Apply active/inactive filter
  if (filters.activeForContext !== null) {
    // Note: active_for_context comes from backend
    if (msg.active_for_context !== filters.activeForContext) {
      return false
    }
  }

  // Apply pinned filter
  if (filters.isPinned !== null) {
    // Note: is_pinned comes from backend
    if (msg.is_pinned !== filters.isPinned) {
      return false
    }
  }

  // Apply sender type filter
  if (filters.senderType !== "all") {
    if (msg.sender_type !== filters.senderType) {
      return false
    }
  }

  return true
})

const pinnedMessages = filteredMessages.filter(m => m.is_pinned)

// Add before message list:
<MessageFilters
  filters={filters}
  onFilterChange={updateFilter}
  onClearFilters={clearFilters}
/>

<PinnedMessagesSection messages={pinnedMessages} roomId={roomId} />
```

**Acceptance Criteria:**
- [ ] Shows filter controls at top
- [ ] Shows pinned messages section
- [ ] Filters work client-side (no API calls)
- [ ] Clear filters button resets all
- [ ] Maintains existing pagination
- [ ] Maintains existing streaming display

---

## Phase 4: Integration & Testing

### Task 4.1: Wire Up Components in Room View

**File:** Route component that uses MessageList (likely `frontend/src/routes/rooms.$roomId.tsx`)

**Changes:**
1. Import EditDrawer
2. Add state for edit drawer (isOpen, editingMessage)
3. Pass message management callbacks to MessageList
4. Handle edit/pin/delete mutations using useRoomMessages hook
5. Show confirmation dialogs for destructive actions

**Acceptance Criteria:**
- [ ] Edit drawer opens when edit action clicked
- [ ] Pin/unpin updates message immediately (optimistic)
- [ ] Delete shows confirmation before executing
- [ ] Toggle context updates message immediately
- [ ] WebSocket updates reflected in real-time
- [ ] Loading states shown during mutations
- [ ] Error toasts on mutation failures

---

### Task 4.2: Type Definitions

**Update `MessageViewModel` interface** to include Phase 5 fields:

```tsx
// frontend/src/services/roomService.ts
export interface MessageViewModel {
  message_id: string
  room_id: string
  sender_type: "user" | "agent"
  sender_name: string
  sender_id: string | null
  agent_name: string | null
  content: string
  button_options?: Record<string, unknown> | null
  created_at: Date
  is_own_message: boolean

  // Phase 5: Message management fields
  edited_at?: string | null
  edited_by?: string | null
  is_pinned: boolean
  pinned_at?: string | null
  pinned_by?: string | null
  active_for_context: boolean
}
```

**Acceptance Criteria:**
- [ ] Interface includes all Phase 5 fields
- [ ] Transform function handles new fields
- [ ] Dates parsed correctly
- [ ] Null/undefined handled gracefully

---

## Testing Checklist

### Component Tests
- [ ] MessageBadge renders all 4 variants
- [ ] MessageBadge shows tooltips
- [ ] MessageActionMenu shows only permitted actions
- [ ] MessageActionMenu calls correct callbacks
- [ ] EditDrawer validates required field
- [ ] EditDrawer disables save when unchanged
- [ ] MessageFilters updates filter state
- [ ] PinnedMessagesSection shows correct count
- [ ] useRoomPermissions returns correct permissions

### Integration Tests
- [ ] Edit workflow: open drawer → edit → save → see update
- [ ] Pin workflow: click pin → message moves to pinned section
- [ ] Delete workflow: click delete → confirm → message removed
- [ ] Toggle context: click toggle → badge updates
- [ ] Filters: change filter → message list updates
- [ ] WebSocket: edit on another client → see real-time update

### Permission Tests
- [ ] Non-owner cannot delete messages
- [ ] Non-owner cannot pin messages
- [ ] Author can edit own messages
- [ ] Owner can edit any message
- [ ] Owner can edit agent messages
- [ ] Non-author cannot edit user messages

### Edge Cases
- [ ] Empty message list shows empty state
- [ ] No pinned messages hides pinned section
- [ ] Editing message preserves active_for_context
- [ ] Pinning message auto-sets active_for_context
- [ ] Deleting message removes from cache
- [ ] WebSocket disconnect → reconnect → catch up events

---

## Completion Criteria

Phase 5 frontend is considered complete when:

1. ✅ All 8 components implemented and tested
2. ✅ All components follow FrontendRULES.md patterns
3. ✅ TypeScript with strict types (no `any`)
4. ✅ Chakra UI components used consistently
5. ✅ React Query for mutations
6. ✅ Error handling with useCustomToast
7. ✅ Permission checks via useRoomPermissions
8. ✅ WebSocket real-time updates working
9. ✅ Client-side filtering working
10. ✅ All manual tests passing

---

## Notes

### Why This Plan Differs from phase-5-full.md

1. **No useAGUISession hook** - Already have useRoomStream which is better
2. **No useRoomEvents hook** - Event handling already in useRoomStream
3. **No server-side filtering** - Implementing client-side (simpler, already have all messages)
4. **No debouncing needed** - Client-side filtering is instant
5. **Fewer components** - Consolidated where possible
6. **Stricter rules adherence** - Following FrontendRULES.md explicitly

### Development Order

Day 1: UI primitives (message-badge, permissions hook)
Day 2: Action components (menu, edit drawer)
Day 3: Display components (filters, pinned section, update Message/MessageList)

### Key Architectural Decisions

- **Client-side filtering** - Already fetch all messages, filter in component
- **Permissions hook** - Centralize auth logic, reusable across components
- **UI primitive badge** - Reusable across app, not just messages
- **Common EditDrawer** - Generic, could edit other entities later
- **Feature-specific components** - MessageActionMenu, MessageFilters in Rooms/

---

## Ready to Implement

This plan provides:
- ✅ Clear component hierarchy following FrontendRULES.md
- ✅ Exact file locations and names
- ✅ Full TypeScript implementations
- ✅ Acceptance criteria for each component
- ✅ Integration testing checklist
- ✅ Reconciliation with actual codebase state

**Next Step:** Begin with Phase 1, Task 1.1 - Create `ui/message-badge.tsx`
