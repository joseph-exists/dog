import { LayoutPanelLeft } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import type { ThemeViewModel } from "@/services/themeService"

interface DemoHeaderProps {
  title: string
  description: string
  autoRespond: boolean
  onAutoRespondChange: (value: boolean) => void
  isConnected: boolean
  pageTheme: ThemeViewModel | null
  cardsTheme: ThemeViewModel | null
  availablePageThemes: ThemeViewModel[]
  availableCardThemes: ThemeViewModel[]
  onPageThemeChange: (themeId: string) => void
  onCardsThemeChange: (themeId: string) => void
  onCustomizeLayout?: () => void
  canResetLayout?: boolean
  onResetLayout?: () => void
  onCollapseAll?: () => void
  onExpandAll?: () => void
}

export function DemoHeader({
  title,
  description,
  autoRespond,
  onAutoRespondChange,
  isConnected,
  pageTheme,
  cardsTheme,
  availablePageThemes,
  availableCardThemes,
  onPageThemeChange,
  onCardsThemeChange,
  onCustomizeLayout,
  canResetLayout = false,
  onResetLayout,
  onCollapseAll,
  onExpandAll,
}: DemoHeaderProps) {
  const pageThemeId = pageTheme?.id ?? ""
  const cardsThemeId = cardsTheme?.id ?? ""

  return (
    <div className="demo-header flex items-center justify-between px-4 py-3 border-b border-border shrink-0 bg-background text-foreground">
      <div className="flex flex-col gap-0.5">
        <h1 className="text-lg font-semibold text-foreground">{title}</h1>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <div className="flex items-center gap-4">
        <Select value={pageThemeId} onValueChange={onPageThemeChange}>
          <SelectTrigger className="w-40 h-8 text-xs">
            <SelectValue>Page: {pageTheme?.name ?? "Loading..."}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            {availablePageThemes.map((theme) => (
              <SelectItem key={theme.id} value={theme.id}>
                {theme.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={cardsThemeId} onValueChange={onCardsThemeChange}>
          <SelectTrigger className="w-40 h-8 text-xs">
            <SelectValue>Cards: {cardsTheme?.name ?? "Loading..."}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            {availableCardThemes.map((theme) => (
              <SelectItem key={theme.id} value={theme.id}>
                {theme.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {onCustomizeLayout && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-8 gap-2 text-xs"
            onClick={onCustomizeLayout}
          >
            <LayoutPanelLeft className="h-3.5 w-3.5" />
            Layout
          </Button>
        )}
        {onResetLayout && canResetLayout && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-8 text-xs"
            onClick={onResetLayout}
          >
            Reset View
          </Button>
        )}
        {onCollapseAll && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-8 text-xs"
            onClick={onCollapseAll}
          >
            Collapse All
          </Button>
        )}
        {onExpandAll && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-8 text-xs"
            onClick={onExpandAll}
          >
            Expand All
          </Button>
        )}
        <Badge
          variant={isConnected ? "default" : "secondary"}
          className="text-xs"
        >
          {isConnected ? "Connected" : "Disconnected"}
        </Badge>
        <div className="flex items-center gap-2">
          <Switch
            id="auto-respond"
            checked={autoRespond}
            onCheckedChange={onAutoRespondChange}
          />
          <Label htmlFor="auto-respond" className="text-sm cursor-pointer">
            Auto-respond
          </Label>
        </div>
      </div>
    </div>
  )
}
