# Agents Page: Implementation Plan

> **Location:** `frontend/src/components/Agents/Shell/`  
> **Status:** COMPLETE - LEGACY DOC, NOT REFLECTION OF CURRENT STATE.  IMPLEMENTATION HAS PROGRESSED AND MAY DEVIATE.  THIS IS A HISTORICAL MOMENT IN TIME THAT HAS BEEN PASSED SUCCESSFULLY.
> **Created:** 2025-02-09  

---

## Goal

Build a net-new `agents.tsx` page using the compositional shell+panel pattern 
established by Room. This page proves the ambient theme cascade (page-level 
theme composing with per-card presentation via CSS specificity) and establishes 
the structural pattern for all top-level pages.

---

## Architectural Model

```
agents.tsx (route — orchestrator)
│  Fetches agent data, builds panel registry, manages page-level state
│
└─ AgentsShell
     │  Structural container: header + ambient theme wrapper + layout
     │  Analogous to RoomShell
     │
     ├─ AgentsHeader
     │    Title, theme selector, create agent trigger, layout mode toggle
     │    Analogous to RoomHeader (simplified — no participants)
     │
     └─ Ambient Theme Wrapper (div with CSS variables from selected theme)
          │  This is the KEY new element — proves the cascade
          │  All panels inherit these variables
          │
          └─ AgentsLayout
               │  Resizable panels / tabs, primary + auxiliary
               │  Reuses the same pattern as RoomLayout
               │
               └─ AgentsGridPanel [primary]
                    │  Collection view: agent cards in grid
                    │  Wrapped in PanelContainer
                    │  Cards render with own presentation (overrides ambient)
                    │
                    └─ AgentCard (existing, unmodified)
```

### Why this structure

- **AgentsShell** owns the ambient theme div, ensuring every panel inherits 
  the theme variables. This is the page-level scope from REFERENCE.md.
- **AgentsLayout** handles arrangement (panels/tabs, resize) following 
  RoomLayout's proven pattern.
- **AgentsGridPanel** is a panel — same shape as ChatPanel, ParticipantPanel, 
  etc. Lives inside PanelContainer for consistent header/scroll/footer.
- **AgentCard** is untouched. Its presentation wrapper div sets CSS variables 
  closer to the component, winning over ambient via specificity. This is the 
  proven steel thread.

---

## What Already Exists (DO NOT REWRITE)

### Components — stable, current, tested

| Component | Location | Used as |
|---|---|---|
| `AgentCard` (Full/Compact/Mini) | `Agents/Display/AgentCard.tsx` | Primary display. All three variants. Presentation pipeline proven. |
| `AgentAvatar` | `Agents/Display/AgentAvatar.tsx` | Avatar with presentation support. |
| `AgentBadge` (all variants) | `Agents/Display/AgentBadge.tsx` | Scope, mode, status, coordinator, provider badges. |
| `AgentDetailDialog` | `Agents/Dialogs/AgentDetailDialog.tsx` | Edit dialog for existing agents. |
| `CreateAgentDialog` | `Agents/Dialogs/CreateAgentDialog.tsx` | Simple create dialog (AgentForm). |
| `CreateAgentusDialog` | `Agents/Dialogs/CreateAgentusDialog.tsx` | Wizard create dialog (AgentusFormulaicus). |
| `AgentCloneButton` | `Agents/Dialogs/AgentCloneButton.tsx` | Clone action for system agents. |

CHANGED: moved PanelContainer into Page/primitives/PanelContainer.tsx - set that as the import.
| `PanelContainer` | `Room/primitives/PanelContainer.tsx` | Standard panel wrapper. General-purpose but lives in Room. |

### Types, utilities, resolution — stable, current

| Module | Location | Notes |
|---|---|---|
| Types | `Agents/types.ts` | `UserAgentConfigData`, `AgentPresentation`, `PresentationTokens`, type guards. |
| Resolution | `Agents/resolve.ts` | `resolveAgentPresentation`, `presentationToStyle`, `AGENT_TYPE_PRESENTATIONS`. |
| Utils | `Agents/utils.ts` | Avatar colors, initials, hashing, `sparseAgentUpdate`. |
| Hooks | `Agents/hooks.ts` | `useProviderTypeName` — used by AgentCard and badges. |

### Data layer — stable, current

| What | How |
|---|---|
| List agents | `AgentsService.listAgents()` → `UserAgentConfigPublic[]` |
| Get single agent | `AgentsService.getAgent({ agentId })` |
| Create agent | `AgentsService.createAgent({ requestBody })` |
| Delete agent | `AgentsService.deleteAgent({ agentId })` |
| Generate slug | `AgentsService.generateAgentSlug()` |
| Query key | `["agents"]` for list, `["agent", agentId]` for single |

