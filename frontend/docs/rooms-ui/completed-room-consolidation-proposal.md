# Room Routes Consolidation Proposal

## Executive Summary

We have three room route implementations representing evolutionary stages of the UI:

| Route | Path | Purpose | Status |
|-------|------|---------|--------|
| `room.$roomId.tsx` | `/room/:id` | Original fixed layout | Legacy |
| `room-v2.$roomId.tsx` | `/room-v2/:id` | Enhanced with tabbed agents | Legacy |
| `r.$roomId.tsx` | `/r/:id` | Dynamic panel system | **Current** |

**Recommendation:** Consolidate to a single route (`r.$roomId.tsx`) with configuration-driven layouts that replicate V1/V2 behaviors via presets.

---

## Current State Analysis

### Route Comparison

```
┌──────────────────┬─────────────────┬─────────────────┬─────────────────┐
│                  │ V1 (room)       │ V2 (room-v2)    │ V3 (r)          │
├──────────────────┼─────────────────┼─────────────────┼─────────────────┤
│ Layout           │ Fixed 3-column  │ Fixed 2-column  │ Dynamic panels  │
│ Sidebar          │ Participant list│ Tabbed agents   │ Configurable    │
│ Agent Mgmt       │ Basic toggle    │ Party picker    │ Full panel      │
│ Resizable        │ No              │ No              │ Yes             │
│ Mobile           │ No              │ No              │ Yes (tabs)      │
│ Configuration    │ Hard-coded      │ Hard-coded      │ Backend-driven  │
│ Panel Types      │ 3 fixed         │ 3 fixed         │ 6+ pluggable    │
├──────────────────┼─────────────────┼─────────────────┼─────────────────┤
│ Components From  │ Rooms/          │ Rooms/ + Agents/│ Room/ + panels/ │
│ Lines of Code    │ ~280            │ ~350            │ ~200            │
└──────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

### Shared Infrastructure

All three routes already share:
- `useRoom()` - Aggregate room state
- `useRoomStream()` - WebSocket real-time updates
- `MessageList` / `MessageInput` - Core chat components
- Message operations (edit, pin, delete, context toggle)
- `useCustomToast()` - Notifications

### Component Directory Duplication

```
components/
├── Rooms/                    ← V1/V2 use these (legacy)
│   ├── RoomHeader.tsx
│   ├── MessageList.tsx
│   ├── ParticipantList.tsx
│   └── ...
│
└── Room/                     ← V3 uses these (current)
    ├── RoomHeader.tsx        ← Different implementation!
    ├── RoomShell.tsx
    ├── RoomLayout.tsx
    └── panels/
        ├── ChatPanel.tsx     ← Wraps MessageList/Input
        └── AgentPanel.tsx
```

---

## Consolidation Strategy

### Phase 1: Preset-Based Migration

Create presets that replicate V1/V2 layouts using V3's panel system:

```typescript
// V1-equivalent preset
const CLASSIC_PRESET = {
  id: "classic",
  name: "Classic",
  panels: [
    { id: "chat", kind: "chat", prominence: "primary" },
    { id: "participants", kind: "participantList", prominence: "auxiliary" },
  ],
}

// V2-equivalent preset
const ENHANCED_PRESET = {
  id: "enhanced",
  name: "Enhanced",
  panels: [
    { id: "chat", kind: "chat", prominence: "primary" },
    { id: "agents", kind: "agentPanel", prominence: "auxiliary" },
  ],
}
```

### Phase 2: Add Missing Panel Type

V1 has a dedicated `ParticipantList` sidebar. Create `ParticipantPanel`:

```typescript
// New panel in Room/panels/
export function ParticipantPanel({ roomId }: { roomId: string }) {
  // Wraps existing ParticipantList component from Rooms/
  return (
    <PanelContainer title="Participants">
      <ParticipantList roomId={roomId} />
    </PanelContainer>
  )
}
```

### Phase 3: Route Consolidation

```
Before:                          After:
/room/:id    → room.$roomId      /r/:id → r.$roomId (unified)
/room-v2/:id → room-v2.$roomId
/r/:id       → r.$roomId

