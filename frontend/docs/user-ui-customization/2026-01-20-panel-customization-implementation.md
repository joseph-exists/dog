# Panel Layout Customization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement delightful panel customization with drag-to-reorder, collapse/minimize, presets, keyboard shortcuts, and smooth Framer Motion animations.

**Architecture:** Build from primitives up - animation foundation first, then composable primitives, then backend persistence, then UI components. Frontend follows ViewModel pattern with services and hooks. All animations use shared spring configs from `components/ui/motion.tsx`.

**Tech Stack:** React 19, TypeScript, Framer Motion, TanStack Query, shadcn/ui, FastAPI, SQLModel

**Design Reference:** `frontend/docs/user-ui-customization/2026-01-20-panel-customization-design.md`

**Frontend Patterns Reference:** Follow patterns in `.claude/skills/frontend/` - ViewModels, services, JSDoc documentation

---

## Phase 1: Animation Foundation

### Task 1: Install Framer Motion

**Files:**
- Modify: `frontend/package.json`

**Step 1: Install dependency**

```bash
cd /home/josep/dog/frontend && npm install framer-motion
```

**Step 2: Verify installation**

```bash
cd /home/josep/dog/frontend && npm ls framer-motion
```

Expected: `framer-motion@11.x.x` (or latest)

**Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "chore(deps): add framer-motion for panel animations"
```

---

### Task 2: Create Motion Config Primitive

**Files:**
- Create: `frontend/src/components/ui/motion.tsx`

**Step 1: Create the motion configuration file**

```typescript
/**
 * Motion Configuration
 *
 * Shared animation configuration for consistent motion across the app.
 * Provides spring configs, transition presets, and reduce motion support.
 *
 * @example
 * ```tsx
 * import { springConfig, useReduceMotion } from "@/components/ui/motion"
 *
 * const reducedMotion = useReduceMotion()
 * <motion.div
 *   animate={{ scale: 1 }}
 *   transition={reducedMotion ? { duration: 0 } : springConfig.snappy}
 * />
 * ```
 */

import * as React from "react"
import { createContext, useContext, useEffect, useState } from "react"

// ============================================================================
// Spring Configurations
// ============================================================================

/**
 * Spring animation configurations
 *
 * - snappy: Quick, responsive feedback (buttons, drag)
 * - gentle: Smooth transitions (collapse, expand)
 * - bouncy: Playful motion (drop into place)
 */
export const springConfig = {
  snappy: { type: "spring" as const, stiffness: 500, damping: 30 },
  gentle: { type: "spring" as const, stiffness: 300, damping: 25 },
  bouncy: { type: "spring" as const, stiffness: 400, damping: 20 },
}

/**
 * Tween transition configurations
 *
 * - collapse: Panel collapse/expand
 * - fade: Opacity transitions
 * - preset: Layout preset switches
 */
export const transitions = {
  collapse: { duration: 0.2, ease: "easeOut" as const },
  fade: { duration: 0.15, ease: "easeInOut" as const },
  preset: { duration: 0.3, ease: "easeInOut" as const },
}

/**
 * Instant transition for reduced motion
 */
export const instantTransition = { duration: 0 }

// ============================================================================
// Reduce Motion Context
// ============================================================================

interface ReduceMotionContextValue {
  reduceMotion: boolean
  setReduceMotion: (value: boolean) => void
}

const ReduceMotionContext = createContext<ReduceMotionContextValue | undefined>(
  undefined
)

interface ReduceMotionProviderProps {
  children: React.ReactNode
  /** Override the initial value (for testing or user preference) */
  initialValue?: boolean
}

/**
 * ReduceMotionProvider
 *
 * Provides reduce motion preference throughout the app.
 * Respects system preference and allows user override.
 *
 * @example
 * ```tsx
 * // In app root
 * <ReduceMotionProvider>
 *   <App />
 * </ReduceMotionProvider>
 *
 * // In components
 * const reduceMotion = useReduceMotion()
 * ```
 */
export function ReduceMotionProvider({
  children,
  initialValue,
}: ReduceMotionProviderProps) {
  const [reduceMotion, setReduceMotion] = useState(() => {
    if (initialValue !== undefined) return initialValue
    // Check system preference
    if (typeof window !== "undefined") {
      return window.matchMedia("(prefers-reduced-motion: reduce)").matches
    }
    return false
  })

  // Listen for system preference changes
  useEffect(() => {
    if (typeof window === "undefined") return

    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)")
    const handler = (e: MediaQueryListEvent) => {
      // Only update if user hasn't set a manual preference
      // (we could add localStorage tracking here in the future)
      setReduceMotion(e.matches)
    }

    mediaQuery.addEventListener("change", handler)
    return () => mediaQuery.removeEventListener("change", handler)
  }, [])

  return (
    <ReduceMotionContext.Provider value={{ reduceMotion, setReduceMotion }}>
      {children}
    </ReduceMotionContext.Provider>
  )
}

/**
 * useReduceMotion
 *
 * Returns whether reduced motion is preferred.
 * Use this to conditionally disable animations.
 *
 * @example
 * ```tsx
 * const reduceMotion = useReduceMotion()
 * const transition = reduceMotion ? instantTransition : springConfig.snappy
 * ```
 */
export function useReduceMotion(): boolean {
  const context = useContext(ReduceMotionContext)
  if (context === undefined) {
    // Fallback: check system preference directly
    if (typeof window !== "undefined") {
      return window.matchMedia("(prefers-reduced-motion: reduce)").matches
    }
    return false
  }
  return context.reduceMotion
}

/**
 * useReduceMotionControl
 *
 * Returns both the value and setter for reduce motion.
 * Use in settings UI to toggle the preference.
 */
export function useReduceMotionControl(): ReduceMotionContextValue {
  const context = useContext(ReduceMotionContext)
  if (context === undefined) {
    throw new Error(
      "useReduceMotionControl must be used within ReduceMotionProvider"
    )
  }
  return context
}

// ============================================================================
// Animation Variants
// ============================================================================

/**
 * Common animation variants for reuse
 */
export const variants = {
  /** Fade in/out */
  fade: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
  },

  /** Scale + fade (for dialogs) */
  scaleIn: {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.95 },
  },

  /** Slide up (for sheets) */
  slideUp: {
    initial: { y: "100%" },
    animate: { y: 0 },
    exit: { y: "100%" },
  },

  /** Panel drag lift */
  dragLift: {
    rest: { scale: 1, boxShadow: "0 0 0 rgba(0,0,0,0)" },
    dragging: {
      scale: 1.02,
      boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
    },
  },

  /** Collapse/expand height */
  collapse: {
    open: { height: "auto", opacity: 1 },
    closed: { height: 0, opacity: 0 },
  },
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Get transition config based on reduce motion preference
 */
export function getTransition(
  config: typeof springConfig.snappy | typeof transitions.collapse,
  reduceMotion: boolean
) {
  return reduceMotion ? instantTransition : config
}
```

**Step 2: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

Expected: No errors related to motion.tsx

**Step 3: Commit**

```bash
git add frontend/src/components/ui/motion.tsx
git commit -m "feat(ui): add motion configuration primitive with spring configs"
```

---

### Task 3: Add ReduceMotionProvider to App

**Files:**
- Modify: `frontend/src/main.tsx`

**Step 1: Read current main.tsx structure**

```bash
# Worker: Read frontend/src/main.tsx to understand current provider structure
```

**Step 2: Wrap app with ReduceMotionProvider**

Add import and wrap the app:

```typescript
import { ReduceMotionProvider } from "@/components/ui/motion"

// In the render tree, wrap at appropriate level (inside QueryClientProvider):
<ReduceMotionProvider>
  {/* existing app content */}
</ReduceMotionProvider>
```

**Step 3: Verify app still loads**

```bash
cd /home/josep/dog/frontend && npm run dev
```

Open http://localhost:5173, verify no console errors.

**Step 4: Commit**

```bash
git add frontend/src/main.tsx
git commit -m "feat(app): wrap app with ReduceMotionProvider"
```

---

## Phase 2: Draggable Panel Primitive

### Task 4: Create DraggablePanel Primitive

**Files:**
- Create: `frontend/src/components/Room/primitives/DraggablePanel.tsx`
- Modify: `frontend/src/components/Room/primitives/index.ts`

**Step 1: Create DraggablePanel component**

```typescript
/**
 * DraggablePanel Primitive
 *
 * Wraps any panel with drag-and-drop functionality.
 * Provides drag handle, drag state, and drop zone detection.
 *
 * @example
 * ```tsx
 * <DraggablePanel
 *   panelId="chat"
 *   onDrop={(fromId, toId) => reorderPanels(fromId, toId)}
 * >
 *   <PanelContainer title="Chat">
 *     <ChatPanel />
 *   </PanelContainer>
 * </DraggablePanel>
 * ```
 */

