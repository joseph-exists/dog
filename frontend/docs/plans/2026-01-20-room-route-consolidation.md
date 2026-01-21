# Room Route Consolidation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Consolidate three room routes (V1, V2, V3) into a single unified route at `/r/:id` with full feature parity.

**Architecture:** Create a `ParticipantPanel` to replicate V1's combined user/agent sidebar, add a "classic" preset, redirect legacy routes to the unified route, then delete legacy code.

**Tech Stack:** React, TanStack Router, TypeScript, shadcn/ui

---

## Task 1: Create ParticipantPanel Component

**Files:**
- Create: `src/components/Room/panels/ParticipantPanel.tsx`
- Modify: `src/components/Room/panels/index.ts`

**Step 1: Create the ParticipantPanel**

```typescript
/**
 * ParticipantPanel
 *
 * Combined participants panel showing users and agents.
 * Replicates V1 sidebar functionality for "classic" layout.
 */

import { Loader2 } from "lucide-react"

import type { ParticipantViewModel } from "@/services/roomService"
import { PanelContainer } from "../primitives/PanelContainer"
import AgentToggle from "@/components/Rooms/AgentToggle"
import RemoveParticipantButton from "@/components/Rooms/RemoveParticipantButton"

interface ParticipantPanelProps {
  activeUsers: ParticipantViewModel[]
  activeAgents: ParticipantViewModel[]
  isLoading?: boolean
  currentUserRole: "owner" | "member" | null
  onRemoveParticipant?: (participantId: string) => Promise<void>
  onToggleAgent?: (agentId: string, activate: boolean) => Promise<void>
}

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)
}

export function ParticipantPanel({
  activeUsers,
  activeAgents,
  isLoading,
  currentUserRole,
  onRemoveParticipant,
  onToggleAgent,
}: ParticipantPanelProps) {
  const canManage = currentUserRole === "owner"

  if (isLoading) {
    return (
      <PanelContainer title="Participants">
        <div className="flex items-center justify-center p-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      </PanelContainer>
    )
  }

  return (
    <PanelContainer title="Participants">
      <div className="flex flex-col h-full overflow-y-auto">
        {/* Users Section */}
        <div className="p-3 border-b">
          <h3 className="text-xs font-medium text-muted-foreground mb-2">
            Users ({activeUsers.length})
          </h3>
          <div className="space-y-1">
            {activeUsers.map((user) => (
              <div
                key={user.participant_id}
                className="flex items-center gap-2 p-2 rounded-md hover:bg-muted/50"
              >
                <div className="size-8 rounded-full bg-primary/10 flex items-center justify-center text-xs font-medium">
                  {getInitials(user.display_name)}
                </div>
                <span className="flex-1 text-sm truncate">
                  {user.display_name}
                </span>
                {canManage && user.role !== "owner" && onRemoveParticipant && (
                  <RemoveParticipantButton
                    participantId={user.participant_id}
                    participantName={user.display_name}
                    onRemove={onRemoveParticipant}
                  />
                )}
              </div>
            ))}
            {activeUsers.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-2">
                No users
              </p>
            )}
          </div>
        </div>

        {/* Agents Section */}
        <div className="p-3 flex-1">
          <h3 className="text-xs font-medium text-muted-foreground mb-2">
            Agents ({activeAgents.length})
          </h3>
          <div className="space-y-1">
            {activeAgents.map((agent) => (
              <div
                key={agent.participant_id}
                className="flex items-center gap-2 p-2 rounded-md hover:bg-muted/50"
              >
                <div className="size-8 rounded-full bg-accent flex items-center justify-center text-xs">
                  🤖
                </div>
                <span className="flex-1 text-sm truncate">
                  {agent.display_name}
                </span>
                {canManage && onToggleAgent && (
                  <AgentToggle
                    agentId={agent.participant_id}
                    agentName={agent.display_name}
                    isActive={agent.is_active}
                    onToggle={onToggleAgent}
                  />
                )}
              </div>
            ))}
            {activeAgents.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-2">
                No agents
              </p>
            )}
          </div>
        </div>
      </div>
    </PanelContainer>
  )
}
```

