/**
 * PanelLayoutDialog Component
 *
 * Main dialog for panel layout customization.
 * Supports entity-level and user-default editing modes.
 * Uses Page/registry/panelTypes as single source of truth for available panels.
 *
 * @example
 * ```tsx
 * <PanelLayoutDialog
 *   open={isOpen}
 *   onOpenChange={setIsOpen}
 *   entityId={storyId}
 *   context="story"
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
import { useRoomPanels } from "@/hooks/useRoomPanels"
import type { PanelConfig } from "@/services/panelService"
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
  type PanelContext,
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
  /** Entity ID (roomId, storyId, etc.) - null for editing user defaults */
  entityId: string | null
  /** Panel context - determines which panels are available */
  context: PanelContext
  /** Whether current user owns the entity */
  isOwner?: boolean
  /** User's permission level on this entity */
  userPermission?: PanelPermission
  /** Whether user is admin/superuser */
  isAdmin?: boolean
  /** Mode: entity settings or user defaults */
  mode?: "entity" | "user-defaults"
}

// ============================================================================
// Component
// ============================================================================

export function PanelLayoutDialog({
  open,
  onOpenChange,
  entityId,
  context,
  isOwner = false,
  userPermission = "participant",
  isAdmin = false,
  mode = "entity",
}: PanelLayoutDialogProps) {
  // Room panels hook (only used in room/entity mode)
  // TODO: Generalize to usePanels hook that accepts entityType
  const roomPanels = useRoomPanels(entityId ?? "", {
    enabled: mode === "entity" && context === "room" && !!entityId,
  })

  // Derive available panels from registry
  const availablePanelsFromRegistry = useMemo(() => {
    // Filter by context
    let panels = getPanelsForContext(context)

    // Filter by entity permission
    const permittedPanels = getPanelsForEntityPermission(userPermission)
    panels = panels.filter((p) =>
      permittedPanels.some((pp) => pp.kind === p.kind)
    )

    // Filter by system role (exclude admin-only for non-admins)
    if (!isAdmin) {
      panels = panels.filter((p) => p.permission !== "admin")
    }

    // Convert to PreviewPanel format
    return panels.map((p) => ({
      id: p.kind,
      kind: p.kind,
      prominence: p.defaultProminence,
    }))
  }, [context, userPermission, isAdmin])

  // Local state for editing
  const [panels, setPanels] = useState<PreviewPanel[]>([])
  const [source, setSource] = useState<LayoutSource>("user_defaults")
  const [savedSource, setSavedSource] = useState<LayoutSource>("user_defaults")
  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(null)
  const [addPanelOpen, setAddPanelOpen] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  // Initialize from current config
  useEffect(() => {
    if (!open) return

    if (mode === "entity" && context === "room" && roomPanels.panels.length > 0) {
      setPanels(
        roomPanels.panels.map((p) => ({
          id: p.id,
          kind: p.kind,
          prominence: p.prominence,
        }))
      )
      const initialSource =
        (roomPanels.panelSource as LayoutSource) || "user_defaults"
      setSource(initialSource)
      setSavedSource(initialSource)
    } else {
      // Default to collaborate preset
      const defaultPreset = SYSTEM_PRESETS.find((p) => p.id === "collaborate")
      setPanels(defaultPreset?.panels || [])
      setSelectedPresetId("collaborate")
      setSource("user_defaults")
      setSavedSource("user_defaults")
    }
  }, [open, mode, context, roomPanels.panels, roomPanels.panelSource])

  // Auto-switch to custom when user modifies panels
  const switchToCustom = () => {
    if (source !== "custom" && source !== "room_override") {
      setSource("custom")
    }
  }

  // Handle preset selection
  const handlePresetSelect = (presetId: string) => {
    const preset = SYSTEM_PRESETS.find((p) => p.id === presetId)
    if (preset) {
      setPanels(preset.panels)
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

  // Get panels not yet added
  const availablePanelsToAdd = availablePanelsFromRegistry.filter(
    (ap) => !panels.some((p) => p.id === ap.id)
  )

  // Handle save
  const handleSave = async () => {
    setIsSaving(true)
    try {
      if (mode === "entity" && context === "room" && entityId) {
        if (source === "custom" || source === "room_override") {
          await roomPanels.setCustomPanels(panels as PanelConfig[])
        } else if (source === "user_defaults" || source === "room_defaults") {
          // User chose a default source — clear any custom override
          await roomPanels.resetToDefaults()
        }
      }
      // TODO: Handle story entity type
      // TODO: Handle user-defaults mode

      showSuccessToast("Your panel layout has been updated.")
      onOpenChange(false)
    } catch {
      showErrorToast("Could not save your layout. Please try again.")
    } finally {
      setIsSaving(false)
    }
  }

  // Context-aware description
  const description = context === "room"
    ? "Customize how panels are arranged in this room."
    : context === "story"
    ? "Customize how panels are arranged for this story."
    : "Customize your panel layout."

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Panel Layout</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Source selector (entity mode only, room context for now) */}
          {mode === "entity" && context === "room" && (
            <LayoutSourceSelector
              currentSource={source}
              onSourceChange={setSource}
              isRoomOwner={isOwner}
              hasRoomDefaults={!!roomPanels.roomDefaults}
              savedSource={savedSource}
            />
          )}

          {/* Presets */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Quick Presets</h4>
            <PresetPicker
              presets={SYSTEM_PRESETS}
              currentPresetId={selectedPresetId}
              onSelect={handlePresetSelect}
              variant="buttons"
            />
          </div>

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