import * as React from "react"
import { useState, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { GripVertical } from "lucide-react"
import { cn } from "@/lib/utils"
import {
  springConfig,
  variants,
  useReduceMotion,
  getTransition,
} from "@/components/ui/motion"

// ============================================================================
// Types
// ============================================================================

export interface DraggablePanelProps {
  /** Unique identifier for this panel */
  panelId: string
  /** Children to render inside the draggable wrapper */
  children: React.ReactNode
  /** Called when a panel is dropped onto this panel's drop zone */
  onDrop?: (draggedId: string, targetId: string, position: "before" | "after") => void
  /** Called when drag starts */
  onDragStart?: (panelId: string) => void
  /** Called when drag ends */
  onDragEnd?: (panelId: string) => void
  /** Whether dragging is disabled */
  disabled?: boolean
  /** Position of drag handle */
  dragHandlePosition?: "left" | "header"
  /** Additional className */
  className?: string
}

export interface DragHandleProps {
  /** Whether currently dragging */
  isDragging: boolean
  /** Mouse/touch event handlers */
  onPointerDown: (e: React.PointerEvent) => void
  /** Additional className */
  className?: string
}

// ============================================================================
// Drag Context (for coordinating between panels)
// ============================================================================

interface DragContextValue {
  draggedId: string | null
  setDraggedId: (id: string | null) => void
}

const DragContext = React.createContext<DragContextValue | undefined>(undefined)

/**
 * DragContextProvider
 *
 * Wrap panel groups to coordinate drag state between panels.
 */
export function DragContextProvider({ children }: { children: React.ReactNode }) {
  const [draggedId, setDraggedId] = useState<string | null>(null)

  return (
    <DragContext.Provider value={{ draggedId, setDraggedId }}>
      {children}
    </DragContext.Provider>
  )
}

function useDragContext() {
  const context = React.useContext(DragContext)
  if (!context) {
    // Return standalone state if no provider
    const [draggedId, setDraggedId] = useState<string | null>(null)
    return { draggedId, setDraggedId }
  }
  return context
}

// ============================================================================
// DragHandle Component
// ============================================================================

/**
 * DragHandle
 *
 * Visual handle for initiating drag. Renders as grip icon.
 */
export function DragHandle({ isDragging, onPointerDown, className }: DragHandleProps) {
  return (
    <button
      type="button"
      onPointerDown={onPointerDown}
      className={cn(
        "flex items-center justify-center p-1 rounded cursor-grab touch-none",
        "text-muted-foreground hover:text-foreground hover:bg-muted/50",
        "transition-colors",
        isDragging && "cursor-grabbing",
        className
      )}
      aria-label="Drag to reorder"
    >
      <GripVertical className="h-4 w-4" />
    </button>
  )
}

// ============================================================================
// DropZone Component
// ============================================================================

interface DropZoneProps {
  position: "before" | "after"
  isActive: boolean
  onDrop: () => void
  onDragEnter: () => void
  onDragLeave: () => void
}

function DropZone({
  position,
  isActive,
  onDrop,
  onDragEnter,
  onDragLeave,
}: DropZoneProps) {
  const reduceMotion = useReduceMotion()

  return (
    <motion.div
      className={cn(
        "absolute z-10 transition-opacity",
        position === "before" ? "left-0 -translate-x-1/2" : "right-0 translate-x-1/2",
        "top-0 bottom-0 w-4"
      )}
      onPointerEnter={onDragEnter}
      onPointerLeave={onDragLeave}
      onPointerUp={onDrop}
      initial={{ opacity: 0 }}
      animate={{ opacity: isActive ? 1 : 0 }}
      transition={getTransition(springConfig.snappy, reduceMotion)}
    >
      <div
        className={cn(
          "h-full w-1 mx-auto rounded-full",
          "bg-primary/50",
          isActive && "animate-pulse"
        )}
      />
    </motion.div>
  )
}

// ============================================================================
// DraggablePanel Component
// ============================================================================

export function DraggablePanel({
  panelId,
  children,
  onDrop,
  onDragStart,
  onDragEnd,
  disabled = false,
  dragHandlePosition = "header",
  className,
}: DraggablePanelProps) {
  const { draggedId, setDraggedId } = useDragContext()
  const [isDragging, setIsDragging] = useState(false)
  const [activeDropZone, setActiveDropZone] = useState<"before" | "after" | null>(null)
  const reduceMotion = useReduceMotion()

  const isBeingDragged = isDragging || draggedId === panelId
  const showDropZones = draggedId !== null && draggedId !== panelId

  const handlePointerDown = useCallback(
    (e: React.PointerEvent) => {
      if (disabled) return
      e.preventDefault()
      setIsDragging(true)
      setDraggedId(panelId)
      onDragStart?.(panelId)
    },
    [disabled, panelId, setDraggedId, onDragStart]
  )

  const handlePointerUp = useCallback(() => {
    if (!isDragging) return
    setIsDragging(false)
    setDraggedId(null)
    onDragEnd?.(panelId)
  }, [isDragging, panelId, setDraggedId, onDragEnd])

  // Global pointer up listener
  React.useEffect(() => {
    if (!isDragging) return

    const handleGlobalPointerUp = () => {
      setIsDragging(false)
      setDraggedId(null)
      onDragEnd?.(panelId)
    }

    window.addEventListener("pointerup", handleGlobalPointerUp)
    return () => window.removeEventListener("pointerup", handleGlobalPointerUp)
  }, [isDragging, panelId, setDraggedId, onDragEnd])

  const handleDrop = useCallback(
    (position: "before" | "after") => {
      if (draggedId && draggedId !== panelId && onDrop) {
        onDrop(draggedId, panelId, position)
      }
      setActiveDropZone(null)
    },
    [draggedId, panelId, onDrop]
  )

  // Clone children to inject drag handle
  const childrenWithHandle = React.Children.map(children, (child) => {
    if (!React.isValidElement(child)) return child

    // If child is PanelContainer, inject drag handle into headerActions
    if (dragHandlePosition === "header") {
      return React.cloneElement(child as React.ReactElement<any>, {
        headerActions: (
          <div className="flex items-center gap-1">
            <DragHandle
              isDragging={isBeingDragged}
              onPointerDown={handlePointerDown}
            />
            {(child as React.ReactElement<any>).props.headerActions}
          </div>
        ),
      })
    }

    return child
  })

  return (
    <motion.div
      className={cn("relative", className)}
      variants={variants.dragLift}
      initial="rest"
      animate={isBeingDragged ? "dragging" : "rest"}
      transition={getTransition(springConfig.snappy, reduceMotion)}
      style={{ zIndex: isBeingDragged ? 50 : undefined }}
    >
      {/* Drop zones */}
      {showDropZones && (
        <>
          <DropZone
            position="before"
            isActive={activeDropZone === "before"}
            onDrop={() => handleDrop("before")}
            onDragEnter={() => setActiveDropZone("before")}
            onDragLeave={() => setActiveDropZone(null)}
          />
          <DropZone
            position="after"
            isActive={activeDropZone === "after"}
            onDrop={() => handleDrop("after")}
            onDragEnter={() => setActiveDropZone("after")}
            onDragLeave={() => setActiveDropZone(null)}
          />
        </>
      )}

      {dragHandlePosition === "left" && (
        <div className="absolute left-0 top-0 bottom-0 flex items-start pt-3 -ml-6">
          <DragHandle
            isDragging={isBeingDragged}
            onPointerDown={handlePointerDown}
          />
        </div>
      )}

      {childrenWithHandle}
    </motion.div>
  )
}
```

**Step 2: Update primitives barrel export**

Add to `frontend/src/components/Room/primitives/index.ts`:

```typescript
export {
  DraggablePanel,
  DragContextProvider,
  DragHandle,
  type DraggablePanelProps,
  type DragHandleProps,
} from "./DraggablePanel"
```

**Step 3: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 4: Commit**

```bash
git add frontend/src/components/Room/primitives/DraggablePanel.tsx frontend/src/components/Room/primitives/index.ts
git commit -m "feat(room): add DraggablePanel primitive with drag-and-drop"
```

---

### Task 5: Create CollapsiblePanel Primitive

**Files:**
- Create: `frontend/src/components/Room/primitives/CollapsiblePanel.tsx`
- Modify: `frontend/src/components/Room/primitives/index.ts`

**Step 1: Create CollapsiblePanel component**

```typescript
/**
 * CollapsiblePanel Primitive
 *
 * Wraps any panel with collapse/expand functionality.
 * Animated height transition with content fade.
 *
 * @example
 * ```tsx
 * const [collapsed, setCollapsed] = useState(false)
 *
 * <CollapsiblePanel
 *   isCollapsed={collapsed}
 *   onToggle={() => setCollapsed(!collapsed)}
 *   title="Chat"
 * >
 *   <ChatPanel />
 * </CollapsiblePanel>
 * ```
 */

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Minus, Plus } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  transitions,
  useReduceMotion,
  getTransition,
} from "@/components/ui/motion"

// ============================================================================
// Types
// ============================================================================

export interface CollapsiblePanelProps {
  /** Whether the panel is collapsed */
  isCollapsed: boolean
  /** Called when collapse state should toggle */
  onToggle: () => void
  /** Panel title (shown in collapsed state) */
  title: string
  /** Children to render when expanded */
  children: React.ReactNode
  /** Height when collapsed (default: title bar only) */
  collapsedHeight?: number
  /** Additional className for outer wrapper */
  className?: string
  /** Additional className for collapsed title bar */
  titleBarClassName?: string
  /** Keyboard shortcut hint for tooltip */
  shortcutHint?: string
}

// ============================================================================
// CollapseButton Component
// ============================================================================

interface CollapseButtonProps {
  isCollapsed: boolean
  onToggle: () => void
  shortcutHint?: string
}

export function CollapseButton({
  isCollapsed,
  onToggle,
  shortcutHint,
}: CollapseButtonProps) {
  const Icon = isCollapsed ? Plus : Minus
  const label = isCollapsed ? "Expand panel" : "Collapse panel"
  const fullLabel = shortcutHint ? `${label} (${shortcutHint})` : label

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={onToggle}
          aria-label={fullLabel}
          aria-expanded={!isCollapsed}
        >
          <Icon className="h-4 w-4" />
        </Button>
      </TooltipTrigger>
      <TooltipContent side="bottom">
        <p>{fullLabel}</p>
      </TooltipContent>
    </Tooltip>
  )
}

// ============================================================================
// CollapsiblePanel Component
// ============================================================================

