/**
 * StoryPanel
 *
 * Room runtime panel for playing through a story in a room.
 */

import { AlertCircle, BookOpen, Loader2 } from "lucide-react"
import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useRoomRuntime } from "@/hooks/useRoomRuntime"
import { cn } from "@/lib/utils"
import { PanelContainer } from "../../primitives/PanelContainer"
import { PlaceholderContent } from "../../primitives/PlaceholderContent"
import { ChoiceList } from "./ChoiceList"
import { NodeChainCollapsible } from "./NodeChainCollapsible"
import { NodeDisplay } from "./NodeDisplay"
import { RuntimeControls } from "./RuntimeControls"
import { StoryStateCollapsible } from "./StoryStateCollapsible"
import { StoryRuntimeStartDialog } from "./StoryRuntimeStartDialog"

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

  if (isLoading) {
    return (
      <div className={cn("flex h-full flex-col", className)}>
        <PlaceholderContent
          icon={Loader2}
          title="Loading Story Runtime"
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
          title="Unable to load runtime"
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
        <PlaceholderContent
          icon={BookOpen}
          title="No Story Attached"
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
      <div className="flex h-full flex-col gap-4 p-4">
        {runtime.currentNode ? (
          <NodeDisplay node={runtime.currentNode} />
        ) : (
          <div className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
            Runtime is active but no current node is available.
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
