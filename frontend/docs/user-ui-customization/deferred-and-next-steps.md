# Rooms UI Customization: Current State & Next Steps

> **Last Updated:** 2026-01-20
> **Related:** [Design Doc](2026-01-19-rooms-ui-design.md) | [Phase 1 Plan](2026-01-19-rooms-ui-implementation.md) | [Phase 2 Plan](2026-01-19-rooms-ui-phase2-implementation.md)

---

## 1. Current Implementation Status

### Phase 1: Foundation (Tasks 1-13) ✅ Complete

Built the core multi-panel room system:

| Component | File | Purpose |
|-----------|------|---------|
| **Primitives** | `Room/primitives/` | Atomic building blocks |
| `PanelContainer` | `PanelContainer.tsx` | Standard panel wrapper with header/content/footer |
| `ActionBar` | `ActionBar.tsx` | Horizontal icon button row for headers |
| `ParticipantStack` | `ParticipantStack.tsx` | Overlapping avatars with popover list |
| `PlaceholderContent` | `PlaceholderContent.tsx` | Consistent "coming soon" empty states |
| **Panels** | `Room/panels/` | Panel implementations |
| `ChatPanel` | `ChatPanel.tsx` | Chat messages with search/copy/export |
| `AgentPanel` | `AgentPanel.tsx` | Room agent management |
| `DebugPanel` | `DebugPanel.tsx` | Agent debugging info |
| `StoryEditorPanel` | `StoryEditorPanel.tsx` | Story editing in rooms |
| `CanvasPanel` | `CanvasPanel.tsx` | Placeholder for future canvas |
| `A2UIPanel` | `A2UIPanel.tsx` | Placeholder for agent UI rendering |
| **Layout** | | |
| `RoomLayout` | `RoomLayout.tsx` | Resizable panels + tab toggle |
| `RoomHeader` | `RoomHeader.tsx` | Title, participants, layout toggle |
| `RoomShell` | `RoomShell.tsx` | Outer container composing header + layout |
| **Route** | | |
| `r.$roomId.tsx` | `routes/_layout/r.$roomId.tsx` | Unified room route |

### Phase 2: Entity Cards & Backend (Tasks 14-31) ✅ Complete

Extended with theming, cards, and panel persistence:

| Feature | Files | Purpose |
|---------|-------|---------|
| **Theme Tokens** | `index.css` | Entity accent colors (agent/user/doc) |
| **Entity Cards** | `Room/cards/` | Popover details for entities |
| `EntityCardPopover` | Base popover structure |
| `AgentCardPopover` | Agent details with actions |
| `UserCardPopover` | User profile and role |
| `DocCardPopover` | Document preview and metadata |
| **Backend Models** | `backend/app/models.py` | |
| `RoomPanelDefaults` | Room owner's default panel config |
| `UserRoomPanelConfig` | User's personal override per room |
| `ResolvedPanelConfig` | Computed effective config |
| **Backend CRUD** | `backend/app/crud_panels.py` | Panel config operations |
| **API Routes** | `backend/app/api/routes/room_panels.py` | Panel config endpoints |
| **Frontend Service** | `services/panelService.ts` | Typed wrapper for panel APIs |
| **Frontend Hook** | `hooks/useRoomPanels.ts` | React Query integration |

---

## 2. Panel Configuration Architecture

### Three-Tier Resolution

The panel configuration system uses a layered resolution strategy:

```
User Opens Room
      ↓
┌─────────────────────────────────────────────────────────────┐
│ 1. Check UserRoomPanelConfig for this user + room           │
│    └─ If exists AND use_room_defaults=false → USE IT        │
│                                                             │
│ 2. Check RoomPanelDefaults for this room                    │
│    └─ If exists and has panels → USE IT                     │
│                                                             │
│ 3. Fall back to type defaults                               │
│    └─ "chat" → [chat + agentPanel]                          │
│    └─ "story" → [storyEditor + chat + agentPanel]           │
│    └─ "workspace" → []                                      │
└─────────────────────────────────────────────────────────────┘
```

### Data Models

