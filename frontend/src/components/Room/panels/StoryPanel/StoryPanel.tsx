/**
 * StoryPanel
 *
 * Room runtime panel for playing through a story in a room.
 */

import { AlertCircle, BookOpen, ExternalLink, Loader2 } from "lucide-react"
import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useRoomRuntime } from "@/hooks/useRoomRuntime"
import { useRoomWorkspaceConnection } from "@/hooks/useRoomWorkspaceConnection"
import { cn } from "@/lib/utils"
import { PanelContainer } from "../../primitives/PanelContainer"
import { PlaceholderContent } from "../../primitives/PlaceholderContent"
import { ChoiceList } from "./ChoiceList"
import { NodeChainCollapsible } from "./NodeChainCollapsible"
import { NodeDisplay } from "./NodeDisplay"
import { RuntimeControls } from "./RuntimeControls"
import { StoryRuntimeStartDialog } from "./StoryRuntimeStartDialog"
import { StoryStateCollapsible } from "./StoryStateCollapsible"

interface StoryPanelProps {
  roomId: string
  roomTitle?: string | null
  roomStoryId?: string | null
  className?: string
  canWrite?: boolean
}

export function StoryPanel({
  roomId,
  roomTitle,
  roomStoryId,
  className,
  canWrite = true,
}: StoryPanelProps) {
  const [startDialogOpen, setStartDialogOpen] = useState(false)
  const { currentConnection } = useRoomWorkspaceConnection(roomId)
  const {
    runtime,
    isLoading,
    error,
    refetch,
    start,
    advance,
    rewind,
    reset,
    isStarting,
    isAdvancing,
    isRewinding,
    isResetting,
    pendingChoiceId,
  } = useRoomRuntime(roomId)
  const currentEndpoints = currentConnection?.endpoints ?? []
  const availableEndpoints = currentEndpoints.filter((endpoint) => endpoint.url)
  const currentConnectionPurposeLabel =
    currentConnection?.purpose === "agent_runtime_connect"
      ? "Agent Runtime"
      : "Service Link"
  const currentConnectionStatusTone =
    currentConnection?.descriptorStatus === "available"
      ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-700"
      : currentConnection?.descriptorStatus === "pending"
        ? "border-amber-500/40 bg-amber-500/10 text-amber-700"
        : "border-rose-500/40 bg-rose-500/10 text-rose-700"

  const connectionCallout = currentConnection ? (
    <div className="space-y-3 rounded-lg border bg-muted/20 p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="text-sm font-medium">Current workspace connection</div>
          <div className="text-xs text-muted-foreground">
            {currentConnection.workspaceName} · {currentConnectionPurposeLabel}
          </div>
        </div>
        <Badge variant="outline" className={currentConnectionStatusTone}>
          {currentConnection.descriptorStatus}
        </Badge>
      </div>

      <div className="flex flex-wrap gap-2">
        <Badge variant="secondary">{currentConnectionPurposeLabel}</Badge>
        <Badge variant="outline">
          {currentConnection.readyServiceCount}/{currentConnection.serviceCount} services ready
        </Badge>
        {currentConnection.capabilities.map((capability) => (
          <Badge key={capability} variant="outline">
            {capability}
          </Badge>
        ))}
      </div>

      <div className="text-xs text-muted-foreground">
        {currentConnection.reason ??
          "This room is using a descriptor-backed workspace connection for the current session."}
      </div>

      {availableEndpoints.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {availableEndpoints.map((endpoint) => (
            <Button key={endpoint.id} asChild size="sm" variant="outline">
              <a href={endpoint.url ?? undefined} target="_blank" rel="noreferrer">
                {endpoint.label}
                <ExternalLink className="ml-1 h-3.5 w-3.5" />
              </a>
            </Button>
          ))}
        </div>
      ) : (
        <div className="rounded-md border border-dashed px-3 py-3 text-xs text-muted-foreground">
          {currentConnection.descriptorStatus === "pending"
            ? "This connection is still being prepared. Return to Workspace Links to refresh or wait for readiness."
            : "No usable endpoint has been issued for the current connection yet."}
        </div>
      )}
    </div>
  ) : null

  if (isLoading) {
    return (
      <div className={cn("flex h-full flex-col", className)}>
        <PlaceholderContent
          icon={Loader2}
          title="you must wait until you wait no more"
          description="Please wait while the runtime loads..."
          className="[&_svg]:animate-spin"
        />
      </div>
    )
  }

  if (error) {
    return (
      <div className={cn("flex h-full flex-col", className)}>
        <PlaceholderContent
          icon={AlertCircle}
          title="runtime has failed you, as you have failed runtime"
          description={error.message || "Please try again."}
          action={
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              Retry
            </Button>
          }
        />
      </div>
    )
  }

  if (!runtime || !runtime.hasRuntime) {
    return (
      <div className={cn("flex h-full flex-col", className)}>
        {connectionCallout ? <div className="px-4 pt-4">{connectionCallout}</div> : null}
        <PlaceholderContent
          icon={BookOpen}
          title="no story attachment. luck fails us all."
          description="Attach a story to begin playing in this room."
          action={
            <Button
              size="sm"
              onClick={() => setStartDialogOpen(true)}
              disabled={!canWrite}
              title={
                canWrite
                  ? undefined
                  : "Only room owners can start the runtime right now."
              }
            >
              Start Runtime
            </Button>
          }
        />
        {!canWrite && (
          <p className="px-4 text-xs text-muted-foreground">
            Only room owners can start the runtime right now.
          </p>
        )}
        <StoryRuntimeStartDialog
          open={startDialogOpen}
          onOpenChange={setStartDialogOpen}
          roomTitle={roomTitle ?? null}
          roomStoryId={roomStoryId ?? null}
          isStarting={isStarting}
          onStartRuntime={start}
        />
      </div>
    )
  }

  const headerActions = (
    <div className="flex items-center gap-2">
      <Badge variant="secondary" className="text-xs">
        v{runtime.storyVersion}
      </Badge>
      {runtime.isAtEndNode && (
        <Badge variant="default" className="text-xs">
          Story Complete
        </Badge>
      )}
    </div>
  )

  return (
    <PanelContainer
      title="Story Runtime"
      headerActions={headerActions}
      className={className}
    >
      <div className="demo-story-content flex h-full flex-col gap-4 p-4">
        {connectionCallout}

        {runtime.currentNode ? (
          <NodeDisplay node={runtime.currentNode} />
        ) : (
          <div className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
            runtime is active but no current node is available.
          </div>
        )}

        <ChoiceList
          choices={runtime.availableChoices}
          isDisabled={isAdvancing || !canWrite}
          pendingChoiceId={pendingChoiceId}
          onSelect={(choice) => {
            void advance(choice.id)
          }}
        />

        <div className="space-y-3 pt-2">
          <NodeChainCollapsible
            nodes={runtime.nodeChain}
            currentNodeId={runtime.currentNode?.id}
          />
          <StoryStateCollapsible storyState={runtime.storyState} />
          <RuntimeControls
            canRewind={runtime.canRewind}
            canReset={runtime.canReset}
            isRewinding={isRewinding}
            isResetting={isResetting}
            onRewind={() => {
              if (!runtime.headChoiceId) return
              void rewind(runtime.headChoiceId)
            }}
            onReset={() => {
              void reset()
            }}
            isReadOnly={!canWrite}
          />
        </div>
      </div>
    </PanelContainer>
  )
}
