import { ArrowDown, ArrowUp, CopyPlus, Plus, Trash2 } from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import {
  type ActiveRepoBuilderPanelKind,
  getRepoPanelCapabilityAvailability,
  REPO_BUILDER_PANEL_CAPABILITIES,
  REPO_BUILDER_PANEL_FIELD_SPECS,
  type RepoBuilderPanelConfig,
  type RepoCapabilityAvailabilityInput,
} from "@/components/Repo"
import {
  cloneRepoPanelConfigForPanelId,
  createDefaultRepoFileViewerPanelConfig,
  createDefaultRepoPanelConfig,
  normalizeRepoPanelConfig,
  parseRepoExplorerPanelConfig,
  parseRepoFileViewerPanelConfig,
} from "@/components/Repo/panels/config"
import type { RepoPanelLayoutItem } from "@/components/Repo/panels/repoPanelLayoutCustomization"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"

function toPrettyJson(value: unknown): string {
  return JSON.stringify(value ?? {}, null, 2)
}

function parseInteger(value: string): number | undefined {
  const trimmed = value.trim()
  if (!trimmed) return undefined
  const parsed = Number.parseInt(trimmed, 10)
  return Number.isFinite(parsed) ? parsed : undefined
}

function parseConfigJson(raw: string): Record<string, unknown> | null {
  const trimmed = raw.trim()
  if (!trimmed) return null
  const parsed = JSON.parse(trimmed) as unknown
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("Config JSON must be an object.")
  }
  return parsed as Record<string, unknown>
}

function createPanelId(
  kind: ActiveRepoBuilderPanelKind,
  existingIds: string[],
): string {
  const base = kind
  if (!existingIds.includes(base)) return base
  let index = 2
  while (existingIds.includes(`${base}-${index}`)) {
    index += 1
  }
  return `${base}-${index}`
}

function clonePanelWithFreshId(
  panel: RepoPanelLayoutItem,
  existingIds: string[],
): RepoPanelLayoutItem {
  return {
    ...panel,
    id: createPanelId(panel.kind as ActiveRepoBuilderPanelKind, existingIds),
    title: panel.title ? `${panel.title} Copy` : panel.title,
  }
}

function createPanelConfigTemplate(
  kind: ActiveRepoBuilderPanelKind,
  panelId: string,
): Record<string, unknown> | null {
  return createDefaultRepoPanelConfig(kind, panelId) as unknown as Record<
    string,
    unknown
  > | null
}

function getPanelConfigHelp(kind: RepoBuilderPanelConfig["kind"]) {
  if (kind === "repoExplorer") {
    return "Explorer config supports `initial_path`, optional `ref`, and `selection_key`."
  }
  if (kind === "fileViewer") {
    return "File viewer config supports `path_mode: selection | fixed | readme`, optional `fixed_path`, optional `ref`, and `selection_key`."
  }
  return "Panel-specific runtime config."
}

function reorderPanels(
  panels: RepoPanelLayoutItem[],
  fromIndex: number,
  toIndex: number,
): RepoPanelLayoutItem[] {
  if (toIndex < 0 || toIndex >= panels.length || fromIndex === toIndex)
    return panels
  const next = [...panels]
  const [item] = next.splice(fromIndex, 1)
  if (!item) return panels
  next.splice(toIndex, 0, item)
  return next
}

interface RepoLayoutEditorDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  repoName: string
  panels: RepoPanelLayoutItem[]
  capabilities: RepoCapabilityAvailabilityInput
  onApply: (panels: RepoPanelLayoutItem[]) => void
  onReset: () => void
  canReset: boolean
}

