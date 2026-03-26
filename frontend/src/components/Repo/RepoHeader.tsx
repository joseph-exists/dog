import { BoxesIcon, LayoutPanelTopIcon, Rows3Icon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface RepoHeaderProps {
  title: string
  description: string
  layoutMode: "panels" | "tabs"
  onLayoutModeChange: (mode: "panels" | "tabs") => void
  actions?: React.ReactNode
}

export function RepoHeader({
  title,
  description,
  layoutMode,
  onLayoutModeChange,
  actions,
}: RepoHeaderProps) {
  return (
    <div className="border-b bg-background/80 px-6 py-5 backdrop-blur">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-muted-foreground">
            <BoxesIcon className="size-4" />
            Repository Workspace
          </div>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
            <p className="max-w-3xl text-sm text-muted-foreground">
              {description}
            </p>
          </div>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          {actions}
          <div className="inline-flex rounded-xl border bg-muted/30 p-1">
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                "rounded-lg",
                layoutMode === "panels" && "bg-background shadow-sm",
              )}
              onClick={() => onLayoutModeChange("panels")}
            >
              <LayoutPanelTopIcon className="size-4" />
              Panels
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                "rounded-lg",
                layoutMode === "tabs" && "bg-background shadow-sm",
              )}
              onClick={() => onLayoutModeChange("tabs")}
            >
              <Rows3Icon className="size-4" />
              Tabs
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
