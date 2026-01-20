# Rooms UI Refactor Design

> **For Claude:** This is a design document. Use superpowers:writing-plans to create an implementation plan from this design.

**Goal:** Create a flexible, multi-panel room system that supports preset room types, composable layouts, responsive behavior, and entity cards for drill-down exploration.

**Date:** 2026-01-19

---

## 1. Room Architecture Overview

### Core Concept: Room as Multi-Panel Container

A Room is a collaborative space containing **multiple panels** of varying prominence. Panels are classified by their visual weight, but any number can be active simultaneously.

```
┌─────────────────────────────────────────────────────────────┐
│ RoomShell                                                   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ RoomHeader                                              │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ RoomLayout                                              │ │
│ │ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────┐ │ │
│ │ │ Primary: Chat   │ │ Primary: Story  │ │ Aux: Agents │ │ │
│ │ │                 │ │ Editor          │ │             │ │ │
│ │ │                 │ │                 │ ├─────────────┤ │ │
│ │ │                 │ │                 │ │ Aux: Debug  │ │ │
│ │ └─────────────────┘ └─────────────────┘ └─────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Panel Classification

- **Primary panels** - Large, equal share of main viewport (e.g., 50/50 split)
- **Auxiliary panels** - Smaller, can stack vertically in a sidebar column

Multiple primary panels can be active simultaneously (e.g., Chat + StoryEditor).
Multiple auxiliary panels can be active simultaneously (stacked).

### Room Objects

| Object | Type | Purpose |
|--------|------|---------|
| Chat stream | Primary | Messages + input (base element) |
| Story Editor | Primary | Collaborative story authoring |
| Canvas | Primary | Future agent/user interaction space |
| A2UI container | Primary | AGUI agent tool call rendering |
| Agent Panel | Auxiliary | Managing room agents |
| Debug Panel | Auxiliary | Agent debugging |
| Doc Viewer | Auxiliary | Read-only artifact display |
| Agent Editor | Auxiliary | Editing agent configuration |

---

## 2. Visual Primitives

Atomic building blocks that compose all room objects.

### Identity Primitives

| Primitive | Description | Used In |
|-----------|-------------|---------|
| `Avatar` | Circular image/initials with optional status dot | Messages, participant lists, headers |
| `StatusBadge` | Small pill with label (role, state, count) | Headers, list items, messages |
| `ParticipantChip` | Avatar + name, compact inline display | Room header, mentions |

### Content Primitives

| Primitive | Description | Used In |
|-----------|-------------|---------|
| `MessageBubble` | Sender, content, timestamp, badges, actions | Chat stream |
| `ListItem` | Icon + label + metadata + optional actions | Agent lists, file lists, room cards |
| `PanelContainer` | Header bar + scrollable content + optional footer | All panels |

### Action Primitives

| Primitive | Description | Used In |
|-----------|-------------|---------|
| `ActionBar` | Horizontal row of icon buttons | Panel headers, message input |
| `CopyButton` | One-click copy with toast feedback | Messages, code blocks, docs |
| `SaveButton` | Export/download action | Documents, canvas |
| `SearchInput` | Filter input with clear button | Any list-based panel |
| `FileSelector` | Trigger for file picker dialog | Message input, canvas |

### Layout Primitives

| Primitive | Description | Used In |
|-----------|-------------|---------|
| `ResizablePanel` | Draggable edge for resizing | Between any panels |
| `TabBar` | Switchable tab headers | Mobile view, tab toggle mode |
| `CollapsibleSection` | Expandable content area | Auxiliary panel stacking |

---

## 3. Panel Compositions

Every panel follows the same `PanelContainer` structure (header/content/footer).

### ChatPanel (Primary)

```
┌─────────────────────────────────────────┐
│ PanelContainer                          │
│ ┌─────────────────────────────────────┐ │
│ │ Header: SearchInput + ActionBar     │ │
│ │         (filter, copy all, export)  │ │
│ ├─────────────────────────────────────┤ │
│ │ Content: MessageBubble[]            │ │
│ │          (scrollable, load more)    │ │
│ ├─────────────────────────────────────┤ │
│ │ Footer: MessageInput                │ │
│ │         (textarea + FileSelector +  │ │
│ │          ActionBar)                 │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### StoryEditorPanel (Primary)

