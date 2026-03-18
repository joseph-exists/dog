import {
  ArrowLeft,
  Cpu,
  LayoutPanelLeft,
} from "lucide-react"
import { Link } from "@tanstack/react-router"

import type { ThemeViewModel } from "@/services/themeService"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

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
}: WorkspacesHeaderProps) {
  return (
    <div className="shrink-0 border-b bg-background/80 px-4 py-4 backdrop-blur md:px-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="space-y-2">
          {backHref ? (
            <Button asChild variant="ghost" size="sm" className="-ml-2 w-fit">
              <Link to={backHref}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back
              </Link>
            </Button>
          ) : null}
          <div className="flex items-center gap-3">
            <div className="rounded-xl border bg-card p-2.5">
              <Cpu className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
              <p className="text-sm text-muted-foreground">{description}</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
              <LayoutPanelLeft className="h-3.5 w-3.5" />
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
            <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
              <LayoutPanelLeft className="h-3.5 w-3.5" />
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
    </div>
  )
}
