# Composable Sidebar Design

**Date:** 2026-02-11
**Status:** Ready for implementation

## Overview

Migrate from `@/components/Sidebar/AppSidebar` to a composable, well-documented sidebar system in `@/components/Common/Sidebar/`. The new design follows the Page/Agents shell pattern with a centralized navigation registry.

## Goals

1. **Composable** - Clear separation: Shell orchestrates, Layout composes, Nav components render
2. **Discoverable** - Inline documentation explaining how to add/remove/edit navigation
3. **Context-aware** - Secondary nav sections appear based on current route
4. **Auth-integrated** - Real user data, logout functionality, dynamic items

## MVP Proof of Concept

- **Main nav:** Dashboard, Stories, Rooms, Agents, Personas, Items, My Page, Admin
- **Secondary nav:** Archetypes, Qualities, Traits (visible only in Personas context)

This proves contextual navigation works and the pattern can extend to other domains.

## File Structure

```
src/components/Common/Sidebar/
├── AppSidebar.tsx      # Shell + Registry
├── SidebarLayout.tsx   # Composes sections into zones
├── NavMain.tsx         # Nav items with router integration
├── NavUser.tsx         # User menu with auth
├── types.ts            # NavItem, NavSection, SidebarUser
└── index.ts            # Public exports
```

## Type Definitions

```typescript
// types.ts

import type { LucideIcon } from "lucide-react"

export interface NavItem {
  id: string
  title: string
  path: string
  icon: LucideIcon
  badge?: string
}

export interface NavSection {
  id: string
  label?: string
  items: NavItem[]
  variant: "main" | "secondary" | "footer"
}

export interface SidebarUser {
  id: string
  fullName: string
  email: string
  avatarUrl?: string
  isSuperuser?: boolean
}
```

## Architecture

### Data Flow

```
useAuth() + useRouterState()
        ↓
   AppSidebar (Shell)
        ↓
   buildSections(currentPath, userId, isSuperuser)
        ↓
   NavSection[]
        ↓
   SidebarLayout
        ↓
   NavMain (per section) + NavUser
```

### Centralized Registry Pattern

All navigation configuration lives in `AppSidebar.tsx`:

1. `MAIN_NAV_ITEMS` - Always visible core features
2. `PERSONA_NAV_ITEMS` - Contextual persona tools
3. `buildUserItems()` - Dynamic items based on auth
4. `buildSections()` - Registry that computes sections from route

### Visibility Rules

| Section | Visible When |
|---------|--------------|
| Main | Always |
| Persona Tools | Path matches `/personas`, `/archetypes`, `/qualities`, `/traits` |
| User items (My Page) | User is authenticated |
| Admin | User is superuser |

## Component Responsibilities

| Component | Does | Does Not |
|-----------|------|----------|
| `AppSidebar` | Owns config, reads route/auth, computes sections | Render nav items directly |
| `SidebarLayout` | Arranges sections into Header/Content/Footer | Know about routes or auth |
| `NavMain` | Renders items with RouterLink, handles active state | Decide which items to show |
| `NavUser` | Renders user menu, calls onLogout | Manage auth state |

## Implementation Tasks

1. Create `src/components/Common/Sidebar/` directory
2. Create `types.ts` with type definitions
3. Create `NavMain.tsx` - port from old Main.tsx with section support
4. Create `NavUser.tsx` - merge old User.tsx with new structure
5. Create `SidebarLayout.tsx` - section composer
6. Create `AppSidebar.tsx` - shell with registry
7. Create `index.ts` - exports
8. Update `_layout.tsx` to import from new location
9. Verify: main nav works, active states work, mobile works
10. Verify: navigate to /personas, confirm secondary nav appears
11. Remove old `@/components/Sidebar/` after validation

## Integration Point

Update `src/routes/_layout.tsx`:

```typescript
// Before
import AppSidebar from "@/components/Sidebar/AppSidebar"

// After
import { AppSidebar } from "@/components/Common/Sidebar"
```

## Future Extensions

To add contextual nav for a new domain (e.g., Agents):

1. Define `AGENTS_NAV_ITEMS: NavItem[]` in AppSidebar.tsx
2. Add route check in `buildSections()`:
   ```typescript
   const isAgentsContext = currentPath.startsWith("/agents")
   if (isAgentsContext) {
     sections.push({
       id: "agent-tools",
       label: "Agent Tools",
       items: AGENTS_NAV_ITEMS,
       variant: "secondary",
     })
   }
   ```
3. Import any new icons

## Design Decisions

1. **Centralized registry over domain-injected** - Simpler, single file to edit, matches MVP scope
2. **`path` not `url`** - Signals TanStack Router integration
3. **`SidebarUser` separate from auth user** - Decouples from backend model shape
4. **`onLogout` as prop** - Shell doesn't own auth, receives callback
5. **`variant` on sections** - Enables layout to style main vs secondary differently
