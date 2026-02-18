/**
 * ThemeCard
 *
 * Displays a theme with preview and actions.
 * Shows a color swatch preview based on the theme's tokens.
 */

import { MoreVertical, Pencil, Trash2 } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import type { ThemeViewModel } from "@/services/themeService"

// ============================================================================
// Props
// ============================================================================

export interface ThemeCardProps {
  theme: ThemeViewModel
  onEdit?: (theme: ThemeViewModel) => void
  onDelete?: (theme: ThemeViewModel) => void
}

// ============================================================================
// Component
// ============================================================================

export function ThemeCard({ theme, onEdit, onDelete }: ThemeCardProps) {
  const tokens = theme.tokens ?? {}

  // Extract colors for preview swatches
  const previewColors = [
    tokens["--background"],
    tokens["--card"],
    tokens["--foreground"],
    tokens["--accent"],
    tokens["--border"],
  ].filter(Boolean) as string[]

  const canModify = !theme.isSystem

  return (
    <Card className="group relative">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-base font-medium">
              {theme.name}
            </CardTitle>
            {theme.description && (
              <p className="text-xs text-muted-foreground line-clamp-1">
                {theme.description}
              </p>
            )}
          </div>

          {canModify && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {onEdit && (
                  <DropdownMenuItem onClick={() => onEdit(theme)}>
                    <Pencil className="h-4 w-4 mr-2" />
                    Edit
                  </DropdownMenuItem>
                )}
                {onDelete && (
                  <>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onClick={() => onDelete(theme)}
                      className="text-destructive focus:text-destructive"
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete
                    </DropdownMenuItem>
                  </>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Color swatches preview */}
        {previewColors.length > 0 ? (
          <div className="flex gap-1">
            {previewColors.slice(0, 5).map((color, i) => (
              <div
                key={i}
                className="h-6 flex-1 rounded-sm border border-border/50"
                style={{ backgroundColor: color }}
                title={color}
              />
            ))}
          </div>
        ) : (
          <div className="h-6 rounded-sm border border-dashed border-border flex items-center justify-center">
            <span className="text-xs text-muted-foreground">Inherits</span>
          </div>
        )}

        {/* Badges */}
        <div className="flex gap-2 flex-wrap">
          <Badge variant="secondary" className="text-xs">
            {theme.category}
          </Badge>
          <Badge
            variant={theme.isSystem ? "default" : "outline"}
            className="text-xs"
          >
            {theme.isSystem ? "system" : theme.scope}
          </Badge>
        </div>
      </CardContent>
    </Card>
  )
}
