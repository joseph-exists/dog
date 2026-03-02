import type { PanelProminence } from "@/components/Page/registry/panelTypes"

export interface DemoPanelLayoutItem {
  id: string
  kind: string
  title: string
  prominence: PanelProminence
  hidden: boolean
}

interface DemoPanelLayoutStoragePayload {
  version: 1
  items: DemoPanelLayoutItem[]
}

interface DemoPanelRecord {
  id: string
  kind?: string | null
  title?: string | null
  prominence?: PanelProminence | null
}

const STORAGE_VERSION = 1
const STORAGE_KEY_PREFIX = "demo-panel-layout"
const COLLAPSE_STORAGE_KEY_PREFIX = "demo-view-collapsed"

function isPanelProminence(value: unknown): value is PanelProminence {
  return value === "primary" || value === "auxiliary"
}

function isDemoPanelLayoutItem(value: unknown): value is DemoPanelLayoutItem {
  if (!value || typeof value !== "object") return false
  const item = value as Record<string, unknown>
  return (
    typeof item.id === "string" &&
    item.id.trim().length > 0 &&
    typeof item.kind === "string" &&
    item.kind.trim().length > 0 &&
    typeof item.title === "string" &&
    item.title.trim().length > 0 &&
    isPanelProminence(item.prominence) &&
    typeof item.hidden === "boolean"
  )
}

export function buildDemoPanelLayoutStorageKey(storageScope: string): string {
  return `${STORAGE_KEY_PREFIX}:${storageScope}`
}

export function buildDemoCollapseStorageKey(storageScope: string): string {
  return `${COLLAPSE_STORAGE_KEY_PREFIX}:${storageScope}`
}

export function createDemoPanelLayoutItems(
  panels: DemoPanelRecord[],
): DemoPanelLayoutItem[] {
  return panels.map((panel) => ({
    id: panel.id,
    kind: typeof panel.kind === "string" ? panel.kind : "content",
    title:
      typeof panel.title === "string" && panel.title.trim().length > 0
        ? panel.title
        : typeof panel.kind === "string" && panel.kind.trim().length > 0
          ? panel.kind
          : "Panel",
    prominence: isPanelProminence(panel.prominence)
      ? panel.prominence
      : "primary",
    hidden: false,
  }))
}

export function readDemoPanelLayoutItems(
  storage: Pick<Storage, "getItem">,
  storageKey: string,
): DemoPanelLayoutItem[] | null {
  const raw = storage.getItem(storageKey)
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw) as DemoPanelLayoutStoragePayload
    if (
      parsed.version !== STORAGE_VERSION ||
      !Array.isArray(parsed.items) ||
      parsed.items.some((item) => !isDemoPanelLayoutItem(item))
    ) {
      return null
    }
    return parsed.items
  } catch {
    return null
  }
}

export function writeDemoPanelLayoutItems(
  storage: Pick<Storage, "setItem">,
  storageKey: string,
  items: DemoPanelLayoutItem[],
): void {
  storage.setItem(
    storageKey,
    JSON.stringify({
      version: STORAGE_VERSION,
      items,
    } satisfies DemoPanelLayoutStoragePayload),
  )
}

export function readDemoCollapsedIds(
  storage: Pick<Storage, "getItem">,
  storageKey: string,
): string[] {
  const raw = storage.getItem(storageKey)
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.filter(
      (value): value is string =>
        typeof value === "string" && value.trim().length > 0,
    )
  } catch {
    return []
  }
}

export function writeDemoCollapsedIds(
  storage: Pick<Storage, "setItem">,
  storageKey: string,
  collapsedIds: string[],
): void {
  storage.setItem(storageKey, JSON.stringify(collapsedIds))
}

export function reconcileDemoCollapsedIds(
  collapsedIds: string[],
  validIds: string[],
): string[] {
  const validIdSet = new Set(validIds)
  return collapsedIds.filter((id) => validIdSet.has(id))
}

export function reconcileDemoPanelLayoutItems(
  authoredItems: DemoPanelLayoutItem[],
  storedItems: DemoPanelLayoutItem[] | null,
): DemoPanelLayoutItem[] {
  if (!storedItems || storedItems.length === 0) return authoredItems

  const authoredById = new Map(authoredItems.map((item) => [item.id, item]))
  const reconciled: DemoPanelLayoutItem[] = []
  const seenIds = new Set<string>()

  for (const storedItem of storedItems) {
    const authoredItem = authoredById.get(storedItem.id)
    if (!authoredItem) continue
    reconciled.push({
      ...authoredItem,
      prominence: storedItem.prominence,
      hidden: storedItem.hidden,
    })
    seenIds.add(storedItem.id)
  }

  for (const authoredItem of authoredItems) {
    if (seenIds.has(authoredItem.id)) continue
    reconciled.push(authoredItem)
  }

  return reconciled
}

export function applyDemoPanelLayoutItems<T extends DemoPanelRecord>(
  panels: T[],
  items: DemoPanelLayoutItem[],
): T[] {
  if (items.length === 0) return panels

  const panelsById = new Map(panels.map((panel) => [panel.id, panel]))
  const ordered: T[] = []
  const seenIds = new Set<string>()

  for (const item of items) {
    const panel = panelsById.get(item.id)
    if (!panel) continue
    seenIds.add(item.id)
    if (item.hidden) continue
    ordered.push({
      ...panel,
      prominence: item.prominence,
    })
  }

  for (const panel of panels) {
    if (seenIds.has(panel.id)) continue
    ordered.push(panel)
  }

  return ordered
}

export function demoPanelLayoutItemsEqual(
  left: DemoPanelLayoutItem[],
  right: DemoPanelLayoutItem[],
): boolean {
  if (left.length !== right.length) return false
  return left.every((item, index) => {
    const other = right[index]
    return (
      item.id === other?.id &&
      item.kind === other.kind &&
      item.title === other.title &&
      item.prominence === other.prominence &&
      item.hidden === other.hidden
    )
  })
}
