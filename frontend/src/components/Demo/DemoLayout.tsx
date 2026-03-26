// Follows RoomLayout's implementation. Resizable panels, tabs mode,
// primary/auxiliary split. Mobile → tabs.

/**
 * DemoLayout
 *
 * Manages panel arrangement with resizable splits.
 * Handles responsive behavior and panel/tab toggle.
 */
import React from "react"
import type { PanelImperativeHandle } from "react-resizable-panels"
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
  collapsed?: boolean
  defaultSize?: number
  minSize?: number
  maxSize?: number
  viewportMode?: "panel" | "page"
  render: () => React.ReactNode
}

interface DemoLayoutProps {
  /** Panel configurations */
  panels: PanelConfig[]
  /** Layout mode */
  mode: "panels" | "tabs"
  /** Additional className */
  className?: string
}

function clampPanelSize(value: number | undefined, fallback: number): number {
  if (typeof value !== "number" || !Number.isFinite(value)) return fallback
  return Math.min(90, Math.max(10, value))
}

function getAuxiliaryColumnDefaultSize(auxiliaryPanels: PanelConfig[]): number {
  if (auxiliaryPanels.length === 0) return 35

  // Treat the first auxiliary panel as the column width anchor.
  // Additional auxiliary panels are stacked inside the column.
  return clampPanelSize(auxiliaryPanels[0]?.defaultSize, 35)
}

export const DEMO_LAYOUT_COLLAPSED_PRIMARY_SIZE = 8

export function canPrimaryPanelCollapseToWidth(
  panels: Pick<PanelConfig, "id" | "prominence" | "collapsed">[],
  panelId: string,
): boolean {
  const primaryPanels = panels.filter((panel) => panel.prominence === "primary")
  if (primaryPanels.length < 2) return false
  return primaryPanels.some(
    (panel) => panel.id !== panelId && panel.collapsed !== true,
  )
}

export function getPrimaryPanelCollapsedSize(
  panel: Pick<PanelConfig, "prominence" | "collapsed">,
  canCollapseToWidth = true,
): number | undefined {
  if (
    panel.prominence !== "primary" ||
    panel.collapsed !== true ||
    !canCollapseToWidth
  ) {
    return undefined
  }
  return DEMO_LAYOUT_COLLAPSED_PRIMARY_SIZE
}

function PrimaryResizablePanel({
  panel,
  canCollapseToWidth,
}: {
  panel: PanelConfig
  canCollapseToWidth: boolean
}) {
  const panelRef = React.useRef<PanelImperativeHandle | null>(null)

  React.useEffect(() => {
    const instance = panelRef.current
    if (!instance) return
    if (panel.collapsed && canCollapseToWidth) {
      try {
        instance.collapse()
      } catch (error) {
        if (process.env.NODE_ENV === "development") {
          console.warn("[DemoLayout] Primary width collapse failed", {
            panelId: panel.id,
            error,
          })
        }
      }
    } else if (instance.isCollapsed()) {
      try {
        instance.expand()
      } catch (error) {
        if (process.env.NODE_ENV === "development") {
          console.warn("[DemoLayout] Primary width expand failed", {
            panelId: panel.id,
            error,
          })
        }
      }
    }
  }, [canCollapseToWidth, panel.collapsed, panel.id])

  return (
    <ResizablePanel
      id={panel.id}
      panelRef={panelRef}
      defaultSize={panel.defaultSize}
      minSize={panel.minSize ?? 10}
      maxSize={panel.maxSize}
      collapsible={canCollapseToWidth}
      collapsedSize={getPrimaryPanelCollapsedSize(panel, canCollapseToWidth)}
    >
      {panel.render()}
    </ResizablePanel>
  )
}

export function DemoLayout({ panels, mode, className }: DemoLayoutProps) {
  const isMobile = useIsMobile()
  const pageSizedPanel = panels.find((p) => p.viewportMode === "page")

  const primaryPanels = panels.filter((p) => p.prominence === "primary")
  const auxiliaryPanels = panels.filter((p) => p.prominence === "auxiliary")
  const auxiliaryColumnDefaultSize =
    getAuxiliaryColumnDefaultSize(auxiliaryPanels)

  // Mobile always uses tabs
  const effectiveMode = isMobile ? "tabs" : mode

  if (effectiveMode === "tabs") {
    return (
      <Tabs
        defaultValue={panels[0]?.id}
        className={cn("flex flex-col h-full min-h-0", className)}
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
            className="flex-1 min-h-0 mt-0 overflow-hidden"
          >
            {panel.render()}
          </TabsContent>
        ))}
      </Tabs>
    )
  }

  // Page-sized panels intentionally consume the full workspace.
  if (pageSizedPanel) {
    return (
      <div className={cn("h-full min-h-0 overflow-hidden", className)}>
        {pageSizedPanel.render()}
      </div>
    )
  }

  return (
    <ResizablePanelGroup
      direction="horizontal"
      className={cn("h-full min-h-0", className)}
    >
      {/* Primary panels */}
      {primaryPanels.map((panel, index) => (
        <React.Fragment key={panel.id}>
          {index > 0 && <ResizableHandle withHandle />}
          <PrimaryResizablePanel
            panel={panel}
            canCollapseToWidth={canPrimaryPanelCollapseToWidth(
              primaryPanels,
              panel.id,
            )}
          />
        </React.Fragment>
      ))}

      {/* Auxiliary panels column */}
      {auxiliaryPanels.length > 0 && (
        <>
          <ResizableHandle withHandle />
          <ResizablePanel defaultSize={auxiliaryColumnDefaultSize} minSize={20}>
            <ResizablePanelGroup direction="vertical" className="min-h-0">
              {auxiliaryPanels.map((panel, index) => (
                <React.Fragment key={panel.id}>
                  {index > 0 && <ResizableHandle withHandle />}
                  <ResizablePanel
                    id={panel.id}
                    defaultSize={
                      panel.defaultSize ?? 100 / auxiliaryPanels.length
                    }
                    minSize={panel.minSize ?? 10}
                    maxSize={panel.maxSize}
                  >
                    {panel.render()}
                  </ResizablePanel>
                </React.Fragment>
              ))}
            </ResizablePanelGroup>
          </ResizablePanel>
        </>
      )}
    </ResizablePanelGroup>
  )
}
