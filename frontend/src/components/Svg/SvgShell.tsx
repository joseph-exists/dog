import * as React from "react"
import { SvgHeader } from "./SvgHeader"
import { SvgLayout } from "./SvgLayout"
import type { SvgPanelConfig } from "./types"

interface SvgShellProps {
  title: string
  description: string
  panels: SvgPanelConfig[]
  actions?: React.ReactNode
  className?: string
}

export function SvgShell({
  title,
  description,
  panels,
  actions,
  className,
}: SvgShellProps) {
  const [layoutMode, setLayoutMode] = React.useState<"panels" | "tabs">(
    "panels",
  )

  return (
    <div className={className ?? "flex h-full flex-col"}>
      <SvgHeader
        title={title}
        description={description}
        layoutMode={layoutMode}
        onLayoutModeChange={setLayoutMode}
        actions={actions}
      />
      <div className="min-h-0 flex-1">
        <SvgLayout panels={panels} mode={layoutMode} />
      </div>
    </div>
  )
}

