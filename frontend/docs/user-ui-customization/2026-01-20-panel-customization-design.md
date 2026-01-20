# Panel Layout Customization Design

> **For Claude:** This is a design document. Use superpowers:writing-plans to create an implementation plan from this design.

**Goal:** Give users delightful control over their room panel layouts through multiple interaction patterns - from quick presets to granular drag-and-drop arrangement.

**Date:** 2026-01-20

**Prerequisites:** [Rooms UI Phase 1](2026-01-19-rooms-ui-implementation.md), [Rooms UI Phase 2](2026-01-19-rooms-ui-phase2-implementation.md)

---

## 1. Overview & Philosophy

### Core Philosophy

- **Delight is the goal** - every interaction should feel satisfying, not just functional
- **Progressive disclosure** - simple for casual users, powerful for power users
- **Visible inheritance** - users always understand where their layout comes from
- **Default to more** - invest in polish, micro-interactions, and thoughtful details

### The Three-Layer Inheritance Model

```
Resolution Order (first match wins):
┌─────────────────────────────────────────────────────────────┐
│ 1. User's Room Override                                     │
│    └─ Individual customizes specific room                   │
│                                                             │
│ 2. Room Default                                             │
│    └─ Room owner sets for all participants                  │
│                                                             │
│ 3. User's Global Default                                    │
│    └─ Set on Users page, applies to all rooms               │
│                                                             │
│ 4. System Default                                           │
│    └─ "Collaborate" preset                                  │
└─────────────────────────────────────────────────────────────┘
```

### Five Delightful Features

1. **Drag-to-reorder** - grab panels, move them around, see them settle with spring physics
2. **Collapse/minimize** - shrink panels to title bars, expand with a click
3. **Layout presets** - one-click configurations for common workflows
4. **Keyboard shortcuts** - power users fly through layout changes
5. **Smooth animations** - everything moves with intention via Framer Motion

### Entry Points (Progressive Disclosure)

- **Header menu** → Full Panel Layout dialog
- **Panel drag handles** → Direct reorder
- **Panel header buttons** → Quick collapse/remove
- **Keyboard shortcuts** → Instant actions

---

## 2. Primitive Architecture

> **Worker Agent Note:** All primitives must follow the project's component patterns:
> - JSDoc documentation with `@example` blocks
> - TypeScript interfaces for all props (no `any`)
> - Components under 300 lines
> - Use `cn()` from `@/lib/utils` for className merging

Following our established pattern, we build from reusable primitives that compose together.

### New UI Primitive (in `components/ui/`)

| File | Exports | Purpose |
|------|---------|---------|
| `motion.tsx` | `springConfig`, `ReduceMotionProvider`, `useReduceMotion`, animation variants | Shared animation foundation |

> **Worker Agent Note:** This file lives in `components/ui/` alongside shadcn components to maintain structural hierarchy consistency. Follow shadcn patterns for exports.

### New Room Primitives (in `components/Room/primitives/`)

| Primitive | Responsibility | Key Props |
|-----------|----------------|-----------|
| `DraggablePanel` | Adds drag handle, drag state, drop zone detection | `onDragStart`, `onDragEnd`, `onDrop`, `dragHandlePosition` |
| `CollapsiblePanel` | Adds collapse/expand with animated height transition | `isCollapsed`, `onToggle`, `collapsedHeight` |
| `PresetPicker` | Dropdown showing available presets with mini-previews | `presets`, `currentPreset`, `onSelect` |
| `KeyboardShortcutProvider` | React context that registers shortcuts, handles conflicts | `shortcuts`, `enabled`, `platformAware` |

### Composition Pattern

Wrappers compose *around* existing `PanelContainer` rather than modifying it:

```tsx
<KeyboardShortcutProvider shortcuts={roomShortcuts}>
  <DraggablePanel onDrop={handleReorder}>
    <CollapsiblePanel isCollapsed={collapsed} onToggle={toggle}>
      <PanelContainer title="Chat" headerActions={panelActions}>
        <ChatPanel {...props} />
      </PanelContainer>
    </CollapsiblePanel>
  </DraggablePanel>
</KeyboardShortcutProvider>
```

**Benefits:**
- Existing panels work unchanged
- Features can be mixed and matched
- Easy to disable features (just remove wrapper)
- Testing in isolation is straightforward

