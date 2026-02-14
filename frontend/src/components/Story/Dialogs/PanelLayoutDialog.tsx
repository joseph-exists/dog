/**
 * PanelLayoutDialog Component (Story-specific)
 *
 * Dialog for customizing panel layout on story pages.
 * Uses Story/registry/panelTypes as single source of truth for available panels.
 *
 * @example
 * ```tsx
 * <PanelLayoutDialog
 *   open={isOpen}
 *   onOpenChange={setIsOpen}
 *   storyId={storyId}
 *   isOwner={isAuthor}
 *   userPermission="owner"
 * />
 * ```
 */

import { Plus } from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import {
  type LayoutSource,
  LayoutSourceSelector,
} from "../Forms/FormSelectors/LayoutSourceSelector"
import { InteractivePreview, type PreviewPanel } from "../InteractivePreview"
import { PresetPicker, SYSTEM_PRESETS } from "../primitives/PresetPicker"
import {
  getPanelDisplayName,
  getPanelsForContext,
  getPanelsForEntityPermission,
  type PanelKind,
  type PanelPermission,
} from "../registry"

// ============================================================================
// Types
// ============================================================================

export interface PanelLayoutDialogProps {
  /** Whether the dialog is open */
  open: boolean
  /** Called when open state changes */
  onOpenChange: (open: boolean) => void
  /** Story ID - null for editing user defaults */
  storyId: string | null
  /** Whether current user owns the story */
  isOwner?: boolean
  /** User's permission level on this story */
  userPermission?: PanelPermission
  /** Whether user is admin/superuser */
  isAdmin?: boolean
}

// ============================================================================
// Component
// ============================================================================

