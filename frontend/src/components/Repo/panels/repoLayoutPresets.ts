import { getDefaultRepoPanelConfigs } from "@/components/Repo/registry"
import {
  createRepoPanelLayoutItems,
  type RepoPanelLayoutItem,
  reconcileRepoPanelLayoutItems,
  repoPanelLayoutItemsEqual,
} from "./repoPanelLayoutCustomization"

export type RepoLayoutPresetSource = "system" | "user"

export interface RepoLayoutPreset {
  id: string
  label: string
  description: string
  source: RepoLayoutPresetSource
  immutable: boolean
  items: RepoPanelLayoutItem[]
}

export interface RepoLayoutWorkspaceState {
  activePresetId: string
  items: RepoPanelLayoutItem[]
}

interface RepoLayoutPresetStoragePayload {
  version: 1
  presets: Array<{
    id: string
    label: string
    description: string
    items: RepoPanelLayoutItem[]
  }>
}

interface RepoLayoutWorkspaceStoragePayload {
  version: 1
  activePresetId: string
  items: RepoPanelLayoutItem[]
}

const STORAGE_VERSION = 1
const USER_PRESETS_STORAGE_KEY = "repo-layout-presets:user"
const WORKSPACE_STORAGE_KEY_PREFIX = "repo-layout-workspace"

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function isRepoLayoutPresetRecord(
  value: unknown,
): value is RepoLayoutPresetStoragePayload["presets"][number] {
  return (
    isObjectRecord(value) &&
    typeof value.id === "string" &&
    value.id.trim().length > 0 &&
    typeof value.label === "string" &&
    value.label.trim().length > 0 &&
    typeof value.description === "string" &&
    Array.isArray(value.items)
  )
}

function buildDefaultPresetItems() {
  return createRepoPanelLayoutItems(getDefaultRepoPanelConfigs())
}

function cloneItems(items: RepoPanelLayoutItem[]) {
  return items.map((item) => ({
    ...item,
    config_json: item.config_json ? { ...item.config_json } : null,
  }))
}

function withPanelPatch(
  items: RepoPanelLayoutItem[],
  panelId: string,
  patch: Partial<RepoPanelLayoutItem>,
) {
  return items.map((item) =>
    item.id === panelId ? { ...item, ...patch } : item,
  )
}

function createSystemRepoLayoutPresets(): RepoLayoutPreset[] {
  const defaultItems = buildDefaultPresetItems()

  const browserItems = withPanelPatch(
    withPanelPatch(
      withPanelPatch(
        withPanelPatch(
          withPanelPatch(cloneItems(defaultItems), "repoOverview", {
            hidden: true,
          }),
          "repoImportStatus",
          { hidden: true },
        ),
        "repoReadmeViewer",
        { hidden: true },
      ),
      "repoExplorer",
      { prominence: "primary", default_size: 34, title: "Browser" },
    ),
    "fileViewer",
    { prominence: "primary", default_size: 66, title: "Preview" },
  )

  const overviewItems = withPanelPatch(
    withPanelPatch(
      withPanelPatch(
        withPanelPatch(cloneItems(defaultItems), "repoOverview", {
          hidden: false,
          prominence: "primary",
          default_size: 60,
        }),
        "repoReadmeViewer",
        {
          hidden: false,
          prominence: "auxiliary",
          default_size: 40,
          title: "README",
        },
      ),
      "repoExplorer",
      { hidden: true },
    ),
    "fileViewer",
    { hidden: true },
  )

  return [
    {
      id: "system-default",
      label: "Default",
      description:
        "Overview, README, browser, and viewer in the standard workspace.",
      source: "system",
      immutable: true,
      items: defaultItems,
    },
    {
      id: "system-browser",
      label: "Browser + Viewer",
      description:
        "Focused file browsing with side-by-side browser and preview panes.",
      source: "system",
      immutable: true,
      items: browserItems,
    },
    {
      id: "system-overview",
      label: "Overview + README",
      description:
        "Less operational chrome with repository summary and README first.",
      source: "system",
      immutable: true,
      items: overviewItems,
    },
  ]
}

export function getSystemRepoLayoutPresets(): RepoLayoutPreset[] {
  return createSystemRepoLayoutPresets().map((preset) => ({
    ...preset,
    items: cloneItems(preset.items),
  }))
}

