import {
  GIT_VIEW_METADATA_KEY_PRESETS,
  createDefaultGitViewConfig,
  type GitViewDisplayMode,
  parseGitViewConfig,
  type GitViewPathMode,
  type GitViewEntityIdMode,
  type GitViewSource,
} from "@/components/Demo/gitViewConfig"
import {
  LIVE_REPO_EXPLORER_METADATA_KEY_PRESETS,
  createDefaultLiveRepoExplorerConfig,
  parseLiveRepoExplorerConfig,
  type LiveRepoExplorerSource,
} from "@/components/Demo/liveRepoExplorerConfig"
import {
  LIVE_REPO_FILE_VIEWER_METADATA_KEY_PRESETS,
  createDefaultLiveRepoFileViewerConfig,
  parseLiveRepoFileViewerConfig,
  type LiveRepoFileViewerPathMode,
  type LiveRepoFileViewerSource,
} from "@/components/Demo/liveRepoFileViewerConfig"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"

function normalizeOptionalInput(value: string): string | undefined {
  const trimmed = value.trim()
  return trimmed.length > 0 ? trimmed : undefined
}

function normalizeOptionalDisplayValue(value: string | null | undefined): string {
  return value ?? ""
}

function parseInteger(value: string): number | undefined {
  const trimmed = value.trim()
  if (!trimmed) return undefined
  const parsed = Number.parseInt(trimmed, 10)
  return Number.isFinite(parsed) ? parsed : undefined
}

