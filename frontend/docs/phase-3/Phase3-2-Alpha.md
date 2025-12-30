  Phase 3.2 Implementation Plan

  Foundation (Tasks 1)

  1. Review existing implementation - Understand current Room components, hooks, and services to ensure we build on existing patterns




  Room Creation (Tasks 2-3)

  2. CreateRoomDialog component - Modal form for creating new rooms (follows Dialog pattern from ComponentDevelopmentWalkthrough.md)
  3. Room creation mutation - Add to useRoom hook with TanStack Query, cache invalidation, and optimistic updates


  Participant Management (Tasks 4-6)

  4. AddParticipantDialog component - Modal for adding users/agents with dropdown/search UI
  5. Participant mutations - Add/remove operations in useRoom hook with proper authorization checks
  6. RemoveParticipantButton component - Inline action button with owner permission validation

  Agent Management (Task 7)

  7. AgentToggle component - Toggle switch for activating/deactivating agents in participant list

  Room Metadata (Tasks 8-9)

  8. EditRoomDialog component - Modal form for editing room title and settings
  9. Room update mutation - Add to useRoom hook with cache invalidation

  Room Lifecycle (Tasks 10-11)

  10. DeleteRoomDialog component - Confirmation modal with warning message
  11. Room delete mutation - Add to useRoom hook with navigation to room list after deletion

  Message Enhancement (Task 12)

  12. Update MessageList - Display sender names (usernames for users, agent names for agents) with each message

  UI Integration (Tasks 13-15)

  13. RoomActionsMenu component - Dropdown menu consolidating edit/delete/archive actions (likely in Common/ since it's a pattern)
  14. Integrate into room view - Wire all components into the existing room route
  15. Testing - Verify all CRUD operations, error handling, loading states, and authorization

  Key Alignment Notes

  - Component placement: Dialogs and room-specific components go in src/components/Rooms/, reusable action menu goes in src/components/Common/
  - State management: All mutations use TanStack Query via useRoom hook, following existing patterns
  - Forms: React Hook Form with Chakra UI Field components and validation
  - API integration: Use existing RoomService adapter (already scaffolded per technical spec)
  - Error handling: useCustomToast for notifications, handleError for API errors
  - Authorization: Check currentUserRole from useRoom hook before rendering owner-only actions