import { StoryPanel } from "@/components/Page/panels/StoryPanel"

// Demo story runtime should flow through the canonical room runtime path.
// Do not synthesize chat messages here; agents already see runtime state
// through build_room_context/context_provider.

interface DemoStoryPanelProps {
  roomId: string
  roomTitle?: string | null
  roomStoryId: string | null
  canWrite?: boolean
  autoRespond?: boolean
  onSendMessage?: (message: string) => void
}

export function DemoStoryPanel({
  roomId,
  roomTitle,
  roomStoryId,
  canWrite = true,
  autoRespond: _autoRespond,
  onSendMessage: _onSendMessage,
}: DemoStoryPanelProps) {
  return (
    <StoryPanel
      roomId={roomId}
      roomTitle={roomTitle}
      roomStoryId={roomStoryId}
      canWrite={canWrite}
      className="h-full"
    />
  )
}
