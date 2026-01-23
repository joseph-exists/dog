# Agent UI Component System Refactor

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Decompose the monolithic `AgentUIRenderer.tsx` (538 lines, 12 inline sub-components) into a layered component system following the same primitives → content → variants → orchestrator pattern used by PersonaPicker and Pages.

**Architecture:** Extract each inline component into its own file under `AgentUI/primitives/`. Create a `useAgentUI` hook for the A2UI panel that accumulates UI components from room messages. Build the A2UIPanel as a real panel that aggregates and displays all agent UI components from the room, using the same primitives. The existing `AgentUIRenderer` becomes a thin orchestrator that imports from primitives.

**Tech Stack:** React, TypeScript, shadcn/ui, TanStack Query, lucide-react, existing Room panel infrastructure.

---

## Context

### Current State

- `AgentUIRenderer.tsx` — 538-line monolithic file with 12 inline sub-components (CardComponent, ListComponent, TableComponent, etc.)
- `types.ts` — Well-structured, 144 lines, 12 typed data interfaces. Keep as-is.
- `index.ts` — Barrel export of `AgentUIRenderer` + types. Will be expanded.
- `A2UIPanel.tsx` — Pure placeholder ("Coming soon"). Needs real implementation.

### How Components Flow

```
Backend Agent → emit_ui_component → RoomMessage.ui_components (JSONB)
  → Frontend MessageViewModel.ui_components → AgentUIRenderer per component
```

The A2UIPanel needs to aggregate all UI components from all agent messages in the room into a persistent, browsable panel.

### Consumption Points

1. **Inline in messages** — `Chat/Message.tsx` and `Rooms/Message.tsx` render `AgentUIRenderer` per component
2. **A2UI Panel** — Dedicated room panel showing accumulated agent UI (currently placeholder)

### Files to Create

```
src/components/AgentUI/
├── index.ts                         # Expanded barrel export
├── types.ts                         # UNCHANGED - already well-structured
├── AgentUIRenderer.tsx              # REFACTORED - thin orchestrator importing primitives
├── primitives/
│   ├── index.ts                     # Barrel export
│   ├── UICardBlock.tsx              # Card component (~30 lines)
│   ├── UIListBlock.tsx              # List component (~40 lines)
│   ├── UITableBlock.tsx             # Table component (~50 lines)
│   ├── UIProgressBlock.tsx          # Progress bars (~30 lines)
│   ├── UIActionButtons.tsx          # Interactive buttons (~35 lines)
│   ├── UICodeBlock.tsx              # Code display (~15 lines)
│   ├── UIQuoteBlock.tsx             # Blockquote (~25 lines)
│   ├── UIAlertBlock.tsx             # Alert/notice (~40 lines)
│   ├── UICollapsibleBlock.tsx       # Accordion (~20 lines)
│   ├── UITabsBlock.tsx              # Tabbed content (~20 lines)
│   ├── UIDividerBlock.tsx           # Separator (~25 lines)
│   └── UIPageLayoutPreview.tsx      # Page layout preview (~65 lines)
└── content/
    ├── index.ts                     # Barrel export
    ├── AgentUIStack.tsx             # Vertical stack of UIComponents
    └── AgentUIEmpty.tsx             # Empty state for panel
```

```
src/hooks/
└── useAgentUI.ts                    # Hook to extract UI components from room messages
```

```
src/components/Room/panels/
└── A2UIPanel.tsx                    # REFACTORED - real panel with aggregated UI
```

---

### Task 1: Extract Primitives (Simple Components)

**Files:**
- Create: `src/components/AgentUI/primitives/UICardBlock.tsx`
- Create: `src/components/AgentUI/primitives/UICodeBlock.tsx`
- Create: `src/components/AgentUI/primitives/UIQuoteBlock.tsx`
- Create: `src/components/AgentUI/primitives/UIDividerBlock.tsx`
- Create: `src/components/AgentUI/primitives/UIProgressBlock.tsx`

**Step 1: Create UICardBlock.tsx**

Extract the `CardComponent` function from `AgentUIRenderer.tsx` (lines 131-159) into its own file:

