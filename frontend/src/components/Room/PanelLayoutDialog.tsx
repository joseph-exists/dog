/**
 * PanelLayoutDialog Component
 *
 * Main dialog for panel layout customization.
 * Supports room-level and user-default editing modes.
 *
 * @example
 * ```tsx
 * <PanelLayoutDialog
 *   open={isOpen}
 *   onOpenChange={setIsOpen}
 *   roomId={roomId}
 *   isRoomOwner={canManage}
 * />
 * ```
 */

import { Plus } from "lucide-react"
import { useEffect, useState } from "react"

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
import useCustomToast from "@/hooks/useCustomToast"
import { useRoomPanels } from "@/hooks/useRoomPanels"
import type { PanelConfig } from "@/services/panelService"
import { InteractivePreview, type PreviewPanel } from "./InteractivePreview"
import { type LayoutSource, LayoutSourceSelector } from "./LayoutSourceSelector"
import { PresetPicker, SYSTEM_PRESETS } from "./primitives/PresetPicker"

// ============================================================================
// Types
// ============================================================================

export interface PanelLayoutDialogProps {
  /** Whether the dialog is open */
  open: boolean
  /** Called when open state changes */
  onOpenChange: (open: boolean) => void
  /** Room ID (null for editing user defaults) */
  roomId: string | null
  /** Whether current user is room owner */
  isRoomOwner?: boolean
  /** Mode: room settings or user defaults */
  mode?: "room" | "user-defaults"
}

// ============================================================================
// Available Panels
// ============================================================================

const AVAILABLE_PANELS: PreviewPanel[] = [
  { id: "chat", kind: "chat", prominence: "primary" },
  { id: "story", kind: "storyEditor", prominence: "primary" },
  { id: "runtime", kind: "storyRuntime", prominence: "primary" },
  { id: "canvas", kind: "canvas", prominence: "primary" },
  { id: "a2ui", kind: "a2ui", prominence: "primary" },
  { id: "participants", kind: "participantPanel", prominence: "auxiliary" },
  { id: "debug", kind: "debug", prominence: "auxiliary" },
]

const panelNames: Record<string, string> = {
  chat: "Chat",
  storyEditor: "Story Editor",
  storyRuntime: "Story Runtime",
  canvas: "Canvas",
  a2ui: "Agent UI",
  participantPanel: "Participants",
  debug: "Debug",
}

// ============================================================================
// Component
// ============================================================================

export function PanelLayoutDialog({
  open,
  onOpenChange,
  roomId,
  isRoomOwner = false,
  mode = "room",
}: PanelLayoutDialogProps) {
  const { showSuccessToast, showErrorToast } = useCustomToast()

  // Room panels hook (only used in room mode)
  const roomPanels = useRoomPanels(roomId ?? "", {
    enabled: mode === "room" && !!roomId,
  })

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

    if (mode === "room" && roomPanels.panels.length > 0) {
      setPanels(
        roomPanels.panels.map((p) => ({
          id: p.id,
          kind: p.kind,
          prominence: p.prominence,
        })),
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
  }, [open, mode, roomPanels.panels, roomPanels.panelSource])

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
  const availablePanelsToAdd = AVAILABLE_PANELS.filter(
    (ap) => !panels.some((p) => p.id === ap.id),
  )

  // Handle save
  const handleSave = async () => {
    setIsSaving(true)
    try {
      if (mode === "room" && roomId) {
        if (source === "custom" || source === "room_override") {
          await roomPanels.setCustomPanels(panels as PanelConfig[])
        } else if (source === "user_defaults" || source === "room_defaults") {
          // User chose a default source — clear any custom override
          await roomPanels.resetToDefaults()
        }
      }
      // TODO: Handle user-defaults mode

      showSuccessToast("Your panel layout has been updated.")
      onOpenChange(false)
    } catch {
      showErrorToast("Could not save your layout. Please try again.")
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Panel Layout</DialogTitle>
          <DialogDescription>
            Customize how panels are arranged in this room.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Source selector (room mode only) */}
          {mode === "room" && (
            <LayoutSourceSelector
              currentSource={source}
              onSourceChange={setSource}
              isRoomOwner={isRoomOwner}
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
                      {panelNames[panel.kind] || panel.kind}
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
