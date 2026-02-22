# Panel Layout Reference Card

Quick reference for engineers working with the panel customization system.

## Scope Note

This card documents the current room-oriented panel customization flow. It is not the full composition contract for demos/pages that require nested composition (panels-in-panels, blocks-in-blocks) or headless/invisible mounted nodes.

For composition-contract decisions, align with demo composition v2 planning and active demo integration docs.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Resolution Order                          │
├─────────────────────────────────────────────────────────────────┤
│  1. User's room override    → "room_override"                   │
│  2. Room owner's defaults   → "room_defaults"                   │
│  3. User's global defaults  → "user_defaults"                   │
│  4. System preset           → "system_defaults" (collaborate)   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
Component → Service (ViewModel) → API Client → Backend
    ↑                                              ↓
    ←←←←←←←← TanStack Query (cache) ←←←←←←←←←←←←←←
```

## Key Files

| Layer | File | Purpose |
|-------|------|---------|
| **Backend** | `backend/app/crud_panels.py` | CRUD operations |
| **Backend** | `backend/app/api/routes/user_panels.py` | User defaults API |
| **Backend** | `backend/app/api/routes/presets.py` | System presets API |
| **Service** | `src/services/panelService.ts` | Room-level panels |
| **Service** | `src/services/userPanelDefaultsService.ts` | User global defaults |
| **Service** | `src/services/presetService.ts` | Layout presets |
| **Hook** | `src/hooks/useRoomPanels.ts` | Room panel state |
| **Hook** | `src/hooks/useUserPanelDefaults.ts` | User defaults state |
| **Hook** | `src/hooks/usePanelPresets.ts` | Preset list |
| **Component** | `src/components/Room/PanelLayoutDialog.tsx` | Main dialog |

## API Endpoints

```
GET  /api/v1/users/me/panel-defaults     → UserPanelDefaultsPublic | null
PUT  /api/v1/users/me/panel-defaults     → UserPanelDefaultsPublic

GET  /api/v1/presets                     → { presets: PresetResponse[] }
GET  /api/v1/presets/{preset_id}         → PresetResponse

GET  /api/v1/rooms/{room_id}/panels/resolved  → ResolvedPanelConfig
GET  /api/v1/rooms/{room_id}/panels/defaults  → RoomPanelDefaultsPublic
PUT  /api/v1/rooms/{room_id}/panels/defaults  → RoomPanelDefaultsPublic
GET  /api/v1/rooms/{room_id}/panels/me        → UserRoomPanelConfigPublic
PUT  /api/v1/rooms/{room_id}/panels/me        → UserRoomPanelConfigPublic
```

## Types

### PanelConfig
```typescript
interface PanelConfig {
  id: string                              // Unique panel instance ID
  kind: "chat" | "storyEditor" | "agentPanel" | "debug" | "canvas" | "a2ui"
  prominence: "primary" | "auxiliary"     // Layout position
}
```

### Composition Guardrails (Do Not Contradict)

```typescript
type VisibilityMode = "visible" | "hidden_unmounted" | "hidden_mounted"

type LayoutNode =
  | { node_type: "panel"; id: string; panel: PanelConfig; visibility?: VisibilityMode }
  | { node_type: "block"; id: string; block_type: string; visibility?: VisibilityMode }
  | {
      node_type: "container"
      id: string
      layout_mode: "stack" | "split" | "tabs" | "overlay"
      children: LayoutNode[]
      visibility?: VisibilityMode
    }
```

Practical implications:
1. Flat `PanelConfig[]` is an editor projection, not the canonical long-term composition graph.
2. Invisible panels may still be mounted (`hidden_mounted`) to preserve runtime state.
3. Stacked blocks are represented by container nodes with `layout_mode: "stack"`.
4. Theme precedence must remain composition-aware:
- composition page/cards themes
- node-level theme overrides
- renderer/content-level overrides

### System Presets
| ID | Name | Panels |
|----|------|--------|
| `focus` | Focus | chat |
| `collaborate` | Collaborate | chat + agents |
| `story_mode` | Story Mode | story + chat + agents |
| `debug` | Debug | chat + debug + agents |
| `canvas` | Canvas | canvas + chat + agents |

## Hook Usage

### useRoomPanels
```typescript
const {
  panels,              // PanelConfig[] - effective config
  panelSource,         // "room_override" | "room_defaults" | "user_defaults" | "system_defaults"
  isLoading,
  roomDefaults,        // Room owner's default config
  setCustomPanels,     // (panels: PanelConfig[]) => void
  setUseRoomDefaults,  // (useDefaults: boolean) => void
  resetToDefaults,     // () => void
} = useRoomPanels(roomId)
```

### useUserPanelDefaults
```typescript
const {
  defaults,            // UserPanelDefaultsViewModel | null
  isLoading,
  updateDefaults,      // (input: UpdateUserPanelDefaultsInput) => void
  setPreset,           // (presetId: string) => void
  setCustomPanels,     // (panels: PanelConfig[]) => void
  setReduceMotion,     // (reduceMotion: boolean) => void
} = useUserPanelDefaults()
```

### usePanelPresets
```typescript
const {
  presets,             // PresetViewModel[]
  isLoading,
  getPreset,           // (id: string) => PresetViewModel | undefined
  isValidPreset,       // (id: string) => boolean
} = usePanelPresets()
```

## Component Usage

### PanelLayoutDialog
```tsx
import { PanelLayoutDialog } from "@/components/Room"

<PanelLayoutDialog
  open={isOpen}
  onOpenChange={setIsOpen}
  roomId={roomId}           // null for user-defaults mode
  isRoomOwner={canEdit}     // Shows room default options
  mode="room"               // "room" | "user-defaults"
/>
```

### Opening from RoomHeader
The dialog is already integrated into `RoomHeader`. Pass `roomId` prop:

```tsx
<RoomHeader
  roomId={room.id}          // Enables "Panel Layout" menu item
  title={room.name}
  // ...other props
/>
```

## Query Keys

```typescript
["rooms", roomId, "panels"]           // Resolved panels
["rooms", roomId, "panels", "defaults"] // Room defaults
["rooms", roomId, "panels", "me"]     // User's room config
["user", "panel-defaults"]            // User global defaults
["presets"]                           // System presets
```

## Common Patterns

### Apply a preset to user defaults
```typescript
const { setPreset } = useUserPanelDefaults()
setPreset("focus")  // Sets presetId, clears custom panels
```

### Set custom room layout
```typescript
const { setCustomPanels } = useRoomPanels(roomId)
setCustomPanels([
  { id: "chat", kind: "chat", prominence: "primary" },
  { id: "agents", kind: "agentPanel", prominence: "auxiliary" },
])
```

### Reset room to defaults
```typescript
const { resetToDefaults } = useRoomPanels(roomId)
resetToDefaults()  // Clears user override, uses room/user/system defaults
```

### Check current source
```typescript
const { panelSource } = useRoomPanels(roomId)

if (panelSource === "room_override") {
  // User has custom config for this room
}
```

## Caveats

1. **ViewModel pattern required** - Never use raw API types in components
2. **Presets are static** - Cached for 1 hour, no user-created presets yet
3. **Room defaults need ownership** - Only room owner can set room defaults
4. **Mutation invalidation** - User default changes invalidate room queries

## Related Docs

- Implementation plan: `docs/user-ui-customization/2026-01-20-panel-customization-implementation.md`
- Room UI design: `docs/plans/2026-01-19-rooms-ui-design.md`
