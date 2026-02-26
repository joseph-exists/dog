import { Loader2 } from "lucide-react"
import { useRoomRuntime } from "@/hooks/useRoomRuntime"
import type { RoomRuntimeViewModel } from "@/services/roomRuntimeService"

interface StoryMetadataBlockProps {
  title?: string | null
  roomId: string
  roomTitle: string
  roomStoryId: string | null
  runtimePolicy: "auto" | "manual" | "owner_only"
  runtimeHasRuntime: boolean
  autoStartError: string | null
  config: unknown
  calloutLabel?: string | null
}

interface StoryMetadataRuntimeState {
  isLoading: boolean
  hasRuntime: boolean
  statusLabel: "running" | "not started"
  revisionLabel: string | number
  currentNodeLabel: string
  availableChoices: number
}

export function shouldShowRawStoryMetadataConfig(value: unknown): boolean {
  if (!value || typeof value !== "object") return false
  const raw = value as Record<string, unknown>
  return raw.show_config_json === true
}

export function deriveStoryMetadataRuntimeState({
  runtime,
  isLoading,
  runtimeHasRuntime,
}: {
  runtime: RoomRuntimeViewModel | null
  isLoading: boolean
  runtimeHasRuntime: boolean
}): StoryMetadataRuntimeState {
  const hasRuntime = runtime?.hasRuntime ?? runtimeHasRuntime
  return {
    isLoading,
    hasRuntime,
    statusLabel: hasRuntime ? "running" : "not started",
    revisionLabel: runtime?.revision ?? "-",
    currentNodeLabel: runtime?.currentNode?.title ?? "-",
    availableChoices: runtime?.availableChoices.length ?? 0,
  }
}

export function StoryMetadataBlock({
  title,
  roomId,
  roomTitle,
  roomStoryId,
  runtimePolicy,
  runtimeHasRuntime,
  autoStartError,
  config,
  calloutLabel,
}: StoryMetadataBlockProps) {
  const { runtime, isLoading } = useRoomRuntime(roomId)
  const derived = deriveStoryMetadataRuntimeState({
    runtime,
    isLoading,
    runtimeHasRuntime,
  })

  return (
    <div className="p-4 space-y-4">
      <div className="space-y-1">
        <div className="text-sm font-medium">{title ?? "Story Metadata"}</div>
        <div className="text-xs text-muted-foreground">
          Live metadata bound to room runtime.
        </div>
      </div>
      {calloutLabel && (
        <div className="rounded border bg-muted/30 px-2 py-1 text-xs text-muted-foreground">
          {calloutLabel}
        </div>
      )}

      <div className="grid gap-2 text-sm md:grid-cols-2">
        <div className="rounded-md border bg-muted/20 p-3">
          <div className="text-xs text-muted-foreground">Room</div>
          <div className="mt-1 font-medium">{roomTitle}</div>
          <div className="mt-1 text-xs text-muted-foreground">{roomId}</div>
        </div>

        <div className="rounded-md border bg-muted/20 p-3">
          <div className="text-xs text-muted-foreground">Story</div>
          <div className="mt-1 font-medium">
            {roomStoryId ?? "No story attached"}
          </div>
          <div className="mt-1 text-xs text-muted-foreground">
            Runtime policy: {runtimePolicy}
          </div>
        </div>
      </div>

      <div className="rounded-md border bg-muted/20 p-3 space-y-2">
        <div className="text-xs text-muted-foreground">Runtime state</div>
        {derived.isLoading ? (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Loading runtime...
          </div>
        ) : (
          <>
            <div className="text-sm">Status: {derived.statusLabel}</div>
            <div className="text-xs text-muted-foreground">
              Revision: {derived.revisionLabel}
            </div>
            <div className="text-xs text-muted-foreground">
              Current node: {derived.currentNodeLabel}
            </div>
            <div className="text-xs text-muted-foreground">
              Available choices: {derived.availableChoices}
            </div>
          </>
        )}
        {autoStartError && (
          <div className="rounded border border-red-200 bg-red-50 px-2 py-1 text-xs text-red-700">
            Auto-start error: {autoStartError}
          </div>
        )}
      </div>

      {shouldShowRawStoryMetadataConfig(config) && (
        <pre className="max-h-64 overflow-auto rounded border bg-muted/40 p-3 text-xs">
          {JSON.stringify(config ?? {}, null, 2)}
        </pre>
      )}
    </div>
  )
}
