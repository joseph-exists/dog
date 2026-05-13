# Workspaces Paradigm Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate the Workspaces page shell/layout/header to match the established Agents paradigm — `ResizablePanelGroup` + tabs fallback, `layoutMode` state in shell, `SidebarTrigger` in header.

**Architecture:** Three coordinated file changes with no backend involvement. `WorkspacesLayout` swaps CSS grid for `ResizablePanelGroup` (desktop) and `Tabs` (mobile/tabs mode). `WorkspacesShell` gains `layoutMode` state and removes the misplaced `overflow-y-auto` scroll. `WorkspacesHeader` gains `SidebarTrigger`, a panels/tabs toggle, and JSDoc. The route (`workspace.$workspaceId.tsx`) is unchanged.

**Tech Stack:** React, TypeScript, Tailwind, shadcn (`@/components/ui/resizable`, `@/components/ui/tabs`, `@/components/ui/toggle-group`, `@/components/ui/sidebar`), `useIsMobile` hook, lucide-react.

**Reference implementation:** `frontend/src/components/Agents/AgentsLayout.tsx`, `AgentsShell.tsx`, `AgentsHeader.tsx`

---

## Context: What the paradigm looks like

The Agents pattern defines three clear layers:

1. **Shell** — owns `layoutMode` state, applies theme CSS variables, passes mode down to header + layout
2. **Header** — renders `SidebarTrigger`, layout toggle (panels/tabs), theme pickers, actions
3. **Layout** — `ResizablePanelGroup` on desktop, `Tabs` on mobile (via `useIsMobile`) or when `mode === "tabs"`

The current Workspaces constructs diverge at the Layout level (CSS grid, no resize) and at the Shell level (scroll at wrong layer). The Header is missing sidebar integration.

---

## Task 1: Replace WorkspacesLayout with ResizablePanelGroup pattern

**Files:**
- Modify: `frontend/src/components/Workspaces/WorkspacesLayout.tsx`

**What changes:**
- Add `mode: "panels" | "tabs"` prop to `WorkspacesLayoutProps`
- Import `ResizablePanelGroup`, `ResizablePanel`, `ResizableHandle` from `@/components/ui/resizable`
- Import `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent` from `@/components/ui/tabs`
- Import `useIsMobile` from `@/hooks/use-mobile`
- Desktop panels mode: horizontal `ResizablePanelGroup`, primary panels left, auxiliary column right with a scrollable `div` inside it
- Mobile / tabs mode: flat `Tabs` with all panels as `TabsContent`

**Step 1: Write the new file**

Replace `WorkspacesLayout.tsx` entirely:

```tsx
import * as React from "react"
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useIsMobile } from "@/hooks/use-mobile"
import { cn } from "@/lib/utils"

export interface PanelConfig {
  id: string
  kind: string
  prominence: "primary" | "auxiliary"
  title: string
  render: () => React.ReactNode
}

export interface WorkspacesLayoutProps {
  panels: PanelConfig[]
  mode: "panels" | "tabs"
  className?: string
}

export function WorkspacesLayout({
  panels,
  mode,
  className,
}: WorkspacesLayoutProps) {
  const isMobile = useIsMobile()
  const primaryPanels = panels.filter((p) => p.prominence === "primary")
  const auxiliaryPanels = panels.filter((p) => p.prominence === "auxiliary")

  // Mobile always forces tabs
  const effectiveMode = isMobile ? "tabs" : mode

  if (effectiveMode === "tabs") {
    return (
      <Tabs
        defaultValue={panels[0]?.id}
        className={cn("flex flex-col h-full", className)}
      >
        <TabsList className="w-full justify-start rounded-none border-b bg-transparent h-auto p-0">
          {panels.map((panel) => (
            <TabsTrigger
              key={panel.id}
              value={panel.id}
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-2"
            >
              {panel.title}
            </TabsTrigger>
          ))}
        </TabsList>
        {panels.map((panel) => (
          <TabsContent
            key={panel.id}
            value={panel.id}
            className="flex-1 mt-0 overflow-hidden"
          >
            {panel.render()}
          </TabsContent>
        ))}
      </Tabs>
    )
  }

  // Desktop panels mode
  return (
    <ResizablePanelGroup
      direction="horizontal"
      className={cn("h-full", className)}
    >
      {/* Primary panels */}
      {primaryPanels.map((panel, index) => (
        <React.Fragment key={panel.id}>
          {index > 0 && <ResizableHandle withHandle />}
          <ResizablePanel minSize={20}>{panel.render()}</ResizablePanel>
        </React.Fragment>
      ))}

      {/* Auxiliary panels — scrollable column of stacked cards */}
      {auxiliaryPanels.length > 0 && (
        <>
          <ResizableHandle withHandle />
          <ResizablePanel defaultSize={35} minSize={20}>
            <div className="h-full overflow-y-auto p-4 space-y-4">
              {auxiliaryPanels.map((panel) => (
                <React.Fragment key={panel.id}>
                  {panel.render()}
                </React.Fragment>
              ))}
            </div>
          </ResizablePanel>
        </>
      )}
    </ResizablePanelGroup>
  )
}
```

