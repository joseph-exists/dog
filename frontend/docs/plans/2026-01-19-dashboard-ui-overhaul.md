# Dashboard UI Overhaul Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract and adapt UI patterns from shadcn dashboard-01 block into the existing TanStack Router architecture.

**Architecture:** Keep existing Sidebar structure (`components/Sidebar/`) and auth integration. Extract reusable components from dashboard-01, convert @tabler icons to Lucide, remove Next.js artifacts, and genericize components to accept props instead of hardcoded data.

**Tech Stack:** React 19, TanStack Router, TanStack Query, shadcn/ui, Lucide React, Recharts

---

## Phase 1: Cleanup & Standardization

### Task 1: Remove Next.js Artifacts

**Files:**
- Modify: `frontend/src/components/chart-area-interactive.tsx:1`

**Step 1: Remove "use client" directive**

The `"use client"` directive is Next.js-specific and not needed in Vite/React.

```tsx
// DELETE this line at the top of chart-area-interactive.tsx:
"use client"
```

**Step 2: Verify no build errors**

Run: `cd /home/josep/dog/frontend && npm run build`
Expected: Build succeeds without errors

**Step 3: Commit**

```bash
git add frontend/src/components/chart-area-interactive.tsx
git commit -m "chore: remove Next.js 'use client' directive"
```

---

### Task 2: Convert Icons in nav-main.tsx

**Files:**
- Modify: `frontend/src/components/nav-main.tsx`

**Step 1: Replace @tabler imports with Lucide equivalents**

Replace the entire imports section:

```tsx
// OLD (delete):
import { IconCirclePlusFilled, IconMail, type Icon } from "@tabler/icons-react"

// NEW:
import type { LucideIcon } from "lucide-react"
import { CirclePlus, Mail } from "lucide-react"
```

**Step 2: Update the component props type**

```tsx
// OLD:
export function NavMain({
  items,
}: {
  items: {
    title: string
    url: string
    icon?: Icon
  }[]
}) {

// NEW:
export function NavMain({
  items,
}: {
  items: {
    title: string
    url: string
    icon?: LucideIcon
  }[]
}) {
```

**Step 3: Replace icon usages in JSX**

```tsx
// OLD:
<IconCirclePlusFilled />
// NEW:
<CirclePlus className="fill-current" />

// OLD:
<IconMail />
// NEW:
<Mail />
```

**Step 4: Verify no TypeScript errors**

Run: `cd /home/josep/dog/frontend && npm run lint`
Expected: No errors related to nav-main.tsx

**Step 5: Commit**

```bash
git add frontend/src/components/nav-main.tsx
git commit -m "refactor(nav-main): convert @tabler icons to Lucide"
```

---

### Task 3: Convert Icons in nav-user.tsx

**Files:**
- Modify: `frontend/src/components/nav-user.tsx`

**Step 1: Replace @tabler imports with Lucide equivalents**

```tsx
// OLD (delete):
import {
  IconCreditCard,
  IconDotsVertical,
  IconLogout,
  IconNotification,
  IconUserCircle,
} from "@tabler/icons-react"

// NEW:
import {
  CreditCard,
  MoreVertical,
  LogOut,
  Bell,
  UserCircle,
} from "lucide-react"
```

**Step 2: Replace all icon usages in JSX**

```tsx
// Replacements:
// IconDotsVertical -> MoreVertical
// IconUserCircle -> UserCircle
// IconCreditCard -> CreditCard
// IconNotification -> Bell
// IconLogout -> LogOut
```

**Step 3: Verify no TypeScript errors**

Run: `cd /home/josep/dog/frontend && npm run lint`
Expected: No errors related to nav-user.tsx

**Step 4: Commit**

```bash
git add frontend/src/components/nav-user.tsx
git commit -m "refactor(nav-user): convert @tabler icons to Lucide"
```

---

### Task 4: Convert Icons in section-cards.tsx

**Files:**
- Modify: `frontend/src/components/section-cards.tsx`

**Step 1: Replace @tabler imports with Lucide equivalents**

```tsx
// OLD (delete):
import { IconTrendingDown, IconTrendingUp } from "@tabler/icons-react"

// NEW:
import { TrendingDown, TrendingUp } from "lucide-react"
```

**Step 2: Replace all icon usages in JSX**

Search and replace:
- `<IconTrendingUp />` -> `<TrendingUp />`
- `<IconTrendingUp className="size-4" />` -> `<TrendingUp className="size-4" />`
- `<IconTrendingDown />` -> `<TrendingDown />`
- `<IconTrendingDown className="size-4" />` -> `<TrendingDown className="size-4" />`