```tsx
// src/components/AgentUI/primitives/UICardBlock.tsx
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"
import type { UICardData } from "../types"

const variantStyles = {
  default: "",
  highlight: "border-primary bg-primary/5",
  warning: "border-yellow-500 bg-yellow-50 dark:bg-yellow-900/10",
  success: "border-green-500 bg-green-50 dark:bg-green-900/10",
  info: "border-blue-500 bg-blue-50 dark:bg-blue-900/10",
}

export function UICardBlock({ data }: { data: UICardData }) {
  return (
    <Card className={cn(variantStyles[data.variant || "default"])}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center gap-2">
          {data.icon && <span className="text-lg">📌</span>}
          {data.title}
        </CardTitle>
        {data.subtitle && <CardDescription>{data.subtitle}</CardDescription>}
      </CardHeader>
      <CardContent>
        <p className="text-sm whitespace-pre-wrap">{data.body}</p>
      </CardContent>
      {data.footer && (
        <CardFooter className="text-xs text-muted-foreground">
          {data.footer}
        </CardFooter>
      )}
    </Card>
  )
}
```

Note: We remove the `mt-3` class from primitives — spacing is handled by the parent container (stack or message wrapper). This enables reuse in different contexts without hardcoded margins.

**Step 2: Create UICodeBlock.tsx**

Extract from lines 324-339:

```tsx
// src/components/AgentUI/primitives/UICodeBlock.tsx
import type { UICodeData } from "../types"

export function UICodeBlock({ data }: { data: UICodeData }) {
  return (
    <div>
      {data.title && (
        <div className="text-xs text-muted-foreground mb-1 font-mono">
          {data.title}
        </div>
      )}
      <pre className="bg-muted rounded-md p-3 overflow-x-auto text-sm">
        <code className={data.language ? `language-${data.language}` : ""}>
          {data.code}
        </code>
      </pre>
    </div>
  )
}
```

**Step 3: Create UIQuoteBlock.tsx**

Extract from lines 341-363:

```tsx
// src/components/AgentUI/primitives/UIQuoteBlock.tsx
import { Quote } from "lucide-react"
import { cn } from "@/lib/utils"
import type { UIQuoteData } from "../types"

const variantStyles = {
  default: "border-l-muted-foreground",
  highlight: "border-l-primary bg-primary/5",
  subtle: "border-l-muted opacity-80",
}

export function UIQuoteBlock({ data }: { data: UIQuoteData }) {
  return (
    <blockquote
      className={cn(
        "border-l-4 pl-4 py-2",
        variantStyles[data.variant || "default"],
      )}
    >
      <Quote className="h-4 w-4 text-muted-foreground mb-1" />
      <p className="text-sm italic">{data.text}</p>
      {data.attribution && (
        <cite className="text-xs text-muted-foreground mt-1 block">
          — {data.attribution}
        </cite>
      )}
    </blockquote>
  )
}
```

**Step 4: Create UIDividerBlock.tsx**

Extract from lines 446-470:

```tsx
// src/components/AgentUI/primitives/UIDividerBlock.tsx
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"
import type { UIDividerData } from "../types"

const variantStyles = {
  solid: "",
  dashed: "border-dashed",
  dotted: "border-dotted",
}

export function UIDividerBlock({ data }: { data: UIDividerData }) {
  if (data.label) {
    return (
      <div className="flex items-center gap-4">
        <Separator
          className={cn("flex-1", variantStyles[data.variant || "solid"])}
        />
        <span className="text-xs text-muted-foreground">{data.label}</span>
        <Separator
          className={cn("flex-1", variantStyles[data.variant || "solid"])}
        />
      </div>
    )
  }

  return (
    <Separator className={cn(variantStyles[data.variant || "solid"])} />
  )
}
```

**Step 5: Create UIProgressBlock.tsx**

Extract from lines 252-283:

```tsx
// src/components/AgentUI/primitives/UIProgressBlock.tsx
import { cn } from "@/lib/utils"
import type { UIProgressData } from "../types"

const colorClasses = {
  blue: "bg-blue-500",
  green: "bg-green-500",
  yellow: "bg-yellow-500",
  red: "bg-red-500",
  purple: "bg-purple-500",
}

export function UIProgressBlock({ data }: { data: UIProgressData }) {
  return (
    <div className="space-y-2">
      {data.title && <h4 className="text-sm font-medium">{data.title}</h4>}
      {data.items.map((item, idx) => (
        <div key={idx} className="space-y-1">
          <div className="flex justify-between text-xs">
            <span>{item.label}</span>
            {data.show_percentage !== false && <span>{item.value}%</span>}
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div
              className={cn(
                "h-full transition-all",
                colorClasses[item.color || "blue"],
              )}
              style={{ width: `${Math.min(100, Math.max(0, item.value))}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}
