import type React from "react"
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUp, Plus, X } from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import { InteractivePreview, type PreviewPanel } from "@/components/Page/InteractivePreview"
import { PresetPicker } from "@/components/Page/primitives/PresetPicker"
import type { RepoLayoutPreset } from "@/components/Repo/panels/repoLayoutPresets"
import type { RepoPanelLayoutItem } from "@/components/Repo/panels/repoPanelLayoutCustomization"
import { createDefaultRepoPanelConfig } from "@/components/Repo/panels/config"
import {
  REPO_PANEL_PREVIEW_COLORS,
  REPO_PANEL_PREVIEW_LABELS,
} from "@/components/Repo/panels/previewConfig"
import { getRepoPanelDefinition, REPO_PANEL_DEFINITIONS } from "@/components/Repo/registry"
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

function createPanelId(kind: RepoPanelLayoutItem["kind"], existingIds: string[]): string {
  const base = kind
  if (!existingIds.includes(base)) return base
  let index = 2
  while (existingIds.includes(`${base}-${index}`)) {
    index += 1
  }
  return `${base}-${index}`
}

function toPreviewPanels(items: RepoPanelLayoutItem[]): PreviewPanel[] {
  return items
    .filter((item) => !item.hidden)
    .map((item) => ({
      id: item.id,
      kind: item.kind,
      prominence: item.prominence,
    }))
}

function applyPreviewPanels(
  items: RepoPanelLayoutItem[],
  previewPanels: PreviewPanel[],
): RepoPanelLayoutItem[] {
  const visibleById = new Map(items.filter((item) => !item.hidden).map((item) => [item.id, item]))
  const hidden = items.filter((item) => item.hidden)

  const nextVisible = previewPanels
    .map((panel) => {
      const item = visibleById.get(panel.id)
      if (!item) return null
      return {
        ...item,
        prominence: panel.prominence,
      }
    })
    .filter((item): item is RepoPanelLayoutItem => item !== null)

  return [...nextVisible, ...hidden]
}

function movePreviewPanel(
  previewPanels: PreviewPanel[],
  panelId: string,
  direction: -1 | 1,
) {
  const index = previewPanels.findIndex((panel) => panel.id === panelId)
  if (index < 0) return previewPanels
  const nextIndex = index + direction
  if (nextIndex < 0 || nextIndex >= previewPanels.length) return previewPanels

  const nextPanels = [...previewPanels]
  const [item] = nextPanels.splice(index, 1)
  if (!item) return previewPanels
  nextPanels.splice(nextIndex, 0, item)
  return nextPanels
}

function toPresetPickerPanels(items: RepoPanelLayoutItem[]) {
  return toPreviewPanels(items)
}

function moveSelection<T>(items: T[], currentIndex: number, direction: -1 | 1) {
  if (items.length === 0) return -1
  const nextIndex = currentIndex + direction
  if (nextIndex < 0) return items.length - 1
  if (nextIndex >= items.length) return 0
  return nextIndex
}

interface RepoPanelLayoutDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  repoName: string
  presets: RepoLayoutPreset[]
  activePresetId: string
  panels: RepoPanelLayoutItem[]
  canReset: boolean
  onApply: (items: RepoPanelLayoutItem[], presetId: string | null) => void
  onReset: () => void
  onOpenAdvanced: (items: RepoPanelLayoutItem[]) => void
}