### Patterns to follow (from Room)

| Pattern | Source | Adapt for |
|---|---|---|
| Shell structure | `Room/RoomShell.tsx` | `AgentsShell` |
| Layout (panels/tabs, resize) | `Room/RoomLayout.tsx` | `AgentsLayout` |
| Panel config shape | `RoomLayout.PanelConfig` | Same interface |
| Panel component registry | `r.$roomId.tsx` (panelComponents record) | `agents.tsx` route |
| PanelContainer usage | `Room/panels/ParticipantPanel.tsx` | `AgentsGridPanel` |

---

## What We Build New

### 1. `Agents/Shell/themes.ts` — Stub theme data

Typed interface matching future API shape. Importable, not inline.

```typescript
export interface AmbientTheme {
  id: string
  name: string
  style: React.CSSProperties  // the full variable surface from REFERENCE.md
}

export const AMBIENT_THEMES: AmbientTheme[] = [
  { id: "default", name: "Default", style: {} },
  { id: "midnight", name: "Midnight", style: { /* full surface */ } },
  // 2-3 more themes with complete variable surfaces
]
```

**Critical:** Every theme that changes surface lightness MUST include the 
full variable set per REFERENCE.md. The "default" theme is empty (defers 
to `:root`). All others must be complete.

**Migration path:** When API endpoint exists, replace the static array with 
a query. Interface stays the same. Components don't change.

### 2. `Agents/Shell/AgentsLayout.tsx` — Panel arrangement

Follows RoomLayout's implementation. Resizable panels, tabs mode, 
primary/auxiliary split. Mobile → tabs.

Uses same `PanelConfig` interface shape.

**NOT imported from Room** (avoids coupling). Independent implementation 
following the same pattern. If convergence happens later, extract to shared.

### 3. `Agents/Shell/panels/AgentsGridPanel.tsx` — Collection view

The primary panel. Migrates working logic from current `agents.tsx`:
- `getAgentsQueryOptions()` query factory
- Personal/system agent split
- Grid of `AgentCard` (full variant)
- `DeleteAgentButton` with confirmation
- Loading skeletons, empty state

Wrapped in `PanelContainer`. Panel owns its own data query.

### 4. `Agents/Shell/AgentsHeader.tsx` — Page header

Title, theme selector, create agent triggers, layout mode toggle.

**Theme selector:** Dropdown or toggle group reading from `AMBIENT_THEMES`. 
Does not own state — receives `selectedThemeId` and `onThemeChange` from shell.

**Create actions:** Both `CreateAgentDialog` and `CreateAgentusDialog` 
accessible from header. Clearer UX distinction than current side-by-side.

### 5. `Agents/Shell/AgentsShell.tsx` — Structural container

Composes: AgentsHeader → ambient theme wrapper div → AgentsLayout.

```typescript
interface AgentsShellProps {
  title: string
  panels: PanelConfig[]
  ambientTheme?: AmbientTheme | null
  selectedThemeId: string
  onThemeChange: (themeId: string) => void
  className?: string
}
```

The ambient theme wrapper is the architectural centerpiece:
```tsx
<div style={ambientTheme?.style} className="flex-1 min-h-0">
  <AgentsLayout panels={panels} mode={layoutMode} />
</div>
```

### 6. Updated `agents.tsx` route — Orchestrator

Rewired following `r.$roomId.tsx` pattern:
- Theme selection state (local `useState`, future: persisted preference)
- Panel component registry (`Record<string, () => ReactNode>`)
- Panel configs (static for now, future: backend-driven with resolution)
- Passes everything to AgentsShell

---

## What We Migrate (move logic, don't rewrite)

From current `agents.tsx` → `AgentsGridPanel`:

| What | Treatment |
|---|---|
| `getAgentsQueryOptions()` | Move as-is |
| `AgentCardSkeleton` / `PendingAgents` | Move as-is |
| `DeleteAgentButton` | Move as-is |
| `AgentCardItem` | Move, adjust to work within PanelContainer |
| `AgentsListContent` | Move grid rendering logic |

These are working code with correct query/mutation patterns. Container 
wrapping changes (PanelContainer), grid structure preserved.

---

## What We Do NOT Build Yet