**Step 2: Export from panels index**

Add to `src/components/Room/panels/index.ts`:

```typescript
export { ParticipantPanel } from "./ParticipantPanel"
```

**Step 3: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

Expected: No errors in ParticipantPanel.tsx

**Step 4: Commit**

```bash
git add src/components/Room/panels/ParticipantPanel.tsx src/components/Room/panels/index.ts
git commit -m "feat(room): add ParticipantPanel for classic layout"
```

---

## Task 2: Register ParticipantPanel in Route

**Files:**
- Modify: `src/routes/_layout/r.$roomId.tsx`
- Modify: `src/services/panelService.ts`

**Step 1: Add participantPanel to panelService kinds**

In `src/services/panelService.ts`, update the PanelConfig kind type:

```typescript
export interface PanelConfig {
  id: string
  kind: "chat" | "storyEditor" | "agentPanel" | "debug" | "canvas" | "a2ui" | "participantPanel"
  prominence: "primary" | "auxiliary"
}
```

Also update `isValidPanelKind` and `getPanelDisplayName`:

```typescript
export function isValidPanelKind(kind: string): kind is PanelConfig["kind"] {
  return [
    "chat",
    "storyEditor",
    "agentPanel",
    "debug",
    "canvas",
    "a2ui",
    "participantPanel",
  ].includes(kind)
}

export function getPanelDisplayName(kind: PanelConfig["kind"]): string {
  const names: Record<PanelConfig["kind"], string> = {
    chat: "Chat",
    storyEditor: "Story Editor",
    agentPanel: "Agents",
    debug: "Debug",
    canvas: "Canvas",
    a2ui: "Agent UI",
    participantPanel: "Participants",
  }
  return names[kind]
}
```

**Step 2: Add ParticipantPanel to route's panel registry**

In `src/routes/_layout/r.$roomId.tsx`, add import and register:

```typescript
// Add to imports
import {
  A2UIPanel,
  AgentPanel,
  CanvasPanel,
  ChatPanel,
  DebugPanel,
  ParticipantPanel,  // ADD THIS
  type PanelConfig,
  RoomShell,
  StoryEditorPanel,
} from "@/components/Room"

// Add to panelComponents registry (around line 260)
const panelComponents: Record<string, () => React.ReactNode> = {
  // ... existing panels ...
  participantPanel: () => (
    <ParticipantPanel
      activeUsers={activeUsers}
      activeAgents={activeAgents}
      isLoading={isLoadingParticipants}
      currentUserRole={currentUserRole}
      onRemoveParticipant={removeParticipant}
      onToggleAgent={async (agentId, activate) => {
        if (activate) {
          await addParticipant(agentId, "agent")
        } else {
          await removeParticipant(agentId)
        }
      }}
    />
  ),
}
```

Note: You'll need to extract `activeUsers` from `useRoom` - it's already there but not destructured. Add it to the destructuring.

**Step 3: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 4: Commit**

```bash
git add src/routes/_layout/r.\$roomId.tsx src/services/panelService.ts
git commit -m "feat(room): register ParticipantPanel in panel system"
```

---

## Task 3: Add Classic Preset to Backend

**Files:**
- Modify: `backend/app/api/routes/presets.py`

**Step 1: Add classic preset to SYSTEM_PRESETS**

```python
SYSTEM_PRESETS = {
    "focus": {
        "id": "focus",
        "name": "Focus",
        "description": "Chat only, full width",
        "panels": [{"id": "chat", "kind": "chat", "prominence": "primary"}],
        "is_system": True,
    },
    "classic": {
        "id": "classic",
        "name": "Classic",
        "description": "Chat with participants sidebar (V1 style)",
        "panels": [
            {"id": "chat", "kind": "chat", "prominence": "primary"},
            {"id": "participants", "kind": "participantPanel", "prominence": "auxiliary"},
        ],
        "is_system": True,
    },
    "collaborate": {
        # ... existing ...
    },
    # ... rest of presets ...
}
```