**Step 3: Verify no TypeScript errors**

Run: `cd /home/josep/dog/frontend && npm run lint`
Expected: No errors related to section-cards.tsx

**Step 4: Commit**

```bash
git add frontend/src/components/section-cards.tsx
git commit -m "refactor(section-cards): convert @tabler icons to Lucide"
```

---

### Task 5: Convert Icons in data-table.tsx

**Files:**
- Modify: `frontend/src/components/data-table.tsx`

**Step 1: Replace @tabler imports with Lucide equivalents**

```tsx
// OLD (delete):
import {
  IconChevronDown,
  IconChevronLeft,
  IconChevronRight,
  IconChevronsLeft,
  IconChevronsRight,
  IconCircleCheckFilled,
  IconDotsVertical,
  IconGripVertical,
  IconLayoutColumns,
  IconLoader,
  IconPlus,
  IconTrendingUp,
} from "@tabler/icons-react"

// NEW:
import {
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  CheckCircle2,
  MoreVertical,
  GripVertical,
  Columns3,
  Loader2,
  Plus,
  TrendingUp,
} from "lucide-react"
```

**Step 2: Replace all icon usages in JSX**

Search and replace throughout the file:
- `<IconChevronDown />` -> `<ChevronDown />`
- `<IconChevronLeft />` -> `<ChevronLeft />`
- `<IconChevronRight />` -> `<ChevronRight />`
- `<IconChevronsLeft />` -> `<ChevronsLeft />`
- `<IconChevronsRight />` -> `<ChevronsRight />`
- `<IconCircleCheckFilled className="fill-green-500 dark:fill-green-400" />` -> `<CheckCircle2 className="text-green-500 dark:text-green-400 fill-current" />`
- `<IconDotsVertical />` -> `<MoreVertical />`
- `<IconGripVertical className="text-muted-foreground size-3" />` -> `<GripVertical className="text-muted-foreground size-3" />`
- `<IconLayoutColumns />` -> `<Columns3 />`
- `<IconLoader />` -> `<Loader2 className="animate-spin" />`
- `<IconPlus />` -> `<Plus />`
- `<IconTrendingUp className="size-4" />` -> `<TrendingUp className="size-4" />`

**Step 3: Verify no TypeScript errors**

Run: `cd /home/josep/dog/frontend && npm run lint`
Expected: No errors related to data-table.tsx

**Step 4: Commit**

```bash
git add frontend/src/components/data-table.tsx
git commit -m "refactor(data-table): convert @tabler icons to Lucide"
```

---

### Task 6: Convert Icons in app-sidebar.tsx (dashboard-01 version)

**Files:**
- Modify: `frontend/src/components/app-sidebar.tsx`

**Step 1: Replace @tabler imports with Lucide equivalents**

```tsx
// OLD (delete entire import block):
import {
  IconCamera,
  IconChartBar,
  IconDashboard,
  IconDatabase,
  IconFileAi,
  IconFileDescription,
  IconFileWord,
  IconFolder,
  IconHelp,
  IconInnerShadowTop,
  IconListDetails,
  IconReport,
  IconSearch,
  IconSettings,
  IconUsers,
} from "@tabler/icons-react"

// NEW:
import {
  Camera,
  BarChart3,
  LayoutDashboard,
  Database,
  FileText,
  FileType,
  FileCode,
  Folder,
  HelpCircle,
  Hexagon,
  ListTodo,
  FileBarChart,
  Search,
  Settings,
  Users,
} from "lucide-react"
```

**Step 2: Update the data object icons**

```tsx
const data = {
  // ... user stays same
  navMain: [
    { title: "Dashboard", url: "#", icon: LayoutDashboard },
    { title: "Lifecycle", url: "#", icon: ListTodo },
    { title: "Analytics", url: "#", icon: BarChart3 },
    { title: "Projects", url: "#", icon: Folder },
    { title: "Team", url: "#", icon: Users },
  ],
  navClouds: [
    { title: "Capture", icon: Camera, isActive: true, url: "#", items: [...] },
    { title: "Proposal", icon: FileText, url: "#", items: [...] },
    { title: "Prompts", icon: FileCode, url: "#", items: [...] },
  ],
  navSecondary: [
    { title: "Settings", url: "#", icon: Settings },
    { title: "Get Help", url: "#", icon: HelpCircle },
    { title: "Search", url: "#", icon: Search },
  ],
  documents: [
    { name: "Data Library", url: "#", icon: Database },
    { name: "Reports", url: "#", icon: FileBarChart },
    { name: "Word Assistant", url: "#", icon: FileType },
  ],
}
```

