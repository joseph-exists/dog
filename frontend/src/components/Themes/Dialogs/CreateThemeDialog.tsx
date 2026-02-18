/**
 * CreateThemeDialog
 *
 * Dialog for creating new custom themes.
 * Owns: open/close state, mutation, toast feedback.
 * Delegates: form state, validation → ThemeForm.
 */

import { PaletteIcon, PlusIcon } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { useThemeManagement } from "@/hooks/useThemeRegistry"
import type { ThemeCategory, ThemeScope } from "@/services/themeService"
import { ThemeForm, type ThemeFormData } from "../Forms/ThemeForm"

// ============================================================================
// Props
// ============================================================================

interface CreateThemeDialogProps {
  trigger?: React.ReactNode
  onOpenChange?: (open: boolean) => void
  onSuccess?: () => void
  className?: string
}

// ============================================================================
// Component
// ============================================================================

export function CreateThemeDialog({
  trigger,
  onOpenChange,
  onSuccess,
  className,
}: CreateThemeDialogProps) {
  const [isOpen, setIsOpen] = useState(false)
  const { createThemeAsync, isCreating } = useThemeManagement()

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    onOpenChange?.(open)
  }

  const handleSubmit = async (data: ThemeFormData) => {
    try {
      // Build tokens from form data
      const tokens: Record<string, string> = {}

      if (data.category === "page" || data.category === "card") {
        if (data.category === "page" && data.background) {
          tokens["--background"] = data.background
        }
        if (data.foreground) tokens["--foreground"] = data.foreground
        if (data.card) tokens["--card"] = data.card
        if (data.cardForeground)
          tokens["--card-foreground"] = data.cardForeground
        if (data.border) tokens["--border"] = data.border
        if (data.muted) tokens["--muted"] = data.muted
        if (data.mutedForeground)
          tokens["--muted-foreground"] = data.mutedForeground
        if (data.secondary) tokens["--secondary"] = data.secondary
        if (data.secondaryForeground)
          tokens["--secondary-foreground"] = data.secondaryForeground
        if (data.accent) tokens["--accent"] = data.accent
        if (data.accentForeground)
          tokens["--accent-foreground"] = data.accentForeground
      }

      await createThemeAsync({
        name: data.name,
        description: data.description,
        category: data.category as ThemeCategory,
        scope: data.scope as ThemeScope,
        tokens,
      })

      showSuccessToast(`Theme "${data.name}" created.`)
      handleOpenChange(false)
      onSuccess?.()
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to create theme"
      showErrorToast(message)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        {trigger ?? (
          <Button variant="outline" size="sm" className={className}>
            <PlusIcon className="size-4 mr-2" />
            New Theme
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <PaletteIcon className="size-5" />
            Create Theme
          </DialogTitle>
          <DialogDescription>
            Create a custom theme for your pages and cards.
          </DialogDescription>
        </DialogHeader>

        <ThemeForm
          mode="create"
          onSubmit={handleSubmit}
          isSubmitting={isCreating}
          onCancel={() => handleOpenChange(false)}
        />
      </DialogContent>
    </Dialog>
  )
}