---

## 3. Animation System

> **Worker Agent Note:** Use Framer Motion for all animations. Import spring configs from `@/components/ui/motion` - do not define custom springs inline.

### Motion Config (`components/ui/motion.tsx`)

```typescript
/**
 * Shared animation configuration
 *
 * Provides consistent spring physics and motion variants
 * across all panel interactions.
 */

export const springConfig = {
  snappy: { type: "spring", stiffness: 500, damping: 30 },
  gentle: { type: "spring", stiffness: 300, damping: 25 },
  bouncy: { type: "spring", stiffness: 400, damping: 20 },
} as const

export const transitions = {
  collapse: { duration: 0.2, ease: "easeOut" },
  fade: { duration: 0.15, ease: "easeInOut" },
  preset: { duration: 0.3, ease: "easeInOut" },
} as const
```

### Animation Vocabulary

| Interaction | Animation | Feel |
|-------------|-----------|------|
| Panel resize | Spring physics with slight overshoot | Responsive, physical |
| Panel collapse | Smooth height transition (200ms ease-out) + content fade | Gentle, not jarring |
| Panel expand | Height springs open + content fades in with slight delay | Anticipation, reveal |
| Drag start | Slight scale up (1.02x) + subtle shadow elevation | "Picked up" |
| Drag over valid zone | Target zone pulses/highlights | Clear affordance |
| Drop | Spring settle into place | Satisfying landing |
| Preset switch | Crossfade between layouts (300ms) | Smooth transformation |
| Dialog open | Scale from 0.95 + fade (150ms) | Quick, not sluggish |

### Reduce Motion Support

```typescript
/**
 * ReduceMotionProvider
 *
 * Wraps app to provide reduce motion preference.
 * Reads from user settings + system preference.
 */
export function ReduceMotionProvider({ children }: { children: React.ReactNode })

export function useReduceMotion(): boolean
```

When `reduceMotion` is true, all springs become instant transitions (0ms duration).

---

## 4. Panel Layout Dialog

> **Worker Agent Note:** This component will likely exceed 300 lines. Split into subcomponents:
> - `PanelLayoutDialog.tsx` - main shell
> - `LayoutSourceSelector.tsx` - the inheritance radio buttons
> - `InteractivePreview.tsx` - the draggable preview area
> - `PresetButtonGroup.tsx` - preset quick-select buttons

Accessible from room header menu or `Ctrl/Cmd+Shift+L`.

### Structure

```
┌──────────────────────────────────────────────────────────────┐
│ Panel Layout                                             [×] │
├──────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Currently using: Your Default Layout              [↗]    │ │
│ │                                                          │ │
│ │ ○ Room default   ● My default   ○ Custom for this room  │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │                  INTERACTIVE PREVIEW                     │ │
│ │  ┌─────────────┐ ┌─────────────┐ ┌─────────┐            │ │
│ │  │ ≡  Chat     │ │ ≡  Story    │ │ ≡ Agents│            │ │
│ │  │             │ │             │ ├─────────┤            │ │
│ │  │             │ │             │ │ ≡ Debug │            │ │
│ │  └─────────────┘ └─────────────┘ └─────────┘            │ │
│ │                                                          │ │
│ │  Drag panels to reorder • Click ≡ to collapse           │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Quick Presets                                            │ │
│ │ [Focus] [Collaborate] [Story Mode] [Debug] [Canvas]      │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ + Add Panel                                              │ │
│ │   ○ Chat  ○ Story Editor  ○ Canvas  ○ A2UI              │ │
│ │   ○ Agents  ○ Debug                                      │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
│                              [Cancel]  [Save]                │
└──────────────────────────────────────────────────────────────┘
```

### Key Interactions

- **Source selector** - radio buttons switch between room default, user default, or custom
- **Interactive preview** - miniature representation of layout; panels are draggable within it
- **[↗] link** - when using "My default", links to Users page to edit the default itself
- **Preset buttons** - one click applies a preset (updates preview immediately)
- **Add Panel** - expandable section to add panels not currently shown
- **Save** - persists changes; what gets saved depends on which source is selected

### Context Awareness

- If opened from Users page, hides source selector and saves to user default
- If user isn't room owner, "Room default" option is view-only (shows what owner set)

---

## 5. Direct Manipulation & Panel Actions

