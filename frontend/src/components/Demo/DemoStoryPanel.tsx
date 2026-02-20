import { useEffect, useRef } from "react"
import { StoryPanel } from "@/components/Page/panels/StoryPanel"
import { useRoomRuntime } from "@/hooks/useRoomRuntime"

// TODO: we need to finish revising the DemoPages to use the 'rest' of the functionality in StoryPanel that is currently overloaded.  

interface DemoStoryPanelProps {
  roomId: string
  roomStoryId: string | null
  autoRespond: boolean
  onSendMessage: (message: string) => void
}

export function DemoStoryPanel({
  roomId,
  roomStoryId,
  autoRespond,
  onSendMessage,
}: DemoStoryPanelProps) {
  const { runtime } = useRoomRuntime(roomId)
  const prevNodeIdRef = useRef<string | null>(null)
  const prevRevisionRef = useRef<number | null>(null)

  // Watch for runtime state changes and send synthetic messages
  useEffect(() => {
    if (!runtime || !autoRespond) {
      // Track current state even when auto-respond is off
      prevNodeIdRef.current = runtime?.currentNode?.id ?? null
      prevRevisionRef.current = runtime?.revision ?? null
      return
    }

    const currentNodeId = runtime.currentNode?.id ?? null
    const currentRevision = runtime.revision

    // Skip initial render
    if (prevRevisionRef.current === null) {
      prevNodeIdRef.current = currentNodeId
      prevRevisionRef.current = currentRevision
      return
    }

    // Detect state change via revision bump
    if (currentRevision !== prevRevisionRef.current) {
      const currentNodeTitle = runtime.currentNode?.title ?? "unknown"

      if (currentRevision === 0 && runtime.canReset) {
        // Reset detected (revision goes back to 0)
        onSendMessage("[Reset story to beginning]")
      } else if (currentNodeId !== prevNodeIdRef.current) {
        // Node changed -- advance or rewind
        onSendMessage(`[Story moved to: ${currentNodeTitle}]`)
      }

      prevNodeIdRef.current = currentNodeId
      prevRevisionRef.current = currentRevision
    }
  }, [
    runtime?.currentNode?.id,
    runtime?.revision,
    autoRespond,
    onSendMessage,
    runtime,
  ])

  return (
    <StoryPanel
      roomId={roomId}
      roomStoryId={roomStoryId}
      canWrite={true}
      className="h-full"
    />
  )
}
