import { AgentUIEmpty, AgentUIStack } from "@/components/AgentUI/content"
import type { UIComponent } from "@/components/AgentUI/types"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { useAgentUI } from "@/hooks/useAgentUI"
import { useRoomMessages } from "@/hooks/useRoomMessages"
import { cn } from "@/lib/utils"
import { PanelContainer } from "../primitives/PanelContainer"

interface A2UIPanelProps {
  roomId: string
  hideHeader?: boolean
  className?: string
}

export function A2UIPanel({
  roomId,
  hideHeader = false,
  className,
}: A2UIPanelProps) {
  const { messages } = useRoomMessages(roomId)
  const { byAgent, hasComponents } = useAgentUI({
    messages: messages ?? [],
  })

  const handleAction = (action: string, component: UIComponent) => {
    // TODO: Route actions back to the agent that emitted the component
    console.log("[A2UIPanel] Action:", action, "Component:", component.id)
  }

  const content = hasComponents ? (
    <ScrollArea className="h-full">
      <div className="p-4 space-y-4">
        {[...byAgent.entries()].map(([agentName, agentEntries]) => (
          <div key={agentName}>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-medium text-muted-foreground">
                {agentName}
              </span>
              <Badge variant="secondary" className="text-xs">
                {agentEntries.length}
              </Badge>
            </div>
            <AgentUIStack
              components={agentEntries.map((e) => e.component)}
              onAction={handleAction}
              spacing="compact"
            />
            <Separator className="mt-4" />
          </div>
        ))}
      </div>
    </ScrollArea>
  ) : (
    <AgentUIEmpty />
  )

  if (hideHeader) {
    return <div className={cn("h-full", className)}>{content}</div>
  }

  return <PanelContainer title="Agent UI">{content}</PanelContainer>
}
