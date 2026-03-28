/**
 * WorkspacesHeader
 *
 * Page header for the workspace detail view. Contains:
 * - Sidebar trigger + separator (standard app nav integration)
 * - Back navigation (when backHref is provided)
 * - Workspace title and description
 * - Layout mode toggle (panels / tabs)
 * - Page theme selector
 * - Cards theme selector
 */

import { Link } from "@tanstack/react-router"
import { ArrowLeft, Cpu, Layout, LayoutList } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import type { ThemeViewModel } from "@/services/themeService"

export interface WorkspacesHeaderProps {
  title: string
  description: string
  pageTheme: ThemeViewModel | null
  cardsTheme: ThemeViewModel | null
  availablePageThemes: ThemeViewModel[]
  availableCardThemes: ThemeViewModel[]
  onPageThemeChange: (themeId: string) => void
  onCardsThemeChange: (themeId: string) => void
  backHref?: string
  layoutMode: "panels" | "tabs"
  onLayoutModeChange: (mode: "panels" | "tabs") => void
}

export function WorkspacesHeader({
  title,
  description,
  pageTheme,
  cardsTheme,
  availablePageThemes,
  availableCardThemes,
  onPageThemeChange,
  onCardsThemeChange,
  backHref,
  layoutMode,
  onLayoutModeChange,
}: WorkspacesHeaderProps) {
  return (
    <div className="shrink-0 border-b bg-background/80 backdrop-blur">
      {/* Top bar: sidebar trigger + separator (standard app chrome) */}
      <div className="flex h-12 items-center gap-2 px-4">
        <SidebarTrigger className="-ml-1" />
        {backHref ? (
          <>
            <Separator orientation="vertical" className="h-4" />
            <Button asChild variant="ghost" size="sm" className="-ml-1">
              <Link to={backHref}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Workspaces
              </Link>
            </Button>
          </>
        ) : null}
      </div>

      {/* Main header row: title + controls */}
      <div className="flex flex-col gap-4 px-4 pb-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-xl border bg-card p-2.5">
            <Cpu className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
            <p className="text-sm text-muted-foreground">{description}</p>
          </div>
        </div>

        <TooltipProvider>
          <div className="flex flex-wrap items-end gap-4">
            {/* Layout mode toggle */}
            <ToggleGroup
              type="single"
              value={layoutMode}
              onValueChange={(value) => {
                if (value === "panels" || value === "tabs")
                  onLayoutModeChange(value)
              }}
              className="hidden md:flex border rounded-md"
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <ToggleGroupItem value="panels" aria-label="Panels layout">
                    <Layout className="h-4 w-4" />
                  </ToggleGroupItem>
                </TooltipTrigger>
                <TooltipContent>Panels</TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <ToggleGroupItem value="tabs" aria-label="Tabs layout">
                    <LayoutList className="h-4 w-4" />
                  </ToggleGroupItem>
                </TooltipTrigger>
                <TooltipContent>Tabs</TooltipContent>
              </Tooltip>
            </ToggleGroup>

            {/* Theme selectors */}
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <div className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
                  Page Theme
                </div>
                <Select
                  value={pageTheme?.id ?? ""}
                  onValueChange={onPageThemeChange}
                >
                  <SelectTrigger className="min-w-44">
                    <SelectValue placeholder="Select page theme" />
                  </SelectTrigger>
                  <SelectContent>
                    {availablePageThemes.map((theme) => (
                      <SelectItem key={theme.id} value={theme.id}>
                        {theme.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1.5">
                <div className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
                  Cards Theme
                </div>
                <Select
                  value={cardsTheme?.id ?? ""}
                  onValueChange={onCardsThemeChange}
                >
                  <SelectTrigger className="min-w-44">
                    <SelectValue placeholder="Select cards theme" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableCardThemes.map((theme) => (
                      <SelectItem key={theme.id} value={theme.id}>
                        {theme.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        </TooltipProvider>
      </div>
    </div>
  )
}
