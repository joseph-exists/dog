import type { RepoBuilderPanelConfig } from "@/components/Repo/builder"
import type { DefaultRepoPanelConfig } from "@/components/Repo/registry"
import { normalizeRepoPanelConfig } from "./config"

export interface RepoPanelLayoutItem extends RepoBuilderPanelConfig {
  hidden: boolean
}

interface RepoPanelLayoutStoragePayload {
  version: 1
  items: RepoPanelLayoutItem[]
}

const STORAGE_VERSION = 1
const STORAGE_KEY_PREFIX = "repo-panel-layout"

function isProminence(value: unknown): value is RepoBuilderPanelConfig["prominence"] {
  return value === "primary" || value === "auxiliary"
}

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function sanitizeConfigJson(value: unknown): Record<string, unknown> | null {
  return isObjectRecord(value) ? value : null
}

function normalizeLayoutConfig(
  kind: RepoBuilderPanelConfig["kind"],
  panelId: string,
  value: unknown,
): Record<string, unknown> | null {
  return normalizeRepoPanelConfig(kind, panelId, sanitizeConfigJson(value))
}

export function isRepoPanelLayoutItem(value: unknown): value is RepoPanelLayoutItem {
  if (!isObjectRecord(value)) return false
  return (
    typeof value.id === "string" &&
    value.id.trim().length > 0 &&
    typeof value.kind === "string" &&
    value.kind.trim().length > 0 &&
    isProminence(value.prominence) &&
    typeof value.hidden === "boolean"
  )
}

export function buildRepoPanelLayoutStorageKey(repoId: string): string {
  return `${STORAGE_KEY_PREFIX}:${repoId}`
}

export function createRepoPanelLayoutItems(
  panels: Array<
    Pick<
      DefaultRepoPanelConfig,
      | "id"
      | "kind"
      | "title"
      | "prominence"
      | "default_size"
      | "min_size"
      | "max_size"
      | "config_json"
    >
  >,
): RepoPanelLayoutItem[] {
  return panels.map((panel) => ({
    id: panel.id,
    kind: panel.kind,
    title: panel.title,
    prominence: panel.prominence,
    default_size: panel.default_size,
    min_size: panel.min_size,
    max_size: panel.max_size,
    config_json: normalizeLayoutConfig(panel.kind, panel.id, panel.config_json),
    hidden: false,
  }))
}

export function readRepoPanelLayoutItems(
  storage: Pick<Storage, "getItem">,
  storageKey: string,
): RepoPanelLayoutItem[] | null {
  const raw = storage.getItem(storageKey)
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw) as RepoPanelLayoutStoragePayload
    if (
      parsed.version !== STORAGE_VERSION ||
      !Array.isArray(parsed.items) ||
      parsed.items.some((item) => !isRepoPanelLayoutItem(item))
    ) {
      return null
    }
    return parsed.items.map((item) => ({
      ...item,
      config_json: normalizeLayoutConfig(item.kind, item.id, item.config_json),
    }))
  } catch {
    return null
  }
}

export function writeRepoPanelLayoutItems(
  storage: Pick<Storage, "setItem">,
  storageKey: string,
  items: RepoPanelLayoutItem[],
): void {
  const normalizedItems = items.map((item) => ({
    ...item,
    config_json: normalizeLayoutConfig(item.kind, item.id, item.config_json),
  }))
  storage.setItem(
    storageKey,
    JSON.stringify({
      version: STORAGE_VERSION,
      items: normalizedItems,
    } satisfies RepoPanelLayoutStoragePayload),
  )
}

export function reconcileRepoPanelLayoutItems(
  authoredItems: RepoPanelLayoutItem[],
  storedItems: RepoPanelLayoutItem[] | null,
): RepoPanelLayoutItem[] {
  if (!storedItems || storedItems.length === 0) return authoredItems

  const authoredById = new Map(authoredItems.map((item) => [item.id, item]))
  const reconciled: RepoPanelLayoutItem[] = []
  const seenIds = new Set<string>()

  for (const storedItem of storedItems) {
    const authoredItem = authoredById.get(storedItem.id)
    if (authoredItem) {
      reconciled.push({
        ...authoredItem,
        ...storedItem,
        config_json:
          normalizeLayoutConfig(storedItem.kind, storedItem.id, storedItem.config_json) ??
          authoredItem.config_json ??
          null,
      })
    } else {
      reconciled.push({
        ...storedItem,
        config_json: normalizeLayoutConfig(storedItem.kind, storedItem.id, storedItem.config_json),
      })
    }
    seenIds.add(storedItem.id)
  }

  for (const authoredItem of authoredItems) {
    if (seenIds.has(authoredItem.id)) continue
    reconciled.push(authoredItem)
  }

  return reconciled
}

export function applyRepoPanelLayoutItems<
  T extends Pick<
    RepoBuilderPanelConfig,
    | "id"
    | "kind"
    | "title"
    | "prominence"
    | "default_size"
    | "min_size"
    | "max_size"
    | "config_json"
  >,
>(basePanels: T[], items: RepoPanelLayoutItem[]): T[] {
  if (items.length === 0) return basePanels

  const basePanelsById = new Map(basePanels.map((panel) => [panel.id, panel]))
  const ordered: T[] = []
  const seenBaseIds = new Set<string>()

  for (const item of items) {
    const basePanel = basePanelsById.get(item.id)
    if (item.hidden) {
      if (basePanel) seenBaseIds.add(item.id)
      continue
    }

    if (basePanel) {
      ordered.push({
        ...basePanel,
        id: item.id,
        kind: item.kind,
        title: item.title || basePanel.title,
        prominence: item.prominence,
        default_size: item.default_size,
        min_size: item.min_size,
        max_size: item.max_size,
        config_json: normalizeLayoutConfig(item.kind, item.id, item.config_json),
      })
      seenBaseIds.add(item.id)
      continue
    }

    ordered.push({
      id: item.id,
      kind: item.kind,
      title: item.title || item.kind,
      prominence: item.prominence,
      default_size: item.default_size,
      min_size: item.min_size,
      max_size: item.max_size,
      config_json: normalizeLayoutConfig(item.kind, item.id, item.config_json),
    } as T)
  }

  for (const basePanel of basePanels) {
    if (seenBaseIds.has(basePanel.id)) continue
    ordered.push(basePanel)
  }

  return ordered
}

export function repoPanelLayoutItemsEqual(
  left: RepoPanelLayoutItem[],
  right: RepoPanelLayoutItem[],
): boolean {
  if (left.length !== right.length) return false
  return left.every((item, index) => JSON.stringify(item) === JSON.stringify(right[index]))
}
