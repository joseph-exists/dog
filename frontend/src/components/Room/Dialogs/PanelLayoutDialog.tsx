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
import {
  createDefaultRepoExplorerPanelConfig,
  createDefaultRepoFileViewerPanelConfig,
  normalizeRepoPanelConfig,
  parseRepoExplorerPanelConfig,
  parseRepoFileViewerPanelConfig,
} from "@/components/Repo/panels/config"

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
import { Input } from "@/components/ui/input"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { useRoomPanels } from "@/hooks/useRoomPanels"
import type { PanelConfig } from "@/services/panelService"
import { PresetPicker, SYSTEM_PRESETS } from "../primitives/PresetPicker"
import {
  InteractivePreview,
  type PreviewPanel,
} from "../RoomShell/InteractivePreview"
import {
  type LayoutSource,
  LayoutSourceSelector,
} from "../RoomShell/LayoutSourceSelector"

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
  { id: "solo-story", kind: "storyPlayer", prominence: "primary" },
  { id: "repo-explorer", kind: "repoExplorer", prominence: "primary" },
  { id: "file-viewer", kind: "fileViewer", prominence: "primary" },
  { id: "canvas", kind: "canvas", prominence: "primary" },
  { id: "a2ui", kind: "a2ui", prominence: "primary" },
  { id: "participants", kind: "participantPanel", prominence: "auxiliary" },
  { id: "debug", kind: "debug", prominence: "auxiliary" },
]

const panelNames: Record<string, string> = {
  chat: "Chat",
  storyEditor: "Story Editor",
  storyRuntime: "Story Runtime",
  storyPlayer: "Solo Story Player",
  repoExplorer: "Repo Explorer",
  fileViewer: "File Viewer",
  canvas: "Canvas",
  a2ui: "Agent UI",
  participantPanel: "Participants",
  debug: "Debug",
}

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function isRepoPanelKind(kind: string): kind is "repoExplorer" | "fileViewer" {
  return kind === "repoExplorer" || kind === "fileViewer"
}

