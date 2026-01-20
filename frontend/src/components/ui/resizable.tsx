import * as React from "react"
import { GripVerticalIcon } from "lucide-react"
import { Group, Panel, Separator } from "react-resizable-panels"

import { cn } from "@/lib/utils"

/**
 * Context to share orientation from ResizablePanelGroup to ResizableHandle.
 * Required because v4 doesn't automatically propagate direction to Separator.
 */
const ResizableContext = React.createContext<{
  direction: "horizontal" | "vertical"
}>({ direction: "horizontal" })

/**
 * ResizablePanelGroup wraps react-resizable-panels v4 Group component.
 * Maps `direction` prop to `orientation` for backwards compatibility.
 * Provides context for ResizableHandle to know orientation.
 */
function ResizablePanelGroup({
  className,
  direction = "horizontal",
  children,
  ...props
}: Omit<React.ComponentProps<typeof Group>, "orientation"> & {
  direction?: "horizontal" | "vertical"
}) {
  return (
    <ResizableContext.Provider value={{ direction }}>
      <Group
        data-slot="resizable-panel-group"
        data-panel-group-direction={direction}
        orientation={direction}
        className={cn(
          "flex h-full w-full data-[panel-group-direction=vertical]:flex-col",
          className
        )}
        {...props}
      >
        {children}
      </Group>
    </ResizableContext.Provider>
  )
}

/**
 * ResizablePanel wraps react-resizable-panels v4 Panel component.
 */
function ResizablePanel({
  className,
  ...props
}: React.ComponentProps<typeof Panel>) {
  return (
    <Panel
      data-slot="resizable-panel"
      className={className}
      {...props}
    />
  )
}

/**
 * ResizableHandle wraps react-resizable-panels v4 Separator component.
 * Uses context to get orientation from parent ResizablePanelGroup.
 * Provides optional drag handle indicator.
 */
function ResizableHandle({
  withHandle,
  className,
  ...props
}: React.ComponentProps<typeof Separator> & {
  withHandle?: boolean
}) {
  const { direction } = React.useContext(ResizableContext)

  return (
    <Separator
      data-slot="resizable-handle"
      data-panel-group-direction={direction}
      className={cn(
        "bg-border focus-visible:ring-ring relative flex w-px items-center justify-center after:absolute after:inset-y-0 after:left-1/2 after:w-1 after:-translate-x-1/2 focus-visible:ring-1 focus-visible:ring-offset-1 focus-visible:outline-hidden data-[panel-group-direction=vertical]:h-px data-[panel-group-direction=vertical]:w-full data-[panel-group-direction=vertical]:after:left-0 data-[panel-group-direction=vertical]:after:h-1 data-[panel-group-direction=vertical]:after:w-full data-[panel-group-direction=vertical]:after:translate-x-0 data-[panel-group-direction=vertical]:after:-translate-y-1/2 [&[data-panel-group-direction=vertical]>div]:rotate-90",
        className
      )}
      {...props}
    >
      {withHandle && (
        <div className="bg-border z-10 flex h-4 w-3 items-center justify-center rounded-xs border">
          <GripVerticalIcon className="size-2.5" />
        </div>
      )}
    </Separator>
  )
}

export { ResizablePanelGroup, ResizablePanel, ResizableHandle }