| Deferred | Reason |
|---|---|
| Backend panel config for pages | Room has `useRoomPanels`. Pages need equivalent. Start with static config. |
| User-saved named page configurations | Requires persistence. Prove structure first. |
| Individual agent pages (`agent.$agentId.tsx`) | Separate build. Current page works. |
| Compact/Mini card usage on this page | No UI need yet. Components are ready when needed. |
| Presentation editing forms | Separate feature track. |
| Ambient theme persistence to DB | Model designed, waiting on this implementation to validate. |
| Additional panels (detail, activity, etc.) | Structure supports them. Build when needed. |

---

## Cascade Proof: What Success Looks Like

After this build, we can demonstrate:

1. **No ambient theme (default):** Cards render with own presentation or type 
   defaults. Visually identical to today but in new shell structure.

2. **Ambient theme active:** Page surface shifts. Cards WITHOUT instance 
   presentation inherit ambient. Cards WITH presentation retain identity.

3. **Theme switching:** Ambient changes, presentated cards hold steady, 
   unpresentated cards adapt. No invisible text anywhere.

4. **Variable surface completeness:** Every theme includes full set. All badge 
   variants (outline → `--foreground`, secondary → `--secondary`, etc.) remain 
   visible across all theme combinations.

---

## Contracts to Preserve

| Contract | Used by | Rule |
|---|---|---|
| `AgentCard` props | Room ParticipantPanel, other consumers | Don't change interface. |
| `AgentsService.*` query patterns | Current agents.tsx, agent.$agentId.tsx | Same service calls. |
| `["agents"]` query key | Create/delete dialogs invalidate this | Must remain the list cache key. |
| Route path `/_layout/agents` | Navigation, breadcrumbs | Route stays at same path. |
| `UserAgentConfigPublic` type | Generated from backend | Don't wrap or transform. |
| `AgentPresentation` / `PresentationTokens` | AgentCard, resolve.ts | Don't change. |

---

## Risks and Watchpoints

1. **RoomLayout coupling.** Don't import RoomLayout. Follow its pattern 
   independently. Future extraction to shared primitive is fine; premature 
   coupling is not.

2. **Theme variable completeness.** Every stub theme MUST include the full 
   variable surface. Partial themes = invisible text. Test visually with 
   every badge variant.

3. **PanelContainer import path.** Currently `Room/primitives/PanelContainer.tsx`. 
   General-purpose component in Room-specific location. Import from there for 
   now. Flag for future extraction.

4. **Create dialog consolidation.** Current page has two create buttons 
   side-by-side. New header should present these with clearer distinction. 
   Don't remove either — both forms serve different UX needs.

5. **Query ownership.** AgentsGridPanel owns the data query (useSuspenseQuery). 
   Route does NOT pre-fetch and pass down. Matches Room panel pattern. 
   Exception: theme state lives in route/shell (affects ambient wrapper above 
   all panels).

---

## Implementation Order

### Phase 1: Structure (no visual change yet)

1. `Shell/themes.ts` — typed interface + stub data
2. `Shell/AgentsLayout.tsx` — panel arrangement
3. `Shell/panels/AgentsGridPanel.tsx` — migrate listing logic
4. `Shell/AgentsHeader.tsx` — header with theme selector, create actions
5. `Shell/AgentsShell.tsx` — compose header + ambient + layout
6. `Shell/index.ts` — barrel exports

### Phase 2: Wire the route

7. Rewrite `agents.tsx` as orchestrator

**Checkpoint:** Page looks and functions identically to current. New structure, 
no visible change. Default theme = empty = :root.

### Phase 3: Prove the cascade

8. Add 3-4 complete stub themes
9. Wire theme selector → ambient wrapper
10. Visual testing: cards with/without presentation × all themes

**Checkpoint:** Cascade proven. Evidence collected.

### Phase 4: Polish

11. Layout mode toggle (panels/tabs)
12. Loading/error/empty states in panel
13. Responsive (mobile → tabs)

---

## File Structure

```
src/components/Agents/
├── Shell/
│   ├── index.ts
│   ├── IMPLEMENTATION-PLAN.md      ← this document
│   ├── AgentsShell.tsx
│   ├── AgentsHeader.tsx
│   ├── AgentsLayout.tsx
│   ├── themes.ts
│   └── panels/
│       ├── index.ts
│       └── AgentsGridPanel.tsx
│
├── Display/                        ← UNCHANGED
├── Dialogs/                        ← UNCHANGED
├── Forms/                          ← UNCHANGED
├── RoomManagers/                   ← UNCHANGED
├── Presentation/                   ← UNCHANGED (reference docs)
├── types.ts                        ← UNCHANGED
├── resolve.ts                      ← UNCHANGED
├── hooks.ts                        ← UNCHANGED
└── utils.ts                        ← UNCHANGED
```