**Step 2: Verify backend starts**

```bash
cd /home/josep/dog/backend && source .venv/bin/activate && timeout 5 fastapi dev app/main.py || true
```

**Step 3: Commit**

```bash
git add backend/app/api/routes/presets.py
git commit -m "feat(presets): add classic preset for V1-style layout"
```

---

## Task 4: Update Frontend PresetPicker with Classic

**Files:**
- Modify: `src/components/Room/primitives/PresetPicker.tsx`

**Step 1: Add classic to SYSTEM_PRESETS constant**

```typescript
export const SYSTEM_PRESETS: Preset[] = [
  {
    id: "focus",
    name: "Focus",
    description: "Chat only, full width",
    panels: [{ id: "chat", kind: "chat", prominence: "primary" }],
  },
  {
    id: "classic",
    name: "Classic",
    description: "Chat with participants sidebar",
    panels: [
      { id: "chat", kind: "chat", prominence: "primary" },
      { id: "participants", kind: "participantPanel", prominence: "auxiliary" },
    ],
  },
  {
    id: "collaborate",
    name: "Collaborate",
    description: "Chat with agents sidebar",
    panels: [
      { id: "chat", kind: "chat", prominence: "primary" },
      { id: "agents", kind: "agentPanel", prominence: "auxiliary" },
    ],
  },
  // ... rest unchanged ...
]
```

**Step 2: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 3: Commit**

```bash
git add src/components/Room/primitives/PresetPicker.tsx
git commit -m "feat(presets): add classic preset to frontend picker"
```

---

## Task 5: Regenerate API Client

**Step 1: Ensure backend is running**

```bash
cd /home/josep/dog/backend && source .venv/bin/activate && fastapi dev app/main.py &
```

**Step 2: Regenerate client**

```bash
cd /home/josep/dog/frontend && npm run generate-client
```

**Step 3: Verify classic preset in types**

```bash
grep -l "classic" src/client/ || echo "Check generation"
```

**Step 4: Commit**

```bash
git add src/client/
git commit -m "chore(client): regenerate with classic preset"
```

---

## Task 6: Add Redirects for Legacy Routes

**Files:**
- Modify: `src/routes/_layout/room.$roomId.tsx`
- Modify: `src/routes/_layout/room-v2.$roomId.tsx`

**Step 1: Replace room.$roomId.tsx with redirect**

Replace entire file content:

```typescript
/**
 * Legacy Room Route - Redirects to unified route
 * @deprecated Use /r/:roomId instead
 */

import { createFileRoute, redirect } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/room/$roomId")({
  beforeLoad: ({ params }) => {
    throw redirect({
      to: "/r/$roomId",
      params: { roomId: params.roomId },
      replace: true,
    })
  },
  component: () => null,
})
```

**Step 2: Replace room-v2.$roomId.tsx with redirect**

Replace entire file content:

```typescript
/**
 * Legacy Room V2 Route - Redirects to unified route
 * @deprecated Use /r/:roomId instead
 */

import { createFileRoute, redirect } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/room-v2/$roomId")({
  beforeLoad: ({ params }) => {
    throw redirect({
      to: "/r/$roomId",
      params: { roomId: params.roomId },
      replace: true,
    })
  },
  component: () => null,
})
```

**Step 3: Verify redirects work**

```bash
cd /home/josep/dog/frontend && npm run build
```

**Step 4: Commit**

```bash
git add src/routes/_layout/room.\$roomId.tsx src/routes/_layout/room-v2.\$roomId.tsx
git commit -m "feat(routes): redirect legacy room routes to /r/:id"
```

---

## Task 7: Remove Switch View from Unified Route

**Files:**
- Modify: `src/routes/_layout/r.$roomId.tsx`

**Step 1: Remove handleSwitchView and related props**

Remove from `r.$roomId.tsx`:

1. Remove the `handleSwitchView` function (around line 227-229)
2. Remove `onSwitchView={handleSwitchView}` prop from RoomShell
3. Remove `switchViewLabel="Switch to Classic View"` prop from RoomShell

