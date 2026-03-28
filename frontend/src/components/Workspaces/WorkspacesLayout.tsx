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