```
┌─────────────────────────────────────────┐
│ PanelContainer                          │
│ ┌─────────────────────────────────────┐ │
│ │ Header: Title + StatusBadge +       │ │
│ │         ActionBar (save, export)    │ │
│ ├─────────────────────────────────────┤ │
│ │ Content: StoryEditor component      │ │
│ │          (existing component)       │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### AgentPanel (Auxiliary)

```
┌─────────────────────────┐
│ PanelContainer          │
│ ┌─────────────────────┐ │
│ │ Header: "Agents" +  │ │
│ │   ActionBar (add)   │ │
│ ├─────────────────────┤ │
│ │ Content:            │ │
│ │   ListItem[] with   │ │
│ │   Avatar + badges   │ │
│ └─────────────────────┘ │
└─────────────────────────┘
```

### CanvasPanel / A2UIPanel (Primary - Future)

```
┌─────────────────────────────────────────┐
│ PanelContainer                          │
│ ┌─────────────────────────────────────┐ │
│ │ Header: Title + ActionBar           │ │
│ ├─────────────────────────────────────┤ │
│ │ Content: Canvas/A2UI renderer       │ │
│ │          (future implementation)    │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

## 4. Entity Cards

Any element with associated data can trigger a **Card** - a popover showing expanded details and actions.

### Card Structure

```
┌─────────────────────────────────────┐
│ EntityCard                          │
│ ┌─────────────────────────────────┐ │
│ │ Header: Avatar + Name + Status  │ │
│ ├─────────────────────────────────┤ │
│ │ Content: Entity-specific info   │ │
│ │  - Agent: model, description,   │ │
│ │           participation mode    │ │
│ │  - User: role, joined date      │ │
│ │  - Doc: preview, metadata       │ │
│ ├─────────────────────────────────┤ │
│ │ Footer: ActionBar               │ │
│ │  (edit, remove, view full, etc) │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Card Types

| Card | Triggered From | Shows |
|------|----------------|-------|
| `AgentCard` | Agent avatar, mentions, list items | Config, status, quick actions |
| `UserCard` | User avatar, mentions | Profile, role, presence |
| `DocCard` | File references, doc viewer items | Preview, metadata, open/download |
| `MessageCard` | (future) Pinned/referenced messages | Full message with context |

---

## 5. Responsive Layout & Panel/Tab Toggle

### Desktop Layout (≥1024px)

Primary panels split horizontally with resizable dividers. Auxiliary panels stack in a collapsible right column.

```
┌────────────────────────────────────────────────────────────────┐
│ RoomHeader                                                     │
├───────────────────────┬───────────────────────┬───────────────┤
│                       │                       │ AgentPanel    │
│   ChatPanel           │   StoryEditorPanel    ├───────────────┤
│   (primary)           │   (primary)           │ DebugPanel    │
│                       │                       │ (collapsed)   │
│                    ←→ │                    ←→ │            ←→ │
└───────────────────────┴───────────────────────┴───────────────┘
        ←→ = ResizablePanel drag handles