**Step 3: Update logo icon in JSX**

```tsx
// OLD:
<IconInnerShadowTop className="!size-5" />

// NEW:
<Hexagon className="size-5" />
```

**Step 4: Verify no TypeScript errors**

Run: `cd /home/josep/dog/frontend && npm run lint`
Expected: No errors related to app-sidebar.tsx

**Step 5: Commit**

```bash
git add frontend/src/components/app-sidebar.tsx
git commit -m "refactor(app-sidebar): convert @tabler icons to Lucide"
```

---

## Phase 2: File Organization

### Task 7: Delete src/app Directory

The `src/app/` directory follows Next.js App Router conventions which don't apply to this TanStack Router project.

**Files:**
- Delete: `frontend/src/app/dashboard/page.tsx`
- Delete: `frontend/src/app/dashboard/data.json`
- Delete: `frontend/src/app/` directory

**Step 1: Remove the app directory**

```bash
rm -rf /home/josep/dog/frontend/src/app
```

**Step 2: Verify build still works**

Run: `cd /home/josep/dog/frontend && npm run build`
Expected: Build succeeds (app directory was not imported anywhere)

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove unused src/app directory (Next.js artifact)"
```

---

### Task 8: Organize Dashboard Components into Subdirectory

**Files:**
- Move: `frontend/src/components/section-cards.tsx` -> `frontend/src/components/Dashboard/SectionCards.tsx`
- Move: `frontend/src/components/chart-area-interactive.tsx` -> `frontend/src/components/Dashboard/ChartAreaInteractive.tsx`
- Move: `frontend/src/components/data-table.tsx` -> `frontend/src/components/Dashboard/DataTable.tsx`

**Step 1: Create Dashboard directory**

```bash
mkdir -p /home/josep/dog/frontend/src/components/Dashboard
```

**Step 2: Move and rename files (PascalCase convention)**

```bash
mv /home/josep/dog/frontend/src/components/section-cards.tsx /home/josep/dog/frontend/src/components/Dashboard/SectionCards.tsx
mv /home/josep/dog/frontend/src/components/chart-area-interactive.tsx /home/josep/dog/frontend/src/components/Dashboard/ChartAreaInteractive.tsx
mv /home/josep/dog/frontend/src/components/data-table.tsx /home/josep/dog/frontend/src/components/Dashboard/DataTable.tsx
```

**Step 3: Create index.ts barrel export**

Create `frontend/src/components/Dashboard/index.ts`:

```typescript
export { SectionCards } from "./SectionCards"
export { ChartAreaInteractive } from "./ChartAreaInteractive"
export { DataTable, schema } from "./DataTable"
```

**Step 4: Update imports in moved files if needed**

The imports use `@/` aliases, so no changes needed.

**Step 5: Verify no import errors**

Run: `cd /home/josep/dog/frontend && npm run lint`
Expected: No errors

**Step 6: Commit**

```bash
git add -A
git commit -m "refactor: organize dashboard components into Dashboard/ directory"
```

---

### Task 9: Clean Up Unused Dashboard-01 Navigation Components

These components duplicate functionality already in `components/Sidebar/`. We'll delete them and keep the existing well-integrated versions.

**Files:**
- Delete: `frontend/src/components/nav-main.tsx`
- Delete: `frontend/src/components/nav-user.tsx`
- Delete: `frontend/src/components/nav-documents.tsx`
- Delete: `frontend/src/components/nav-secondary.tsx`
- Delete: `frontend/src/components/app-sidebar.tsx` (dashboard-01 version)
- Delete: `frontend/src/components/site-header.tsx`

**Step 1: Remove unused navigation components**

```bash
rm /home/josep/dog/frontend/src/components/nav-main.tsx
rm /home/josep/dog/frontend/src/components/nav-user.tsx
rm /home/josep/dog/frontend/src/components/nav-documents.tsx
rm /home/josep/dog/frontend/src/components/nav-secondary.tsx
rm /home/josep/dog/frontend/src/components/app-sidebar.tsx
rm /home/josep/dog/frontend/src/components/site-header.tsx
```

**Step 2: Verify build still works**

Run: `cd /home/josep/dog/frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove unused dashboard-01 navigation components"
```

---

## Phase 3: Enhance Existing Components

### Task 10: Enhance Layout Header with Dynamic Title

**Files:**
- Modify: `frontend/src/routes/_layout.tsx`

**Step 1: Add route-aware header with separator**

Update the header section in `_layout.tsx`:

```tsx
import { createFileRoute, Outlet, redirect, useMatches } from "@tanstack/react-router"