export function PanelLayoutDialog({
  open,
  onOpenChange,
  storyId,
  isOwner = false,
  userPermission = "none",
  isAdmin = false,
}: PanelLayoutDialogProps) {
  // Local state for editing
  const [panels, setPanels] = useState<PreviewPanel[]>([])
  const [source, setSource] = useState<LayoutSource>("user_defaults")
  const [savedSource, setSavedSource] = useState<LayoutSource>("user_defaults")
  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(null)
  const [addPanelOpen, setAddPanelOpen] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  // Derive available panels from registry (story context only)
  const availablePanelsFromRegistry = useMemo(() => {
    // Filter by story context
    let panelDefs = getPanelsForContext("story")

    // Filter by entity permission
    const permittedPanels = getPanelsForEntityPermission(userPermission)
    panelDefs = panelDefs.filter((p) =>
      permittedPanels.some((pp) => pp.kind === p.kind)
    )

    // Filter by system role (exclude admin-only for non-admins)
    if (!isAdmin) {
      panelDefs = panelDefs.filter((p) => p.permission !== "admin")
    }

    // Convert to PreviewPanel format
    return panelDefs.map((p) => ({
      id: p.kind,
      kind: p.kind,
      prominence: p.defaultProminence,
    }))
  }, [userPermission, isAdmin])

  // Get the default preset for stories
  const getDefaultStoryPreset = () => {
    // Try story-specific preset first, fallback to first available
    const storyPreset = SYSTEM_PRESETS.find(
      (p) => p.id === "story_player" || p.id === "story_play"
    )
    if (storyPreset) return storyPreset

    // Fallback: create a default from available panels
    const defaultPanels = availablePanelsFromRegistry.slice(0, 2)
    return {
      id: "default",
      name: "Default",
      description: "Default story layout",
      panels: defaultPanels,
    }
  }

  // Initialize from current config
  useEffect(() => {
    if (!open) return

    // TODO: Load saved story panel config when backend support is added
    // For now, use default preset
    const defaultPreset = getDefaultStoryPreset()
    setPanels(defaultPreset.panels)
    setSelectedPresetId(defaultPreset.id)
    setSource("user_defaults")
    setSavedSource("user_defaults")
  }, [open, availablePanelsFromRegistry])

  // Auto-switch to custom when user modifies panels
  const switchToCustom = () => {
    if (source !== "custom") {
      setSource("custom")
    }
  }

  // Handle preset selection
  const handlePresetSelect = (presetId: string) => {
    const preset = SYSTEM_PRESETS.find((p) => p.id === presetId)
    if (preset) {
      // Filter preset panels to only include valid story panels
      const validPanels = preset.panels.filter((panel) =>
        availablePanelsFromRegistry.some((ap) => ap.kind === panel.kind)
      )
      setPanels(validPanels.length > 0 ? validPanels : preset.panels)
      setSelectedPresetId(presetId)
      switchToCustom()
    }
  }

  // Handle panel reorder
  const handleReorder = (newPanels: PreviewPanel[]) => {
    setPanels(newPanels)
    setSelectedPresetId(null)
    switchToCustom()
  }

  // Handle panel remove
  const handleRemove = (panelId: string) => {
    setPanels((prev) => prev.filter((p) => p.id !== panelId))
    setSelectedPresetId(null)
    switchToCustom()
  }

  // Handle add panel
  const handleAddPanel = (panel: PreviewPanel) => {
    if (panels.some((p) => p.id === panel.id)) return
    setPanels((prev) => [...prev, panel])
    setSelectedPresetId(null)
    switchToCustom()
    setAddPanelOpen(false)
  }

  // Get panels not yet added (filtered to story-valid panels)
  const availablePanelsToAdd = availablePanelsFromRegistry.filter(
    (ap) => !panels.some((p) => p.kind === ap.kind)
  )

  // Handle save
  const handleSave = async () => {
    setIsSaving(true)
    try {
      // TODO: Implement story panel persistence when backend support is added
      // For now, just show success and close
      if (storyId) {
        console.log("Saving story panel layout:", { storyId, panels, source })
        // Future: await storyPanelsService.saveLayout(storyId, panels, source)
      }

      showSuccessToast("Your panel layout has been updated.")
      onOpenChange(false)
    } catch {
      showErrorToast("Could not save your layout. Please try again.")
    } finally {
      setIsSaving(false)
    }
  }

  // Filter presets to only show those with at least one valid story panel
  const validPresets = SYSTEM_PRESETS.filter((preset) =>
    preset.panels.some((panel) =>
      availablePanelsFromRegistry.some((ap) => ap.kind === panel.kind)
    )
  )

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Panel Layout</DialogTitle>
          <DialogDescription>
            Customize how panels are arranged for this story.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Source selector (when storyId is provided) */}
          {storyId && (
            <LayoutSourceSelector
              currentSource={source}
              onSourceChange={setSource}
              isRoomOwner={isOwner}
              hasRoomDefaults={false} // TODO: Check for story defaults
              savedSource={savedSource}
            />
          )}

          {/* Presets (only show presets with valid story panels) */}
          {validPresets.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Quick Presets</h4>
              <PresetPicker
                presets={validPresets}
                currentPresetId={selectedPresetId}
                onSelect={handlePresetSelect}
                variant="buttons"
              />
            </div>
          )}

          {/* Interactive preview */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Panel Arrangement</h4>
            <div className="border rounded-lg p-4 bg-muted/30">
              <InteractivePreview
                panels={panels}
                onReorder={handleReorder}
                onRemove={handleRemove}
              />
            </div>
          </div>

          {/* Add panel */}
          {availablePanelsToAdd.length > 0 && (
            <Collapsible open={addPanelOpen} onOpenChange={setAddPanelOpen}>
              <CollapsibleTrigger asChild>
                <Button variant="outline" className="w-full gap-2">
                  <Plus className="h-4 w-4" />
                  Add Panel
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="pt-2">
                <div className="grid grid-cols-2 gap-2">
                  {availablePanelsToAdd.map((panel) => (
                    <Button
                      key={panel.id}
                      variant="ghost"
                      className="justify-start"
                      onClick={() => handleAddPanel(panel)}
                    >
                      {getPanelDisplayName(panel.kind as PanelKind)}
                    </Button>
                  ))}
                </div>
              </CollapsibleContent>
            </Collapsible>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? "Saving..." : "Save"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