> **Worker Agent Note:** Panel header actions should use the existing `ActionBar` primitive from `Room/primitives/`. Extend with new action types, don't create parallel implementations.

### Panel Header Enhancements

Each panel header gets subtle action buttons (visible on hover, always visible on touch):

```
┌─────────────────────────────────────────────────────────────┐
│ ≡  Chat                              [−] [⚙] [×]            │
├─────────────────────────────────────────────────────────────┤
│   (panel content)                                           │
└─────────────────────────────────────────────────────────────┘
```

| Button | Icon | Action | Animation |
|--------|------|--------|-----------|
| **Drag handle** | `≡` (GripVertical) | Drag to reorder | Scale up 1.02x + shadow on grab |
| **Collapse** | `−` (Minus) | Minimize to title bar | Smooth height transition |
| **Settings** | `⚙` (Settings) | Opens panel-specific options | Standard popover |
| **Remove** | `×` (X) | Remove panel from layout | Fade out + siblings fill space |

### Collapsed State

```
┌─────────────────────────────────────────────────────────────┐
│ ≡  Chat (collapsed)                          [+] [⚙] [×]   │
└─────────────────────────────────────────────────────────────┘
```

### Drag-to-Reorder Flow

1. **Grab** - User grabs drag handle; panel lifts (scale + shadow)
2. **Drag** - Panel follows cursor; valid drop zones highlight with pulsing border
3. **Hover** - Other panels make room (animated gap appears)
4. **Drop** - Panel springs into place; layout saves automatically
5. **Cancel** - `Escape` or drop outside valid zone; panel returns to origin

### Drop Zones

- Between panels (creates new position)
- Primary ↔ Auxiliary boundary (changes prominence)
- Visual indicator: dashed border + subtle background pulse

### Auto-Save

Direct manipulation changes save automatically with debounce (500ms after last action). Subtle toast: "Layout saved" with undo link for 5 seconds.

---

## 6. Keyboard Shortcuts

> **Worker Agent Note:** Implement `KeyboardShortcutProvider` as a React context. Shortcuts must be disabled when focus is in text inputs. Use `useEffect` cleanup to prevent memory leaks.

### Shortcut Map

| Shortcut | Action | Feedback |
|----------|--------|----------|
| `Mod+1` / `Mod+2` / `Mod+3` | Focus panel by position (left to right) | Panel border briefly highlights |
| `Mod+Shift+L` | Open Panel Layout dialog | Dialog opens |
| `Mod+Shift+T` | Toggle panels ↔ tabs mode | Layout animates between modes |
| `Mod+Shift+M` | Collapse/expand focused panel | Panel animates |
| `Mod+Shift+F` | Apply "Focus" preset (quick escape to chat-only) | Layout transitions with crossfade |
| `Escape` | Close dialog, cancel drag, deselect | Context-dependent |

*`Mod` = `Cmd` on Mac, `Ctrl` on Windows/Linux*

### Discoverability

1. **Tooltips** - Every action button shows shortcut in tooltip: "Collapse panel (⌘⇧M)"
2. **Settings dialog footer** - Small "Keyboard shortcuts" link opens cheat sheet
3. **First-time hint** - On first room visit, subtle hint badge on header

### Cheat Sheet Popover

```
┌─────────────────────────────────────────────┐
│ Keyboard Shortcuts                          │
├─────────────────────────────────────────────┤
│ Panel Navigation                            │
│   ⌘1 ⌘2 ⌘3      Focus panel by position    │
│   ⌘⇧M           Collapse/expand panel       │
│                                             │
│ Layout                                      │
│   ⌘⇧L           Open layout settings        │
│   ⌘⇧T           Toggle panels/tabs          │
│   ⌘⇧F           Focus mode (chat only)      │
│                                             │
│ General                                     │
│   Escape        Close, cancel, deselect     │
└─────────────────────────────────────────────┘
```

### Implementation Notes

- Shortcuts are disabled when focus is in a text input/textarea
- Shortcuts are disabled when a modal is open (except `Escape`)
- `reduceMotion` doesn't affect shortcuts, only the resulting animations

---

## 7. Users Page Integration

> **Worker Agent Note:** Create a new service `userSettingsService.ts` with ViewModel pattern. Do NOT make inline API calls from the component. Follow the existing `panelService.ts` pattern.

