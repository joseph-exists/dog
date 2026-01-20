Rooms UI Refactor - Completed Implementation

  What Was Built

  New Component Architecture (frontend/src/components/Room/)
  ┌──────────────────┬───────────────────────────────────────────────────────────┐
  │    Component     │                          Purpose                          │
  ├──────────────────┼───────────────────────────────────────────────────────────┤
  │ PanelContainer   │ Reusable header/content/footer container for panels       │
  ├──────────────────┼───────────────────────────────────────────────────────────┤
  │ ActionBar        │ Row of icon buttons with tooltips                         │
  ├──────────────────┼───────────────────────────────────────────────────────────┤
  │ ParticipantStack │ Overlapping avatars with popover list                     │
  ├──────────────────┼───────────────────────────────────────────────────────────┤
  │ ChatPanel        │ Wraps MessageList + MessageInput with search/copy actions │
  ├──────────────────┼───────────────────────────────────────────────────────────┤
  │ AgentPanel       │ Agent management with quick-add and party picker          │
  ├──────────────────┼───────────────────────────────────────────────────────────┤
  │ RoomLayout       │ Resizable panel groups + tab mode switching               │
  ├──────────────────┼───────────────────────────────────────────────────────────┤
  │ RoomHeader       │ Room title, participants, layout toggle, menu             │
  ├──────────────────┼───────────────────────────────────────────────────────────┤
  │ RoomShell        │ Main container composing header + layout                  │
  └──────────────────┴───────────────────────────────────────────────────────────┘
  New Route: /r/:roomId - Unified room view with multi-panel support

  ---

 Problems:

 1: Navigation:
 Expectation:
  - Sidebar shows "Rooms (Old)" link → Goes to /room-v2/:roomId for comparison
Actual: 404 page (add this as a toggle jump button on the r/:roomId that jumps to room-v2/:roomId - and then add one to room-v2/:roomId that jumps back.)

  - Resize handle between panels works (drag to resize)
Actual: doesn't work.  I think this has to do with our nested containers - our main container isn't responsive, it only takes up a smaller percentage of a large screen.  We can't test agent panels or most of the work because of this error.

  Chat Panel:

  - Message actions (edit, pin, delete) work for owner 
Actual: no

  Agent Debug panel:
  Not selectable - we need this to be available somewhere
