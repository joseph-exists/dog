# Full-Bleed Layout Pattern

Reference for converting pages to full-bleed layout (page owns its own header).

## The Problem: Stacked Headers

Pages that have their own header component (like `AgentsHeader`) can end up with multiple stacked headers:

1. **Site header** (`_layout.tsx`) - Shows page title from `routeTitles`
2. **Page header** (e.g., `AgentsHeader`) - Shows title + page-specific controls
3. **Panel header** (e.g., `PanelContainer`) - Shows panel title

This creates visual redundancy and wastes vertical space.

## The Solution: Full-Bleed Layout

Full-bleed pages:
- Skip the site header entirely
- Own their own header with all necessary controls
- Include the `SidebarTrigger` so users can still toggle the sidebar

## Step-by-Step: Converting a Page to Full-Bleed

### Step 1: Add route to fullBleedRoutes

**File:** `src/routes/_layout.tsx`

```typescript
const fullBleedRoutes = [
  "/agents",        // ← Add your route here
  "/r/",
  "/room/",
  // ... other routes
]
```

**Note:** Use exact path (`"/agents"`) or prefix (`"/agents/"`) depending on whether child routes should also be full-bleed.

### Step 2: Add SidebarTrigger to your page header

**File:** Your page's header component (e.g., `AgentsHeader.tsx`)

1. Import the required components:

```typescript
import { Separator } from "@/components/ui/separator"
import { SidebarTrigger } from "@/components/ui/sidebar"
```

2. Add to the left side of your header:

```tsx
<div className="flex items-center gap-2">
  <SidebarTrigger className="-ml-1 text-muted-foreground" />
  <Separator orientation="vertical" className="h-4" />
  <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
</div>
```

### Step 3: Verify

1. Rebuild: `npm run build`
2. Restart: `docker compose up frontend --build -d`
3. Check:
   - Site header should NOT appear
   - Your page header should show with SidebarTrigger
   - Sidebar toggle should work

## Example: AgentsHeader

**Before:**
```
┌─────────────────────────────────────────────┐
│ [☰] │ Agents-Alpha                          │  ← Site header
├─────────────────────────────────────────────┤
│ Agents        [themes] [layout] [+create]   │  ← Page header
├─────────────────────────────────────────────┤
│ Agents                                      │  ← Panel header
├─────────────────────────────────────────────┤
│ (content)                                   │
└─────────────────────────────────────────────┘
```

**After:**
```
┌─────────────────────────────────────────────┐
│ [☰] │ Agents   [themes] [layout] [+create]  │  ← Page header (with trigger)
├─────────────────────────────────────────────┤
│ Agents                                      │  ← Panel header
├─────────────────────────────────────────────┤
│ (content)                                   │
└─────────────────────────────────────────────┘
```

## When to Use Full-Bleed

Use full-bleed for pages that:
- Have their own header with page-specific controls
- Need maximum vertical space (dashboards, editors, chat rooms)
- Follow the Shell pattern (like `AgentsShell`, `RoomShell`)

Keep standard layout for pages that:
- Are simple content pages
- Don't have page-specific header controls
- Benefit from the consistent site header

## Files Reference

| File | Purpose |
|------|---------|
| `src/routes/_layout.tsx` | Defines `fullBleedRoutes` array |
| `src/components/ui/sidebar.tsx` | Exports `SidebarTrigger` |
| `src/components/ui/separator.tsx` | Exports `Separator` |

## Troubleshooting

**Header still showing after adding to fullBleedRoutes:**
- Check the route matching logic: `currentPath.startsWith(route)`
- Ensure your route path matches exactly (e.g., `/agents` vs `/agents/`)
- Hard refresh the browser (Ctrl+Shift+R)

**SidebarTrigger not working:**
- Ensure your page is rendered inside `SidebarProvider` (comes from `_layout.tsx`)
- Check that `SidebarTrigger` is imported from `@/components/ui/sidebar`

**Panel header redundant:**
- If single-panel layout, consider removing `title` prop from `PanelContainer`
- For multi-panel layouts, keep panel titles for identification