export function DemoGitViewConfigFields({
  value,
  fallbackSelectionKey,
  onChange,
}: {
  value: unknown
  fallbackSelectionKey: string
  onChange: (nextValue: Record<string, unknown>) => void
}) {
  const config = parseGitViewConfig(value) ?? createDefaultGitViewConfig()

  const updateConfig = (patch: Record<string, unknown>) => {
    onChange({
      ...config,
      ...patch,
    })
  }

  return (
    <div className="rounded border p-3 space-y-3">
      <div className="rounded border border-dashed bg-muted/20 p-2 text-[11px] text-muted-foreground">
        Use a shared <code>selection_key</code> when one explorer should drive
        multiple file viewers or git views in the same room. New demos should
        target <code>user_repo</code>; legacy story/shadow configs still resolve.
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Source</label>
          <Select
            value={config.source}
            onValueChange={(nextValue) =>
              updateConfig({
                source: nextValue as GitViewSource,
              })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Select source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="user_repo">user_repo (recommended)</SelectItem>
              <SelectItem value="shadow_repo">shadow_repo (legacy)</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Entity Type</label>
          <Input
            value={config.entity_type}
            placeholder="user_repo"
            onChange={(event) =>
              updateConfig({
                entity_type: event.target.value,
              })
            }
          />
          <p className="text-[11px] text-muted-foreground">
            Common values: <code>user_repo</code> for managed repos,{" "}
            <code>story</code> for legacy shadow demos.
          </p>
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Entity ID Source</label>
          <Select
            value={config.entity_id_mode}
            onValueChange={(nextValue) => {
              const entityIdMode = nextValue as GitViewEntityIdMode
              updateConfig({
                entity_id_mode: entityIdMode,
                entity_id:
                  entityIdMode === "explicit" ? config.entity_id ?? "" : undefined,
                entity_id_metadata_key:
                  entityIdMode === "metadata"
                    ? config.entity_id_metadata_key ?? "repo_id"
                    : undefined,
              })
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select ID source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="metadata">metadata_json</SelectItem>
              <SelectItem value="explicit">explicit entity ID</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {config.entity_id_mode === "explicit" ? (
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Entity ID</label>
            <Input
              value={normalizeOptionalDisplayValue(config.entity_id)}
              placeholder="uuid"
              onChange={(event) =>
                updateConfig({
                  entity_id: event.target.value,
                })
              }
            />
          </div>
        ) : (
          <div className="space-y-2">
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">
                metadata_json key
              </label>
              <Select
                value={config.entity_id_metadata_key ?? "__custom"}
                onValueChange={(nextValue) =>
                  updateConfig({
                    entity_id_metadata_key:
                      nextValue === "__custom" ? "" : nextValue,
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select metadata key" />
                </SelectTrigger>
                <SelectContent>
                  {GIT_VIEW_METADATA_KEY_PRESETS.map((preset) => (
                    <SelectItem key={preset} value={preset}>
                      {preset}
                    </SelectItem>
                  ))}
                  <SelectItem value="__custom">Custom key</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Input
              value={normalizeOptionalDisplayValue(config.entity_id_metadata_key)}
              placeholder="repo_id"
              onChange={(event) =>
                updateConfig({
                  entity_id_metadata_key: event.target.value,
                })
              }
            />
            <p className="text-[11px] text-muted-foreground">
              Use <code>repo_id</code> for room/project repo surfaces. Legacy
              story-backed demos typically use <code>story_id</code>.
            </p>
          </div>
        )}
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Selection Key</label>
          <Input
            value={normalizeOptionalDisplayValue(config.selection_key)}
            placeholder={fallbackSelectionKey}
            onChange={(event) =>
              updateConfig({
                selection_key: normalizeOptionalInput(event.target.value),
              })
            }
          />
          <p className="text-[11px] text-muted-foreground">
            Match this key across related repo surfaces when one selection should
            drive several panels.
          </p>
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Initial Path</label>
          <Input
            value={config.initial_path}
            placeholder="src"
            onChange={(event) =>
              updateConfig({
                initial_path: event.target.value,
              })
            }
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Display Mode</label>
          <Select
            value={config.display_mode ?? "split"}
            onValueChange={(nextValue) =>
              updateConfig({
                display_mode: nextValue as GitViewDisplayMode,
                path_mode:
                  nextValue === "viewer"
                    ? config.path_mode ?? "selection"
                    : "selection",
              })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Select display mode" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="split">Explorer + Viewer</SelectItem>
              <SelectItem value="explorer">Explorer Only</SelectItem>
              <SelectItem value="viewer">Viewer Only</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Commit Limit</label>
          <Input
            value={String(config.commit_limit)}
            placeholder="10"
            onChange={(event) =>
              updateConfig({
                commit_limit: parseInteger(event.target.value) ?? 10,
              })
            }
          />
        </div>
        {config.display_mode === "viewer" ? (
          <>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">Path Mode</label>
              <Select
                value={config.path_mode ?? "selection"}
                onValueChange={(nextValue) => {
                  const pathMode = nextValue as GitViewPathMode
                  updateConfig({
                    path_mode: pathMode,
                    fixed_path: pathMode === "fixed" ? config.fixed_path ?? "" : "",
                    selection_key:
                      pathMode === "readme"
                        ? undefined
                        : config.selection_key ?? fallbackSelectionKey,
                  })
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select path mode" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="selection">Selection-driven</SelectItem>
                  <SelectItem value="fixed">Fixed path</SelectItem>
                  <SelectItem value="readme">README</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {config.path_mode === "fixed" ? (
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground">Fixed Path</label>
                <Input
                  value={config.fixed_path ?? ""}
                  placeholder="src/main.tsx"
                  onChange={(event) =>
                    updateConfig({
                      fixed_path: event.target.value,
                    })
                  }
                />
              </div>
            ) : null}
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">Ref</label>
              <Input
                value={normalizeOptionalDisplayValue(config.ref)}
                placeholder="main"
                onChange={(event) =>
                  updateConfig({
                    ref: normalizeOptionalInput(event.target.value) ?? null,
                  })
                }
              />
            </div>
            <div className="space-y-1 md:col-span-2">
              <label className="text-xs text-muted-foreground">Empty Label</label>
              <Input
                value={normalizeOptionalDisplayValue(config.empty_label)}
                placeholder="Select a file from the repo explorer"
                onChange={(event) =>
                  updateConfig({
                    empty_label: normalizeOptionalInput(event.target.value) ?? null,
                  })
                }
              />
            </div>
          </>
        ) : null}
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="flex items-center justify-between gap-2 rounded border p-2">
          <label className="text-xs text-muted-foreground">
            Show File Content
          </label>
          <Switch
            checked={config.show_file_content}
            onCheckedChange={(checked) =>
              updateConfig({
                show_file_content: checked,
              })
            }
          />
        </div>
        <div className="flex items-center justify-between gap-2 rounded border p-2">
          <label className="text-xs text-muted-foreground">
            Show Config JSON
          </label>
          <Switch
            checked={config.show_config_json}
            onCheckedChange={(checked) =>
              updateConfig({
                show_config_json: checked,
              })
            }
          />
        </div>
        <div className="flex items-center justify-between gap-2 rounded border p-2">
          <label className="text-xs text-muted-foreground">Show Sizes</label>
          <Switch
            checked={config.show_sizes !== false}
            onCheckedChange={(checked) =>
              updateConfig({
                show_sizes: checked,
              })
            }
          />
        </div>
        <div className="flex items-center justify-between gap-2 rounded border p-2">
          <label className="text-xs text-muted-foreground">
            Show Commit Badge
          </label>
          <Switch
            checked={config.show_commit_badge !== false}
            onCheckedChange={(checked) =>
              updateConfig({
                show_commit_badge: checked,
              })
            }
          />
        </div>
        {config.display_mode === "viewer" ? (
          <>
            <div className="flex items-center justify-between gap-2 rounded border p-2">
              <label className="text-xs text-muted-foreground">
                Show Path Badge
              </label>
              <Switch
                checked={config.show_path_badge !== false}
                onCheckedChange={(checked) =>
                  updateConfig({
                    show_path_badge: checked,
                  })
                }
              />
            </div>
            <div className="flex items-center justify-between gap-2 rounded border p-2">
              <label className="text-xs text-muted-foreground">
                Show Copy Control
              </label>
              <Switch
                checked={config.show_copy_control !== false}
                onCheckedChange={(checked) =>
                  updateConfig({
                    show_copy_control: checked,
                  })
                }
              />
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}

export function DemoLiveRepoExplorerConfigFields({
  value,
  fallbackSelectionKey,
  onChange,
}: {
  value: unknown
  fallbackSelectionKey: string
  onChange: (nextValue: Record<string, unknown>) => void
}) {
  const config =
    parseLiveRepoExplorerConfig(value, fallbackSelectionKey) ??
    createDefaultLiveRepoExplorerConfig(fallbackSelectionKey)

  const updateConfig = (patch: Record<string, unknown>) => {
    onChange({
      ...config,
      ...patch,
    })
  }

  return (
    <div className="rounded border p-3 space-y-3">
      <div className="rounded border border-dashed bg-muted/20 p-2 text-[11px] text-muted-foreground">
        This explorer targets a live repo surface. Reuse the same{" "}
        <code>selection_key</code> across explorers and viewers when users need
        to add, remove, or switch repo files in room context without changing
        the layout.
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Source</label>
          <Select
            value={config.source}
            onValueChange={(nextValue) =>
              updateConfig({
                source: nextValue as LiveRepoExplorerSource,
              })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Select source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="user_repo">user_repo (recommended)</SelectItem>
              <SelectItem value="shadow_repo">shadow_repo (legacy)</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Entity Type</label>
          <Input
            value={config.entity_type}
            placeholder="user_repo"
            onChange={(event) =>
              updateConfig({
                entity_type: event.target.value,
              })
            }
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Entity ID Source</label>
          <Select
            value={config.entity_id_mode}
            onValueChange={(nextValue) => {
              const entityIdMode = nextValue as GitViewEntityIdMode
              updateConfig({
                entity_id_mode: entityIdMode,
                entity_id:
                  entityIdMode === "explicit" ? config.entity_id ?? "" : undefined,
                entity_id_metadata_key:
                  entityIdMode === "metadata"
                    ? config.entity_id_metadata_key ?? "repo_id"
                    : undefined,
              })
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select ID source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="metadata">metadata_json</SelectItem>
              <SelectItem value="explicit">explicit entity ID</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {config.entity_id_mode === "explicit" ? (
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Entity ID</label>
            <Input
              value={normalizeOptionalDisplayValue(config.entity_id)}
              placeholder="uuid"
              onChange={(event) =>
                updateConfig({
                  entity_id: event.target.value,
                })
              }
            />
          </div>
        ) : (
          <div className="space-y-2">
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">
                metadata_json key
              </label>
              <Select
                value={config.entity_id_metadata_key ?? "__custom"}
                onValueChange={(nextValue) =>
                  updateConfig({
                    entity_id_metadata_key:
                      nextValue === "__custom" ? "" : nextValue,
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select metadata key" />
                </SelectTrigger>
                <SelectContent>
                  {LIVE_REPO_EXPLORER_METADATA_KEY_PRESETS.map((preset) => (
                    <SelectItem key={preset} value={preset}>
                      {preset}
                    </SelectItem>
                  ))}
                  <SelectItem value="__custom">Custom key</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Input
              value={normalizeOptionalDisplayValue(config.entity_id_metadata_key)}
              placeholder="repo_id"
              onChange={(event) =>
                updateConfig({
                  entity_id_metadata_key: event.target.value,
                })
              }
            />
          </div>
        )}
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Selection Key</label>
          <Input
            value={normalizeOptionalDisplayValue(config.selection_key)}
            placeholder={fallbackSelectionKey}
            onChange={(event) =>
              updateConfig({
                selection_key: normalizeOptionalInput(event.target.value) ?? null,
              })
            }
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Initial Path</label>
          <Input
            value={config.initial_path}
            placeholder="src"
            onChange={(event) =>
              updateConfig({
                initial_path: event.target.value,
              })
            }
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Ref</label>
          <Input
            value={normalizeOptionalDisplayValue(config.ref)}
            placeholder="main"
            onChange={(event) =>
              updateConfig({
                ref: normalizeOptionalInput(event.target.value) ?? null,
              })
            }
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Title Override</label>
          <Input
            value={normalizeOptionalDisplayValue(config.title)}
            placeholder="Frontend Repo"
            onChange={(event) =>
              updateConfig({
                title: normalizeOptionalInput(event.target.value) ?? null,
              })
            }
          />
        </div>
        <div className="space-y-1 md:col-span-2">
          <label className="text-xs text-muted-foreground">Empty Label</label>
          <Input
            value={normalizeOptionalDisplayValue(config.empty_label)}
            placeholder="Pick a file to inspect"
            onChange={(event) =>
              updateConfig({
                empty_label: normalizeOptionalInput(event.target.value) ?? null,
              })
            }
          />
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="flex items-center justify-between gap-2 rounded border p-2">
          <label className="text-xs text-muted-foreground">Show Sizes</label>
          <Switch
            checked={config.show_sizes}
            onCheckedChange={(checked) =>
              updateConfig({
                show_sizes: checked,
              })
            }
          />
        </div>
        <div className="flex items-center justify-between gap-2 rounded border p-2">
          <label className="text-xs text-muted-foreground">
            Show Commit Badge
          </label>
          <Switch
            checked={config.show_commit_badge}
            onCheckedChange={(checked) =>
              updateConfig({
                show_commit_badge: checked,
              })
            }
          />
        </div>
      </div>
    </div>
  )
}

export function DemoLiveRepoFileViewerConfigFields({
  value,
  fallbackSelectionKey,
  onChange,
}: {
  value: unknown
  fallbackSelectionKey: string
  onChange: (nextValue: Record<string, unknown>) => void
}) {
  const config =
    parseLiveRepoFileViewerConfig(value, fallbackSelectionKey) ??
    createDefaultLiveRepoFileViewerConfig(fallbackSelectionKey)

  const updateConfig = (patch: Record<string, unknown>) => {
    onChange({
      ...config,
      ...patch,
    })
  }

  return (
    <div className="rounded border p-3 space-y-3">
      <div className="rounded border border-dashed bg-muted/20 p-2 text-[11px] text-muted-foreground">
        Use standalone file viewers when one repo explorer should feed multiple
        focused viewers. Shared <code>selection_key</code> values let authors
        route one selection into several panels, while fixed-path viewers stay
        pinned to a specific file.
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Source</label>
          <Select
            value={config.source}
            onValueChange={(nextValue) =>
              updateConfig({
                source: nextValue as LiveRepoFileViewerSource,
              })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Select source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="user_repo">user_repo (recommended)</SelectItem>
              <SelectItem value="shadow_repo">shadow_repo (legacy)</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Entity Type</label>
          <Input
            value={config.entity_type}
            placeholder="user_repo"
            onChange={(event) =>
              updateConfig({
                entity_type: event.target.value,
              })
            }
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Entity ID Source</label>
          <Select
            value={config.entity_id_mode}
            onValueChange={(nextValue) => {
              const entityIdMode = nextValue as GitViewEntityIdMode
              updateConfig({
                entity_id_mode: entityIdMode,
                entity_id:
                  entityIdMode === "explicit" ? config.entity_id ?? "" : undefined,
                entity_id_metadata_key:
                  entityIdMode === "metadata"
                    ? config.entity_id_metadata_key ?? "repo_id"
                    : undefined,
              })
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select ID source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="metadata">metadata_json</SelectItem>
              <SelectItem value="explicit">explicit entity ID</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {config.entity_id_mode === "explicit" ? (
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Entity ID</label>
            <Input
              value={normalizeOptionalDisplayValue(config.entity_id)}
              placeholder="uuid"
              onChange={(event) =>
                updateConfig({
                  entity_id: event.target.value,
                })
              }
            />
          </div>
        ) : (
          <div className="space-y-2">
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">
                metadata_json key
              </label>
              <Select
                value={config.entity_id_metadata_key ?? "__custom"}
                onValueChange={(nextValue) =>
                  updateConfig({
                    entity_id_metadata_key:
                      nextValue === "__custom" ? "" : nextValue,
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select metadata key" />
                </SelectTrigger>
                <SelectContent>
                  {LIVE_REPO_FILE_VIEWER_METADATA_KEY_PRESETS.map((preset) => (
                    <SelectItem key={preset} value={preset}>
                      {preset}
                    </SelectItem>
                  ))}
                  <SelectItem value="__custom">Custom key</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Input
              value={normalizeOptionalDisplayValue(config.entity_id_metadata_key)}
              placeholder="repo_id"
              onChange={(event) =>
                updateConfig({
                  entity_id_metadata_key: event.target.value,
                })
              }
            />
          </div>
        )}
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Path Mode</label>
          <Select
            value={config.path_mode}
            onValueChange={(nextValue) => {
              const pathMode = nextValue as LiveRepoFileViewerPathMode
              updateConfig({
                path_mode: pathMode,
                fixed_path:
                  pathMode === "fixed" ? config.fixed_path ?? "" : "",
                selection_key:
                  pathMode === "readme"
                    ? null
                    : config.selection_key ?? fallbackSelectionKey,
              })
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select path mode" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="selection">Selection-driven</SelectItem>
              <SelectItem value="fixed">Fixed path</SelectItem>
              <SelectItem value="readme">README</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {config.path_mode === "fixed" ? (
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Fixed Path</label>
            <Input
              value={config.fixed_path ?? ""}
              placeholder="src/main.tsx"
              onChange={(event) =>
                updateConfig({
                  fixed_path: event.target.value,
                })
              }
            />
          </div>
        ) : config.path_mode === "selection" ? (
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Selection Key</label>
            <Input
              value={normalizeOptionalDisplayValue(config.selection_key)}
              placeholder={fallbackSelectionKey}
              onChange={(event) =>
                updateConfig({
                  selection_key: normalizeOptionalInput(event.target.value) ?? null,
                })
              }
            />
            <p className="text-[11px] text-muted-foreground">
              Match the explorer key when this viewer should follow that repo
              selection. Use different keys for separate repo clusters.
            </p>
          </div>
        ) : (
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">README Mode</label>
            <p className="rounded border border-dashed bg-muted/20 p-2 text-[11px] text-muted-foreground">
              README mode ignores selection state and always shows the repo’s
              default readme for the chosen ref.
            </p>
          </div>
        )}
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Ref</label>
          <Input
            value={normalizeOptionalDisplayValue(config.ref)}
            placeholder="main"
            onChange={(event) =>
              updateConfig({
                ref: normalizeOptionalInput(event.target.value) ?? null,
              })
            }
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Title Override</label>
          <Input
            value={normalizeOptionalDisplayValue(config.title)}
            placeholder="Primary Viewer"
            onChange={(event) =>
              updateConfig({
                title: normalizeOptionalInput(event.target.value) ?? null,
              })
            }
          />
        </div>
        <div className="space-y-1 md:col-span-2">
          <label className="text-xs text-muted-foreground">Empty Label</label>
          <Input
            value={normalizeOptionalDisplayValue(config.empty_label)}
            placeholder="Select a file from the repo explorer"
            onChange={(event) =>
              updateConfig({
                empty_label: normalizeOptionalInput(event.target.value) ?? null,
              })
            }
          />
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="flex items-center justify-between gap-2 rounded border p-2">
          <label className="text-xs text-muted-foreground">Show Path Badge</label>
          <Switch
            checked={config.show_path_badge}
            onCheckedChange={(checked) =>
              updateConfig({
                show_path_badge: checked,
              })
            }
          />
        </div>
        <div className="flex items-center justify-between gap-2 rounded border p-2">
          <label className="text-xs text-muted-foreground">
            Show Copy Control
          </label>
          <Switch
            checked={config.show_copy_control}
            onCheckedChange={(checked) =>
              updateConfig({
                show_copy_control: checked,
              })
            }
          />
        </div>
      </div>
    </div>
  )
}