export function CollapsiblePanel({
  isCollapsed,
  onToggle,
  title,
  children,
  collapsedHeight = 48,
  className,
  titleBarClassName,
  shortcutHint,
}: CollapsiblePanelProps) {
  const reduceMotion = useReduceMotion()

  return (
    <motion.div
      className={cn("flex flex-col overflow-hidden", className)}
      initial={false}
      animate={{
        height: isCollapsed ? collapsedHeight : "auto",
      }}
      transition={getTransition(transitions.collapse, reduceMotion)}
    >
      {/* Collapsed title bar - always visible */}
      {isCollapsed && (
        <div
          className={cn(
            "flex items-center justify-between px-4 h-12 bg-background border-b border-border",
            titleBarClassName
          )}
        >
          <span className="text-sm font-medium text-muted-foreground">
            {title} <span className="text-xs">(collapsed)</span>
          </span>
          <CollapseButton
            isCollapsed={isCollapsed}
            onToggle={onToggle}
            shortcutHint={shortcutHint}
          />
        </div>
      )}

      {/* Content - animated */}
      <AnimatePresence mode="wait">
        {!isCollapsed && (
          <motion.div
            key="content"
            className="flex-1 min-h-0"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={getTransition(transitions.fade, reduceMotion)}
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

// ============================================================================
// Hook for managing collapse state
// ============================================================================

/**
 * useCollapsiblePanels
 *
 * Manages collapse state for multiple panels with localStorage persistence.
 *
 * @example
 * ```tsx
 * const { isCollapsed, toggle, collapseAll, expandAll } = useCollapsiblePanels({
 *   panelIds: ["chat", "agents", "debug"],
 *   storageKey: "room-panel-collapsed",
 * })
 *
 * <CollapsiblePanel isCollapsed={isCollapsed("chat")} onToggle={() => toggle("chat")}>
 * ```
 */
export function useCollapsiblePanels(options: {
  panelIds: string[]
  storageKey?: string
  defaultCollapsed?: string[]
}) {
  const { panelIds, storageKey, defaultCollapsed = [] } = options

  const [collapsed, setCollapsed] = React.useState<Set<string>>(() => {
    if (storageKey && typeof window !== "undefined") {
      const stored = localStorage.getItem(storageKey)
      if (stored) {
        try {
          return new Set(JSON.parse(stored))
        } catch {
          // Invalid JSON, use defaults
        }
      }
    }
    return new Set(defaultCollapsed)
  })

  // Persist to localStorage
  React.useEffect(() => {
    if (storageKey && typeof window !== "undefined") {
      localStorage.setItem(storageKey, JSON.stringify([...collapsed]))
    }
  }, [collapsed, storageKey])

  const isCollapsed = React.useCallback(
    (panelId: string) => collapsed.has(panelId),
    [collapsed]
  )

  const toggle = React.useCallback((panelId: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev)
      if (next.has(panelId)) {
        next.delete(panelId)
      } else {
        next.add(panelId)
      }
      return next
    })
  }, [])

  const collapseAll = React.useCallback(() => {
    setCollapsed(new Set(panelIds))
  }, [panelIds])

  const expandAll = React.useCallback(() => {
    setCollapsed(new Set())
  }, [])

  return { isCollapsed, toggle, collapseAll, expandAll }
}
```

**Step 2: Update primitives barrel export**

Add to `frontend/src/components/Room/primitives/index.ts`:

```typescript
export {
  CollapsiblePanel,
  CollapseButton,
  useCollapsiblePanels,
  type CollapsiblePanelProps,
} from "./CollapsiblePanel"
```

**Step 3: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 4: Commit**

```bash
git add frontend/src/components/Room/primitives/CollapsiblePanel.tsx frontend/src/components/Room/primitives/index.ts
git commit -m "feat(room): add CollapsiblePanel primitive with animated collapse"
```

---

### Task 6: Create MiniPreview Primitive

**Files:**
- Create: `frontend/src/components/Room/primitives/MiniPreview.tsx`
- Modify: `frontend/src/components/Room/primitives/index.ts`

**Step 1: Create MiniPreview component**

```typescript
/**
 * MiniPreview Primitive
 *
 * Small visual representation of a panel layout.
 * Used in preset picker, settings dialogs, and Users page.
 *
 * @example
 * ```tsx
 * <MiniPreview
 *   panels={[
 *     { id: "chat", kind: "chat", prominence: "primary" },
 *     { id: "agents", kind: "agentPanel", prominence: "auxiliary" },
 *   ]}
 * />
 * ```
 */

import * as React from "react"
import { cn } from "@/lib/utils"

// ============================================================================
// Types
// ============================================================================

export interface MiniPreviewPanel {
  id: string
  kind: string
  prominence: "primary" | "auxiliary"
}

export interface MiniPreviewProps {
  /** Panels to display */
  panels: MiniPreviewPanel[]
  /** Width of the preview (default: 120) */
  width?: number
  /** Height of the preview (default: 80) */
  height?: number
  /** Show panel labels */
  showLabels?: boolean
  /** Additional className */
  className?: string
}

// ============================================================================
// Panel kind to display name mapping
// ============================================================================

const panelNames: Record<string, string> = {
  chat: "Chat",
  storyEditor: "Story",
  agentPanel: "Agents",
  debug: "Debug",
  canvas: "Canvas",
  a2ui: "A2UI",
}

// ============================================================================
// Panel kind to color mapping (using CSS variables)
// ============================================================================

const panelColors: Record<string, string> = {
  chat: "bg-blue-500/20 border-blue-500/30",
  storyEditor: "bg-purple-500/20 border-purple-500/30",
  agentPanel: "bg-green-500/20 border-green-500/30",
  debug: "bg-orange-500/20 border-orange-500/30",
  canvas: "bg-pink-500/20 border-pink-500/30",
  a2ui: "bg-cyan-500/20 border-cyan-500/30",
}

// ============================================================================
// MiniPreview Component
// ============================================================================

export function MiniPreview({
  panels,
  width = 120,
  height = 80,
  showLabels = true,
  className,
}: MiniPreviewProps) {
  const primaryPanels = panels.filter((p) => p.prominence === "primary")
  const auxiliaryPanels = panels.filter((p) => p.prominence === "auxiliary")

  const hasPrimary = primaryPanels.length > 0
  const hasAuxiliary = auxiliaryPanels.length > 0

  // Calculate proportions
  const primaryWidth = hasAuxiliary ? 0.7 : 1
  const auxiliaryWidth = 0.3

  return (
    <div
      className={cn(
        "flex rounded border border-border bg-muted/30 overflow-hidden",
        className
      )}
      style={{ width, height }}
      role="img"
      aria-label={`Layout preview: ${panels.map((p) => panelNames[p.kind] || p.kind).join(", ")}`}
    >
      {/* Primary panels */}
      {hasPrimary && (
        <div
          className="flex gap-0.5 p-0.5"
          style={{ width: `${primaryWidth * 100}%` }}
        >
          {primaryPanels.map((panel) => (
            <div
              key={panel.id}
              className={cn(
                "flex-1 rounded-sm border flex items-center justify-center",
                panelColors[panel.kind] || "bg-muted border-border"
              )}
            >
              {showLabels && (
                <span className="text-[8px] text-muted-foreground font-medium truncate px-0.5">
                  {panelNames[panel.kind] || panel.kind}
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Auxiliary panels (stacked) */}
      {hasAuxiliary && (
        <div
          className="flex flex-col gap-0.5 p-0.5 border-l border-border"
          style={{ width: `${auxiliaryWidth * 100}%` }}
        >
          {auxiliaryPanels.map((panel) => (
            <div
              key={panel.id}
              className={cn(
                "flex-1 rounded-sm border flex items-center justify-center",
                panelColors[panel.kind] || "bg-muted border-border"
              )}
            >
              {showLabels && (
                <span className="text-[6px] text-muted-foreground font-medium truncate px-0.5">
                  {panelNames[panel.kind]?.substring(0, 3) || panel.kind.substring(0, 3)}
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {panels.length === 0 && (
        <div className="flex-1 flex items-center justify-center">
          <span className="text-[8px] text-muted-foreground">Empty</span>
        </div>
      )}
    </div>
  )
}
```

**Step 2: Update primitives barrel export**

Add to `frontend/src/components/Room/primitives/index.ts`:

```typescript
export {
  MiniPreview,
  type MiniPreviewPanel,
  type MiniPreviewProps,
} from "./MiniPreview"
```

**Step 3: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 4: Commit**

```bash
git add frontend/src/components/Room/primitives/MiniPreview.tsx frontend/src/components/Room/primitives/index.ts
git commit -m "feat(room): add MiniPreview primitive for layout visualization"
```

---

### Task 7: Create PresetPicker Primitive

**Files:**
- Create: `frontend/src/components/Room/primitives/PresetPicker.tsx`
- Modify: `frontend/src/components/Room/primitives/index.ts`

**Step 1: Create PresetPicker component**

```typescript
/**
 * PresetPicker Primitive
 *
 * Dropdown/button group for selecting layout presets.
 * Shows mini-previews of each preset option.
 *
 * @example
 * ```tsx
 * <PresetPicker
 *   presets={systemPresets}
 *   currentPresetId="collaborate"
 *   onSelect={(id) => applyPreset(id)}
 * />
 * ```
 */

import * as React from "react"
import { Check, ChevronDown, Layout } from "lucide-react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { MiniPreview, type MiniPreviewPanel } from "./MiniPreview"
import { springConfig, useReduceMotion, getTransition } from "@/components/ui/motion"

// ============================================================================
// Types
// ============================================================================

export interface Preset {
  id: string
  name: string
  description?: string
  panels: MiniPreviewPanel[]
}

export interface PresetPickerProps {
  /** Available presets */
  presets: Preset[]
  /** Currently selected preset ID (null if custom) */
  currentPresetId: string | null
  /** Called when a preset is selected */
  onSelect: (presetId: string) => void
  /** Display variant */
  variant?: "dropdown" | "buttons"
  /** Additional className */
  className?: string
}

// ============================================================================
// PresetButton Component (for button variant)
// ============================================================================

interface PresetButtonProps {
  preset: Preset
  isSelected: boolean
  onSelect: () => void
}

function PresetButton({ preset, isSelected, onSelect }: PresetButtonProps) {
  const reduceMotion = useReduceMotion()

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <motion.button
          type="button"
          onClick={onSelect}
          className={cn(
            "flex flex-col items-center gap-2 p-2 rounded-lg border transition-colors",
            isSelected
              ? "border-primary bg-primary/5"
              : "border-transparent hover:border-border hover:bg-muted/50"
          )}
          whileHover={{ scale: reduceMotion ? 1 : 1.02 }}
          whileTap={{ scale: reduceMotion ? 1 : 0.98 }}
          transition={getTransition(springConfig.snappy, reduceMotion)}
        >
          <MiniPreview panels={preset.panels} width={80} height={50} showLabels={false} />
          <span className="text-xs font-medium">{preset.name}</span>
          {isSelected && (
            <Check className="h-3 w-3 text-primary absolute top-1 right-1" />
          )}
        </motion.button>
      </TooltipTrigger>
      <TooltipContent>
        <p>{preset.description || preset.name}</p>
      </TooltipContent>
    </Tooltip>
  )
}

// ============================================================================
// PresetPicker Component
// ============================================================================

export function PresetPicker({
  presets,
  currentPresetId,
  onSelect,
  variant = "dropdown",
  className,
}: PresetPickerProps) {
  const currentPreset = presets.find((p) => p.id === currentPresetId)

  if (variant === "buttons") {
    return (
      <div className={cn("flex flex-wrap gap-2", className)}>
        {presets.map((preset) => (
          <PresetButton
            key={preset.id}
            preset={preset}
            isSelected={preset.id === currentPresetId}
            onSelect={() => onSelect(preset.id)}
          />
        ))}
      </div>
    )
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className={cn("gap-2", className)}>
          <Layout className="h-4 w-4" />
          <span>{currentPreset?.name || "Custom"}</span>
          <ChevronDown className="h-4 w-4 opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-64">
        {presets.map((preset) => (
          <DropdownMenuItem
            key={preset.id}
            onClick={() => onSelect(preset.id)}
            className="flex items-center gap-3 p-3"
          >
            <MiniPreview
              panels={preset.panels}
              width={60}
              height={40}
              showLabels={false}
            />
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm">{preset.name}</p>
              {preset.description && (
                <p className="text-xs text-muted-foreground truncate">
                  {preset.description}
                </p>
              )}
            </div>
            {preset.id === currentPresetId && (
              <Check className="h-4 w-4 text-primary shrink-0" />
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

// ============================================================================
// System Presets (constant data)
// ============================================================================

export const SYSTEM_PRESETS: Preset[] = [
  {
    id: "focus",
    name: "Focus",
    description: "Chat only, full width",
    panels: [{ id: "chat", kind: "chat", prominence: "primary" }],
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
  {
    id: "story_mode",
    name: "Story Mode",
    description: "Story editor with chat",
    panels: [
      { id: "story", kind: "storyEditor", prominence: "primary" },
      { id: "chat", kind: "chat", prominence: "primary" },
      { id: "agents", kind: "agentPanel", prominence: "auxiliary" },
    ],
  },
  {
    id: "debug",
    name: "Debug",
    description: "Chat with debug info",
    panels: [
      { id: "chat", kind: "chat", prominence: "primary" },
      { id: "debug", kind: "debug", prominence: "auxiliary" },
      { id: "agents", kind: "agentPanel", prominence: "auxiliary" },
    ],
  },
  {
    id: "canvas",
    name: "Canvas",
    description: "Canvas with chat",
    panels: [
      { id: "canvas", kind: "canvas", prominence: "primary" },
      { id: "chat", kind: "chat", prominence: "primary" },
      { id: "agents", kind: "agentPanel", prominence: "auxiliary" },
    ],
  },
]
```

**Step 2: Update primitives barrel export**

Add to `frontend/src/components/Room/primitives/index.ts`:

```typescript
export {
  PresetPicker,
  SYSTEM_PRESETS,
  type Preset,
  type PresetPickerProps,
} from "./PresetPicker"
```

**Step 3: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 4: Commit**

```bash
git add frontend/src/components/Room/primitives/PresetPicker.tsx frontend/src/components/Room/primitives/index.ts
git commit -m "feat(room): add PresetPicker primitive with system presets"
```

---

### Task 8: Create KeyboardShortcutProvider Primitive

**Files:**
- Create: `frontend/src/components/Room/primitives/KeyboardShortcutProvider.tsx`
- Modify: `frontend/src/components/Room/primitives/index.ts`

**Step 1: Create KeyboardShortcutProvider component**

```typescript
/**
 * KeyboardShortcutProvider Primitive
 *
 * React context for registering and handling keyboard shortcuts.
 * Platform-aware (Cmd on Mac, Ctrl on Windows/Linux).
 *
 * @example
 * ```tsx
 * const shortcuts = [
 *   { key: "1", modifiers: ["mod"], action: () => focusPanel(0), description: "Focus first panel" },
 *   { key: "l", modifiers: ["mod", "shift"], action: () => openSettings(), description: "Open layout" },
 * ]
 *
 * <KeyboardShortcutProvider shortcuts={shortcuts}>
 *   <RoomContent />
 * </KeyboardShortcutProvider>
 * ```
 */

import * as React from "react"
import { createContext, useContext, useEffect, useCallback, useMemo } from "react"

// ============================================================================
// Types
// ============================================================================

export type Modifier = "mod" | "shift" | "alt" | "ctrl"

export interface KeyboardShortcut {
  /** The key to listen for (lowercase) */
  key: string
  /** Required modifiers */
  modifiers: Modifier[]
  /** Action to execute */
  action: () => void
  /** Description for display */
  description: string
  /** Whether this shortcut is currently enabled */
  enabled?: boolean
}

interface KeyboardShortcutContextValue {
  /** Register a shortcut */
  registerShortcut: (shortcut: KeyboardShortcut) => () => void
  /** Get all registered shortcuts */
  getShortcuts: () => KeyboardShortcut[]
  /** Whether we're on Mac */
  isMac: boolean
  /** Format a shortcut for display (e.g., "⌘⇧L" or "Ctrl+Shift+L") */
  formatShortcut: (modifiers: Modifier[], key: string) => string
}

// ============================================================================
// Context
// ============================================================================

const KeyboardShortcutContext = createContext<KeyboardShortcutContextValue | undefined>(
  undefined
)

// ============================================================================
// Platform Detection
// ============================================================================

function detectPlatform(): boolean {
  if (typeof navigator === "undefined") return false
  return /Mac|iPod|iPhone|iPad/.test(navigator.platform)
}

// ============================================================================
// Shortcut Formatting
// ============================================================================

const MAC_SYMBOLS: Record<Modifier | string, string> = {
  mod: "⌘",
  ctrl: "⌃",
  shift: "⇧",
  alt: "⌥",
}

const WIN_SYMBOLS: Record<Modifier | string, string> = {
  mod: "Ctrl",
  ctrl: "Ctrl",
  shift: "Shift",
  alt: "Alt",
}

function formatShortcutKey(key: string): string {
  const specialKeys: Record<string, string> = {
    escape: "Esc",
    arrowup: "↑",
    arrowdown: "↓",
    arrowleft: "←",
    arrowright: "→",
    enter: "↵",
    backspace: "⌫",
    delete: "Del",
    tab: "Tab",
    space: "Space",
  }
  return specialKeys[key.toLowerCase()] || key.toUpperCase()
}

// ============================================================================
// KeyboardShortcutProvider Component
// ============================================================================

interface KeyboardShortcutProviderProps {
  children: React.ReactNode
  /** Initial shortcuts to register */
  shortcuts?: KeyboardShortcut[]
  /** Whether shortcuts are globally enabled */
  enabled?: boolean
}

export function KeyboardShortcutProvider({
  children,
  shortcuts: initialShortcuts = [],
  enabled = true,
}: KeyboardShortcutProviderProps) {
  const isMac = useMemo(() => detectPlatform(), [])
  const shortcutsRef = React.useRef<Map<string, KeyboardShortcut>>(new Map())

  // Initialize with provided shortcuts
  useEffect(() => {
    initialShortcuts.forEach((shortcut) => {
      const key = `${shortcut.modifiers.sort().join("+")}+${shortcut.key}`
      shortcutsRef.current.set(key, shortcut)
    })
  }, [initialShortcuts])

  const registerShortcut = useCallback((shortcut: KeyboardShortcut) => {
    const key = `${shortcut.modifiers.sort().join("+")}+${shortcut.key}`
    shortcutsRef.current.set(key, shortcut)

    // Return unregister function
    return () => {
      shortcutsRef.current.delete(key)
    }
  }, [])

  const getShortcuts = useCallback(() => {
    return Array.from(shortcutsRef.current.values())
  }, [])

  const formatShortcut = useCallback(
    (modifiers: Modifier[], key: string) => {
      const symbols = isMac ? MAC_SYMBOLS : WIN_SYMBOLS
      const modString = modifiers
        .map((m) => symbols[m] || m)
        .join(isMac ? "" : "+")
      const keyString = formatShortcutKey(key)

      return isMac ? `${modString}${keyString}` : `${modString}+${keyString}`
    },
    [isMac]
  )

  // Global keyboard listener
  useEffect(() => {
    if (!enabled) return

    const handleKeyDown = (e: KeyboardEvent) => {
      // Skip if focus is in an input/textarea
      const target = e.target as HTMLElement
      if (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable
      ) {
        // Allow Escape to still work
        if (e.key !== "Escape") return
      }

      // Build modifier set
      const activeModifiers: Modifier[] = []
      if (e.metaKey || e.ctrlKey) activeModifiers.push("mod")
      if (e.shiftKey) activeModifiers.push("shift")
      if (e.altKey) activeModifiers.push("alt")

      // Also check explicit ctrl on non-Mac
      if (!isMac && e.ctrlKey && !activeModifiers.includes("mod")) {
        activeModifiers.push("ctrl")
      }

      const key = `${activeModifiers.sort().join("+")}+${e.key.toLowerCase()}`
      const shortcut = shortcutsRef.current.get(key)

      if (shortcut && shortcut.enabled !== false) {
        e.preventDefault()
        shortcut.action()
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [enabled, isMac])

  const value = useMemo(
    () => ({
      registerShortcut,
      getShortcuts,
      isMac,
      formatShortcut,
    }),
    [registerShortcut, getShortcuts, isMac, formatShortcut]
  )

  return (
    <KeyboardShortcutContext.Provider value={value}>
      {children}
    </KeyboardShortcutContext.Provider>
  )
}

// ============================================================================
// Hooks
// ============================================================================

/**
 * useKeyboardShortcuts
 *
 * Access the keyboard shortcut context.
 */
export function useKeyboardShortcuts(): KeyboardShortcutContextValue {
  const context = useContext(KeyboardShortcutContext)
  if (!context) {
    throw new Error(
      "useKeyboardShortcuts must be used within KeyboardShortcutProvider"
    )
  }
  return context
}

/**
 * useShortcut
 *
 * Register a single shortcut. Automatically unregisters on unmount.
 *
 * @example
 * ```tsx
 * useShortcut({
 *   key: "l",
 *   modifiers: ["mod", "shift"],
 *   action: () => setOpen(true),
 *   description: "Open layout settings",
 * })
 * ```
 */
export function useShortcut(shortcut: KeyboardShortcut) {
  const { registerShortcut } = useKeyboardShortcuts()

  useEffect(() => {
    return registerShortcut(shortcut)
  }, [registerShortcut, shortcut.key, shortcut.modifiers.join(",")])
}

/**
 * useShortcutDisplay
 *
 * Get formatted shortcut string for display.
 *
 * @example
 * ```tsx
 * const display = useShortcutDisplay(["mod", "shift"], "l")
 * // Returns "⌘⇧L" on Mac, "Ctrl+Shift+L" on Windows
 * ```
 */
export function useShortcutDisplay(modifiers: Modifier[], key: string): string {
  const { formatShortcut } = useKeyboardShortcuts()
  return formatShortcut(modifiers, key)
}
```

**Step 2: Update primitives barrel export**

Add to `frontend/src/components/Room/primitives/index.ts`:

```typescript
export {
  KeyboardShortcutProvider,
  useKeyboardShortcuts,
  useShortcut,
  useShortcutDisplay,
  type KeyboardShortcut,
  type Modifier,
} from "./KeyboardShortcutProvider"
```

**Step 3: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 4: Commit**

```bash
git add frontend/src/components/Room/primitives/KeyboardShortcutProvider.tsx frontend/src/components/Room/primitives/index.ts
git commit -m "feat(room): add KeyboardShortcutProvider with platform-aware shortcuts"
```

---

## Phase 3: Backend Models & API

### Task 9: Add User Panel Defaults Model

**Files:**
- Modify: `backend/app/models.py`

**Step 1: Add UserPanelDefaults model**

Add to `backend/app/models.py` in the Room Panel Configuration section:

```python
class UserPanelDefaults(SQLModel, table=True):
    """User's global default panel layout (applies to all rooms)"""
    __tablename__ = "user_panel_defaults"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", unique=True, index=True)
    preset_id: str | None = Field(default=None)  # "focus", "collaborate", etc.
    panels: list[dict] = Field(default=[], sa_column=Column(JSON))
    reduce_motion: bool = Field(default=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserPanelDefaultsPublic(SQLModel):
    """Public response for user panel defaults"""
    id: uuid.UUID
    user_id: uuid.UUID
    preset_id: str | None
    panels: list[dict]
    reduce_motion: bool
    updated_at: datetime


class UserPanelDefaultsUpdate(SQLModel):
    """Update payload for user panel defaults"""
    preset_id: str | None = None
    panels: list[dict] | None = None
    reduce_motion: bool | None = None
```

**Step 2: Add PanelPreset model (future-proofing)**

```python
class PanelPreset(SQLModel, table=True):
    """Panel layout preset (system or user-created)"""
    __tablename__ = "panel_presets"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", index=True)
    name: str
    description: str | None = None
    panels: list[dict] = Field(sa_column=Column(JSON))
    is_system: bool = Field(default=False)
    shared_to_room_id: uuid.UUID | None = Field(default=None, foreign_key="rooms.room_id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PanelPresetPublic(SQLModel):
    """Public response for panel preset"""
    id: uuid.UUID
    owner_id: uuid.UUID | None
    name: str
    description: str | None
    panels: list[dict]
    is_system: bool
    created_at: datetime
```

**Step 3: Verify no import errors**

```bash
cd /home/josep/dog/backend && python -c "from app.models import UserPanelDefaults, PanelPreset; print('OK')"
```

**Step 4: Commit (migration in next task)**

```bash
git add backend/app/models.py
git commit -m "feat(models): add UserPanelDefaults and PanelPreset models"
```

---

### Task 10: Create Migration for New Models

**Files:**
- Create: `backend/app/alembic/versions/<auto>_add_user_panel_defaults.py`

**Step 1: Generate migration**

```bash
cd /home/josep/dog/backend && alembic revision --autogenerate -m "Add user panel defaults and presets"
```

**Step 2: Review generated migration**

Open the generated file and verify it creates:
- `user_panel_defaults` table
- `panel_presets` table
- Proper foreign keys and indexes

**Step 3: Apply migration**

```bash
cd /home/josep/dog/backend && alembic upgrade head
```

**Step 4: Verify tables exist**

```bash
cd /home/josep/dog/backend && python -c "
from sqlmodel import Session, select
from app.core.db import engine
from app.models import UserPanelDefaults, PanelPreset
with Session(engine) as session:
    print('Tables created successfully')
"
```

**Step 5: Commit**

```bash
git add backend/app/alembic/versions/
git commit -m "feat(db): add migration for user panel defaults and presets"
```

---

### Task 11: Create User Panel Defaults CRUD

**Files:**
- Create: `backend/app/crud_user_panels.py`

**Step 1: Create CRUD functions**

```python
"""
CRUD operations for user panel defaults.
"""

from uuid import UUID
from datetime import datetime
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserPanelDefaults, UserPanelDefaultsUpdate


async def get_user_panel_defaults(
    session: AsyncSession, user_id: UUID
) -> UserPanelDefaults | None:
    """Get user's global panel defaults."""
    statement = select(UserPanelDefaults).where(
        UserPanelDefaults.user_id == user_id
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def create_user_panel_defaults(
    session: AsyncSession,
    user_id: UUID,
    preset_id: str | None = None,
    panels: list[dict] | None = None,
    reduce_motion: bool = False,
) -> UserPanelDefaults:
    """Create user's panel defaults."""
    defaults = UserPanelDefaults(
        user_id=user_id,
        preset_id=preset_id,
        panels=panels or [],
        reduce_motion=reduce_motion,
    )
    session.add(defaults)
    await session.commit()
    await session.refresh(defaults)
    return defaults


async def update_user_panel_defaults(
    session: AsyncSession,
    user_id: UUID,
    update_data: UserPanelDefaultsUpdate,
) -> UserPanelDefaults:
    """Update user's panel defaults, creating if doesn't exist."""
    existing = await get_user_panel_defaults(session, user_id)

    if existing:
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(existing, key, value)
        existing.updated_at = datetime.utcnow()
        session.add(existing)
    else:
        existing = UserPanelDefaults(
            user_id=user_id,
            preset_id=update_data.preset_id,
            panels=update_data.panels or [],
            reduce_motion=update_data.reduce_motion or False,
        )
        session.add(existing)

    await session.commit()
    await session.refresh(existing)
    return existing


async def delete_user_panel_defaults(
    session: AsyncSession, user_id: UUID
) -> bool:
    """Delete user's panel defaults."""
    existing = await get_user_panel_defaults(session, user_id)
    if existing:
        await session.delete(existing)
        await session.commit()
        return True
    return False
```

**Step 2: Verify no import errors**

```bash
cd /home/josep/dog/backend && python -c "from app.crud_user_panels import get_user_panel_defaults; print('OK')"
```

**Step 3: Commit**

```bash
git add backend/app/crud_user_panels.py
git commit -m "feat(crud): add user panel defaults CRUD operations"
```

---

### Task 12: Create User Panel Defaults Routes

**Files:**
- Create: `backend/app/api/routes/user_panels.py`
- Modify: `backend/app/api/main.py`

**Step 1: Create routes**

```python
"""
API routes for user panel defaults.
"""

from typing import Any
from fastapi import APIRouter, HTTPException, status

from app.api.deps import AsyncSessionDep, CurrentUser
from app.crud_user_panels import (
    get_user_panel_defaults,
    update_user_panel_defaults,
)
from app.models import (
    UserPanelDefaultsPublic,
    UserPanelDefaultsUpdate,
)

router = APIRouter()


@router.get("/me/panel-defaults", response_model=UserPanelDefaultsPublic | None)
async def get_my_panel_defaults(
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> Any:
    """Get current user's global panel defaults."""
    return await get_user_panel_defaults(session, current_user.id)


@router.put("/me/panel-defaults", response_model=UserPanelDefaultsPublic)
async def update_my_panel_defaults(
    update_data: UserPanelDefaultsUpdate,
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> Any:
    """Update current user's global panel defaults."""
    return await update_user_panel_defaults(
        session, current_user.id, update_data
    )
```

**Step 2: Register router in main.py**

Add to `backend/app/api/main.py`:

```python
from app.api.routes import user_panels

api_router.include_router(
    user_panels.router,
    prefix="/users",
    tags=["user-panels"],
)
```

**Step 3: Verify backend starts**

```bash
cd /home/josep/dog/backend && timeout 5 fastapi dev app/main.py || true
```

Check `/docs` for new endpoints.

**Step 4: Commit**

```bash
git add backend/app/api/routes/user_panels.py backend/app/api/main.py
git commit -m "feat(api): add user panel defaults endpoints"
```

---

### Task 13: Create Presets Routes

**Files:**
- Create: `backend/app/api/routes/presets.py`
- Modify: `backend/app/api/main.py`

**Step 1: Create system presets constant**

```python
"""
API routes for panel presets.
"""

from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


# System presets (not stored in DB)
SYSTEM_PRESETS = {
    "focus": {
        "id": "focus",
        "name": "Focus",
        "description": "Chat only, full width",
        "panels": [{"id": "chat", "kind": "chat", "prominence": "primary"}],
        "is_system": True,
    },
    "collaborate": {
        "id": "collaborate",
        "name": "Collaborate",
        "description": "Chat with agents sidebar",
        "panels": [
            {"id": "chat", "kind": "chat", "prominence": "primary"},
            {"id": "agents", "kind": "agentPanel", "prominence": "auxiliary"},
        ],
        "is_system": True,
    },
    "story_mode": {
        "id": "story_mode",
        "name": "Story Mode",
        "description": "Story editor with chat",
        "panels": [
            {"id": "story", "kind": "storyEditor", "prominence": "primary"},
            {"id": "chat", "kind": "chat", "prominence": "primary"},
            {"id": "agents", "kind": "agentPanel", "prominence": "auxiliary"},
        ],
        "is_system": True,
    },
    "debug": {
        "id": "debug",
        "name": "Debug",
        "description": "Chat with debug info",
        "panels": [
            {"id": "chat", "kind": "chat", "prominence": "primary"},
            {"id": "debug", "kind": "debug", "prominence": "auxiliary"},
            {"id": "agents", "kind": "agentPanel", "prominence": "auxiliary"},
        ],
        "is_system": True,
    },
    "canvas": {
        "id": "canvas",
        "name": "Canvas",
        "description": "Canvas with chat",
        "panels": [
            {"id": "canvas", "kind": "canvas", "prominence": "primary"},
            {"id": "chat", "kind": "chat", "prominence": "primary"},
            {"id": "agents", "kind": "agentPanel", "prominence": "auxiliary"},
        ],
        "is_system": True,
    },
}


class PresetResponse(BaseModel):
    id: str
    name: str
    description: str
    panels: list[dict]
    is_system: bool


class PresetsListResponse(BaseModel):
    presets: list[PresetResponse]


@router.get("", response_model=PresetsListResponse)
async def list_presets() -> Any:
    """List all available presets (system presets only for now)."""
    return PresetsListResponse(
        presets=[PresetResponse(**p) for p in SYSTEM_PRESETS.values()]
    )


@router.get("/{preset_id}", response_model=PresetResponse)
async def get_preset(preset_id: str) -> Any:
    """Get a specific preset by ID."""
    preset = SYSTEM_PRESETS.get(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return PresetResponse(**preset)
```

**Step 2: Register router in main.py**

Add to `backend/app/api/main.py`:

```python
from app.api.routes import presets

api_router.include_router(
    presets.router,
    prefix="/presets",
    tags=["presets"],
)
```

**Step 3: Verify backend starts**

```bash
cd /home/josep/dog/backend && timeout 5 fastapi dev app/main.py || true
```

**Step 4: Commit**

```bash
git add backend/app/api/routes/presets.py backend/app/api/main.py
git commit -m "feat(api): add presets listing endpoint"
```

---

### Task 14: Update Panel Resolution Logic

**Files:**
- Modify: `backend/app/crud_panels.py`

**Step 1: Update resolve_panels_for_user function**

Update the function in `backend/app/crud_panels.py` to include user defaults:

```python
from app.crud_user_panels import get_user_panel_defaults
from app.api.routes.presets import SYSTEM_PRESETS


async def resolve_panels_for_user(
    session: AsyncSession, user_id: UUID, room_id: UUID
) -> tuple[list[dict], str]:
    """
    Resolve the effective panel configuration for a user in a room.

    Returns: (panels, source) where source is one of:
        - "room_override": User has custom config for this room
        - "room_defaults": Using room owner's defaults
        - "user_defaults": Using user's global defaults
        - "system_defaults": Using built-in system defaults
    """
    # 1. Check for user's room override
    user_room_config = await get_user_room_panel_config(session, user_id, room_id)
    if user_room_config and not user_room_config.use_room_defaults and user_room_config.panels:
        return user_room_config.panels, "room_override"

    # 2. Check for room defaults (set by owner)
    room_defaults = await get_room_panel_defaults(session, room_id)
    if room_defaults and room_defaults.panels:
        return room_defaults.panels, "room_defaults"

    # 3. Check for user's global defaults
    user_defaults = await get_user_panel_defaults(session, user_id)
    if user_defaults:
        # If user has a preset selected, use that
        if user_defaults.preset_id and user_defaults.preset_id in SYSTEM_PRESETS:
            return SYSTEM_PRESETS[user_defaults.preset_id]["panels"], "user_defaults"
        # Otherwise use their custom panels
        if user_defaults.panels:
            return user_defaults.panels, "user_defaults"

    # 4. Fall back to system default (collaborate)
    return SYSTEM_PRESETS["collaborate"]["panels"], "system_defaults"
```

**Step 2: Update imports at top of file**

```python
from app.crud_user_panels import get_user_panel_defaults
from app.api.routes.presets import SYSTEM_PRESETS
```

**Step 3: Verify no import errors**

```bash
cd /home/josep/dog/backend && python -c "from app.crud_panels import resolve_panels_for_user; print('OK')"
```

**Step 4: Commit**

```bash
git add backend/app/crud_panels.py
git commit -m "feat(crud): update panel resolution to include user defaults"
```

---

## Phase 4: Frontend Services & Hooks

### Task 15: Regenerate API Client

**Files:**
- Modify: `frontend/src/client/` (auto-generated)

**Step 1: Regenerate client**

```bash
cd /home/josep/dog/frontend && npm run generate-client
```

**Step 2: Verify new types exist**

```bash
grep -l "UserPanelDefaults" frontend/src/client/ || echo "Type not found - check generation"
```

**Step 3: Commit**

```bash
git add frontend/src/client/
git commit -m "chore(client): regenerate API client with panel defaults types"
```

---

### Task 16: Create User Panel Defaults Service

**Files:**
- Create: `frontend/src/services/userPanelDefaultsService.ts`

**Step 1: Create service**

```typescript
/**
 * User Panel Defaults Service
 *
 * Manages user's global default panel layout.
 * Uses ViewModel pattern - never expose raw API types to components.
 *
 * @see panelService.ts for room-level panel operations
 */

import {
  type UserPanelDefaultsPublic,
  type UserPanelDefaultsUpdate,
  UserPanelsService,
} from "@/client"

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * User panel defaults ViewModel
 */
export interface UserPanelDefaultsViewModel {
  id: string
  userId: string
  presetId: string | null
  panels: PanelConfigItem[]
  reduceMotion: boolean
  updatedAt: Date
}

export interface PanelConfigItem {
  id: string
  kind: string
  prominence: "primary" | "auxiliary"
}

export interface UpdateUserPanelDefaultsInput {
  presetId?: string | null
  panels?: PanelConfigItem[] | null
  reduceMotion?: boolean
}

// ============================================================================
// Mappers
// ============================================================================

function toViewModel(
  data: UserPanelDefaultsPublic
): UserPanelDefaultsViewModel {
  return {
    id: data.id,
    userId: data.user_id,
    presetId: data.preset_id ?? null,
    panels: (data.panels ?? []) as PanelConfigItem[],
    reduceMotion: data.reduce_motion,
    updatedAt: new Date(data.updated_at),
  }
}

// ============================================================================
// Service Functions
// ============================================================================

/**
 * Get current user's global panel defaults
 */
export async function getUserPanelDefaults(): Promise<UserPanelDefaultsViewModel | null> {
  const response = await UserPanelsService.getMyPanelDefaults()
  if (!response) return null
  return toViewModel(response)
}

/**
 * Update current user's global panel defaults
 */
export async function updateUserPanelDefaults(
  input: UpdateUserPanelDefaultsInput
): Promise<UserPanelDefaultsViewModel> {
  const requestBody: UserPanelDefaultsUpdate = {}

  if (input.presetId !== undefined) {
    requestBody.preset_id = input.presetId
  }
  if (input.panels !== undefined) {
    requestBody.panels = input.panels as unknown as Array<{ [key: string]: unknown }>
  }
  if (input.reduceMotion !== undefined) {
    requestBody.reduce_motion = input.reduceMotion
  }

  const response = await UserPanelsService.updateMyPanelDefaults({
    requestBody,
  })
  return toViewModel(response)
}
```

**Step 2: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 3: Commit**

```bash
git add frontend/src/services/userPanelDefaultsService.ts
git commit -m "feat(services): add userPanelDefaultsService with ViewModel pattern"
```

---

### Task 17: Create Preset Service

**Files:**
- Create: `frontend/src/services/presetService.ts`

**Step 1: Create service**

```typescript
/**
 * Preset Service
 *
 * Provides system presets for panel layouts.
 * Uses ViewModel pattern - never expose raw API types to components.
 */

import { PresetsService } from "@/client"

// ============================================================================
// Type Definitions
// ============================================================================

export interface PresetViewModel {
  id: string
  name: string
  description: string
  panels: PanelConfigItem[]
  isSystem: boolean
}

export interface PanelConfigItem {
  id: string
  kind: string
  prominence: "primary" | "auxiliary"
}

// ============================================================================
// Service Functions
// ============================================================================

/**
 * List all available presets
 */
export async function listPresets(): Promise<PresetViewModel[]> {
  const response = await PresetsService.listPresets()
  return response.presets.map((preset) => ({
    id: preset.id,
    name: preset.name,
    description: preset.description,
    panels: preset.panels as PanelConfigItem[],
    isSystem: preset.is_system,
  }))
}

/**
 * Get a specific preset by ID
 */
export async function getPreset(presetId: string): Promise<PresetViewModel> {
  const preset = await PresetsService.getPreset({ presetId })
  return {
    id: preset.id,
    name: preset.name,
    description: preset.description,
    panels: preset.panels as PanelConfigItem[],
    isSystem: preset.is_system,
  }
}
```

**Step 2: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 3: Commit**

```bash
git add frontend/src/services/presetService.ts
git commit -m "feat(services): add presetService for layout presets"
```

---

### Task 18: Create useUserPanelDefaults Hook

**Files:**
- Create: `frontend/src/hooks/useUserPanelDefaults.ts`

**Step 1: Create hook**

```typescript
/**
 * useUserPanelDefaults Hook
 *
 * Manages user's global panel defaults with React Query.
 * Provides the user's default layout that applies to all rooms.
 *
 * @example
 * ```tsx
 * const { defaults, updateDefaults, isLoading } = useUserPanelDefaults()
 *
 * // Apply a preset
 * updateDefaults({ presetId: "focus" })
 *
 * // Set custom panels
 * updateDefaults({ panels: [...], presetId: null })
 * ```
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import {
  getUserPanelDefaults,
  updateUserPanelDefaults,
  type UserPanelDefaultsViewModel,
  type UpdateUserPanelDefaultsInput,
} from "@/services/userPanelDefaultsService"

// ============================================================================
// Query Keys
// ============================================================================

const QUERY_KEY = ["user", "panel-defaults"] as const

// ============================================================================
// Hook
// ============================================================================

export function useUserPanelDefaults() {
  const queryClient = useQueryClient()

  // Fetch user's defaults
  const query = useQuery({
    queryKey: QUERY_KEY,
    queryFn: getUserPanelDefaults,
  })

  // Update mutation
  const mutation = useMutation({
    mutationFn: updateUserPanelDefaults,
    onSuccess: (data) => {
      // Update cache immediately
      queryClient.setQueryData(QUERY_KEY, data)
      // Also invalidate room panels since they might use this default
      queryClient.invalidateQueries({ queryKey: ["rooms"] })
    },
  })

  return {
    /** User's default panel configuration */
    defaults: query.data,

    /** Loading state */
    isLoading: query.isLoading,

    /** Error state */
    error: query.error,

    /** Update defaults */
    updateDefaults: mutation.mutate,

    /** Async update defaults */
    updateDefaultsAsync: mutation.mutateAsync,

    /** Whether update is in progress */
    isUpdating: mutation.isPending,

    /** Convenience: set a preset */
    setPreset: (presetId: string) => {
      mutation.mutate({ presetId, panels: null })
    },

    /** Convenience: set custom panels */
    setCustomPanels: (panels: UpdateUserPanelDefaultsInput["panels"]) => {
      mutation.mutate({ presetId: null, panels })
    },

    /** Convenience: toggle reduce motion */
    setReduceMotion: (reduceMotion: boolean) => {
      mutation.mutate({ reduceMotion })
    },
  }
}
```

**Step 2: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 3: Commit**

```bash
git add frontend/src/hooks/useUserPanelDefaults.ts
git commit -m "feat(hooks): add useUserPanelDefaults hook"
```

---

### Task 19: Create usePanelPresets Hook

**Files:**
- Create: `frontend/src/hooks/usePanelPresets.ts`

**Step 1: Create hook**

```typescript
/**
 * usePanelPresets Hook
 *
 * Provides access to available layout presets.
 *
 * @example
 * ```tsx
 * const { presets, isLoading, getPreset } = usePanelPresets()
 *
 * // Get a specific preset
 * const focusPreset = getPreset("focus")
 * ```
 */

import { useQuery } from "@tanstack/react-query"
import { useMemo } from "react"

import {
  listPresets,
  type PresetViewModel,
} from "@/services/presetService"

// ============================================================================
// Query Keys
// ============================================================================

const QUERY_KEY = ["presets"] as const

// ============================================================================
// Hook
// ============================================================================

export function usePanelPresets() {
  const query = useQuery({
    queryKey: QUERY_KEY,
    queryFn: listPresets,
    // Presets are static, cache aggressively
    staleTime: 1000 * 60 * 60, // 1 hour
  })

  // Create a lookup map for quick access
  const presetMap = useMemo(() => {
    if (!query.data) return new Map<string, PresetViewModel>()
    return new Map(query.data.map((p) => [p.id, p]))
  }, [query.data])

  return {
    /** List of all available presets */
    presets: query.data ?? [],

    /** Loading state */
    isLoading: query.isLoading,

    /** Error state */
    error: query.error,

    /** Get a preset by ID */
    getPreset: (id: string) => presetMap.get(id),

    /** Check if a preset ID is valid */
    isValidPreset: (id: string) => presetMap.has(id),
  }
}
```

**Step 2: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 3: Commit**

```bash
git add frontend/src/hooks/usePanelPresets.ts
git commit -m "feat(hooks): add usePanelPresets hook"
```

---

## Phase 5: Panel Layout Dialog

### Task 20: Create LayoutSourceSelector Component

**Files:**
- Create: `frontend/src/components/Room/LayoutSourceSelector.tsx`

**Step 1: Create component**

```typescript
/**
 * LayoutSourceSelector Component
 *
 * Radio group for selecting layout source (room default, user default, custom).
 * Shows current source and allows switching.
 *
 * @example
 * ```tsx
 * <LayoutSourceSelector
 *   currentSource="user_defaults"
 *   onSourceChange={(source) => handleSourceChange(source)}
 *   isRoomOwner={false}
 * />
 * ```
 */

import * as React from "react"
import { ExternalLink } from "lucide-react"
import { Link } from "@tanstack/react-router"
import { cn } from "@/lib/utils"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"

// ============================================================================
// Types
// ============================================================================

export type LayoutSource =
  | "room_override"
  | "room_defaults"
  | "user_defaults"
  | "system_defaults"
  | "custom"

export interface LayoutSourceSelectorProps {
  /** Current source of the layout */
  currentSource: LayoutSource
  /** Called when source selection changes */
  onSourceChange: (source: LayoutSource) => void
  /** Whether the current user is the room owner */
  isRoomOwner: boolean
  /** Whether room has custom defaults set */
  hasRoomDefaults: boolean
  /** Additional className */
  className?: string
}

// ============================================================================
// Source Labels
// ============================================================================

const sourceLabels: Record<LayoutSource, string> = {
  room_override: "Custom for this room",
  room_defaults: "Room default",
  user_defaults: "My default",
  system_defaults: "System default",
  custom: "Custom for this room",
}

const sourceDescriptions: Record<LayoutSource, string> = {
  room_override: "Your personal layout for this room",
  room_defaults: "Layout set by the room owner",
  user_defaults: "Your default layout for all rooms",
  system_defaults: "Standard layout",
  custom: "Your personal layout for this room",
}

// ============================================================================
// Component
// ============================================================================

export function LayoutSourceSelector({
  currentSource,
  onSourceChange,
  isRoomOwner,
  hasRoomDefaults,
  className,
}: LayoutSourceSelectorProps) {
  // Normalize source for radio selection
  const selectedValue =
    currentSource === "room_override" ? "custom" : currentSource

  const handleChange = (value: string) => {
    onSourceChange(value as LayoutSource)
  }

  return (
    <div className={cn("space-y-3", className)}>
      {/* Current source indicator */}
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">Currently using:</span>
        <span className="font-medium">{sourceLabels[currentSource]}</span>
      </div>

      {/* Source selector */}
      <RadioGroup
        value={selectedValue}
        onValueChange={handleChange}
        className="grid gap-2"
      >
        {/* Room default option */}
        {hasRoomDefaults && (
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="room_defaults" id="source-room" />
            <Label htmlFor="source-room" className="flex-1 cursor-pointer">
              <span>{sourceLabels.room_defaults}</span>
              <span className="text-xs text-muted-foreground ml-2">
                {sourceDescriptions.room_defaults}
              </span>
            </Label>
          </div>
        )}

        {/* User default option */}
        <div className="flex items-center space-x-2">
          <RadioGroupItem value="user_defaults" id="source-user" />
          <Label htmlFor="source-user" className="flex-1 cursor-pointer">
            <span>{sourceLabels.user_defaults}</span>
            <span className="text-xs text-muted-foreground ml-2">
              {sourceDescriptions.user_defaults}
            </span>
          </Label>
          <Link
            to="/settings"
            className="text-xs text-primary hover:underline flex items-center gap-1"
          >
            Edit <ExternalLink className="h-3 w-3" />
          </Link>
        </div>

        {/* Custom option */}
        <div className="flex items-center space-x-2">
          <RadioGroupItem value="custom" id="source-custom" />
          <Label htmlFor="source-custom" className="flex-1 cursor-pointer">
            <span>{sourceLabels.custom}</span>
            <span className="text-xs text-muted-foreground ml-2">
              {sourceDescriptions.custom}
            </span>
          </Label>
        </div>
      </RadioGroup>
    </div>
  )
}
```

**Step 2: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 3: Commit**

```bash
git add frontend/src/components/Room/LayoutSourceSelector.tsx
git commit -m "feat(room): add LayoutSourceSelector component"
```

---

### Task 21: Create InteractivePreview Component

**Files:**
- Create: `frontend/src/components/Room/InteractivePreview.tsx`

**Step 1: Create component**

```typescript
/**
 * InteractivePreview Component
 *
 * Draggable panel preview for the layout settings dialog.
 * Allows reordering panels via drag and drop.
 *
 * @example
 * ```tsx
 * <InteractivePreview
 *   panels={panels}
 *   onReorder={(newPanels) => setPanels(newPanels)}
 *   onRemove={(panelId) => removePanel(panelId)}
 * />
 * ```
 */

import * as React from "react"
import { useState, useCallback } from "react"
import { motion, Reorder, AnimatePresence } from "framer-motion"
import { GripVertical, X, Minus, Plus } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  springConfig,
  useReduceMotion,
  getTransition,
} from "@/components/ui/motion"

// ============================================================================
// Types
// ============================================================================

export interface PreviewPanel {
  id: string
  kind: string
  prominence: "primary" | "auxiliary"
}

export interface InteractivePreviewProps {
  /** Panels to display */
  panels: PreviewPanel[]
  /** Called when panels are reordered */
  onReorder: (panels: PreviewPanel[]) => void
  /** Called when a panel is removed */
  onRemove?: (panelId: string) => void
  /** Called when a panel's collapsed state changes (preview only) */
  onToggleCollapse?: (panelId: string) => void
  /** Collapsed panel IDs (for preview) */
  collapsedPanels?: Set<string>
  /** Whether editing is disabled */
  disabled?: boolean
  /** Additional className */
  className?: string
}

// ============================================================================
// Panel Names
// ============================================================================

const panelNames: Record<string, string> = {
  chat: "Chat",
  storyEditor: "Story Editor",
  agentPanel: "Agents",
  debug: "Debug",
  canvas: "Canvas",
  a2ui: "Agent UI",
}

// ============================================================================
// PreviewPanelItem Component
// ============================================================================

interface PreviewPanelItemProps {
  panel: PreviewPanel
  isCollapsed?: boolean
  onRemove?: () => void
  onToggleCollapse?: () => void
  canRemove: boolean
  disabled?: boolean
}

function PreviewPanelItem({
  panel,
  isCollapsed,
  onRemove,
  onToggleCollapse,
  canRemove,
  disabled,
}: PreviewPanelItemProps) {
  const reduceMotion = useReduceMotion()

  return (
    <motion.div
      layout
      className={cn(
        "flex items-center gap-2 px-3 py-2 rounded-md border bg-card",
        "cursor-grab active:cursor-grabbing",
        isCollapsed && "opacity-60",
        disabled && "pointer-events-none opacity-50"
      )}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={getTransition(springConfig.snappy, reduceMotion)}
    >
      {/* Drag handle */}
      <GripVertical className="h-4 w-4 text-muted-foreground shrink-0" />

      {/* Panel name */}
      <span className="flex-1 text-sm font-medium truncate">
        {panelNames[panel.kind] || panel.kind}
      </span>

      {/* Prominence badge */}
      <span
        className={cn(
          "text-xs px-1.5 py-0.5 rounded",
          panel.prominence === "primary"
            ? "bg-blue-500/10 text-blue-600"
            : "bg-green-500/10 text-green-600"
        )}
      >
        {panel.prominence === "primary" ? "P" : "A"}
      </span>

      {/* Collapse toggle */}
      {onToggleCollapse && (
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={(e) => {
            e.stopPropagation()
            onToggleCollapse()
          }}
        >
          {isCollapsed ? (
            <Plus className="h-3 w-3" />
          ) : (
            <Minus className="h-3 w-3" />
          )}
        </Button>
      )}

      {/* Remove button */}
      {canRemove && onRemove && (
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 text-muted-foreground hover:text-destructive"
          onClick={(e) => {
            e.stopPropagation()
            onRemove()
          }}
        >
          <X className="h-3 w-3" />
        </Button>
      )}
    </motion.div>
  )
}

// ============================================================================
// InteractivePreview Component
// ============================================================================

export function InteractivePreview({
  panels,
  onReorder,
  onRemove,
  onToggleCollapse,
  collapsedPanels = new Set(),
  disabled = false,
  className,
}: InteractivePreviewProps) {
  const primaryPanels = panels.filter((p) => p.prominence === "primary")
  const auxiliaryPanels = panels.filter((p) => p.prominence === "auxiliary")

  // Can't remove the last panel
  const canRemove = panels.length > 1

  const handleReorder = useCallback(
    (type: "primary" | "auxiliary", newOrder: PreviewPanel[]) => {
      if (type === "primary") {
        onReorder([...newOrder, ...auxiliaryPanels])
      } else {
        onReorder([...primaryPanels, ...newOrder])
      }
    },
    [primaryPanels, auxiliaryPanels, onReorder]
  )

  return (
    <div className={cn("space-y-4", className)}>
      {/* Primary panels */}
      <div>
        <h4 className="text-xs font-medium text-muted-foreground mb-2">
          Primary Panels
        </h4>
        <Reorder.Group
          axis="y"
          values={primaryPanels}
          onReorder={(newOrder) => handleReorder("primary", newOrder)}
          className="space-y-2"
        >
          <AnimatePresence mode="popLayout">
            {primaryPanels.map((panel) => (
              <Reorder.Item key={panel.id} value={panel} disabled={disabled}>
                <PreviewPanelItem
                  panel={panel}
                  isCollapsed={collapsedPanels.has(panel.id)}
                  onRemove={onRemove ? () => onRemove(panel.id) : undefined}
                  onToggleCollapse={
                    onToggleCollapse
                      ? () => onToggleCollapse(panel.id)
                      : undefined
                  }
                  canRemove={canRemove}
                  disabled={disabled}
                />
              </Reorder.Item>
            ))}
          </AnimatePresence>
        </Reorder.Group>
        {primaryPanels.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-4">
            No primary panels
          </p>
        )}
      </div>

      {/* Auxiliary panels */}
      <div>
        <h4 className="text-xs font-medium text-muted-foreground mb-2">
          Auxiliary Panels
        </h4>
        <Reorder.Group
          axis="y"
          values={auxiliaryPanels}
          onReorder={(newOrder) => handleReorder("auxiliary", newOrder)}
          className="space-y-2"
        >
          <AnimatePresence mode="popLayout">
            {auxiliaryPanels.map((panel) => (
              <Reorder.Item key={panel.id} value={panel} disabled={disabled}>
                <PreviewPanelItem
                  panel={panel}
                  isCollapsed={collapsedPanels.has(panel.id)}
                  onRemove={onRemove ? () => onRemove(panel.id) : undefined}
                  onToggleCollapse={
                    onToggleCollapse
                      ? () => onToggleCollapse(panel.id)
                      : undefined
                  }
                  canRemove={canRemove}
                  disabled={disabled}
                />
              </Reorder.Item>
            ))}
          </AnimatePresence>
        </Reorder.Group>
        {auxiliaryPanels.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-4">
            No auxiliary panels
          </p>
        )}
      </div>

      {/* Help text */}
      <p className="text-xs text-muted-foreground text-center">
        Drag panels to reorder • P = Primary, A = Auxiliary
      </p>
    </div>
  )
}
```

**Step 2: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 3: Commit**

```bash
git add frontend/src/components/Room/InteractivePreview.tsx
git commit -m "feat(room): add InteractivePreview component with drag-to-reorder"
```

---

### Task 22: Create PanelLayoutDialog Component

**Files:**
- Create: `frontend/src/components/Room/PanelLayoutDialog.tsx`
- Modify: `frontend/src/components/Room/index.ts`

**Step 1: Create the dialog component**

```typescript
/**
 * PanelLayoutDialog Component
 *
 * Main dialog for panel layout customization.
 * Supports room-level and user-default editing modes.
 *
 * @example
 * ```tsx
 * <PanelLayoutDialog
 *   open={isOpen}
 *   onOpenChange={setIsOpen}
 *   roomId={roomId}
 *   isRoomOwner={canManage}
 * />
 * ```
 */

import * as React from "react"
import { useState, useEffect } from "react"
import { Plus } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { useToast } from "@/hooks/use-toast"
import { useRoomPanels } from "@/hooks/useRoomPanels"
import { usePanelPresets } from "@/hooks/usePanelPresets"
import {
  LayoutSourceSelector,
  type LayoutSource,
} from "./LayoutSourceSelector"
import { InteractivePreview, type PreviewPanel } from "./InteractivePreview"
import { PresetPicker, SYSTEM_PRESETS } from "./primitives/PresetPicker"
import type { PanelConfig } from "@/services/panelService"

// ============================================================================
// Types
// ============================================================================

export interface PanelLayoutDialogProps {
  /** Whether the dialog is open */
  open: boolean
  /** Called when open state changes */
  onOpenChange: (open: boolean) => void
  /** Room ID (null for editing user defaults) */
  roomId: string | null
  /** Whether current user is room owner */
  isRoomOwner?: boolean
  /** Mode: room settings or user defaults */
  mode?: "room" | "user-defaults"
}

// ============================================================================
// Available Panels
// ============================================================================

const AVAILABLE_PANELS: PreviewPanel[] = [
  { id: "chat", kind: "chat", prominence: "primary" },
  { id: "story", kind: "storyEditor", prominence: "primary" },
  { id: "canvas", kind: "canvas", prominence: "primary" },
  { id: "a2ui", kind: "a2ui", prominence: "primary" },
  { id: "agents", kind: "agentPanel", prominence: "auxiliary" },
  { id: "debug", kind: "debug", prominence: "auxiliary" },
]

const panelNames: Record<string, string> = {
  chat: "Chat",
  storyEditor: "Story Editor",
  canvas: "Canvas",
  a2ui: "Agent UI",
  agentPanel: "Agents",
  debug: "Debug",
}

// ============================================================================
// Component
// ============================================================================

export function PanelLayoutDialog({
  open,
  onOpenChange,
  roomId,
  isRoomOwner = false,
  mode = "room",
}: PanelLayoutDialogProps) {
  const { toast } = useToast()
  const { presets } = usePanelPresets()

  // Room panels hook (only used in room mode)
  const roomPanels = useRoomPanels(roomId ?? "", {
    enabled: mode === "room" && !!roomId,
  })

  // Local state for editing
  const [panels, setPanels] = useState<PreviewPanel[]>([])
  const [source, setSource] = useState<LayoutSource>("user_defaults")
  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(null)
  const [addPanelOpen, setAddPanelOpen] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  // Initialize from current config
  useEffect(() => {
    if (!open) return

    if (mode === "room" && roomPanels.panels.length > 0) {
      setPanels(roomPanels.panels.map((p) => ({
        id: p.id,
        kind: p.kind,
        prominence: p.prominence,
      })))
      setSource((roomPanels.panelSource as LayoutSource) || "user_defaults")
    } else {
      // Default to collaborate preset
      const defaultPreset = SYSTEM_PRESETS.find((p) => p.id === "collaborate")
      setPanels(defaultPreset?.panels || [])
      setSelectedPresetId("collaborate")
    }
  }, [open, mode, roomPanels.panels, roomPanels.panelSource])

  // Handle preset selection
  const handlePresetSelect = (presetId: string) => {
    const preset = SYSTEM_PRESETS.find((p) => p.id === presetId)
    if (preset) {
      setPanels(preset.panels)
      setSelectedPresetId(presetId)
    }
  }

  // Handle panel reorder
  const handleReorder = (newPanels: PreviewPanel[]) => {
    setPanels(newPanels)
    setSelectedPresetId(null) // Custom layout, no preset
  }

  // Handle panel remove
  const handleRemove = (panelId: string) => {
    setPanels((prev) => prev.filter((p) => p.id !== panelId))
    setSelectedPresetId(null)
  }

  // Handle add panel
  const handleAddPanel = (panel: PreviewPanel) => {
    if (panels.some((p) => p.id === panel.id)) return
    setPanels((prev) => [...prev, panel])
    setSelectedPresetId(null)
    setAddPanelOpen(false)
  }

  // Get panels not yet added
  const availablePanelsToAdd = AVAILABLE_PANELS.filter(
    (ap) => !panels.some((p) => p.id === ap.id)
  )

  // Handle save
  const handleSave = async () => {
    setIsSaving(true)
    try {
      if (mode === "room" && roomId) {
        if (source === "custom" || source === "room_override") {
          await roomPanels.setCustomPanels(panels as PanelConfig[])
        } else if (source === "user_defaults") {
          await roomPanels.setUseRoomDefaults(true)
        }
      }
      // TODO: Handle user-defaults mode

      toast({
        title: "Layout saved",
        description: "Your panel layout has been updated.",
      })
      onOpenChange(false)
    } catch (error) {
      toast({
        title: "Failed to save",
        description: "Could not save your layout. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Panel Layout</DialogTitle>
          <DialogDescription>
            Customize how panels are arranged in this room.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Source selector (room mode only) */}
          {mode === "room" && (
            <LayoutSourceSelector
              currentSource={source}
              onSourceChange={setSource}
              isRoomOwner={isRoomOwner}
              hasRoomDefaults={!!roomPanels.roomDefaults}
            />
          )}

          {/* Presets */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Quick Presets</h4>
            <PresetPicker
              presets={SYSTEM_PRESETS}
              currentPresetId={selectedPresetId}
              onSelect={handlePresetSelect}
              variant="buttons"
            />
          </div>

          {/* Interactive preview */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Panel Arrangement</h4>
            <div className="border rounded-lg p-4 bg-muted/30">
              <InteractivePreview
                panels={panels}
                onReorder={handleReorder}
                onRemove={handleRemove}
                disabled={source === "room_defaults" || source === "user_defaults"}
              />
            </div>
          </div>

          {/* Add panel */}
          {availablePanelsToAdd.length > 0 && (
            <Collapsible open={addPanelOpen} onOpenChange={setAddPanelOpen}>
              <CollapsibleTrigger asChild>
                <Button variant="outline" className="w-full gap-2">
                  <Plus className="h-4 w-4" />
                  Add Panel
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="pt-2">
                <div className="grid grid-cols-2 gap-2">
                  {availablePanelsToAdd.map((panel) => (
                    <Button
                      key={panel.id}
                      variant="ghost"
                      className="justify-start"
                      onClick={() => handleAddPanel(panel)}
                    >
                      {panelNames[panel.kind] || panel.kind}
                    </Button>
                  ))}
                </div>
              </CollapsibleContent>
            </Collapsible>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? "Saving..." : "Save"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
```

**Step 2: Update Room barrel export**

Add to `frontend/src/components/Room/index.ts`:

```typescript
export { PanelLayoutDialog, type PanelLayoutDialogProps } from "./PanelLayoutDialog"
export { LayoutSourceSelector, type LayoutSource } from "./LayoutSourceSelector"
export { InteractivePreview, type PreviewPanel } from "./InteractivePreview"
```

**Step 3: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 4: Commit**

```bash
git add frontend/src/components/Room/PanelLayoutDialog.tsx frontend/src/components/Room/LayoutSourceSelector.tsx frontend/src/components/Room/InteractivePreview.tsx frontend/src/components/Room/index.ts
git commit -m "feat(room): add PanelLayoutDialog with interactive preview"
```

---

## Phase 6: Integration & Polish

### Task 23: Add Layout Dialog to RoomHeader

**Files:**
- Modify: `frontend/src/components/Room/RoomHeader.tsx`

**Step 1: Add menu item and dialog trigger**

Update `RoomHeader.tsx` to include the Panel Layout option in the dropdown menu and manage dialog state:

```typescript
// Add imports
import { useState } from "react"
import { Layout } from "lucide-react"
import { PanelLayoutDialog } from "./PanelLayoutDialog"

// Add state
const [layoutDialogOpen, setLayoutDialogOpen] = useState(false)

// Add menu item in DropdownMenuContent, before settings
<DropdownMenuItem onClick={() => setLayoutDialogOpen(true)}>
  <Layout className="h-4 w-4 mr-2" />
  Panel Layout
</DropdownMenuItem>

// Add dialog at end of component, before closing tag
<PanelLayoutDialog
  open={layoutDialogOpen}
  onOpenChange={setLayoutDialogOpen}
  roomId={roomId}
  isRoomOwner={canEdit}
/>
```

**Step 2: Add roomId prop to RoomHeader**

Update the interface to accept roomId:

```typescript
interface RoomHeaderProps {
  // ... existing props
  /** Room ID for layout settings */
  roomId?: string
}
```

**Step 3: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 4: Commit**

```bash
git add frontend/src/components/Room/RoomHeader.tsx
git commit -m "feat(room): add Panel Layout option to room header menu"
```

---

### Task 24: Add Keyboard Shortcuts to RoomShell

**Files:**
- Modify: `frontend/src/components/Room/RoomShell.tsx`

**Step 1: Wrap RoomShell with KeyboardShortcutProvider**

Update `RoomShell.tsx` to include keyboard shortcuts:

```typescript
// Add imports
import { KeyboardShortcutProvider, type KeyboardShortcut } from "./primitives/KeyboardShortcutProvider"

// Define shortcuts inside component
const shortcuts: KeyboardShortcut[] = [
  {
    key: "l",
    modifiers: ["mod", "shift"],
    action: () => setLayoutDialogOpen(true),
    description: "Open panel layout settings",
  },
  {
    key: "t",
    modifiers: ["mod", "shift"],
    action: () => setLayoutMode((prev) => (prev === "panels" ? "tabs" : "panels")),
    description: "Toggle panels/tabs mode",
  },
  {
    key: "f",
    modifiers: ["mod", "shift"],
    action: () => {
      // Apply focus preset
      // TODO: Implement preset application
    },
    description: "Focus mode (chat only)",
  },
]

// Wrap return with provider
return (
  <KeyboardShortcutProvider shortcuts={shortcuts}>
    <div className={cn("flex flex-col h-full", className)}>
      {/* existing content */}
    </div>
  </KeyboardShortcutProvider>
)
```

**Step 2: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 3: Commit**

```bash
git add frontend/src/components/Room/RoomShell.tsx
git commit -m "feat(room): add keyboard shortcuts to RoomShell"
```

---

### Task 25: Create DefaultPanelLayoutCard for Users Page

**Files:**
- Create: `frontend/src/components/Users/DefaultPanelLayoutCard.tsx`

**Step 1: Create the card component**

```typescript
/**
 * DefaultPanelLayoutCard Component
 *
 * Settings card for user's default panel layout.
 * Displayed on the Users/Settings page.
 *
 * @example
 * ```tsx
 * <DefaultPanelLayoutCard />
 * ```
 */

import * as React from "react"
import { useState } from "react"
import { Settings } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { useUserPanelDefaults } from "@/hooks/useUserPanelDefaults"
import { usePanelPresets } from "@/hooks/usePanelPresets"
import { useReduceMotionControl } from "@/components/ui/motion"
import { MiniPreview } from "@/components/Room/primitives/MiniPreview"
import { PanelLayoutDialog } from "@/components/Room/PanelLayoutDialog"
import { SYSTEM_PRESETS } from "@/components/Room/primitives/PresetPicker"

// ============================================================================
// Component
// ============================================================================

export function DefaultPanelLayoutCard() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const { defaults, isLoading, setReduceMotion } = useUserPanelDefaults()
  const { getPreset } = usePanelPresets()

  // Get current preset or custom panels
  const currentPreset = defaults?.presetId
    ? SYSTEM_PRESETS.find((p) => p.id === defaults.presetId)
    : null
  const displayPanels = currentPreset?.panels || defaults?.panels || []
  const displayName = currentPreset?.name || "Custom"

  // Reduce motion from context (falls back to system preference)
  let reduceMotion = false
  try {
    const motionControl = useReduceMotionControl()
    reduceMotion = motionControl.reduceMotion
  } catch {
    // Not in provider, use default
  }

  const handleReduceMotionChange = (checked: boolean) => {
    setReduceMotion(checked)
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Default Panel Layout</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-24 flex items-center justify-center">
            <p className="text-sm text-muted-foreground">Loading...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Default Panel Layout</CardTitle>
          <CardDescription>
            Your default layout applies to all rooms unless you customize a
            specific room.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Preview */}
          <div className="flex items-center gap-4">
            <MiniPreview
              panels={displayPanels}
              width={120}
              height={80}
              showLabels
            />
            <div className="flex-1">
              <p className="text-sm font-medium">Current: {displayName}</p>
              <p className="text-xs text-muted-foreground">
                {displayPanels.length} panel{displayPanels.length !== 1 && "s"}
              </p>
            </div>
            <Button variant="outline" onClick={() => setDialogOpen(true)}>
              Change Layout
            </Button>
          </div>

          {/* Accessibility */}
          <div className="border-t pt-4">
            <h4 className="text-sm font-medium mb-3">Accessibility</h4>
            <div className="flex items-center justify-between">
              <Label htmlFor="reduce-motion" className="flex flex-col gap-1">
                <span>Reduce motion</span>
                <span className="text-xs text-muted-foreground font-normal">
                  Disable panel animations
                </span>
              </Label>
              <Switch
                id="reduce-motion"
                checked={reduceMotion}
                onCheckedChange={handleReduceMotionChange}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <PanelLayoutDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        roomId={null}
        mode="user-defaults"
      />
    </>
  )
}
```

**Step 2: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 3: Commit**

```bash
git add frontend/src/components/Users/DefaultPanelLayoutCard.tsx
git commit -m "feat(users): add DefaultPanelLayoutCard for settings page"
```

---

### Task 26: Full Build and Verification

**Step 1: Run linter**

```bash
cd /home/josep/dog/frontend && npm run lint
```

Expected: No errors

**Step 2: Run build**

```bash
cd /home/josep/dog/frontend && npm run build
```

Expected: Build succeeds

**Step 3: Run backend tests**

```bash
cd /home/josep/dog/backend && pytest app/tests/ -v -x
```

Expected: Tests pass

**Step 4: Manual verification checklist**

```markdown
- [ ] Navigate to room → header shows "Panel Layout" in menu
- [ ] Open Panel Layout dialog → shows current configuration
- [ ] Preset buttons switch layout preview
- [ ] Drag panels to reorder → preview updates
- [ ] Save layout → toast confirms
- [ ] Keyboard shortcut Cmd/Ctrl+Shift+L → opens dialog
- [ ] Keyboard shortcut Cmd/Ctrl+Shift+T → toggles panels/tabs
- [ ] Navigate to Settings/Users page → shows Default Panel Layout card
- [ ] Change default layout → persists on refresh
- [ ] Reduce motion toggle → disables animations
```

**Step 5: Final commit**

```bash
git add -A
git commit -m "feat: complete panel layout customization implementation

- Framer Motion animations with reduce motion support
- Drag-to-reorder panels via DraggablePanel primitive
- Collapse/minimize via CollapsiblePanel primitive
- System presets (Focus, Collaborate, Story, Debug, Canvas)
- Platform-aware keyboard shortcuts
- User defaults on Settings page
- Full backend API for panel persistence"
```

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1 | 1-3 | Animation foundation (Framer Motion, motion config) |
| 2 | 4-8 | Primitives (Draggable, Collapsible, MiniPreview, PresetPicker, Shortcuts) |
| 3 | 9-14 | Backend (models, migration, CRUD, routes) |
| 4 | 15-19 | Frontend services & hooks |
| 5 | 20-22 | Panel Layout Dialog components |
| 6 | 23-26 | Integration & polish |

**Total: 26 tasks**

**Files Created:** ~20
**Files Modified:** ~10

**Key Deliverables:**
- ✨ Drag-to-reorder with spring physics
- ✨ Collapse/minimize with smooth animations
- ✨ Five system presets
- ✨ Platform-aware keyboard shortcuts
- ✨ User defaults on Settings page
- ✨ Reduce motion accessibility toggle