export function buildRepoLayoutWorkspaceStorageKey(repoId: string): string {
  return `${WORKSPACE_STORAGE_KEY_PREFIX}:${repoId}`
}

export function readUserRepoLayoutPresets(
  storage: Pick<Storage, "getItem">,
): RepoLayoutPreset[] {
  const raw = storage.getItem(USER_PRESETS_STORAGE_KEY)
  if (!raw) return []

  try {
    const parsed = JSON.parse(raw) as RepoLayoutPresetStoragePayload
    if (
      parsed.version !== STORAGE_VERSION ||
      !Array.isArray(parsed.presets) ||
      parsed.presets.some((preset) => !isRepoLayoutPresetRecord(preset))
    ) {
      return []
    }

    return parsed.presets.map((preset) => ({
      id: preset.id,
      label: preset.label,
      description: preset.description,
      source: "user",
      immutable: false,
      items: reconcileRepoPanelLayoutItems([], cloneItems(preset.items)),
    }))
  } catch {
    return []
  }
}

export function writeUserRepoLayoutPresets(
  storage: Pick<Storage, "setItem">,
  presets: RepoLayoutPreset[],
): void {
  storage.setItem(
    USER_PRESETS_STORAGE_KEY,
    JSON.stringify({
      version: STORAGE_VERSION,
      presets: presets
        .filter((preset) => preset.source === "user")
        .map((preset) => ({
          id: preset.id,
          label: preset.label,
          description: preset.description,
          items: cloneItems(preset.items),
        })),
    } satisfies RepoLayoutPresetStoragePayload),
  )
}

export function readRepoLayoutWorkspaceState(
  storage: Pick<Storage, "getItem">,
  repoId: string,
): RepoLayoutWorkspaceState | null {
  const raw = storage.getItem(buildRepoLayoutWorkspaceStorageKey(repoId))
  if (!raw) return null

  try {
    const parsed = JSON.parse(raw) as RepoLayoutWorkspaceStoragePayload
    if (
      parsed.version !== STORAGE_VERSION ||
      typeof parsed.activePresetId !== "string" ||
      parsed.activePresetId.trim().length === 0 ||
      !Array.isArray(parsed.items)
    ) {
      return null
    }

    return {
      activePresetId: parsed.activePresetId,
      items: reconcileRepoPanelLayoutItems([], cloneItems(parsed.items)),
    }
  } catch {
    return null
  }
}

export function writeRepoLayoutWorkspaceState(
  storage: Pick<Storage, "setItem">,
  repoId: string,
  state: RepoLayoutWorkspaceState,
): void {
  storage.setItem(
    buildRepoLayoutWorkspaceStorageKey(repoId),
    JSON.stringify({
      version: STORAGE_VERSION,
      activePresetId: state.activePresetId,
      items: cloneItems(state.items),
    } satisfies RepoLayoutWorkspaceStoragePayload),
  )
}

export function resolveRepoLayoutPreset(
  presets: RepoLayoutPreset[],
  presetId: string | null | undefined,
): RepoLayoutPreset {
  return (
    presets.find((preset) => preset.id === presetId) ??
    presets.find((preset) => preset.id === "system-default") ??
    presets[0]!
  )
}

export function buildRepoUserLayoutPresetId(
  label: string,
  existingIds: string[],
): string {
  const base =
    label
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "") || "repo-layout"

  let nextId = `user-${base}`
  let index = 2
  while (existingIds.includes(nextId)) {
    nextId = `user-${base}-${index}`
    index += 1
  }
  return nextId
}

export function createUserRepoLayoutPreset(input: {
  id?: string
  label: string
  description?: string | null
  items: RepoPanelLayoutItem[]
}): RepoLayoutPreset {
  return {
    id: input.id ?? "",
    label: input.label.trim(),
    description: input.description?.trim() ?? "",
    source: "user",
    immutable: false,
    items: cloneItems(input.items),
  }
}

export function repoLayoutPresetItemsEqual(
  left: RepoLayoutPreset,
  right: RepoPanelLayoutItem[],
): boolean {
  return repoPanelLayoutItemsEqual(left.items, right)
}