export function RepoPanelLayoutDialog({
  open,
  onOpenChange,
  repoName,
  presets,
  activePresetId,
  panels,
  canReset,
  onApply,
  onReset,
  onOpenAdvanced,
}: RepoPanelLayoutDialogProps) {
  const [draftPanels, setDraftPanels] = useState<RepoPanelLayoutItem[]>(panels)
  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(activePresetId)
  const [addPanelOpen, setAddPanelOpen] = useState(false)
  const [focusedPanelId, setFocusedPanelId] = useState<string | null>(null)
  const [focusedAddPanelKind, setFocusedAddPanelKind] =
    useState<RepoPanelLayoutItem["kind"] | null>(null)

  useEffect(() => {
    if (!open) return
    setDraftPanels(panels)
    setSelectedPresetId(activePresetId)
    setAddPanelOpen(false)
    setFocusedPanelId(toPreviewPanels(panels)[0]?.id ?? null)
    setFocusedAddPanelKind(REPO_PANEL_DEFINITIONS[0]?.kind ?? null)
  }, [activePresetId, open, panels])

  const previewPanels = useMemo(() => toPreviewPanels(draftPanels), [draftPanels])

  const presetPickerOptions = useMemo(
    () =>
      presets.map((preset) => ({
        id: preset.id,
        name: preset.label,
        description: preset.description,
        panels: toPresetPickerPanels(preset.items),
      })),
    [presets],
  )
  const addablePanels = useMemo(() => REPO_PANEL_DEFINITIONS, [])

  const handleReorder = (nextPreviewPanels: PreviewPanel[]) => {
    setDraftPanels((current) => applyPreviewPanels(current, nextPreviewPanels))
    setSelectedPresetId(null)
  }

  const handleRemove = (panelId: string) => {
    setDraftPanels((current) => {
      const nextPanels = current.filter((item) => item.id !== panelId)
      const nextVisiblePanels = toPreviewPanels(nextPanels)
      setFocusedPanelId(nextVisiblePanels[0]?.id ?? null)
      return nextPanels
    })
    setSelectedPresetId(null)
  }

  const handleToggleProminence = (panelId: string) => {
    setDraftPanels((current) =>
      current.map((item) =>
        item.id === panelId
          ? {
              ...item,
              prominence: item.prominence === "primary" ? "auxiliary" : "primary",
            }
          : item,
      ),
    )
    setSelectedPresetId(null)
  }

  const handleAddPanel = (kind: RepoPanelLayoutItem["kind"]) => {
    setDraftPanels((current) => {
      const nextId = createPanelId(
        kind,
        current.map((item) => item.id),
      )
      const definition = getRepoPanelDefinition(kind)
      const nextPanels = [
        ...current,
        {
          id: nextId,
          kind,
          title: definition?.label ?? kind,
          prominence: definition?.defaultProminence ?? "primary",
          config_json: createDefaultRepoPanelConfig(kind, nextId) as unknown as Record<
            string,
            unknown
          > | null,
          hidden: false,
        },
      ]
      setFocusedPanelId(nextId)
      return nextPanels
    })
    setSelectedPresetId(null)
    setAddPanelOpen(false)
  }

  const handleMoveFocusedPanel = (direction: -1 | 1) => {
    if (!focusedPanelId) return
    setDraftPanels((current) =>
      applyPreviewPanels(
        current,
        movePreviewPanel(toPreviewPanels(current), focusedPanelId, direction),
      ),
    )
    setSelectedPresetId(null)
  }

  const handleMoveFocusedPanelProminence = () => {
    if (!focusedPanelId) return
    handleToggleProminence(focusedPanelId)
  }

  const handleDialogKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    const hasMod = event.metaKey || event.ctrlKey
    if (hasMod && event.shiftKey && event.key.toLowerCase() === "a") {
      event.preventDefault()
      setAddPanelOpen((current) => !current)
      return
    }

    if (event.altKey && event.key.toLowerCase() === "a") {
      event.preventDefault()
      if (focusedAddPanelKind) {
        handleAddPanel(focusedAddPanelKind)
      }
      return
    }

    if (addPanelOpen && (event.key === "ArrowDown" || event.key === "ArrowUp")) {
      event.preventDefault()
      const currentIndex = addablePanels.findIndex(
        (panel) => panel.kind === focusedAddPanelKind,
      )
      const nextIndex = moveSelection(
        addablePanels,
        currentIndex >= 0 ? currentIndex : 0,
        event.key === "ArrowDown" ? 1 : -1,
      )
      setFocusedAddPanelKind(addablePanels[nextIndex]?.kind ?? null)
      return
    }

    if (addPanelOpen && event.key === "Enter" && focusedAddPanelKind) {
      event.preventDefault()
      handleAddPanel(focusedAddPanelKind)
      return
    }

    if (
      focusedPanelId &&
      (event.key === "Backspace" || event.key === "Delete") &&
      !event.altKey
    ) {
      event.preventDefault()
      handleRemove(focusedPanelId)
      return
    }

    if (!focusedPanelId) return
    if (event.altKey && event.key === "ArrowUp") {
      event.preventDefault()
      handleMoveFocusedPanel(-1)
    }
    if (event.altKey && event.key === "ArrowDown") {
      event.preventDefault()
      handleMoveFocusedPanel(1)
    }
    if (
      event.altKey &&
      (event.key === "ArrowLeft" || event.key === "ArrowRight")
    ) {
      event.preventDefault()
      handleMoveFocusedPanelProminence()
    }
  }

  const handleApply = () => {
    onApply(draftPanels, selectedPresetId)
    onOpenChange(false)
  }

  const hasVisiblePanels = previewPanels.length > 0

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-3xl" onKeyDown={handleDialogKeyDown}>
        <DialogHeader>
          <DialogTitle>Panel Layout</DialogTitle>
          <DialogDescription>
            Arrange the visible repository panels for {repoName}. Use the advanced
            editor for per-instance config and duplicate-heavy layouts.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Quick Presets</h4>
            <PresetPicker
              presets={presetPickerOptions}
              currentPresetId={selectedPresetId}
              panelLabels={REPO_PANEL_PREVIEW_LABELS}
              panelColors={REPO_PANEL_PREVIEW_COLORS}
              onSelect={(presetId) => {
                setSelectedPresetId(presetId)
                const preset = presets.find((item) => item.id === presetId)
                if (preset) {
                  setDraftPanels(preset.items)
                  setFocusedPanelId(toPreviewPanels(preset.items)[0]?.id ?? null)
                }
              }}
              variant="buttons"
            />
          </div>

          <div className="space-y-2">
            <h4 className="text-sm font-medium">Panel Arrangement</h4>
            <div className="rounded-lg border bg-muted/30 p-4">
              <InteractivePreview
                panels={previewPanels}
                onReorder={handleReorder}
                onRemove={handleRemove}
                panelLabels={REPO_PANEL_PREVIEW_LABELS}
              />
            </div>
            <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1">
                <ArrowUp className="size-3" />
                <ArrowDown className="size-3" />
                `Alt` + arrows move focused panel
              </span>
              <span className="inline-flex items-center gap-1">
                <ArrowLeft className="size-3" />
                <ArrowRight className="size-3" />
                `Alt` + left/right toggles primary and auxiliary
              </span>
              <span className="inline-flex items-center gap-1">
                <X className="size-3" />
                `Delete` removes focused panel
              </span>
              <span className="inline-flex items-center gap-1">
                <Plus className="size-3" />
                `Ctrl/Cmd` + `Shift` + `A` opens add panel
              </span>
              <span className="inline-flex items-center gap-1">
                <Plus className="size-3" />
                `Alt` + `A` inserts the selected add-panel option
              </span>
            </div>
          </div>

          {hasVisiblePanels ? (
            <div className="grid gap-2 md:grid-cols-2">
              {previewPanels.map((panel) => (
                <div
                  key={panel.id}
                  className="flex items-center justify-between rounded-lg border px-3 py-2 outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  tabIndex={0}
                  onFocus={() => setFocusedPanelId(panel.id)}
                >
                    <div>
                      <div className="text-sm font-medium">
                        {getRepoPanelDefinition(panel.kind as RepoPanelLayoutItem["kind"])?.label ??
                          panel.kind}
                      </div>
                    <div className="text-xs text-muted-foreground">{panel.id}</div>
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => handleToggleProminence(panel.id)}
                  >
                    Move to {panel.prominence === "primary" ? "Auxiliary" : "Primary"}
                    <span className="ml-2 text-[10px] text-muted-foreground">
                      Alt+{panel.prominence === "primary" ? "→" : "←"}
                    </span>
                  </Button>
                </div>
              ))}
            </div>
          ) : null}

          <Collapsible open={addPanelOpen} onOpenChange={setAddPanelOpen}>
            <CollapsibleTrigger asChild>
              <Button variant="outline" className="w-full gap-2">
                <Plus className="h-4 w-4" />
                Add Panel
                <span className="ml-auto text-xs text-muted-foreground">Ctrl+Shift+A</span>
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="pt-2">
              <div className="grid gap-2 md:grid-cols-2">
                {addablePanels.map((panel) => (
                  <Button
                    key={panel.kind}
                    variant="ghost"
                    className="justify-start"
                    onClick={() => handleAddPanel(panel.kind)}
                    onFocus={() => setFocusedAddPanelKind(panel.kind)}
                  >
                    {panel.label}
                    {focusedAddPanelKind === panel.kind ? (
                      <span className="ml-auto text-[10px] text-muted-foreground">
                        Alt+A
                      </span>
                    ) : null}
                  </Button>
                ))}
              </div>
            </CollapsibleContent>
          </Collapsible>
        </div>

        <DialogFooter className="justify-between gap-2 sm:justify-between">
          <div className="flex gap-2">
            {canReset ? (
              <Button type="button" variant="outline" onClick={onReset}>
                Reset to Preset
              </Button>
            ) : null}
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenAdvanced(draftPanels)}
            >
              Advanced Editor
              <span className="ml-2 text-xs text-muted-foreground">Ctrl+Alt+L</span>
            </Button>
          </div>
          <div className="flex gap-2">
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="button" onClick={handleApply}>
              Apply Layout
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
