import * as React from "react"

export interface PanelConfig {
  id: string
  kind: string
  prominence: "primary" | "auxiliary"
  title: string
  render: () => React.ReactNode
}

export interface WorkspacesLayoutProps {
  panels: PanelConfig[]
}

export function WorkspacesLayout({ panels }: WorkspacesLayoutProps) {
  const primaryPanels = panels.filter((panel) => panel.prominence === "primary")
  const auxiliaryPanels = panels.filter(
    (panel) => panel.prominence === "auxiliary",
  )

  return (
    <div className="grid flex-1 min-h-0 grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1.7fr)_minmax(320px,0.9fr)]">
      <div className="min-h-0 space-y-4">
        {primaryPanels.map((panel) => (
          <React.Fragment key={panel.id}>{panel.render()}</React.Fragment>
        ))}
      </div>
      <div className="min-h-0 space-y-4">
        {auxiliaryPanels.map((panel) => (
          <React.Fragment key={panel.id}>{panel.render()}</React.Fragment>
        ))}
      </div>
    </div>
  )
}