export function RepoLayoutEditorDialog({
  open,
  onOpenChange,
  repoName,
  panels,
  capabilities,
  onApply,
  onReset,
  canReset,
}: RepoLayoutEditorDialogProps) {
  const [draftPanels, setDraftPanels] = useState<RepoPanelLayoutItem[]>(panels)
  const [configDrafts, setConfigDrafts] = useState<Record<string, string>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [nextKind, setNextKind] =
    useState<ActiveRepoBuilderPanelKind>("repoOverview")

  useEffect(() => {
    if (!open) return
    setDraftPanels(panels)
    setConfigDrafts(
      Object.fromEntries(
        panels.map((panel) => [
          panel.id,
          toPrettyJson(panel.config_json ?? {}),
        ]),
      ),
    )
    setErrors({})
  }, [open, panels])

  const fieldLabels = useMemo(
    () =>
      Object.fromEntries(
        REPO_BUILDER_PANEL_FIELD_SPECS.map((field) => [field.key, field.label]),
      ),
    [],
  )

  const getRawConfigDraft = (panel: RepoPanelLayoutItem) =>
    configDrafts[panel.id] ?? toPrettyJson(panel.config_json ?? {})

  const getNormalizedConfig = (panel: RepoPanelLayoutItem) => {
    try {
      return normalizeRepoPanelConfig(
        panel.kind,
        panel.id,
        parseConfigJson(getRawConfigDraft(panel)),
      )
    } catch {
      return normalizeRepoPanelConfig(panel.kind, panel.id, panel.config_json)
    }
  }

  const updatePanelConfig = (
    panel: RepoPanelLayoutItem,
    patch: Record<string, unknown>,
  ) => {
    const baseConfig = getNormalizedConfig(panel) ?? {}
    const nextConfig = normalizeRepoPanelConfig(panel.kind, panel.id, {
      ...baseConfig,
      ...patch,
    })
    handleConfigChange(panel.id, toPrettyJson(nextConfig ?? {}))
  }

  const updatePanel = (index: number, patch: Partial<RepoPanelLayoutItem>) => {
    setDraftPanels((current) => {
      const currentPanel = current[index]
      if (!currentPanel) return current
      const nextPanel = { ...currentPanel, ...patch }

      if (typeof patch.kind === "string" && patch.kind !== currentPanel.kind) {
        const nextTitle =
          REPO_BUILDER_PANEL_CAPABILITIES.find(
            (panelCapability) => panelCapability.kind === patch.kind,
          )?.displayName ?? patch.kind
        nextPanel.title = patch.title ?? nextTitle
        nextPanel.config_json = createPanelConfigTemplate(
          patch.kind as ActiveRepoBuilderPanelKind,
          nextPanel.id,
        )
        setConfigDrafts((drafts) => ({
          ...drafts,
          [nextPanel.id]: toPrettyJson(nextPanel.config_json ?? {}),
        }))
      }

      if (
        typeof patch.id === "string" &&
        patch.id !== currentPanel.id &&
        patch.id.trim().length > 0
      ) {
        const nextId = patch.id
        setConfigDrafts((drafts) => {
          const currentDraft =
            drafts[currentPanel.id] ??
            toPrettyJson(currentPanel.config_json ?? {})
          const migratedConfig = normalizeRepoPanelConfig(
            nextPanel.kind,
            nextId,
            (() => {
              try {
                return parseConfigJson(currentDraft)
              } catch {
                return currentPanel.config_json
              }
            })(),
          )
          const { [currentPanel.id]: _removed, ...rest } = drafts
          return { ...rest, [nextId]: toPrettyJson(migratedConfig ?? {}) }
        })
        setErrors((currentErrors) => {
          const nextErrors = { ...currentErrors }
          if (nextErrors[currentPanel.id]) {
            nextErrors[nextId] = nextErrors[currentPanel.id]
            delete nextErrors[currentPanel.id]
          }
          return nextErrors
        })
      }

      return current.map((panel, panelIndex) =>
        panelIndex === index ? nextPanel : panel,
      )
    })
  }

  const handleConfigChange = (panelId: string, value: string) => {
    setConfigDrafts((current) => ({ ...current, [panelId]: value }))
    setErrors((current) => {
      if (!current[panelId]) return current
      const { [panelId]: _removed, ...rest } = current
      return rest
    })
  }

  const handleApply = () => {
    const nextErrors: Record<string, string> = {}
    const normalizedPanels = draftPanels.map((panel) => {
      const rawConfig =
        configDrafts[panel.id] ?? toPrettyJson(panel.config_json ?? {})
      try {
        return {
          ...panel,
          config_json: normalizeRepoPanelConfig(
            panel.kind,
            panel.id,
            parseConfigJson(rawConfig),
          ),
        }
      } catch (error) {
        nextErrors[panel.id] =
          error instanceof Error ? error.message : "Invalid config JSON."
        return panel
      }
    })

    const ids = normalizedPanels.map((panel) => panel.id.trim()).filter(Boolean)
    if (
      ids.length !== normalizedPanels.length ||
      new Set(ids).size !== ids.length
    ) {
      nextErrors.__ids = "Each panel instance needs a unique non-empty ID."
    }

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors)
      return
    }

    onApply(
      normalizedPanels.map((panel) => ({
        ...panel,
        id: panel.id.trim(),
        title: panel.title?.trim() || panel.kind,
      })),
    )
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl">
        <DialogHeader>
          <DialogTitle>Repo Layout Editor</DialogTitle>
          <DialogDescription>
            Configure duplicate panel instances, panel sizing, and per-instance
            `config_json` for {repoName}.
          </DialogDescription>
        </DialogHeader>

        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Select
              value={nextKind}
              onValueChange={(value) =>
                setNextKind(value as ActiveRepoBuilderPanelKind)
              }
            >
              <SelectTrigger className="w-[220px]">
                <SelectValue placeholder="Panel kind" />
              </SelectTrigger>
              <SelectContent>
                {REPO_BUILDER_PANEL_CAPABILITIES.map((panelCapability) => (
                  <SelectItem
                    key={panelCapability.kind}
                    value={panelCapability.kind}
                  >
                    {panelCapability.displayName}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                const nextId = createPanelId(
                  nextKind,
                  draftPanels.map((panel) => panel.id),
                )
                const nextPanel: RepoPanelLayoutItem = {
                  id: nextId,
                  kind: nextKind,
                  title:
                    REPO_BUILDER_PANEL_CAPABILITIES.find(
                      (panelCapability) => panelCapability.kind === nextKind,
                    )?.displayName ?? nextKind,
                  prominence: "primary",
                  hidden: false,
                  config_json: createPanelConfigTemplate(nextKind, nextId),
                }
                setDraftPanels((current) => [...current, nextPanel])
                setConfigDrafts((current) => ({
                  ...current,
                  [nextId]: toPrettyJson(
                    createPanelConfigTemplate(nextKind, nextId) ?? {},
                  ),
                }))
              }}
            >
              <Plus className="size-4" />
              Add Panel
            </Button>
          </div>
          {canReset ? (
            <Button type="button" variant="ghost" onClick={onReset}>
              Reset to Default
            </Button>
          ) : null}
        </div>

        {errors.__ids ? (
          <div className="rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
            {errors.__ids}
          </div>
        ) : null}

        <ScrollArea className="max-h-[70vh] pr-4">
          <div className="space-y-4 py-1">
            {draftPanels.map((panel, index) => {
              const availability = getRepoPanelCapabilityAvailability(
                panel.kind as ActiveRepoBuilderPanelKind,
                capabilities,
              )
              const definition = REPO_BUILDER_PANEL_CAPABILITIES.find(
                (panelCapability) => panelCapability.kind === panel.kind,
              )
              const fieldPath = `panel.${panel.id}`
              const normalizedConfig = getNormalizedConfig(panel)
              const explorerConfig =
                panel.kind === "repoExplorer"
                  ? parseRepoExplorerPanelConfig(normalizedConfig, panel.id)
                  : null
              const fileViewerConfig =
                panel.kind === "fileViewer"
                  ? parseRepoFileViewerPanelConfig(normalizedConfig, panel.id)
                  : null

              return (
                <div key={panel.id} className="rounded-2xl border p-4">
                  <div className="mb-4 flex items-start justify-between gap-3">
                    <div>
                      <div className="text-sm font-medium">
                        {panel.title || definition?.displayName || panel.kind}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {panel.id} · {definition?.displayName ?? panel.kind}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        disabled={index === 0}
                        onClick={() =>
                          setDraftPanels((current) =>
                            reorderPanels(current, index, index - 1),
                          )
                        }
                      >
                        <ArrowUp className="size-4" />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        disabled={index === draftPanels.length - 1}
                        onClick={() =>
                          setDraftPanels((current) =>
                            reorderPanels(current, index, index + 1),
                          )
                        }
                      >
                        <ArrowDown className="size-4" />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          const clone = clonePanelWithFreshId(
                            panel,
                            draftPanels.map((draftPanel) => draftPanel.id),
                          )
                          setDraftPanels((current) => [
                            ...current.slice(0, index + 1),
                            clone,
                            ...current.slice(index + 1),
                          ])
                          setConfigDrafts((current) => ({
                            ...current,
                            [clone.id]: toPrettyJson(
                              cloneRepoPanelConfigForPanelId(
                                panel.kind,
                                panel.id,
                                clone.id,
                                (() => {
                                  try {
                                    return parseConfigJson(
                                      getRawConfigDraft(panel),
                                    )
                                  } catch {
                                    return panel.config_json
                                  }
                                })(),
                              ) ?? {},
                            ),
                          }))
                        }}
                      >
                        <CopyPlus className="size-4" />
                        Clone
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setDraftPanels((current) =>
                            current.filter(
                              (draftPanel) => draftPanel.id !== panel.id,
                            ),
                          )
                          setConfigDrafts((current) => {
                            const { [panel.id]: _removed, ...rest } = current
                            return rest
                          })
                          setErrors((current) => {
                            const { [panel.id]: _removed, ...rest } = current
                            return rest
                          })
                        }}
                      >
                        <Trash2 className="size-4" />
                        Remove
                      </Button>
                    </div>
                  </div>

                  <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                    <div
                      className="space-y-2"
                      data-builder-path={`${fieldPath}.kind`}
                    >
                      <Label>{fieldLabels.kind}</Label>
                      <Select
                        value={panel.kind}
                        onValueChange={(value) =>
                          updatePanel(index, {
                            kind: value as RepoBuilderPanelConfig["kind"],
                          })
                        }
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Kind" />
                        </SelectTrigger>
                        <SelectContent>
                          {REPO_BUILDER_PANEL_CAPABILITIES.map(
                            (panelCapability) => (
                              <SelectItem
                                key={panelCapability.kind}
                                value={panelCapability.kind}
                              >
                                {panelCapability.displayName}
                              </SelectItem>
                            ),
                          )}
                        </SelectContent>
                      </Select>
                    </div>

                    <div
                      className="space-y-2"
                      data-builder-path={`${fieldPath}.id`}
                    >
                      <Label>{fieldLabels.id}</Label>
                      <Input
                        value={panel.id}
                        onChange={(event) =>
                          updatePanel(index, { id: event.target.value })
                        }
                      />
                    </div>

                    <div
                      className="space-y-2"
                      data-builder-path={`${fieldPath}.title`}
                    >
                      <Label>{fieldLabels.title}</Label>
                      <Input
                        value={panel.title ?? ""}
                        onChange={(event) =>
                          updatePanel(index, { title: event.target.value })
                        }
                      />
                    </div>

                    <div
                      className="space-y-2"
                      data-builder-path={`${fieldPath}.prominence`}
                    >
                      <Label>{fieldLabels.prominence}</Label>
                      <Select
                        value={panel.prominence}
                        onValueChange={(value) =>
                          updatePanel(index, {
                            prominence:
                              value as RepoBuilderPanelConfig["prominence"],
                          })
                        }
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Prominence" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="primary">primary</SelectItem>
                          <SelectItem value="auxiliary">auxiliary</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div
                      className="space-y-2"
                      data-builder-path={`${fieldPath}.default_size`}
                    >
                      <Label>{fieldLabels.default_size}</Label>
                      <Input
                        value={String(panel.default_size ?? "")}
                        onChange={(event) =>
                          updatePanel(index, {
                            default_size: parseInteger(event.target.value),
                          })
                        }
                      />
                    </div>

                    <div
                      className="space-y-2"
                      data-builder-path={`${fieldPath}.min_size`}
                    >
                      <Label>{fieldLabels.min_size}</Label>
                      <Input
                        value={String(panel.min_size ?? "")}
                        onChange={(event) =>
                          updatePanel(index, {
                            min_size: parseInteger(event.target.value),
                          })
                        }
                      />
                    </div>

                    <div
                      className="space-y-2"
                      data-builder-path={`${fieldPath}.max_size`}
                    >
                      <Label>{fieldLabels.max_size}</Label>
                      <Input
                        value={String(panel.max_size ?? "")}
                        onChange={(event) =>
                          updatePanel(index, {
                            max_size: parseInteger(event.target.value),
                          })
                        }
                      />
                    </div>

                    <div className="flex items-center justify-between rounded-xl border px-3 py-2">
                      <div>
                        <div className="text-sm font-medium">Hidden</div>
                        <div className="text-xs text-muted-foreground">
                          Keep instance in draft but do not render it.
                        </div>
                      </div>
                      <Switch
                        checked={panel.hidden}
                        onCheckedChange={(checked) =>
                          updatePanel(index, { hidden: checked })
                        }
                      />
                    </div>
                  </div>

                  {explorerConfig ? (
                    <div className="mt-4 grid gap-3 rounded-xl border border-dashed p-3 md:grid-cols-2 xl:grid-cols-4">
                      <div className="space-y-2">
                        <Label>Initial Path</Label>
                        <Input
                          value={explorerConfig.initial_path}
                          onChange={(event) =>
                            updatePanelConfig(panel, {
                              initial_path: event.target.value,
                            })
                          }
                          placeholder="src/"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Selection Key</Label>
                        <Input
                          value={explorerConfig.selection_key ?? ""}
                          onChange={(event) =>
                            updatePanelConfig(panel, {
                              selection_key: event.target.value || null,
                            })
                          }
                          placeholder="workspace.primary-file"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Ref</Label>
                        <Input
                          value={explorerConfig.ref ?? ""}
                          onChange={(event) =>
                            updatePanelConfig(panel, {
                              ref: event.target.value || null,
                            })
                          }
                          placeholder="default branch"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Empty Label</Label>
                        <Input
                          value={explorerConfig.empty_label ?? ""}
                          onChange={(event) =>
                            updatePanelConfig(panel, {
                              empty_label: event.target.value || null,
                            })
                          }
                          placeholder="No files available."
                        />
                      </div>
                      <div className="flex items-center justify-between rounded-xl border px-3 py-2">
                        <div>
                          <div className="text-sm font-medium">Show Sizes</div>
                          <div className="text-xs text-muted-foreground">
                            Display file sizes in the tree.
                          </div>
                        </div>
                        <Switch
                          checked={explorerConfig.show_sizes}
                          onCheckedChange={(checked) =>
                            updatePanelConfig(panel, { show_sizes: checked })
                          }
                        />
                      </div>
                      <div className="flex items-center justify-between rounded-xl border px-3 py-2">
                        <div>
                          <div className="text-sm font-medium">
                            Commit Badge
                          </div>
                          <div className="text-xs text-muted-foreground">
                            Show the active ref badge in panel chrome.
                          </div>
                        </div>
                        <Switch
                          checked={explorerConfig.show_commit_badge}
                          onCheckedChange={(checked) =>
                            updatePanelConfig(panel, {
                              show_commit_badge: checked,
                            })
                          }
                        />
                      </div>
                    </div>
                  ) : null}

                  {fileViewerConfig ? (
                    <div className="mt-4 grid gap-3 rounded-xl border border-dashed p-3 md:grid-cols-2 xl:grid-cols-4">
                      <div className="space-y-2">
                        <Label>Path Mode</Label>
                        <Select
                          value={fileViewerConfig.path_mode}
                          onValueChange={(value) =>
                            updatePanelConfig(panel, {
                              path_mode: value,
                              ...(value === "readme"
                                ? { selection_key: null, fixed_path: "" }
                                : {}),
                            })
                          }
                        >
                          <SelectTrigger className="w-full">
                            <SelectValue placeholder="Path mode" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="selection">selection</SelectItem>
                            <SelectItem value="fixed">fixed</SelectItem>
                            <SelectItem value="readme">readme</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      {fileViewerConfig.path_mode === "fixed" ? (
                        <div className="space-y-2">
                          <Label>Fixed Path</Label>
                          <Input
                            value={fileViewerConfig.fixed_path ?? ""}
                            onChange={(event) =>
                              updatePanelConfig(panel, {
                                fixed_path: event.target.value,
                              })
                            }
                            placeholder="README.md"
                          />
                        </div>
                      ) : null}
                      {fileViewerConfig.path_mode !== "readme" ? (
                        <div className="space-y-2">
                          <Label>Selection Key</Label>
                          <Input
                            value={fileViewerConfig.selection_key ?? ""}
                            onChange={(event) =>
                              updatePanelConfig(panel, {
                                selection_key: event.target.value || null,
                              })
                            }
                            placeholder="workspace.primary-file"
                          />
                        </div>
                      ) : null}
                      <div className="space-y-2">
                        <Label>Ref</Label>
                        <Input
                          value={fileViewerConfig.ref ?? ""}
                          onChange={(event) =>
                            updatePanelConfig(panel, {
                              ref: event.target.value || null,
                            })
                          }
                          placeholder="default branch"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Empty Label</Label>
                        <Input
                          value={fileViewerConfig.empty_label ?? ""}
                          onChange={(event) =>
                            updatePanelConfig(panel, {
                              empty_label: event.target.value || null,
                            })
                          }
                          placeholder="Select a file to preview."
                        />
                      </div>
                      <div className="flex items-center justify-between rounded-xl border px-3 py-2">
                        <div>
                          <div className="text-sm font-medium">
                            Show Path Badge
                          </div>
                          <div className="text-xs text-muted-foreground">
                            Show path metadata in the viewer header.
                          </div>
                        </div>
                        <Switch
                          checked={fileViewerConfig.show_path_badge}
                          onCheckedChange={(checked) =>
                            updatePanelConfig(panel, {
                              show_path_badge: checked,
                            })
                          }
                        />
                      </div>
                      <div className="flex items-center justify-between rounded-xl border px-3 py-2">
                        <div>
                          <div className="text-sm font-medium">
                            Copy Control
                          </div>
                          <div className="text-xs text-muted-foreground">
                            Allow copying viewer content when supported.
                          </div>
                        </div>
                        <Switch
                          checked={fileViewerConfig.show_copy_control}
                          onCheckedChange={(checked) =>
                            updatePanelConfig(panel, {
                              show_copy_control: checked,
                            })
                          }
                        />
                      </div>
                    </div>
                  ) : null}

                  <div
                    className="mt-4 space-y-2"
                    data-builder-path={`${fieldPath}.config_json`}
                  >
                    <Label>{fieldLabels.config_json}</Label>
                    <div className="flex flex-wrap gap-2">
                      {(panel.kind === "repoExplorer" ||
                        panel.kind === "fileViewer") && (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            handleConfigChange(
                              panel.id,
                              toPrettyJson(
                                createPanelConfigTemplate(
                                  panel.kind as ActiveRepoBuilderPanelKind,
                                  panel.id,
                                ) ?? {},
                              ),
                            )
                          }
                        >
                          Reset Config
                        </Button>
                      )}
                      {panel.kind === "fileViewer" && (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            handleConfigChange(
                              panel.id,
                              toPrettyJson({
                                ...createDefaultRepoFileViewerPanelConfig(
                                  panel.id,
                                ),
                                path_mode: "readme",
                                title: "README",
                                empty_label:
                                  "No README is available for this repository.",
                              }),
                            )
                          }
                        >
                          README Mode
                        </Button>
                      )}
                    </div>
                    <Textarea
                      className="min-h-[180px] font-mono text-xs"
                      value={
                        configDrafts[panel.id] ??
                        toPrettyJson(panel.config_json ?? {})
                      }
                      onChange={(event) =>
                        handleConfigChange(panel.id, event.target.value)
                      }
                    />
                    <div className="text-xs text-muted-foreground">
                      {getPanelConfigHelp(panel.kind)}
                    </div>
                    {errors[panel.id] ? (
                      <div className="text-xs text-destructive">
                        {errors[panel.id]}
                      </div>
                    ) : null}
                  </div>

                  <div className="mt-3 text-xs text-muted-foreground">
                    {availability.available
                      ? "Available with current repo route capabilities."
                      : `Requires ${availability.unmetRequirements.join(", ")}.`}
                  </div>
                </div>
              )
            })}
          </div>
        </ScrollArea>

        <DialogFooter>
          <Button
            type="button"
            variant="ghost"
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
          <Button type="button" onClick={handleApply}>
            Apply Layout
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