Redirects:
/room/:id    → /r/:id?preset=classic
/room-v2/:id → /r/:id?preset=enhanced
```

### Phase 4: Cleanup

1. Remove `room.$roomId.tsx`
2. Remove `room-v2.$roomId.tsx`
3. Deprecate `components/Rooms/` (migrate any remaining utilities)
4. Update all internal links

---

## Implementation Tasks

### Task 1: Create ParticipantPanel
```
Files:
- Create: src/components/Room/panels/ParticipantPanel.tsx
- Modify: src/components/Room/panels/index.ts
- Modify: r.$roomId.tsx (add to panel registry)
```

### Task 2: Add Classic/Enhanced Presets
```
Files:
- Modify: backend/app/api/routes/presets.py (add presets)
- Modify: src/components/Room/primitives/PresetPicker.tsx
```

### Task 3: URL Preset Support
```
Files:
- Modify: r.$roomId.tsx (read ?preset query param)
- Apply preset on first visit if specified
```

### Task 4: Route Redirects
```
Files:
- Modify: room.$roomId.tsx → redirect to /r/:id?preset=classic
- Modify: room-v2.$roomId.tsx → redirect to /r/:id?preset=enhanced
```

### Task 5: Cleanup
```
Files:
- Delete: room.$roomId.tsx
- Delete: room-v2.$roomId.tsx
- Audit: components/Rooms/ for unused files
```

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Feature parity gaps | Create detailed feature matrix, test each before removal |
| Broken external links | Maintain redirects for 2 releases |
| User confusion | Clear migration messaging, preset picker in UI |
| Missing edge cases | Keep V1/V2 as feature flags initially |

---

## Feature Parity Checklist

Before removing V1/V2, ensure V3 supports:

### From V1 (room.$roomId)
- [x] Message list with filters
- [x] Message input with send
- [x] Participant list display
- [ ] **Participant list as dedicated panel** ← Need to add
- [x] Debug panel toggle
- [x] Edit drawer for messages
- [x] Pin/delete/context toggle

### From V2 (room-v2.$roomId)
- [x] Tabbed sidebar UI
- [x] Agent quick add
- [x] Agent party picker
- [x] Room agent list
- [x] Switch view button ← Can remove (will be unified)
- [x] All V1 features

### V3 Exclusive Features (keep)
- [x] Resizable panels
- [x] Mobile tab mode
- [x] Backend-driven config
- [x] Story editor panel
- [x] Canvas panel
- [x] A2UI panel
- [x] Panel layout dialog ← Just added!

---

## Recommendation

**Proceed with consolidation.** V3 (`r.$roomId`) is architecturally superior:

1. **Maintainability** - One route vs three, configuration over code
2. **Flexibility** - Users choose layout, not hardcoded
3. **Mobile-ready** - Automatic responsive behavior
4. **Extensible** - New panels without route changes
5. **Testable** - Fewer code paths to test

### Suggested Timeline

| Week | Tasks |
|------|-------|
| 1 | Create ParticipantPanel, add presets |
| 2 | Add URL preset support, test parity |
| 3 | Add redirects, internal testing |
| 4 | Remove legacy routes, cleanup |

### Quick Win Option

If full consolidation is too large, a minimal approach:

1. Add redirects from `/room/*` and `/room-v2/*` to `/r/*`
2. Keep legacy routes but mark deprecated
3. Stop all new development on V1/V2

This gets users onto V3 immediately while deferring cleanup.

---

## Questions for Product

1. Are there users/features dependent on specific V1/V2 behaviors?
2. Should presets be user-visible in settings?
3. Do we need analytics on which layouts are used?
4. Timeline preferences for migration?