function toPreviewPanel(panel: PanelConfig): PreviewPanel {
  return {
    id: panel.id,
    kind: panel.kind,
    prominence: panel.prominence,
  }
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
  // Room panels hook (only used in room mode)
  const roomPanels = useRoomPanels(roomId ?? "", {
    enabled: mode === "room" && !!roomId,
  })

  // Local state for editing
  const [panels, setPanels] = useState<PanelConfig[]>([])
  const [source, setSource] = useState<LayoutSource>("user_defaults")
  const [savedSource, setSavedSource] = useState<LayoutSource>("user_defaults")
  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(null)
  const [addPanelOpen, setAddPanelOpen] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  // Initialize from current config
  useEffect(() => {
    if (!open) return

    if (mode === "room" && roomPanels.panels.length > 0) {
      setPanels(roomPanels.panels)
      const initialSource =
        (roomPanels.panelSource as LayoutSource) || "user_defaults"
      setSource(initialSource)
      setSavedSource(initialSource)
    } else {
      // Default to collaborate preset
      const defaultPreset = SYSTEM_PRESETS.find((p) => p.id === "collaborate")
      setPanels(
        (defaultPreset?.panels || []).map((panel) => ({
          id: panel.id,
          kind: panel.kind as PanelConfig["kind"],
          prominence: panel.prominence,
          config_json: null,
          entity_binding: null,
        })),
      )
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
      setPanels(
        preset.panels.map((panel) => ({
          id: panel.id,
          kind: panel.kind as PanelConfig["kind"],
          prominence: panel.prominence,
          config_json: null,
          entity_binding: null,
        })),
      )
      setSelectedPresetId(presetId)
      switchToCustom()
    }
  }

  // Handle panel reorder
  const handleReorder = (newPanels: PreviewPanel[]) => {
    setPanels((prev) => {
      const byId = new Map(prev.map((panel) => [panel.id, panel]))
      return newPanels.map((previewPanel) => {
        const existing = byId.get(previewPanel.id)
        if (existing) {
          return {
            ...existing,
            kind: previewPanel.kind as PanelConfig["kind"],
            prominence: previewPanel.prominence,
          }
        }
        return {
          id: previewPanel.id,
          kind: previewPanel.kind as PanelConfig["kind"],
          prominence: previewPanel.prominence,
          config_json: null,
          entity_binding: null,
        }
      })
    })
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
    setPanels((prev) => {
      const basePanel: PanelConfig = {
        id: panel.id,
        kind: panel.kind as PanelConfig["kind"],
        prominence: panel.prominence,
        config_json: null,
        entity_binding: null,
      }

      if (panel.kind === "repoExplorer") {
        return [
          ...prev,
          {
            ...basePanel,
            config_json: {
              ...createDefaultRepoExplorerPanelConfig(panel.id),
              repo_id: null,
            },
          },
        ]
      }

      if (panel.kind === "fileViewer") {
        return [
          ...prev,
          {
            ...basePanel,
            config_json: {
              ...createDefaultRepoFileViewerPanelConfig(panel.id),
              repo_id: null,
            },
          },
        ]
      }

      return [...prev, basePanel]
    })
    setSelectedPresetId(null)
    switchToCustom()
    setAddPanelOpen(false)
  }

  const handleUpdateRepoPanelConfig = (
    panelId: string,
    patch: Record<string, unknown>,
  ) => {
    setPanels((prev) =>
      prev.map((panel) => {
        if (panel.id !== panelId || !isRepoPanelKind(panel.kind)) return panel
        const currentConfig = isObjectRecord(panel.config_json)
          ? panel.config_json
          : {}
        const nextConfig = {
          ...currentConfig,
          ...patch,
        }
        return {
          ...panel,
          config_json: normalizeRepoPanelConfig(panel.kind, panel.id, nextConfig),
        }
      }),
    )
    switchToCustom()
  }

  // Get panels not yet added
  const availablePanelsToAdd = AVAILABLE_PANELS.filter(
    (ap) => !panels.some((p) => p.id === ap.id),
  )
  const repoPanels = panels.filter((panel) => isRepoPanelKind(panel.kind))
  const previewPanels = panels.map(toPreviewPanel)

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

          {repoPanels.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-sm font-medium">Repo Panel Bindings</h4>
              <div className="space-y-3">
                {repoPanels.map((panel) => {
                  const config = isObjectRecord(panel.config_json)
                    ? panel.config_json
                    : {}
                  const repoIdValue =
                    typeof config.repo_id === "string" ? config.repo_id : ""

                  if (panel.kind === "repoExplorer") {
                    const parsed = parseRepoExplorerPanelConfig(
                      panel.config_json,
                      panel.id,
                    )
                    return (
                      <div key={panel.id} className="rounded-md border p-3 space-y-2">
                        <div className="text-xs font-medium text-muted-foreground">
                          {panelNames[panel.kind]} ({panel.id})
                        </div>
                        <Input
                          value={repoIdValue}
                          onChange={(event) =>
                            handleUpdateRepoPanelConfig(panel.id, {
                              repo_id: event.target.value || null,
                            })
                          }
                          placeholder="repo_id"
                        />
                        <Input
                          value={parsed.initial_path}
                          onChange={(event) =>
                            handleUpdateRepoPanelConfig(panel.id, {
                              initial_path: event.target.value,
                            })
                          }
                          placeholder="initial_path"
                        />
                        <Input
                          value={parsed.selection_key || ""}
                          onChange={(event) =>
                            handleUpdateRepoPanelConfig(panel.id, {
                              selection_key: event.target.value || null,
                            })
                          }
                          placeholder="selection_key"
                        />
                      </div>
                    )
                  }

                  const parsed = parseRepoFileViewerPanelConfig(
                    panel.config_json,
                    panel.id,
                  )
                  return (
                    <div key={panel.id} className="rounded-md border p-3 space-y-2">
                      <div className="text-xs font-medium text-muted-foreground">
                        {panelNames[panel.kind]} ({panel.id})
                      </div>
                      <Input
                        value={repoIdValue}
                        onChange={(event) =>
                          handleUpdateRepoPanelConfig(panel.id, {
                            repo_id: event.target.value || null,
                          })
                        }
                        placeholder="repo_id"
                      />
                      <select
                        value={parsed.path_mode}
                        onChange={(event) =>
                          handleUpdateRepoPanelConfig(panel.id, {
                            path_mode: event.target.value,
                          })
                        }
                        className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                      >
                        <option value="selection">selection</option>
                        <option value="fixed">fixed</option>
                        <option value="readme">readme</option>
                      </select>
                      {parsed.path_mode === "fixed" && (
                        <Input
                          value={parsed.fixed_path || ""}
                          onChange={(event) =>
                            handleUpdateRepoPanelConfig(panel.id, {
                              fixed_path: event.target.value,
                            })
                          }
                          placeholder="fixed_path"
                        />
                      )}
                      <Input
                        value={parsed.selection_key || ""}
                        onChange={(event) =>
                          handleUpdateRepoPanelConfig(panel.id, {
                            selection_key: event.target.value || null,
                          })
                        }
                        placeholder="selection_key"
                      />
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Interactive preview */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Panel Arrangement</h4>
            <div className="border rounded-lg p-4 bg-muted/30">
              <InteractivePreview
                panels={previewPanels}
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
                {availablePanelsToAdd.some(
                  (panel) => panel.kind === "storyPlayer",
                ) ? (
                  <p className="mt-3 text-xs text-muted-foreground">
                    Solo Story Player is local-only. It does not sync with
                    shared room runtime.
                  </p>
                ) : null}
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