```

### Tablet Layout (768px - 1023px)

Auxiliary column becomes a collapsible drawer (slide-in from right).

```
┌────────────────────────────────────────────┐ ┌─────────────┐
│ RoomHeader                           [☰]   │ │ Drawer      │
├────────────────────┬───────────────────────┤ │ AgentPanel  │
│                    │                       │ │ DebugPanel  │
│   ChatPanel        │   StoryEditorPanel    │→│             │
│                    │                       │ │             │
└────────────────────┴───────────────────────┘ └─────────────┘
```

### Mobile Layout (<768px)

All panels become tabs. Only one visible at a time.

```
┌─────────────────────────────────┐
│ RoomHeader                      │
├─────────────────────────────────┤
│ [Chat] [Story] [Agents] [Debug] │  ← TabBar
├─────────────────────────────────┤
│                                 │
│   Active Panel Content          │
│   (full width, full height)     │
│                                 │
└─────────────────────────────────┘
```

### Panel/Tab Toggle (Desktop)

User can switch between spatial layout and tabbed view via toggle button in RoomHeader:

```
[ ⊞ Panels | ▦ Tabs ]   ← ToggleGroup in header
```

- **Panels mode:** Side-by-side with resize (default)
- **Tabs mode:** Full-width tabs, one active at a time

State (scroll position, form data) preserved when toggling.

---

## 6. RoomHeader Design

Consistent across all room types.

### Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ┌──────────────────────────────────┐  ┌──────────────────────────────┐ │
│ │ Left: Identity                   │  │ Right: Actions               │ │
│ │                                  │  │                              │ │
│ │ [Icon] Room Title                │  │ [Participants] [⊞/▦] [⋮]    │ │
│ │        StatusBadge (type/mode)   │  │                              │ │
│ └──────────────────────────────────┘  └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### Left Section - Room Identity

- Room type icon (chat bubble, book, grid, etc.)
- Room title (editable inline for owners)
- StatusBadge showing room type or connection status

### Right Section - Actions

| Element | Description |
|---------|-------------|
| `ParticipantStack` | Overlapping avatars (max 4) + "+N" overflow, clickable to open participant list |
| `LayoutToggle` | Switch between Panels/Tabs mode (desktop only) |
| `RoomMenu` (⋮) | Dropdown: Add panel, Room settings, Copy link, Delete room |

### ParticipantStack Popover

```
┌───────────────────────────────────────────┐
│ Participants (7)                    [?]   │  ← [?] toggles legend
├───────────────────────────────────────────┤
│ Legend:                                   │
│ 👑 Orchestrator  🖼️ Image  🔧 Tools       │
│ 📝 Memory        🌐 Web    🔍 Search      │
├───────────────────────────────────────────┤
│ 👤 Alice         👑           (owner)     │
│ 👤 Bob                                    │
│ 🤖 Claude        👑 📝 🔧                 │
│ 🤖 Summarizer       📝                    │
│ 🤖 ImageGen      🖼️ 🔧                    │
│ 🤖 Researcher    🌐 🔍                    │
│ 🤖 Coder            🔧                    │
└───────────────────────────────────────────┘
```

### Participant Row Structure

```
┌─────────────────────────────────────────────────┐
│ [Avatar] [Name]     [Badges...]    [RoleBadge]  │
│  🤖      Claude     👑 📝 🔧       (active)     │
└─────────────────────────────────────────────────┘
```

### Capability Badges

| Badge | Meaning |
|-------|---------|
| 👑 | Orchestrator (can direct other agents) |
| 🖼️ | Image generation/processing |
| 🔧 | Tool use enabled |
| 📝 | Memory/context persistence |
| 🌐 | Web access |
| 🔍 | Search capability |
| ⚡ | Streaming responses |

Badges come from agent configuration (backend provides capability list).

---

## 7. Room Presets & Configuration

### Room Configuration Schema

```typescript
interface RoomConfig {
  type: 'chat' | 'story' | 'workspace'
  panels: {
    id: string
    kind: 'chat' | 'storyEditor' | 'canvas' | 'a2ui' | 'agentPanel' | 'debug' | 'docViewer' | 'agentEditor'
    prominence: 'primary' | 'auxiliary'
  }[]
}
```

### Chat Room (Default)

```typescript
{
  type: 'chat',
  panels: [
    { id: 'chat', kind: 'chat', prominence: 'primary' },
    { id: 'agents', kind: 'agentPanel', prominence: 'auxiliary' },
  ]
}
```

```
┌────────────────────────────────┬────────────┐
│                                │   Agents   │
│          ChatPanel             │            │
│                                │            │
└────────────────────────────────┴────────────┘
```

### Story Room

```typescript
{
  type: 'story',
  panels: [
    { id: 'story', kind: 'storyEditor', prominence: 'primary' },
    { id: 'chat', kind: 'chat', prominence: 'primary' },
    { id: 'agents', kind: 'agentPanel', prominence: 'auxiliary' },
  ]
}
```

```
┌──────────────────┬──────────────────┬────────────┐
│                  │                  │   Agents   │
│   StoryEditor    │    ChatPanel     │            │
│                  │                  │            │
└──────────────────┴──────────────────┴────────────┘
```

### Workspace (Composable)

```typescript
{
  type: 'workspace',
  panels: [] // User adds panels via RoomMenu → "Add Panel"
}
```

### Add Panel Flow

```
RoomMenu (⋮) → "Add Panel" →
┌─────────────────────────────┐
│ Add Panel                   │
├─────────────────────────────┤
│ Primary:                    │
│   ○ Chat                    │
│   ○ Story Editor            │
│   ○ Canvas                  │
│   ○ A2UI Container          │
├─────────────────────────────┤
│ Auxiliary:                  │
│   ○ Agent Panel             │
│   ○ Debug Panel             │
│   ○ Document Viewer         │
│   ○ Agent Editor            │
├─────────────────────────────┤
│         [Cancel] [Add]      │
└─────────────────────────────┘
```

### Persistence

- Panel configuration saved per-room in backend
- Layout preferences (sizes, collapsed state) saved in localStorage

---

## 8. Migration Path & File Organization

### New Route Structure

```
frontend/src/routes/_layout/
├── rooms.tsx                    # Room list (keep, minimal changes)
├── room.$roomId.tsx             # V1 - DEPRECATE (keep for testing)
├── room-v2.$roomId.tsx          # V2 - DEPRECATE (keep for testing)
└── r.$roomId.tsx                # NEW unified room route
```

**Why `r.$roomId`?**
- Short, clean URL: `/r/abc-123`
- Distinct from deprecated routes during transition
- Can rename to `room.$roomId` after V1/V2 removal

### Sidebar Navigation (During Transition)

```
├── Dashboard
├── Stories
├── Rooms          ← Links to new /r/ routes
├── Rooms (V2)     ← Temporary link to /room-v2/ for comparison
├── Agents
└── ...
```

### New Component Organization

```
frontend/src/components/
├── Room/                        # NEW - unified room system
│   ├── RoomShell.tsx           # Outer container, room-level state
│   ├── RoomHeader.tsx          # Header with participants, actions
│   ├── RoomLayout.tsx          # Panel arrangement, responsive logic
│   ├── panels/
│   │   ├── ChatPanel.tsx       # Chat stream + input
│   │   ├── StoryEditorPanel.tsx
│   │   ├── CanvasPanel.tsx     # Placeholder for future
│   │   ├── A2UIPanel.tsx       # Placeholder for future
│   │   ├── AgentPanel.tsx
│   │   ├── DebugPanel.tsx
│   │   ├── DocViewerPanel.tsx
│   │   └── AgentEditorPanel.tsx
│   ├── cards/
│   │   ├── AgentCard.tsx
│   │   ├── UserCard.tsx
│   │   └── DocCard.tsx
│   ├── primitives/
│   │   ├── MessageBubble.tsx
│   │   ├── ParticipantStack.tsx
│   │   ├── PanelContainer.tsx
│   │   ├── ActionBar.tsx
│   │   └── ...
│   └── index.ts                # Barrel exports
│
├── Rooms/                       # OLD - keep during transition
│   └── ... (existing files)
```

### What to Reuse vs Build New

| Reuse (adapt) | Build New |
|---------------|-----------|
| `MessageList` logic | `RoomShell` |
| `MessageInput` | `RoomLayout` |
| `useRoom` hook | `PanelContainer` |
| `useRoomStream` hook | `ParticipantStack` |
| Agent components | Card components |
| Existing UI primitives | Panel wrapper components |

---

## 9. Summary

### What We're Building

A flexible, multi-panel room system that supports:
- **Preset room types** (Chat, Story, Workspace)
- **Composable layouts** with primary + auxiliary panels
- **Responsive behavior** (desktop panels → mobile tabs)
- **Panel/tab toggle** for user preference
- **Entity cards** for drill-down on any participant/doc/agent
- **Capability badges** with legend for participant metadata

### Key Components

| Layer | Components |
|-------|------------|
| **Route** | `r.$roomId.tsx` (new unified route) |
| **Shell** | `RoomShell` → `RoomHeader` + `RoomLayout` |
| **Panels** | `ChatPanel`, `StoryEditorPanel`, `AgentPanel`, `DebugPanel`, etc. |
| **Cards** | `AgentCard`, `UserCard`, `DocCard` |
| **Primitives** | `MessageBubble`, `PanelContainer`, `ParticipantStack`, `ActionBar`, etc. |

### Design Principles

- **Composition over inheritance** - Panels are interchangeable, not specialized subclasses
- **Progressive disclosure** - Cards reveal detail without leaving context
- **Responsive by default** - Layout adapts, content stays consistent
- **YAGNI** - Canvas/A2UI are placeholders until needed
