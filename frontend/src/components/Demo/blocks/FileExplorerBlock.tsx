import { FileText, FolderOpen } from "lucide-react"
import { Badge } from "@/components/ui/badge"

interface FileExplorerBlockProps {
  title?: string | null
  config: unknown
}

type ExplorerEntryType = "file" | "dir"

interface ExplorerEntry {
  path: string
  type: ExplorerEntryType
  depth: number
  size?: string
  status?: string
}

interface FileExplorerConfig {
  root_label: string
  entries: ExplorerEntry[]
  show_config_json: boolean
}

function toEntries(value: unknown): ExplorerEntry[] {
  if (!Array.isArray(value)) return []
  const entries: ExplorerEntry[] = []
  for (const item of value) {
    if (!item || typeof item !== "object") continue
    const raw = item as Record<string, unknown>
    const path = typeof raw.path === "string" ? raw.path : ""
    if (!path) continue

    const rawType = raw.type
    const type: ExplorerEntryType = rawType === "dir" ? "dir" : "file"
    const depthRaw = raw.depth
    const depth =
      typeof depthRaw === "number" && Number.isFinite(depthRaw) && depthRaw >= 0
        ? Math.floor(depthRaw)
        : 0

    entries.push({
      path,
      type,
      depth,
      size: typeof raw.size === "string" ? raw.size : undefined,
      status: typeof raw.status === "string" ? raw.status : undefined,
    })
  }
  return entries
}

function toConfig(value: unknown): FileExplorerConfig {
  const raw =
    value && typeof value === "object" ? (value as Record<string, unknown>) : {}
  return {
    root_label:
      typeof raw.root_label === "string" && raw.root_label.length > 0
        ? raw.root_label
        : "workspace",
    entries: toEntries(raw.entries),
    show_config_json: raw.show_config_json === true,
  }
}

export function FileExplorerBlock({ title, config }: FileExplorerBlockProps) {
  const parsedConfig = toConfig(config)
  const dirCount = parsedConfig.entries.filter(
    (entry) => entry.type === "dir",
  ).length
  const fileCount = parsedConfig.entries.length - dirCount

  return (
    <div className="p-4 space-y-4">
      <div className="space-y-1">
        <div className="text-sm font-medium">{title ?? "File Explorer"}</div>
        <div className="text-xs text-muted-foreground">
          File tree projection for configured demo resources.
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <Badge variant="outline">Root: {parsedConfig.root_label}</Badge>
        <Badge variant="secondary">Dirs: {dirCount}</Badge>
        <Badge variant="secondary">Files: {fileCount}</Badge>
      </div>

      <div className="rounded-md border bg-muted/20 p-3">
        {parsedConfig.entries.length === 0 ? (
          <div className="text-xs text-muted-foreground">
            No entries supplied in config.
          </div>
        ) : (
          <div className="space-y-1">
            {parsedConfig.entries.map((entry) => (
              <div
                key={`${entry.type}:${entry.path}`}
                className="flex items-center justify-between gap-2 rounded px-1 py-1 text-xs hover:bg-background/70"
                style={{ paddingLeft: `${entry.depth * 14 + 4}px` }}
              >
                <div className="min-w-0 flex items-center gap-2">
                  {entry.type === "dir" ? (
                    <FolderOpen className="h-3.5 w-3.5 text-amber-600" />
                  ) : (
                    <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                  )}
                  <span className="truncate">{entry.path}</span>
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  {entry.size && (
                    <span className="text-[10px] text-muted-foreground">
                      {entry.size}
                    </span>
                  )}
                  {entry.status && (
                    <Badge variant="outline" className="text-[10px]">
                      {entry.status}
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {parsedConfig.show_config_json && (
        <pre className="max-h-64 overflow-auto rounded border bg-muted/40 p-3 text-xs">
          {JSON.stringify(config ?? {}, null, 2)}
        </pre>
      )}
    </div>
  )
}