**Design note — auxiliary column:** Workspaces auxiliary panels are collapsible cards (not side-by-side panels like Agents). They belong in a single scrollable `ResizablePanel` column, not a nested `ResizablePanelGroup`. The `p-4 space-y-4` inside the column replaces the scroll padding that was previously on the shell.

**Step 2: Verify it compiles**

```bash
cd frontend && npm run build 2>&1 | head -40
```

Expected: no TypeScript errors in `WorkspacesLayout.tsx`. (Will fail downstream in Shell since `mode` prop is not yet passed — that's expected at this stage.)

**Step 3: Commit**

```bash
git add frontend/src/components/Workspaces/WorkspacesLayout.tsx
git commit -m "refactor(workspaces): replace CSS grid layout with ResizablePanelGroup + tabs"
```

---

## Task 2: Fix WorkspacesShell — add layoutMode state, fix scroll layer

**Files:**
- Modify: `frontend/src/components/Workspaces/WorkspacesShell.tsx`

**What changes:**
- Import `React.useState`
- Add `layoutMode` state (`"panels" | "tabs"`, default `"panels"`)
- Pass `layoutMode` + `onLayoutModeChange` to `WorkspacesHeader`
- Pass `mode={layoutMode}` to `WorkspacesLayout`
- Remove `overflow-y-auto p-4 md:p-6` from the cards wrapper div — the `WorkspacesLayout` now handles its own scroll/padding
- Remove `min-h-0` from outer shell div (not needed with the new layout)

**Step 1: Write the updated file**

Replace `WorkspacesShell.tsx` entirely:

```tsx
/**
 * WorkspacesShell
 *
 * Structural container for the workspace detail page.
 * Composes: Page theme wrapper → WorkspacesHeader → Cards theme wrapper → WorkspacesLayout.
 *
 * Two nested theme wrappers enable the 4-layer cascade:
 *   Application (:root) → Page theme → Cards theme → Individual card presentation
 *
 * layoutMode state lives here so both the header toggle and layout renderer
 * stay in sync without prop-drilling through an intermediate component.
 */

import * as React from "react"
import { cn } from "@/lib/utils"
import {
  type ThemeViewModel,
  themeTokensToStyle,
} from "@/services/themeService"
import { WorkspacesHeader } from "./WorkspacesHeader"
import { type PanelConfig, WorkspacesLayout } from "./WorkspacesLayout"

export interface WorkspacesShellProps {
  title: string
  description: string
  panels: PanelConfig[]
  pageTheme: ThemeViewModel | null
  cardsTheme: ThemeViewModel | null
  availablePageThemes: ThemeViewModel[]
  availableCardThemes: ThemeViewModel[]
  onPageThemeChange: (themeId: string) => void
  onCardsThemeChange: (themeId: string) => void
  backHref?: string
  className?: string
}

export function WorkspacesShell({
  title,
  description,
  panels,
  pageTheme,
  cardsTheme,
  availablePageThemes,
  availableCardThemes,
  onPageThemeChange,
  onCardsThemeChange,
  backHref,
  className,
}: WorkspacesShellProps) {
  const [layoutMode, setLayoutMode] = React.useState<"panels" | "tabs">(
    "panels",
  )

  const pageThemeStyle = themeTokensToStyle(pageTheme?.tokens)
  const cardsThemeStyle = themeTokensToStyle(cardsTheme?.tokens)

  return (
    // Outermost: Page theme scope (affects header + content)
    // Transparent wrapper — only sets CSS variables, does not render a surface
    <div
      style={pageThemeStyle}
      className={cn("flex h-full flex-col", className)}
    >
      <WorkspacesHeader
        title={title}
        description={description}
        pageTheme={pageTheme}
        cardsTheme={cardsTheme}
        availablePageThemes={availablePageThemes}
        availableCardThemes={availableCardThemes}
        onPageThemeChange={onPageThemeChange}
        onCardsThemeChange={onCardsThemeChange}
        backHref={backHref}
        layoutMode={layoutMode}
        onLayoutModeChange={setLayoutMode}
      />

      {/* Inner: Cards theme scope (overrides page theme for card areas) */}
      {/* Transparent wrapper — only sets CSS variables, does not render a surface */}
      <div style={cardsThemeStyle} className="flex-1 min-h-0">
        <WorkspacesLayout panels={panels} mode={layoutMode} />
      </div>
    </div>
  )
}
```

**Step 2: Verify TypeScript**

```bash
cd frontend && npm run build 2>&1 | head -40
```

Expected: errors in `WorkspacesHeader` only (new props not yet accepted). No errors in `WorkspacesShell` or `WorkspacesLayout`.

**Step 3: Commit**

```bash
git add frontend/src/components/Workspaces/WorkspacesShell.tsx
git commit -m "refactor(workspaces): add layoutMode state to shell, fix scroll layer"
```

---

## Task 3: Update WorkspacesHeader — add SidebarTrigger, layout toggle, JSDoc

**Files:**
- Modify: `frontend/src/components/Workspaces/WorkspacesHeader.tsx`

**What changes:**
- Add JSDoc comment block
- Add `layoutMode: "panels" | "tabs"` and `onLayoutModeChange` props
- Import `SidebarTrigger` from `@/components/ui/sidebar`
- Import `Separator` from `@/components/ui/separator`
- Import `ToggleGroup`, `ToggleGroupItem` from `@/components/ui/toggle-group`
- Import `Layout`, `LayoutList` from `lucide-react` (panels / tabs icons)
- Add `SidebarTrigger` + `Separator` to the left side of the header (same pattern as `AgentsHeader`)
- Add `ToggleGroup` for panels/tabs toggle in the right controls area

**Step 1: Write the updated file**

Replace `WorkspacesHeader.tsx` entirely:

```tsx
/**
 * WorkspacesHeader
 *
 * Page header for the workspace detail view. Contains:
 * - Sidebar trigger + separator (standard app nav integration)
 * - Back navigation (when backHref is provided)
 * - Workspace title and description
 * - Layout mode toggle (panels / tabs)
 * - Page theme selector
 * - Cards theme selector
 */

import { Link } from "@tanstack/react-router"
import { ArrowLeft, Cpu, Layout, LayoutList } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import type { ThemeViewModel } from "@/services/themeService"

export interface WorkspacesHeaderProps {
  title: string
  description: string
  pageTheme: ThemeViewModel | null
  cardsTheme: ThemeViewModel | null
  availablePageThemes: ThemeViewModel[]
  availableCardThemes: ThemeViewModel[]
  onPageThemeChange: (themeId: string) => void
  onCardsThemeChange: (themeId: string) => void
  backHref?: string
  layoutMode: "panels" | "tabs"
  onLayoutModeChange: (mode: "panels" | "tabs") => void
}

export function WorkspacesHeader({
  title,
  description,
  pageTheme,
  cardsTheme,
  availablePageThemes,
  availableCardThemes,
  onPageThemeChange,
  onCardsThemeChange,
  backHref,
  layoutMode,
  onLayoutModeChange,
}: WorkspacesHeaderProps) {
  return (
    <div className="shrink-0 border-b bg-background/80 backdrop-blur">
      {/* Top bar: sidebar trigger + separator (standard app chrome) */}
      <div className="flex h-12 items-center gap-2 px-4">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="h-4" />
        {backHref ? (
          <Button asChild variant="ghost" size="sm" className="-ml-1">
            <Link to={backHref}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Workspaces
            </Link>
          </Button>
        ) : null}
      </div>

      {/* Main header row: title + controls */}
      <div className="flex flex-col gap-4 px-4 pb-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-xl border bg-card p-2.5">
            <Cpu className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
            <p className="text-sm text-muted-foreground">{description}</p>
          </div>
        </div>

        <div className="flex flex-wrap items-end gap-4">
          {/* Layout mode toggle */}
          <TooltipProvider>
            <ToggleGroup
              type="single"
              value={layoutMode}
              onValueChange={(value) => {
                if (value) onLayoutModeChange(value as "panels" | "tabs")
              }}
              className="border rounded-md"
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <ToggleGroupItem value="panels" aria-label="Panels layout">
                    <Layout className="h-4 w-4" />
                  </ToggleGroupItem>
                </TooltipTrigger>
                <TooltipContent>Panels</TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <ToggleGroupItem value="tabs" aria-label="Tabs layout">
                    <LayoutList className="h-4 w-4" />
                  </ToggleGroupItem>
                </TooltipTrigger>
                <TooltipContent>Tabs</TooltipContent>
              </Tooltip>
            </ToggleGroup>
          </TooltipProvider>

          {/* Theme selectors */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <div className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
                Page Theme
              </div>
              <Select
                value={pageTheme?.id ?? ""}
                onValueChange={onPageThemeChange}
              >
                <SelectTrigger className="min-w-44">
                  <SelectValue placeholder="Select page theme" />
                </SelectTrigger>
                <SelectContent>
                  {availablePageThemes.map((theme) => (
                    <SelectItem key={theme.id} value={theme.id}>
                      {theme.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <div className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
                Cards Theme
              </div>
              <Select
                value={cardsTheme?.id ?? ""}
                onValueChange={onCardsThemeChange}
              >
                <SelectTrigger className="min-w-44">
                  <SelectValue placeholder="Select cards theme" />
                </SelectTrigger>
                <SelectContent>
                  {availableCardThemes.map((theme) => (
                    <SelectItem key={theme.id} value={theme.id}>
                      {theme.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
```

**Step 2: Verify the full build**

```bash
cd frontend && npm run build 2>&1 | head -60
```

Expected: clean compile, no TypeScript errors. If Biome lint errors appear, run:

```bash
cd frontend && npm run lint -- --write
```

**Step 3: Verify in dev server**

```bash
cd frontend && npm run dev
```

Navigate to a workspace detail page (`/workspace/<id>`). Verify:
- Sidebar trigger appears and toggles the app sidebar
- "Back to Workspaces" link appears
- Panels/tabs toggle appears and switches layout
- On narrow viewport (< 768px), layout forces tabs regardless of toggle
- Terminal panel fills its resizable column height (no fixed-height clipping)
- Auxiliary cards (Details, Controls, Project) stack and scroll within their column
- Resizable handle drag works between primary and auxiliary columns

**Step 4: Commit**

```bash
git add frontend/src/components/Workspaces/WorkspacesHeader.tsx
git commit -m "refactor(workspaces): add SidebarTrigger, layout mode toggle, JSDoc to header"
```

---

## Task 4: Smoke-test the full integration

**No file changes — verification only.**

**Step 1: Check the route still compiles cleanly**

The route at `frontend/src/routes/_layout/workspace.$workspaceId.tsx` passes `panels` to `WorkspacesShell` — verify it remains unchanged (no new props needed at the route level since `layoutMode` lives in the shell).

```bash
cd frontend && npm run build 2>&1 | tail -20
```

Expected: `✓ built in Xs` or equivalent success output.

**Step 2: Check the index export**

`frontend/src/components/Workspaces/index.ts` exports `WorkspacesShell` — no changes needed there since `WorkspacesShellProps` interface is unchanged at the route boundary.

```bash
grep -n "WorkspacesShell\|WorkspacesLayout\|PanelConfig" frontend/src/components/Workspaces/index.ts
```

Verify `PanelConfig` is still exported (the `WorkspacesLayout`'s `PanelConfig` is re-exported through here and used by the route).

**Step 3: Final commit**

If any lint/format fixes were made in prior steps and not yet committed:

```bash
cd frontend && git add -p
git commit -m "chore(workspaces): lint/format fixes from paradigm migration"
```

---

## Summary of changes

| File | Change |
|------|--------|
| `WorkspacesLayout.tsx` | CSS grid → `ResizablePanelGroup` + Tabs, add `mode` prop |
| `WorkspacesShell.tsx` | Add `layoutMode` state, remove misplaced scroll, JSDoc |
| `WorkspacesHeader.tsx` | Add `SidebarTrigger`, layout toggle, JSDoc, restructured layout |
| `workspace.$workspaceId.tsx` | **No changes** |
| `Workspaces/index.ts` | **No changes** |

## What this does NOT change
- Panel content components (`WorkspaceDetailsPanel`, `WorkspaceTerminalPanel`, etc.) — untouched
- The route's `panels` array construction — untouched
- Backend — no changes required
- The collapsible behavior added to Details/Terminal panels earlier — preserved and works within the new layout