```

**Step 6: Run lint**

Run: `cd frontend && npx biome check src/components/AgentUI/primitives/ --write`

---

### Task 2: Extract Primitives (Stateful/Complex Components)

**Files:**
- Create: `src/components/AgentUI/primitives/UIListBlock.tsx`
- Create: `src/components/AgentUI/primitives/UITableBlock.tsx`
- Create: `src/components/AgentUI/primitives/UIActionButtons.tsx`
- Create: `src/components/AgentUI/primitives/UIAlertBlock.tsx`
- Create: `src/components/AgentUI/primitives/UICollapsibleBlock.tsx`
- Create: `src/components/AgentUI/primitives/UITabsBlock.tsx`
- Create: `src/components/AgentUI/primitives/UIPageLayoutPreview.tsx`

**Step 1: Create UIListBlock.tsx**

Extract from lines 161-202:

```tsx
// src/components/AgentUI/primitives/UIListBlock.tsx
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { UIListData } from "../types"

export function UIListBlock({ data }: { data: UIListData }) {
  const ListTag = data.ordered ? "ol" : "ul"

  return (
    <div>
      {data.title && <h4 className="text-sm font-medium mb-2">{data.title}</h4>}
      <ListTag
        className={cn(
          "space-y-1 pl-4",
          data.ordered ? "list-decimal" : "list-disc",
        )}
      >
        {data.items.map((item, idx) => (
          <li key={idx} className="text-sm">
            <span className="font-medium">{item.label}</span>
            {item.badge && (
              <Badge
                variant={
                  item.badge_variant === "success"
                    ? "default"
                    : item.badge_variant === "warning"
                      ? "secondary"
                      : item.badge_variant === "error"
                        ? "destructive"
                        : "outline"
                }
                className="ml-2 text-xs"
              >
                {item.badge}
              </Badge>
            )}
            {item.description && (
              <p className="text-muted-foreground text-xs mt-0.5">
                {item.description}
              </p>
            )}
          </li>
        ))}
      </ListTag>
    </div>
  )
}
```

**Step 2: Create UITableBlock.tsx**

Extract from lines 204-250:

```tsx
// src/components/AgentUI/primitives/UITableBlock.tsx
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"
import type { UITableData } from "../types"