import { Footer } from "@/components/Common/Footer"
import AppSidebar from "@/components/Sidebar/AppSidebar"
import { Separator } from "@/components/ui/separator"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout")({
  component: Layout,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
      })
    }
  },
})

/** Map route paths to display titles */
const routeTitles: Record<string, string> = {
  "/": "Dashboard",
  "/stories": "Stories",
  "/rooms": "Rooms",
  "/agents": "Agents",
  "/items": "Items",
  "/admin": "Admin",
  "/settings": "Settings",
}

function Layout() {
  const matches = useMatches()
  const currentPath = matches[matches.length - 1]?.pathname || "/"

  // Get title from exact match or find parent route
  const pageTitle = routeTitles[currentPath] ||
    Object.entries(routeTitles).find(([path]) =>
      currentPath.startsWith(path) && path !== "/"
    )?.[1] ||
    "Dashboard"

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-2 border-b bg-background px-4">
          <SidebarTrigger className="-ml-1 text-muted-foreground" />
          <Separator orientation="vertical" className="mx-2 h-4" />
          <h1 className="text-base font-medium">{pageTitle}</h1>
        </header>
        <main className="flex-1 p-6 md:p-8">
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>
        <Footer />
      </SidebarInset>
    </SidebarProvider>
  )
}

export default Layout
```

**Step 2: Verify the layout renders correctly**

Run: `cd /home/josep/dog/frontend && npm run dev`
Navigate to different routes and verify the title updates.

**Step 3: Commit**

```bash
git add frontend/src/routes/_layout.tsx
git commit -m "feat(layout): add dynamic page title to header"
```

---

### Task 11: Enhance User Component with Better Styling

**Files:**
- Modify: `frontend/src/components/Sidebar/User.tsx`

**Step 1: Add grayscale avatar styling from dashboard-01**

Update the Avatar in `UserInfo`:

```tsx
function UserInfo({ fullName, email }: UserInfoProps) {
  return (
    <div className="flex items-center gap-2.5 w-full min-w-0">
      <Avatar className="size-8 grayscale">
        <AvatarFallback className="bg-zinc-600 text-white">
          {getInitials(fullName || "User")}
        </AvatarFallback>
      </Avatar>
      <div className="grid flex-1 text-left text-sm leading-tight min-w-0">
        <span className="truncate font-medium">{fullName}</span>
        <span className="text-muted-foreground truncate text-xs">{email}</span>
      </div>
    </div>
  )
}
```

**Step 2: Verify styling looks correct**

Run: `cd /home/josep/dog/frontend && npm run dev`
Check the sidebar user section has grayscale avatar.

**Step 3: Commit**

```bash
git add frontend/src/components/Sidebar/User.tsx
git commit -m "style(user): add grayscale avatar styling"
```

---

## Phase 4: Genericize Dashboard Components

### Task 12: Make SectionCards Accept Props

**Files:**
- Modify: `frontend/src/components/Dashboard/SectionCards.tsx`

**Step 1: Define TypeScript interfaces**

Add at the top of the file, after imports:

```tsx
export interface MetricCardData {
  title: string
  value: string
  change: number
  changeLabel: string
  subtitle: string
}

export interface SectionCardsProps {
  metrics?: MetricCardData[]
}