### Placement

New "Default Panel Layout" card on the existing Users/Settings page, alongside other user preferences.

### Design

```
┌──────────────────────────────────────────────────────────────┐
│ Default Panel Layout                                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Your default layout applies to all rooms unless you         │
│ customize a specific room.                                   │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │          ┌───────┐ ┌───────┐ ┌─────┐                     │ │
│ │          │ Chat  │ │       │ │Agnts│   Current:          │ │
│ │          │       │ │       │ ├─────┤   Collaborate       │ │
│ │          │       │ │       │ │Debug│                     │ │
│ │          └───────┘ └───────┘ └─────┘                     │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
│                                          [Change Layout]     │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ Accessibility                                                │
│                                                              │
│ [ ] Reduce motion - disable panel animations                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Mini-Preview Component

A small, non-interactive visual representation of the current layout. Shows panel arrangement with labels. **Reusable** - also appears in PresetPicker dropdown items.

> **Worker Agent Note:** Extract `MiniPreview` as a primitive in `Room/primitives/MiniPreview.tsx`. It should accept a `panels` prop and render a scaled-down visual.

### Interactions

- **[Change Layout]** opens the Panel Layout Dialog in "editing user default" mode
- **Reduce motion toggle** sets user preference, propagates via `ReduceMotionProvider`

### First-Time Experience

If user has never set a default, shows "Collaborate" as the system default with subtle prompt: "Customize your workspace →"

---

## 8. Mobile Experience

> **Worker Agent Note:** Use shadcn's `Sheet` component (bottom sheet variant) for mobile. Check `useIsMobile()` hook to conditionally render Sheet vs Dialog.

### Automatic Tab Mode

On mobile (<768px), rooms always display in tab mode. No panel/tab toggle needed.

### Mobile Settings Sheet

```
┌─────────────────────────────────────────────────────────────┐
│ ━━━━━━━━━━                                                  │  ← drag handle
│                                                             │
│ Panel Layout                                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Using: My Default                              [Change ↗]   │
│                                                             │
│ ─────────────────────────────────────────────────────────── │
│                                                             │
│ Quick Presets                                               │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│ │  Focus  │ │Collabor.│ │  Story  │ │  Debug  │            │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘            │
│                                                             │
│ ─────────────────────────────────────────────────────────── │
│                                                             │
│ Visible Panels                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [✓] Chat                                                │ │
│ │ [✓] Agents                                              │ │
│ │ [ ] Story Editor                                        │ │
│ │ [ ] Debug                                               │ │
│ │ [ ] Canvas                                              │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Tab order follows checkbox order.                          │
│                                                             │
│                                          [Done]             │
└─────────────────────────────────────────────────────────────┘
```

### Mobile Differences

- **No panel drag in room** - only in settings sheet (simpler context)
- **Bottom sheet** instead of dialog (native mobile pattern)
- **Checkbox toggles** instead of interactive preview
- **Preset cards** are swipeable horizontally

### Mobile Parity

- Same inheritance model (user default → room default → custom)
- Same presets available
- Same panel options
- Changes sync immediately to desktop if user switches devices

---

## 9. Backend Data Model & API

> **Worker Agent Note:** Follow existing patterns in `models.py`. Use UUID primary keys. Add proper relationship bindings at end of file. Create migration after model changes.

### New Models

```python
# User's global default layout (applies to all rooms)
class UserPanelDefaults(SQLModel, table=True):
    __tablename__ = "user_panel_defaults"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", unique=True, index=True)
    preset_id: str | None = None  # "focus", "collaborate", etc. or None for custom
    panels: list[dict] = Field(default=[], sa_column=Column(JSON))
    reduce_motion: bool = Field(default=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Future-proofing: custom preset storage (schema only, not exposed in UI yet)
class PanelPreset(SQLModel, table=True):
    __tablename__ = "panel_presets"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID | None = Field(foreign_key="user.id", index=True)  # None = system
    name: str
    description: str | None = None
    panels: list[dict] = Field(sa_column=Column(JSON))
    is_system: bool = Field(default=False)
    shared_to_room_id: uuid.UUID | None = Field(foreign_key="rooms.room_id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### New Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/users/me/panel-defaults` | GET | Get user's default layout |
| `/users/me/panel-defaults` | PUT | Update user's default layout |
| `/presets` | GET | List available presets (system only for now) |
| `/presets/{id}` | GET | Get preset details |

### Updated Resolution Logic

```python
def resolve_panels_for_user(session, user_id, room_id) -> tuple[list[dict], str]:
    # 1. User's room override (use_room_defaults=False)
    user_room_config = get_user_room_panel_config(session, user_id, room_id)
    if user_room_config and not user_room_config.use_room_defaults:
        return user_room_config.panels, "room_override"

    # 2. Room defaults (set by owner)
    room_defaults = get_room_panel_defaults(session, room_id)
    if room_defaults and room_defaults.panels:
        return room_defaults.panels, "room_defaults"

    # 3. User's global default (NEW)
    user_defaults = get_user_panel_defaults(session, user_id)
    if user_defaults and user_defaults.panels:
        return user_defaults.panels, "user_defaults"

    # 4. System default
    return SYSTEM_PRESETS["collaborate"], "system_defaults"
```

### System Presets

```python
SYSTEM_PRESETS = {
    "focus": [
        {"id": "chat", "kind": "chat", "prominence": "primary"}
    ],
    "collaborate": [
        {"id": "chat", "kind": "chat", "prominence": "primary"},
        {"id": "agents", "kind": "agentPanel", "prominence": "auxiliary"},
    ],
    "story_mode": [
        {"id": "story", "kind": "storyEditor", "prominence": "primary"},
        {"id": "chat", "kind": "chat", "prominence": "primary"},
        {"id": "agents", "kind": "agentPanel", "prominence": "auxiliary"},
    ],
    "debug": [
        {"id": "chat", "kind": "chat", "prominence": "primary"},
        {"id": "debug", "kind": "debug", "prominence": "auxiliary"},
        {"id": "agents", "kind": "agentPanel", "prominence": "auxiliary"},
    ],
    "canvas": [
        {"id": "canvas", "kind": "canvas", "prominence": "primary"},
        {"id": "chat", "kind": "chat", "prominence": "primary"},
        {"id": "agents", "kind": "agentPanel", "prominence": "auxiliary"},
    ],
}
```

---

## 10. Frontend Services & Hooks

> **Worker Agent Note:**
> - ALL API calls go through services, never inline in components
> - Services return ViewModels, not raw API types
> - Hooks use TanStack Query with proper query keys
> - New hooks require explicit approval - check if existing hooks can be extended first

### New Service: `userPanelDefaultsService.ts`

```typescript
/**
 * User Panel Defaults Service
 *
 * Manages user's global default panel layout.
 *
 * @see panelService.ts for room-level panel operations
 */

export interface UserPanelDefaultsViewModel {
  presetId: string | null
  panels: PanelConfig[]
  reduceMotion: boolean
}

export async function getUserPanelDefaults(): Promise<UserPanelDefaultsViewModel | null>
export async function updateUserPanelDefaults(config: UserPanelDefaultsViewModel): Promise<UserPanelDefaultsViewModel>
```

### New Service: `presetService.ts`

```typescript
/**
 * Preset Service
 *
 * Provides system presets for panel layouts.
 */

export interface PresetViewModel {
  id: string
  name: string
  description: string
  panels: PanelConfig[]
  isSystem: boolean
}

export async function listPresets(): Promise<PresetViewModel[]>
export async function getPreset(id: string): Promise<PresetViewModel>
```

### New Hook: `useUserPanelDefaults.ts`

```typescript
/**
 * useUserPanelDefaults Hook
 *
 * Manages user's global panel default with React Query.
 */
export function useUserPanelDefaults() {
  return {
    defaults: UserPanelDefaultsViewModel | null,
    isLoading: boolean,
    updateDefaults: (config) => void,
    isUpdating: boolean,
  }
}
```

### New Hook: `usePanelPresets.ts`

```typescript
/**
 * usePanelPresets Hook
 *
 * Provides access to available layout presets.
 */
export function usePanelPresets() {
  return {
    presets: PresetViewModel[],
    isLoading: boolean,
    getPreset: (id: string) => PresetViewModel | undefined,
  }
}
```

### Extended: `useRoomPanels.ts`

Add to existing hook:
- `panelSource` now includes `"user_defaults"` as possible value
- Add `applyPreset(presetId: string)` convenience method

---

## 11. Error Handling & Edge Cases

> **Worker Agent Note:** Use `handleError` from `@/utils` with `useCustomToast` for all error handling. Follow existing patterns in the codebase.

### Network Errors

| Scenario | Handling |
|----------|----------|
| Save fails | Toast: "Couldn't save layout. [Retry]" - panel stays in edited state |
| Load fails | Show last cached layout + subtle banner: "Using offline layout" |
| Partial save | Optimistic update, rollback on failure with toast |

### Conflict Resolution

| Scenario | Handling |
|----------|----------|
| Room owner changes default while user has custom | User keeps their override - no disruption |
| Room owner changes default while user uses room default | User sees update on next room visit or refresh |

### Invalid States

| Scenario | Handling |
|----------|----------|
| All panels removed | Prevent - at least one panel required. Disable last panel's remove button |
| Preset references unavailable panel | Skip unavailable panels, show what's available |
| Corrupted config from backend | Fall back to system default + log error |

### Animation Edge Cases

| Scenario | Handling |
|----------|----------|
| Reduce motion enabled | All springs → instant transitions (0ms) |
| Drag cancelled mid-flight | Animate back to origin with spring |
| Multiple rapid preset switches | Cancel in-flight animation, start new one |
| Dialog closed during save | Save completes in background, toast confirms |

### Accessibility

| Feature | Implementation |
|---------|----------------|
| Screen readers | All buttons have `aria-label`, drag state announced via live region |
| Keyboard-only drag | Select panel with Enter, arrow keys to move, Enter to drop |
| Focus management | Focus returns to trigger when dialog closes |
| Color contrast | All text meets WCAG AA, don't rely solely on color for drop zones |

---

## 12. File Structure Summary

### New Files

```
frontend/src/
├── components/
│   ├── ui/
│   │   └── motion.tsx                    # Animation config + ReduceMotionProvider
│   │
│   ├── Room/
│   │   ├── primitives/
│   │   │   ├── DraggablePanel.tsx        # Drag wrapper
│   │   │   ├── CollapsiblePanel.tsx      # Collapse wrapper
│   │   │   ├── PresetPicker.tsx          # Preset dropdown
│   │   │   ├── MiniPreview.tsx           # Layout mini-preview
│   │   │   └── KeyboardShortcutProvider.tsx
│   │   │
│   │   ├── PanelLayoutDialog.tsx         # Main settings dialog
│   │   ├── PanelLayoutSheet.tsx          # Mobile bottom sheet
│   │   ├── LayoutSourceSelector.tsx      # Inheritance radio buttons
│   │   ├── InteractivePreview.tsx        # Draggable preview area
│   │   └── PresetButtonGroup.tsx         # Preset quick-select
│   │
│   └── Users/
│       └── DefaultPanelLayoutCard.tsx    # Users page settings card
│
├── services/
│   ├── userPanelDefaultsService.ts       # User defaults API
│   └── presetService.ts                  # Presets API
│
└── hooks/
    ├── useUserPanelDefaults.ts           # User defaults hook
    └── usePanelPresets.ts                # Presets hook

backend/app/
├── models.py                             # + UserPanelDefaults, PanelPreset
├── crud_user_panels.py                   # User defaults CRUD
├── crud_panels.py                        # Updated resolution logic
└── api/routes/
    ├── user_panels.py                    # User defaults endpoints
    └── presets.py                        # Presets endpoints
```

---

## 13. Key Deliverables Checklist

1. ✨ Drag-to-reorder with spring physics
2. ✨ Collapse/minimize with smooth animations
3. ✨ Five system presets with one-click apply
4. ✨ Platform-aware keyboard shortcuts
5. ✨ Framer Motion throughout
6. ✨ User defaults on Users page
7. ✨ Mobile-optimized bottom sheet
8. ✨ Progressive disclosure of inheritance model
9. ✨ Reduce motion accessibility toggle
10. ✨ Auto-save with undo toast

---

## 14. Future Considerations (Not This Iteration)

Documented for future reference - **do not implement now**:

- **Custom presets** - Users save their own named presets (schema ready in `PanelPreset`)
- **Preset sharing** - Room owners assign a preset to a room (schema ready)
- **Real-time sync** - WebSocket events for panel config changes across devices
- **History/undo** - Full undo stack for panel changes
