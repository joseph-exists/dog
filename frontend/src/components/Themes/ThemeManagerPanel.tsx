/**
 * ThemeManagerPanel
 *
 * Full theme management interface showing all themes with CRUD operations.
 * Can be embedded in a settings page or used as a standalone panel.
 */

import { PaletteIcon } from "lucide-react"
import { useState } from "react"

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { useThemeList, useThemeManagement } from "@/hooks/useThemeRegistry"
import type {
  ThemeCategory,
  ThemeScope,
  ThemeViewModel,
} from "@/services/themeService"
import { CreateThemeDialog } from "./Dialogs/CreateThemeDialog"
import { ThemeCard } from "./Display/ThemeCard"
import { ThemeForm, type ThemeFormData } from "./Forms/ThemeForm"

// ============================================================================
// Component
// ============================================================================

export function ThemeManagerPanel() {
  const [activeCategory, setActiveCategory] = useState<ThemeCategory>("page")
  const [editingTheme, setEditingTheme] = useState<ThemeViewModel | null>(null)
  const [deletingTheme, setDeletingTheme] = useState<ThemeViewModel | null>(
    null,
  )

  const { themes, isLoading, refetch } = useThemeList({
    category: activeCategory,
  })
  const { updateThemeAsync, isUpdating, deleteThemeAsync, isDeleting } =
    useThemeManagement()

  // Separate system themes from user themes
  const systemThemes = themes.filter((t) => t.isSystem)
  const userThemes = themes.filter((t) => !t.isSystem)

  const handleEdit = (theme: ThemeViewModel) => {
    setEditingTheme(theme)
  }

  const handleDelete = (theme: ThemeViewModel) => {
    setDeletingTheme(theme)
  }

  const handleEditSubmit = async (data: ThemeFormData) => {
    if (!editingTheme) return

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

      await updateThemeAsync(editingTheme.id, {
        name: data.name,
        description: data.description,
        scope: data.scope as ThemeScope,
        tokens,
      })

      showSuccessToast(`Theme "${data.name}" updated.`)
      setEditingTheme(null)
      refetch()
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to update theme"
      showErrorToast(message)
    }
  }

  const handleDeleteConfirm = async () => {
    if (!deletingTheme) return

    try {
      await deleteThemeAsync(deletingTheme.id)
      showSuccessToast(`Theme "${deletingTheme.name}" deleted.`)
      setDeletingTheme(null)
      refetch()
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to delete theme"
      showErrorToast(message)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <PaletteIcon className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-lg font-semibold">Theme Manager</h2>
        </div>
        <CreateThemeDialog onSuccess={refetch} />
      </div>

      {/* Category Tabs */}
      <Tabs
        value={activeCategory}
        onValueChange={(v) => setActiveCategory(v as ThemeCategory)}
      >
        <TabsList>
          <TabsTrigger value="page">Page</TabsTrigger>
          <TabsTrigger value="card">Card</TabsTrigger>
          <TabsTrigger value="syntax">Syntax</TabsTrigger>
          <TabsTrigger value="motion">Motion</TabsTrigger>
        </TabsList>

        <TabsContent value={activeCategory} className="mt-4 space-y-6">
          {isLoading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-32" />
              ))}
            </div>
          ) : (
            <>
              {/* User Themes */}
              {userThemes.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-sm font-medium text-muted-foreground">
                    Your Themes
                  </h3>
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {userThemes.map((theme) => (
                      <ThemeCard
                        key={theme.id}
                        theme={theme}
                        onEdit={handleEdit}
                        onDelete={handleDelete}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* System Themes */}
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-muted-foreground">
                  System Themes
                </h3>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {systemThemes.map((theme) => (
                    <ThemeCard key={theme.id} theme={theme} />
                  ))}
                </div>
                {systemThemes.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    No system themes available for this category.
                  </p>
                )}
              </div>
            </>
          )}
        </TabsContent>
      </Tabs>

      {/* Edit Dialog */}
      <Dialog open={!!editingTheme} onOpenChange={() => setEditingTheme(null)}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <PaletteIcon className="size-5" />
              Edit Theme
            </DialogTitle>
            <DialogDescription>
              Modify your custom theme settings.
            </DialogDescription>
          </DialogHeader>

          {editingTheme && (
            <ThemeForm
              mode="edit"
              initialData={editingTheme}
              onSubmit={handleEditSubmit}
              isSubmitting={isUpdating}
              onCancel={() => setEditingTheme(null)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog
        open={!!deletingTheme}
        onOpenChange={() => setDeletingTheme(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Theme</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{deletingTheme?.name}"? This
              action cannot be undone. Any bindings using this theme will fall
              back to defaults.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