const defaultMetrics: MetricCardData[] = [
  {
    title: "Total Revenue",
    value: "$1,250.00",
    change: 12.5,
    changeLabel: "Trending up this month",
    subtitle: "Visitors for the last 6 months",
  },
  {
    title: "New Customers",
    value: "1,234",
    change: -20,
    changeLabel: "Down 20% this period",
    subtitle: "Acquisition needs attention",
  },
  {
    title: "Active Accounts",
    value: "45,678",
    change: 12.5,
    changeLabel: "Strong user retention",
    subtitle: "Engagement exceed targets",
  },
  {
    title: "Growth Rate",
    value: "4.5%",
    change: 4.5,
    changeLabel: "Steady performance increase",
    subtitle: "Meets growth projections",
  },
]
```

**Step 2: Refactor component to use props**

```tsx
export function SectionCards({ metrics = defaultMetrics }: SectionCardsProps) {
  return (
    <div className="*:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card dark:*:data-[slot=card]:bg-card grid grid-cols-1 gap-4 px-4 *:data-[slot=card]:bg-gradient-to-t *:data-[slot=card]:shadow-xs lg:px-6 @xl/main:grid-cols-2 @5xl/main:grid-cols-4">
      {metrics.map((metric, index) => (
        <Card key={index} className="@container/card">
          <CardHeader>
            <CardDescription>{metric.title}</CardDescription>
            <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
              {metric.value}
            </CardTitle>
            <CardAction>
              <Badge variant="outline">
                {metric.change >= 0 ? <TrendingUp /> : <TrendingDown />}
                {metric.change >= 0 ? "+" : ""}{metric.change}%
              </Badge>
            </CardAction>
          </CardHeader>
          <CardFooter className="flex-col items-start gap-1.5 text-sm">
            <div className="line-clamp-1 flex gap-2 font-medium">
              {metric.changeLabel}
              {metric.change >= 0 ? (
                <TrendingUp className="size-4" />
              ) : (
                <TrendingDown className="size-4" />
              )}
            </div>
            <div className="text-muted-foreground">{metric.subtitle}</div>
          </CardFooter>
        </Card>
      ))}
    </div>
  )
}
```

**Step 3: Verify no TypeScript errors**

Run: `cd /home/josep/dog/frontend && npm run lint`
Expected: No errors

**Step 4: Commit**

```bash
git add frontend/src/components/Dashboard/SectionCards.tsx
git commit -m "refactor(section-cards): genericize with props interface"
```

---

### Task 13: Make ChartAreaInteractive Accept Props

**Files:**
- Modify: `frontend/src/components/Dashboard/ChartAreaInteractive.tsx`

**Step 1: Define TypeScript interfaces**

Add after imports:

```tsx
export interface ChartDataPoint {
  date: string
  desktop: number
  mobile: number
}

export interface ChartAreaInteractiveProps {
  data?: ChartDataPoint[]
  title?: string
  description?: string
}
```

**Step 2: Move hardcoded data to default prop**

```tsx
const defaultChartData: ChartDataPoint[] = [
  // ... keep existing chartData array as default
]

export function ChartAreaInteractive({
  data = defaultChartData,
  title = "Total Visitors",
  description = "Total for the last 3 months",
}: ChartAreaInteractiveProps) {
  // ... rest of component, replacing:
  // - chartData -> data
  // - "Total Visitors" -> title
  // - description text -> description prop
}
```

**Step 3: Update CardHeader to use props**

```tsx
<CardHeader>
  <CardTitle>{title}</CardTitle>
  <CardDescription>
    <span className="hidden @[540px]/card:block">{description}</span>
    <span className="@[540px]/card:hidden">Last 3 months</span>
  </CardDescription>
  {/* ... rest stays same */}
</CardHeader>
```

**Step 4: Verify no TypeScript errors**

Run: `cd /home/josep/dog/frontend && npm run lint`
Expected: No errors

**Step 5: Commit**

```bash
git add frontend/src/components/Dashboard/ChartAreaInteractive.tsx
git commit -m "refactor(chart): genericize with props interface"
```

---

## Phase 5: Verification

### Task 14: Full Build and Lint Check

**Step 1: Run full lint**

```bash
cd /home/josep/dog/frontend && npm run lint
```

Expected: No errors

**Step 2: Run full build**

```bash
cd /home/josep/dog/frontend && npm run build
```

Expected: Build succeeds

**Step 3: Manual smoke test**

```bash
cd /home/josep/dog/frontend && npm run dev
```

Verify:
- [ ] Sidebar renders correctly with existing navigation
- [ ] User menu works with logout
- [ ] Header shows dynamic page title
- [ ] No console errors

**Step 4: Final commit if any fixes needed**

```bash
git add -A
git commit -m "chore: final cleanup and verification"
```

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1 | 1-6 | Convert @tabler icons to Lucide, remove "use client" |
| 2 | 7-9 | Delete src/app/, organize Dashboard/, clean unused files |
| 3 | 10-11 | Enhance header with dynamic title, improve User styling |
| 4 | 12-13 | Genericize SectionCards and ChartAreaInteractive with props |
| 5 | 14 | Full verification |

**Total: 14 tasks**

**Files Modified:** ~10
**Files Deleted:** ~8
**Files Created:** 2 (Dashboard/index.ts, this plan)