export function UITableBlock({ data }: { data: UITableData }) {
  return (
    <div>
      {data.title && <h4 className="text-sm font-medium mb-2">{data.title}</h4>}
      <div className="rounded-md border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              {data.columns.map((col) => (
                <TableHead
                  key={col.key}
                  className={cn(
                    col.align === "center" && "text-center",
                    col.align === "right" && "text-right",
                  )}
                >
                  {col.header}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.rows.map((row, idx) => (
              <TableRow
                key={idx}
                className={cn(data.striped && idx % 2 === 1 && "bg-muted/50")}
              >
                {data.columns.map((col) => (
                  <TableCell
                    key={col.key}
                    className={cn(
                      col.align === "center" && "text-center",
                      col.align === "right" && "text-right",
                      data.compact && "py-1 text-xs",
                    )}
                  >
                    {String(row[col.key] ?? "")}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
```

**Step 3: Create UIActionButtons.tsx**

Extract from lines 285-322:

```tsx
// src/components/AgentUI/primitives/UIActionButtons.tsx
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { UIActionButtonsData } from "../types"

const layoutClasses = {
  horizontal: "flex flex-wrap gap-2",
  vertical: "flex flex-col gap-2",
  grid: "grid grid-cols-2 gap-2",
}

interface UIActionButtonsProps {
  data: UIActionButtonsData
  onAction?: (action: string) => void
}

export function UIActionButtons({ data, onAction }: UIActionButtonsProps) {
  const buttons = Array.isArray(data.buttons) ? data.buttons : []

  return (
    <div className={cn(layoutClasses[data.layout || "horizontal"])}>
      {buttons.map((btn, idx) => (
        <Button
          key={idx}
          variant={
            btn.variant === "primary"
              ? "default"
              : btn.variant === "outline"
                ? "outline"
                : btn.variant === "ghost"
                  ? "ghost"
                  : "secondary"
          }
          size="sm"
          disabled={btn.disabled}
          onClick={() => onAction?.(btn.action)}
        >
          {btn.label}
        </Button>
      ))}
    </div>
  )
}
```

**Step 4: Create UIAlertBlock.tsx**

Extract from lines 366-402:

```tsx
// src/components/AgentUI/primitives/UIAlertBlock.tsx
import { AlertCircle, AlertTriangle, CheckCircle, Info } from "lucide-react"
import { useState } from "react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { cn } from "@/lib/utils"
import type { UIAlertData } from "../types"

const icons = {
  info: <Info className="h-4 w-4" />,
  success: <CheckCircle className="h-4 w-4" />,
  warning: <AlertTriangle className="h-4 w-4" />,
  error: <AlertCircle className="h-4 w-4" />,
}

const variantStyles = {
  info: "",
  success: "border-green-500 text-green-700 dark:text-green-400",
  warning: "border-yellow-500 text-yellow-700 dark:text-yellow-400",
  error: "border-red-500 text-red-700 dark:text-red-400",
}

export function UIAlertBlock({ data }: { data: UIAlertData }) {
  const [dismissed, setDismissed] = useState(false)

  if (dismissed) return null

  return (
    <Alert className={cn(variantStyles[data.variant || "info"])}>
      {icons[data.variant || "info"]}
      <div className="flex-1">
        {data.title && <AlertTitle>{data.title}</AlertTitle>}
        <AlertDescription>{data.message}</AlertDescription>
      </div>
      {data.dismissible && (
        <button
          type="button"
          onClick={() => setDismissed(true)}
          className="absolute top-2 right-2 text-muted-foreground hover:text-foreground"
          aria-label="Dismiss alert"
        >
          ×
        </button>
      )}
    </Alert>
  )
}
```

**Step 5: Create UICollapsibleBlock.tsx**

Extract from lines 405-423:

```tsx
// src/components/AgentUI/primitives/UICollapsibleBlock.tsx
import { ChevronDown } from "lucide-react"
import { useState } from "react"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { cn } from "@/lib/utils"
import type { UICollapsibleData } from "../types"

export function UICollapsibleBlock({ data }: { data: UICollapsibleData }) {
  const [open, setOpen] = useState(data.default_open ?? false)

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger className="flex items-center gap-2 text-sm font-medium hover:text-primary transition-colors">
        <ChevronDown
          className={cn("h-4 w-4 transition-transform", open && "rotate-180")}
        />
        {data.title}
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-2 pl-6">
        <p className="text-sm text-muted-foreground whitespace-pre-wrap">
          {data.content}
        </p>
      </CollapsibleContent>
    </Collapsible>
  )
}
```

**Step 6: Create UITabsBlock.tsx**

Extract from lines 425-444:

```tsx
// src/components/AgentUI/primitives/UITabsBlock.tsx
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import type { UITabsData } from "../types"

export function UITabsBlock({ data }: { data: UITabsData }) {
  const defaultTab = `tab-${data.default_tab ?? 0}`

  return (
    <Tabs defaultValue={defaultTab}>
      <TabsList>
        {data.tabs.map((tab, idx) => (
          <TabsTrigger key={idx} value={`tab-${idx}`}>
            {tab.label}
          </TabsTrigger>
        ))}
      </TabsList>
      {data.tabs.map((tab, idx) => (
        <TabsContent key={idx} value={`tab-${idx}`} className="text-sm">
          <p className="whitespace-pre-wrap">{tab.content}</p>
        </TabsContent>
      ))}
    </Tabs>
  )
}
```

**Step 7: Create UIPageLayoutPreview.tsx**

Extract from lines 475-537:

```tsx
// src/components/AgentUI/primitives/UIPageLayoutPreview.tsx
import {
  type BlockType,
  getBlockType,
  type TemplateBlock,
} from "@/components/Page/registry"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import type { UIPageLayoutPreviewData } from "../types"

export function UIPageLayoutPreview({
  data,
}: {
  data: UIPageLayoutPreviewData
}) {
  const layoutBlocks = Array.isArray(data.layout_json) ? data.layout_json : []
  const primaryBlocks = layoutBlocks.filter(
    (block) => block.column === "primary",
  )
  const auxiliaryBlocks = layoutBlocks.filter(
    (block) => block.column === "auxiliary",
  )

  const renderBlockLabel = (block: TemplateBlock) => {
    const def = getBlockType(block.type as BlockType)
    return def?.label ?? block.type
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Proposed Page Layout</CardTitle>
        {data.summary && (
          <CardDescription className="text-xs">{data.summary}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-1">
            Primary
          </p>
          <div className="flex flex-wrap gap-2">
            {primaryBlocks.length > 0 ? (
              primaryBlocks.map((block, index) => (
                <Badge key={`${block.type}-${index}`} variant="secondary">
                  {renderBlockLabel(block)}
                </Badge>
              ))
            ) : (
              <span className="text-xs text-muted-foreground">None</span>
            )}
          </div>
        </div>
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-1">
            Auxiliary
          </p>
          <div className="flex flex-wrap gap-2">
            {auxiliaryBlocks.length > 0 ? (
              auxiliaryBlocks.map((block, index) => (
                <Badge key={`${block.type}-${index}`} variant="outline">
                  {renderBlockLabel(block)}
                </Badge>
              ))
            ) : (
              <span className="text-xs text-muted-foreground">None</span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
```

**Step 8: Create primitives barrel export**

```tsx
// src/components/AgentUI/primitives/index.ts
export { UIActionButtons } from "./UIActionButtons"
export { UIAlertBlock } from "./UIAlertBlock"
export { UICardBlock } from "./UICardBlock"
export { UICodeBlock } from "./UICodeBlock"
export { UICollapsibleBlock } from "./UICollapsibleBlock"
export { UIDividerBlock } from "./UIDividerBlock"
export { UIListBlock } from "./UIListBlock"
export { UIPageLayoutPreview } from "./UIPageLayoutPreview"
export { UIProgressBlock } from "./UIProgressBlock"
export { UIQuoteBlock } from "./UIQuoteBlock"
export { UITableBlock } from "./UITableBlock"
export { UITabsBlock } from "./UITabsBlock"
```

**Step 9: Run lint**

Run: `cd frontend && npx biome check src/components/AgentUI/primitives/ --write`

---

### Task 3: Refactor AgentUIRenderer to Use Primitives

**Files:**
- Modify: `src/components/AgentUI/AgentUIRenderer.tsx` (replace ~470 lines with ~80 lines)

**Step 1: Rewrite AgentUIRenderer.tsx**

Replace the entire file with a thin orchestrator that imports from primitives:

```tsx
// src/components/AgentUI/AgentUIRenderer.tsx
/**
 * Agent UI Renderer
 *
 * Thin orchestrator that dispatches UIComponent rendering to individual primitives.
 * Each primitive is a self-contained component in the primitives/ directory.
 *
 * Usage:
 *   {message.ui_components?.map((component, idx) => (
 *     <AgentUIRenderer key={component.id || idx} component={component} />
 *   ))}
 */

import type {
  UIActionButtonsData,
  UIAlertData,
  UICardData,
  UICodeData,
  UICollapsibleData,
  UIComponent,
  UIDividerData,
  UIListData,
  UIPageLayoutPreviewData,
  UIProgressData,
  UIQuoteData,
  UITableData,
  UITabsData,
} from "./types"
import {
  UIActionButtons,
  UIAlertBlock,
  UICardBlock,
  UICodeBlock,
  UICollapsibleBlock,
  UIDividerBlock,
  UIListBlock,
  UIPageLayoutPreview,
  UIProgressBlock,
  UIQuoteBlock,
  UITableBlock,
  UITabsBlock,
} from "./primitives"

interface AgentUIRendererProps {
  component: UIComponent
  onAction?: (action: string) => void
}

export default function AgentUIRenderer({
  component,
  onAction,
}: AgentUIRendererProps) {
  const { type, data, fallback_text } = component

  switch (type) {
    case "card":
      return <UICardBlock data={data as unknown as UICardData} />
    case "list":
      return <UIListBlock data={data as unknown as UIListData} />
    case "table":
      return <UITableBlock data={data as unknown as UITableData} />
    case "progress":
      return <UIProgressBlock data={data as unknown as UIProgressData} />
    case "action_buttons":
      return (
        <UIActionButtons
          data={data as unknown as UIActionButtonsData}
          onAction={onAction}
        />
      )
    case "code":
      return <UICodeBlock data={data as unknown as UICodeData} />
    case "quote":
      return <UIQuoteBlock data={data as unknown as UIQuoteData} />
    case "alert":
      return <UIAlertBlock data={data as unknown as UIAlertData} />
    case "collapsible":
      return (
        <UICollapsibleBlock data={data as unknown as UICollapsibleData} />
      )
    case "tabs":
      return <UITabsBlock data={data as unknown as UITabsData} />
    case "divider":
      return <UIDividerBlock data={data as unknown as UIDividerData} />
    case "page_layout_preview":
      return (
        <UIPageLayoutPreview
          data={data as unknown as UIPageLayoutPreviewData}
        />
      )
    default:
      return fallback_text ? (
        <p className="text-sm text-muted-foreground italic">{fallback_text}</p>
      ) : null
  }
}
```

**Step 2: Verify message rendering still works**

The inline message usage wraps each `AgentUIRenderer` in `<div className="mt-3 space-y-2">`, so spacing comes from the parent — our removal of `mt-3` from primitives is correct.

**Step 3: Run lint and build**

Run: `cd frontend && npx biome check src/components/AgentUI/ --write && npx tsc --noEmit`

---

### Task 4: Create Content Components

**Files:**
- Create: `src/components/AgentUI/content/AgentUIStack.tsx`
- Create: `src/components/AgentUI/content/AgentUIEmpty.tsx`
- Create: `src/components/AgentUI/content/index.ts`

**Step 1: Create AgentUIStack.tsx**

A reusable component that renders a vertical stack of UIComponents. Used by both the message inline renderer and the A2UI panel:

```tsx
// src/components/AgentUI/content/AgentUIStack.tsx
import { cn } from "@/lib/utils"
import AgentUIRenderer from "../AgentUIRenderer"
import type { UIComponent } from "../types"

interface AgentUIStackProps {
  components: UIComponent[]
  onAction?: (action: string, component: UIComponent) => void
  className?: string
  spacing?: "compact" | "normal" | "relaxed"
}

const spacingClasses = {
  compact: "space-y-1",
  normal: "space-y-3",
  relaxed: "space-y-4",
}

export function AgentUIStack({
  components,
  onAction,
  className,
  spacing = "normal",
}: AgentUIStackProps) {
  if (components.length === 0) return null

  return (
    <div className={cn(spacingClasses[spacing], className)}>
      {components.map((component, index) => (
        <AgentUIRenderer
          key={component.id || `${component.type}-${index}`}
          component={component}
          onAction={onAction ? (action) => onAction(action, component) : undefined}
        />
      ))}
    </div>
  )
}
```

**Step 2: Create AgentUIEmpty.tsx**

Empty state for when no UI components exist:

```tsx
// src/components/AgentUI/content/AgentUIEmpty.tsx
import { Blocks } from "lucide-react"
import { cn } from "@/lib/utils"

interface AgentUIEmptyProps {
  className?: string
  title?: string
  description?: string
}

export function AgentUIEmpty({
  className,
  title = "No agent UI components",
  description = "Structured UI components from agent tool calls will appear here as agents interact in this room.",
}: AgentUIEmptyProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-12 px-4 text-center",
        className,
      )}
    >
      <Blocks className="h-10 w-10 text-muted-foreground/50 mb-3" />
      <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
      <p className="text-xs text-muted-foreground/70 mt-1 max-w-[240px]">
        {description}
      </p>
    </div>
  )
}
```

**Step 3: Create content barrel export**

```tsx
// src/components/AgentUI/content/index.ts
export { AgentUIEmpty } from "./AgentUIEmpty"
export { AgentUIStack } from "./AgentUIStack"
```

**Step 4: Run lint**

Run: `cd frontend && npx biome check src/components/AgentUI/content/ --write`

---

### Task 5: Create useAgentUI Hook

**Files:**
- Create: `src/hooks/useAgentUI.ts`

**Step 1: Create useAgentUI.ts**

This hook extracts and aggregates all UI components from room messages. It provides a flat list of components grouped by agent, suitable for the A2UI panel:

```tsx
// src/hooks/useAgentUI.ts
import { useMemo } from "react"
import type { UIComponent } from "@/components/AgentUI/types"
import type { MessageViewModel } from "@/services/roomService"

export interface AgentUIEntry {
  component: UIComponent
  agentName: string
  messageId: string
  timestamp: string
}

interface UseAgentUIOptions {
  messages: MessageViewModel[]
}

interface UseAgentUIResult {
  /** All UI components from all agent messages, in chronological order */
  entries: AgentUIEntry[]
  /** UI components grouped by agent name */
  byAgent: Map<string, AgentUIEntry[]>
  /** Whether there are any UI components */
  hasComponents: boolean
  /** Total number of UI components */
  count: number
}

/**
 * Extracts and aggregates UI components from room messages.
 * Provides a flat chronological list and agent-grouped view.
 */
export function useAgentUI({ messages }: UseAgentUIOptions): UseAgentUIResult {
  const entries = useMemo(() => {
    const result: AgentUIEntry[] = []

    for (const msg of messages) {
      if (msg.sender_type !== "user" && msg.ui_components) {
        for (const component of msg.ui_components) {
          result.push({
            component,
            agentName: msg.sender_name,
            messageId: msg.message_id,
            timestamp: msg.created_at ?? "",
          })
        }
      }
    }

    return result
  }, [messages])

  const byAgent = useMemo(() => {
    const map = new Map<string, AgentUIEntry[]>()
    for (const entry of entries) {
      const existing = map.get(entry.agentName) ?? []
      existing.push(entry)
      map.set(entry.agentName, existing)
    }
    return map
  }, [entries])

  return {
    entries,
    byAgent,
    hasComponents: entries.length > 0,
    count: entries.length,
  }
}
```

**Step 2: Run lint**

Run: `cd frontend && npx biome check src/hooks/useAgentUI.ts --write`

---

### Task 6: Implement A2UIPanel

**Files:**
- Modify: `src/components/Room/panels/A2UIPanel.tsx` (replace placeholder with real implementation)

**Step 1: Rewrite A2UIPanel.tsx**

Replace the placeholder with a real panel that shows aggregated UI components from room messages:

```tsx
// src/components/Room/panels/A2UIPanel.tsx
import { useMemo } from "react"
import { AgentUIEmpty, AgentUIStack } from "@/components/AgentUI/content"
import type { UIComponent } from "@/components/AgentUI/types"
import { useAgentUI } from "@/hooks/useAgentUI"
import { useRoomMessages } from "@/hooks/useRoomMessages"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"
import { PanelContainer } from "../primitives/PanelContainer"

interface A2UIPanelProps {
  roomId: string
  hideHeader?: boolean
  className?: string
}

export function A2UIPanel({
  roomId,
  hideHeader = false,
  className,
}: A2UIPanelProps) {
  const { messages } = useRoomMessages(roomId)
  const { entries, byAgent, hasComponents } = useAgentUI({
    messages: messages ?? [],
  })

  const handleAction = (action: string, component: UIComponent) => {
    // TODO: Route actions back to the agent that emitted the component
    console.log("[A2UIPanel] Action:", action, "Component:", component.id)
  }

  const content = hasComponents ? (
    <ScrollArea className="h-full">
      <div className="p-4 space-y-4">
        {[...byAgent.entries()].map(([agentName, agentEntries]) => (
          <div key={agentName}>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-medium text-muted-foreground">
                {agentName}
              </span>
              <Badge variant="secondary" className="text-xs">
                {agentEntries.length}
              </Badge>
            </div>
            <AgentUIStack
              components={agentEntries.map((e) => e.component)}
              onAction={handleAction}
              spacing="compact"
            />
            <Separator className="mt-4" />
          </div>
        ))}
      </div>
    </ScrollArea>
  ) : (
    <AgentUIEmpty />
  )

  if (hideHeader) {
    return <div className={cn("h-full", className)}>{content}</div>
  }

  return (
    <PanelContainer title="Agent UI">
      {content}
    </PanelContainer>
  )
}
```

**Step 2: Verify useRoomMessages hook exists and its signature**

The A2UIPanel depends on `useRoomMessages` — verify this hook exists and returns `messages`. If it doesn't exist or has a different name, adapt the import. The hook should be at `src/hooks/useRoomMessages.ts` or similar. The panel route (`r.$roomId.tsx`) likely already fetches messages and passes them to `ChatPanel` — we need to use the same data source.

> **Note to implementer:** If `useRoomMessages` doesn't exist as a standalone hook, check how `ChatPanel` gets its messages. You may need to use `useRoomData` or query the messages from the room service directly. The key query is fetching `RoomMessagePublic[]` for the room.

**Step 3: Run lint**

Run: `cd frontend && npx biome check src/components/Room/panels/A2UIPanel.tsx --write`

---

### Task 7: Update Barrel Export and Verify Build

**Files:**
- Modify: `src/components/AgentUI/index.ts`

**Step 1: Update barrel export**

```tsx
// src/components/AgentUI/index.ts
/**
 * AG-UI (Agent-Generated UI) Components
 *
 * Layered component system:
 * - primitives/  — Individual UI block renderers
 * - content/     — Composite layouts (Stack, Empty)
 * - AgentUIRenderer — Orchestrator dispatching to primitives
 */

export { default as AgentUIRenderer } from "./AgentUIRenderer"
export { AgentUIEmpty, AgentUIStack } from "./content"
export {
  UIActionButtons,
  UIAlertBlock,
  UICardBlock,
  UICodeBlock,
  UICollapsibleBlock,
  UIDividerBlock,
  UIListBlock,
  UIPageLayoutPreview,
  UIProgressBlock,
  UIQuoteBlock,
  UITableBlock,
  UITabsBlock,
} from "./primitives"
export * from "./types"
```

**Step 2: Run full build**

Run: `cd frontend && npx tsc --noEmit`

Fix any TypeScript errors that appear. Common issues:
- Import path mismatches
- Missing `useRoomMessages` hook (see Task 6 Step 2 note)

**Step 3: Run lint on entire AgentUI directory**

Run: `cd frontend && npx biome check src/components/AgentUI/ --write`

**Step 4: Verify existing message rendering**

The existing usage in `Chat/Message.tsx` and `Rooms/Message.tsx` should continue to work unchanged since `AgentUIRenderer` maintains the same public API (same props, same default export).

---

### Task 8: Commit and Verify

**Step 1: Run full lint + build**

Run: `cd frontend && npx biome check --write && npx tsc --noEmit`

**Step 2: Commit**

```bash
git add frontend/src/components/AgentUI/ frontend/src/hooks/useAgentUI.ts frontend/src/components/Room/panels/A2UIPanel.tsx
git commit -m "refactor(agent-ui): decompose monolithic renderer into layered component system

Extract 12 inline sub-components from AgentUIRenderer.tsx into individual
primitives. Add content components (AgentUIStack, AgentUIEmpty) and implement
real A2UIPanel with aggregated UI component display from room messages.

Follows the same primitives → content → orchestrator pattern as PersonaPicker."
```

---

## Summary

| Task | Description | New Files | Modified Files |
|------|-------------|-----------|----------------|
| 1 | Extract simple primitives | 5 | 0 |
| 2 | Extract complex primitives + barrel | 8 | 0 |
| 3 | Refactor AgentUIRenderer | 0 | 1 |
| 4 | Create content components | 3 | 0 |
| 5 | Create useAgentUI hook | 1 | 0 |
| 6 | Implement A2UIPanel | 0 | 1 |
| 7 | Update barrel export + verify | 0 | 1 |
| 8 | Lint + Build + Commit | 0 | 0 |

**Total: 17 new files, 3 modified files**

The refactored system reduces `AgentUIRenderer.tsx` from 538 lines to ~80 lines, enables individual primitive reuse across contexts, and brings the A2UIPanel from placeholder to functional panel aggregating all agent UI components in a room.
