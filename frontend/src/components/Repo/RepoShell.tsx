import * as React from "react"
import { RepoHeader } from "./RepoHeader"
import { RepoLayout, type RepoPanelConfig } from "./RepoLayout"

interface RepoShellProps {
  title: string
  description: string
  panels: RepoPanelConfig[]
  actions?: React.ReactNode
  className?: string
}

export function RepoShell({
  title,
  description,
  panels,
  actions,
  className,
}: RepoShellProps) {
  const [layoutMode, setLayoutMode] = React.useState<"panels" | "tabs">(
    "panels",
  )

  return (
    <div className={className ?? "flex h-full flex-col"}>
      <RepoHeader
        title={title}
        description={description}
        layoutMode={layoutMode}
        onLayoutModeChange={setLayoutMode}
        actions={actions}
      />
      <div className="min-h-0 flex-1">
        <RepoLayout panels={panels} mode={layoutMode} />
      </div>
    </div>
  )
}