```python
# Room owner sets these for all participants
class RoomPanelDefaults:
    room_id: UUID
    panels: list[dict]  # [{ id, kind, prominence }]

# Individual user can override
class UserRoomPanelConfig:
    user_id: UUID
    room_id: UUID
    panels: list[dict] | None
    use_room_defaults: bool  # True = ignore panels, use room/type defaults
```

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/rooms/{id}/panels` | GET | Get resolved config for current user |
| `/rooms/{id}/panels/defaults` | GET | Get room's default config |
| `/rooms/{id}/panels/defaults` | PUT | Update room defaults (owner only) |
| `/rooms/{id}/panels/me` | GET | Get user's personal override |
| `/rooms/{id}/panels/me` | PUT | Update user's personal override |

### Frontend Hook API

```typescript
const {
  // Resolved panels (what to render)
  panels,           // PanelConfig[]
  panelSource,      // "user_override" | "room_defaults" | "type_defaults"

  // Mutations (infrastructure ready, no UI trigger yet)
  updateRoomDefaults,   // (panels) => void - owner only
  setCustomPanels,      // (panels) => void - sets user override
  setUseRoomDefaults,   // (bool) => void - toggle
  resetToDefaults,      // () => void - clear override
} = useRoomPanels(roomId)
```

---

## 3. Deferred Work: User Management Features

These features are **required** for users to manage their panel configurations:

### 3.1 Panel Settings Dialog

**Priority:** High
**Blocking:** User cannot customize panels without this

A dialog accessed from RoomHeader's menu (⋮) allowing users to:

- View current panel configuration with source indicator
- Toggle "Use room defaults" checkbox
- When custom: see panel list with add/remove controls
- Save changes (triggers `setCustomPanels` or `setUseRoomDefaults`)

```
┌─────────────────────────────────────────────┐
│ Panel Settings                          [×] │
├─────────────────────────────────────────────┤
│ Currently using: Room defaults              │
│                                             │
│ [ ] Use my custom layout                    │
│                                             │
│ ─────────────────────────────────────────── │
│ When checked, panels below will be used:    │
│                                             │
│ Primary Panels:                             │
│   ☑ Chat                                    │
│   ☐ Story Editor                            │
│   ☐ Canvas                                  │
│                                             │
│ Auxiliary Panels:                           │
│   ☑ Agents                                  │
│   ☐ Debug                                   │
│                                             │
│              [Cancel] [Save]                │
└─────────────────────────────────────────────┘
```

**Files to create:**
- `components/Room/PanelSettingsDialog.tsx`

**Hook integration:**
```typescript
// In PanelSettingsDialog
const { panels, panelSource, setCustomPanels, setUseRoomDefaults } = useRoomPanels(roomId)
```

### 3.2 Room Owner Defaults Editor

**Priority:** High
**Blocking:** Room owners cannot set defaults for participants

Extends Panel Settings Dialog for room owners:

- Additional tab: "Room Defaults"
- Sets configuration for all participants who use defaults
- Triggers `updateRoomDefaults`

### 3.3 Panel Picker (Add Panel Flow)

**Priority:** Medium
**Blocking:** Workspace rooms not usable without panel adding

Dialog for adding panels to configuration:

```
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
├─────────────────────────────┤
│         [Cancel] [Add]      │
└─────────────────────────────┘
```

**Files to create:**
- `components/Room/PanelPickerDialog.tsx`

---

## 4. Deferred Work: Delightful Enhancements

These features would improve the experience but are not blocking:

### 4.1 Drag-to-Reorder Panels

**Priority:** Low
**Value:** Better UX for panel arrangement

- Drag handle on panel headers
- Reorder within prominence group
- Move between primary ↔ auxiliary
- Auto-save on drop

**Libraries:** `@dnd-kit/core` or `react-beautiful-dnd`

### 4.2 Panel Collapse/Minimize

**Priority:** Low
**Value:** Better space management

- Minimize button in panel header
- Collapsed state shows only title bar
- Click to restore
- State persisted in localStorage

### 4.3 Layout Presets

**Priority:** Low
**Value:** Quick switching between common layouts

Pre-defined configurations:
- "Focus" - Chat only, full width
- "Collaborate" - Chat + Agents
- "Story Mode" - Story + Chat + Agents
- "Debug" - Chat + Debug + Agents

### 4.4 Real-time Panel Sync

**Priority:** Low
**Value:** Multi-device consistency

- WebSocket events for panel config changes
- Other tabs/devices update automatically
- Owner changes propagate to participants using defaults

### 4.5 Keyboard Shortcuts

**Priority:** Low
**Value:** Power user efficiency

- `Ctrl+1/2/3` - Focus panel by position
- `Ctrl+Shift+T` - Toggle tabs/panels mode
- `Ctrl+Shift+D` - Toggle debug panel
- `Esc` - Close any open dialog

### 4.6 Panel History/Undo

**Priority:** Low
**Value:** Safety for accidental changes

- Undo last panel config change
- History of last 5 configurations
- "Reset to default" always available

---

## 5. Technical Debt & Cleanup

### 5.1 Route Consolidation

After transition period, remove deprecated routes:
- `room.$roomId.tsx` (V1)
- `room-v2.$roomId.tsx` (V2)

Rename `r.$roomId.tsx` → `room.$roomId.tsx` if desired.

### 5.2 Sidebar Cleanup

Remove temporary "Rooms (V2)" link from sidebar.

### 5.3 Type Refinement

Current panel config uses `list[dict]` in backend. Consider:
```python
class PanelConfigItem(SQLModel):
    id: str
    kind: Literal["chat", "storyEditor", "agentPanel", "debug", "canvas", "a2ui"]
    prominence: Literal["primary", "auxiliary"]
```

---

## 6. Implementation Sequence

Recommended order for remaining work:

1. **Panel Settings Dialog** - Unblocks user customization
2. **Room Owner Defaults Editor** - Unblocks room owner management
3. **Panel Picker Dialog** - Unblocks workspace room type
4. Route consolidation & cleanup
5. Delightful enhancements (drag-reorder, presets, etc.)

---

## 7. Reference: Completed File Tree

```
frontend/src/
├── components/
│   └── Room/
│       ├── index.ts
│       ├── RoomShell.tsx
│       ├── RoomHeader.tsx
│       ├── RoomLayout.tsx
│       ├── primitives/
│       │   ├── index.ts
│       │   ├── PanelContainer.tsx
│       │   ├── ActionBar.tsx
│       │   ├── ParticipantStack.tsx
│       │   └── PlaceholderContent.tsx
│       ├── panels/
│       │   ├── index.ts
│       │   ├── ChatPanel.tsx
│       │   ├── AgentPanel.tsx
│       │   ├── DebugPanel.tsx
│       │   ├── StoryEditorPanel.tsx
│       │   ├── CanvasPanel.tsx
│       │   └── A2UIPanel.tsx
│       └── cards/
│           ├── index.ts
│           ├── EntityCardPopover.tsx
│           ├── AgentCardPopover.tsx
│           ├── UserCardPopover.tsx
│           └── DocCardPopover.tsx
├── hooks/
│   └── useRoomPanels.ts
├── services/
│   └── panelService.ts
└── routes/_layout/
    └── r.$roomId.tsx

backend/app/
├── models.py              # + RoomPanelDefaults, UserRoomPanelConfig
├── crud_panels.py         # Panel config CRUD
└── api/routes/
    └── room_panels.py     # Panel config endpoints
```
