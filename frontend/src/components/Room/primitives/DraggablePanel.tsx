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

import { motion } from "framer-motion"
import { GripVertical } from "lucide-react"
import * as React from "react"
import { useCallback, useState } from "react"
import {
  getTransition,
  springConfig,
  useReduceMotion,
  variants,
} from "@/components/ui/motion"
import { cn } from "@/lib/utils"

// ============================================================================
// Types
// ============================================================================

export interface DraggablePanelProps {
  /** Unique identifier for this panel */
  panelId: string
  /** Children to render inside the draggable wrapper */
  children: React.ReactNode
  /** Called when a panel is dropped onto this panel's drop zone */
  onDrop?: (
    draggedId: string,
    targetId: string,
    position: "before" | "after",
  ) => void
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
export function DragContextProvider({
  children,
}: {
  children: React.ReactNode
}) {
  const [draggedId, setDraggedId] = useState<string | null>(null)

  const value = React.useMemo(() => ({ draggedId, setDraggedId }), [draggedId])

  return <DragContext.Provider value={value}>{children}</DragContext.Provider>
}

function useDragContext() {
  return React.useContext(DragContext)
}

// ============================================================================
// DragHandle Component
// ============================================================================

/**
 * DragHandle
 *
 * Visual handle for initiating drag. Renders as grip icon.
 */
export function DragHandle({
  isDragging,
  onPointerDown,
  className,
}: DragHandleProps) {
  return (
    <button
      type="button"
      onPointerDown={onPointerDown}
      className={cn(
        "flex items-center justify-center p-1 rounded cursor-grab touch-none",
        "text-muted-foreground hover:text-foreground hover:bg-muted/50",
        "transition-colors",
        isDragging && "cursor-grabbing",
        className,
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
        position === "before"
          ? "left-0 -translate-x-1/2"
          : "right-0 translate-x-1/2",
        "top-0 bottom-0 w-4",
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
          isActive && "animate-pulse",
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
  const dragContext = useDragContext()
  const [localDraggedId, setLocalDraggedId] = useState<string | null>(null)

  // Use context if available, otherwise use local state
  const draggedId = dragContext?.draggedId ?? localDraggedId
  const setDraggedId = dragContext?.setDraggedId ?? setLocalDraggedId

  const [isDragging, setIsDragging] = useState(false)
  const [activeDropZone, setActiveDropZone] = useState<
    "before" | "after" | null
  >(null)
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
    [disabled, panelId, setDraggedId, onDragStart],
  )

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
    [draggedId, panelId, onDrop],
  )

  // Clone children to inject drag handle
  const childrenWithHandle = React.Children.map(children, (child) => {
    if (!React.isValidElement(child)) return child

    // If child is PanelContainer, inject drag handle into headerActions
    if (dragHandlePosition === "header") {
      const childProps = child.props as { headerActions?: React.ReactNode }
      return React.cloneElement(
        child as React.ReactElement<{ headerActions?: React.ReactNode }>,
        {
          headerActions: (
            <div className="flex items-center gap-1">
              <DragHandle
                isDragging={isBeingDragged}
                onPointerDown={handlePointerDown}
              />
              {childProps.headerActions}
            </div>
          ),
        },
      )
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
