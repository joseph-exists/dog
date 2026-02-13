# Panel Registry Refactor Design

**Goal:** Extract hardcoded panel definitions from PanelLayoutDialog into a universal registry, and generalize panelService.ts to work across entity types.

**Approach:** Single source of truth in `Page/registry/panelTypes.ts` with rich metadata (permissions, dependencies, cardinality, relational flags).

---

## File Changes

### 1. Create: `frontend/src/components/Page/registry/panelTypes.ts`

New registry file with:
- Type definitions (PanelKind, PanelPermission, EntityCardinality, etc.)
- Panel definitions organized by context (Room, Story, Universal)
- Helper functions for filtering and lookup

### 2. Update: `frontend/src/components/Page/registry/index.ts`

Add exports for all panelTypes exports.

### 3. Update: `frontend/src/components/Page/Dialogs/PanelLayoutDialog.tsx`

- Remove hardcoded `AVAILABLE_PANELS` and `panelNames`
- Import from registry
- Add new props: `context`, `userPermission`, `isAdmin`
- Rename `roomId` → `entityId`, `isRoomOwner` → `isOwner`
- Derive available panels via `useMemo` using registry functions

### 4. Update: `frontend/src/services/panelService.ts`

- Import types from registry (remove local PanelKind definition)
- Generalize functions to accept `entityType` parameter
- Route to appropriate backend service based on entity type
- Re-export helper functions from registry

---

## Type Definitions

```typescript
export type PanelKind =
  | "chat" | "canvas" | "a2ui" | "participantPanel" | "debug"
  | "storyEditor" | "storyRuntime" | "storyPlayer" | "storyDebug"

export type PanelProminence = "primary" | "auxiliary"
export type PanelContext = "room" | "story" | "universal"
export type PanelPermission = "none" | "participant" | "owner" | "admin"
export type EntityCardinality = "single" | "collection" | "either"

export interface PanelTypeDefinition {
  kind: PanelKind
  label: string
  description: string
  icon: LucideIcon
  defaultProminence: PanelProminence
  contexts: PanelContext[]
  permission?: PanelPermission
  dependencies?: PanelKind[]
  cardinality?: EntityCardinality
  relational?: boolean
}
```

---

## Panel Definitions

### Room Panels
| Kind | Label | Permission | Cardinality | Notes |
|------|-------|------------|-------------|-------|
| chat | Chat | participant | single | |
| canvas | Canvas | participant | single | |
| a2ui | Agent UI | participant | single | |
| participantPanel | Participants | participant | single | relational: true |

### Story Panels
| Kind | Label | Permission | Dependencies | Notes |
|------|-------|------------|--------------|-------|
| storyEditor | Story Editor | owner | - | contexts: room, story |
| storyRuntime | Story Runtime | participant | storyEditor | |
| storyPlayer | Story Player | none | - | Anyone can play published |
| storyDebug | Story Debug | owner | storyPlayer | |

### Universal Panels
| Kind | Label | Permission | Notes |
|------|-------|------------|-------|
| debug | Debug | admin | Dev/admin only |

---

## Helper Functions

```typescript
getPanelType(kind: PanelKind): PanelTypeDefinition | undefined
getPanelDisplayName(kind: PanelKind): string
getPanelsForContext(context: PanelContext): PanelTypeDefinition[]
getPanelsForEntityPermission(level: PanelPermission): PanelTypeDefinition[]
getPanelsForSystemRole(role: "user" | "admin"): PanelTypeDefinition[]
isValidPanelKind(kind: string): kind is PanelKind
getDefaultPanelConfig(kind: PanelKind): { id, kind, prominence } | undefined
getPanelDependents(kind: PanelKind): PanelTypeDefinition[]
areDependenciesSatisfied(kind: PanelKind, activePanels: PanelKind[]): boolean
```

---

## Updated PanelLayoutDialog Props

```typescript
export interface PanelLayoutDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  entityId: string | null        // was: roomId
  isOwner?: boolean              // was: isRoomOwner
  mode?: "entity" | "user-defaults"  // was: "room" | "user-defaults"
  context: PanelContext          // NEW
  userPermission?: PanelPermission   // NEW
  isAdmin?: boolean              // NEW
}
```

---

## Updated panelService Interface

```typescript
// Generalized to accept entityType
getResolvedPanels(entityType: "room" | "story", entityId: string): Promise<ResolvedPanels>
updateMyPanelConfig(entityType: "room" | "story", entityId: string, panels, useDefaults): Promise<void>

// Re-exported from registry
isValidPanelKind, getPanelDisplayName
```

---

## Implementation Order

1. Create `panelTypes.ts` with types, definitions, helpers
2. Update `registry/index.ts` with exports
3. Update `panelService.ts` to import from registry
4. Update `PanelLayoutDialog.tsx` to use registry
5. Verify TypeScript compilation
6. Test in browser