**Step 2: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 3: Commit**

```bash
git add src/routes/_layout/r.\$roomId.tsx
git commit -m "refactor(room): remove legacy view switcher"
```

---

## Task 8: Update RoomShell to Remove switchView Props

**Files:**
- Modify: `src/components/Room/RoomShell.tsx`
- Modify: `src/components/Room/RoomHeader.tsx`

**Step 1: Remove switchView props from RoomShell interface and component**

In `RoomShell.tsx`, remove:
- `onSwitchView` prop
- `switchViewLabel` prop
- Pass-through to RoomHeader

**Step 2: Remove from RoomHeader**

In `RoomHeader.tsx`, remove:
- `onSwitchView` prop
- `switchViewLabel` prop
- The switch view dropdown menu item

**Step 3: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 4: Commit**

```bash
git add src/components/Room/RoomShell.tsx src/components/Room/RoomHeader.tsx
git commit -m "refactor(room): remove legacy view switch from shell/header"
```

---

## Task 9: Update Internal Links

**Files:**
- Search and replace across codebase

**Step 1: Find all references to legacy routes**

```bash
cd /home/josep/dog/frontend && grep -r '"/room/' src/ --include="*.tsx" --include="*.ts" | grep -v "room-v2" | grep -v node_modules
cd /home/josep/dog/frontend && grep -r '"/room-v2/' src/ --include="*.tsx" --include="*.ts" | grep -v node_modules
```

**Step 2: Update any found references to use /r/ instead**

For each file found, update the route path from `/room/` or `/room-v2/` to `/r/`.

**Step 3: Verify no broken links**

```bash
cd /home/josep/dog/frontend && npm run build
```

**Step 4: Commit**

```bash
git add -A
git commit -m "refactor: update internal links to unified room route"
```

---

## Task 10: Final Verification

**Step 1: Run full build**

```bash
cd /home/josep/dog/frontend && npm run build
```

Expected: Build succeeds

**Step 2: Run lint**

```bash
cd /home/josep/dog/frontend && npm run lint
```

Expected: No errors in modified files

**Step 3: Manual test checklist**

```markdown
- [ ] Navigate to /r/:roomId - room loads with default layout
- [ ] Navigate to /room/:roomId - redirects to /r/:roomId
- [ ] Navigate to /room-v2/:roomId - redirects to /r/:roomId
- [ ] Open Panel Layout dialog - "Classic" preset available
- [ ] Select Classic preset - shows chat + participants sidebar
- [ ] Select Collaborate preset - shows chat + agents sidebar
- [ ] Participants panel shows users and agents
- [ ] Can toggle/remove agents in participants panel (as owner)
```

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete room route consolidation"
```

---

## Summary

After completing all tasks:

| Before | After |
|--------|-------|
| `/room/:id` (V1) | Redirects to `/r/:id` |
| `/room-v2/:id` (V2) | Redirects to `/r/:id` |
| `/r/:id` (V3) | Unified route with presets |

| Preset | Replicates |
|--------|------------|
| `classic` | V1 layout (chat + participants) |
| `collaborate` | V2 layout (chat + agents) |
| `focus` | Minimal (chat only) |

**Files deleted:** None (routes now contain only redirects, can be deleted in future cleanup)

**New files:**
- `src/components/Room/panels/ParticipantPanel.tsx`

**Modified files:**
- `src/routes/_layout/room.$roomId.tsx` (replaced with redirect)
- `src/routes/_layout/room-v2.$roomId.tsx` (replaced with redirect)
- `src/routes/_layout/r.$roomId.tsx` (added participantPanel, removed switchView)
- `src/services/panelService.ts` (added participantPanel kind)
- `src/components/Room/panels/index.ts` (export ParticipantPanel)
- `src/components/Room/primitives/PresetPicker.tsx` (added classic preset)
- `src/components/Room/RoomShell.tsx` (removed switchView props)
- `src/components/Room/RoomHeader.tsx` (removed switchView props)
- `backend/app/api/routes/presets.py` (added classic preset)
