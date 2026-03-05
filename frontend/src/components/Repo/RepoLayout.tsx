import React from "react"
import type { RepoPanelKind, RepoPanelProminence } from "@/components/Repo/registry"
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useIsMobile } from "@/hooks/use-mobile"
import { cn } from "@/lib/utils"

export interface RepoPanelConfig {
  id: string
  kind: RepoPanelKind
  prominence: RepoPanelProminence
  title: string
  default_size?: number
  min_size?: number
  max_size?: number
  config_json?: Record<string, unknown> | null
  render: () => React.ReactNode
}

interface RepoLayoutProps {
  panels: RepoPanelConfig[]
  mode: "panels" | "tabs"
  className?: string
}

export function RepoLayout({ panels, mode, className }: RepoLayoutProps) {
  const isMobile = useIsMobile()
  const effectiveMode = isMobile ? "tabs" : mode
  const primaryPanels = panels.filter((panel) => panel.prominence === "primary")
  const auxiliaryPanels = panels.filter((panel) => panel.prominence === "auxiliary")

  if (effectiveMode === "tabs") {
    return (
      <Tabs
        defaultValue={panels[0]?.id}
        className={cn("flex h-full flex-col", className)}
      >
        <TabsList className="h-auto w-full justify-start rounded-none border-b bg-transparent p-0">
          {panels.map((panel) => (
            <TabsTrigger
              key={panel.id}
              value={panel.id}
              className="rounded-none border-b-2 border-transparent px-4 py-2 data-[state=active]:border-primary data-[state=active]:bg-transparent"
            >
              {panel.title}
            </TabsTrigger>
          ))}
        </TabsList>
        {panels.map((panel) => (
          <TabsContent
            key={panel.id}
            value={panel.id}
            className="mt-0 flex-1 overflow-hidden"
          >
            {panel.render()}
          </TabsContent>
        ))}
      </Tabs>
    )
  }

  return (
    <ResizablePanelGroup
      direction="horizontal"
      className={cn("h-full", className)}
    >
      {primaryPanels.map((panel, index) => (
        <React.Fragment key={panel.id}>
          {index > 0 && <ResizableHandle withHandle />}
          <ResizablePanel
            defaultSize={panel.default_size}
            minSize={panel.min_size}
            maxSize={panel.max_size}
          >
            {panel.render()}
          </ResizablePanel>
        </React.Fragment>
      ))}

      {auxiliaryPanels.length > 0 && (
        <>
          <ResizableHandle withHandle />
          <ResizablePanel defaultSize={34} minSize={20}>
            <ResizablePanelGroup direction="vertical">
              {auxiliaryPanels.map((panel, index) => (
                <React.Fragment key={panel.id}>
                  {index > 0 && <ResizableHandle withHandle />}
                  <ResizablePanel
                    defaultSize={panel.default_size ?? 100 / auxiliaryPanels.length}
                    minSize={panel.min_size ?? 15}
                    maxSize={panel.max_size}
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
