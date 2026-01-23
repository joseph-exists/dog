import { cn } from "@/lib/utils"
import AgentUIRenderer from "../AgentUIRenderer"
import type { UIComponent } from "../types"

interface AgentUIStackProps {
  components: UIComponent[]
  onAction?: (action: string, component: UIComponent) => void
  className?: string
  spacing?: "compact" | "normal" | "relaxed"
}

const spacingClasses = {
  compact: "space-y-1",
  normal: "space-y-3",
  relaxed: "space-y-4",
}

export function AgentUIStack({
  components,
  onAction,
  className,
  spacing = "normal",
}: AgentUIStackProps) {
  if (components.length === 0) return null

  return (
    <div className={cn(spacingClasses[spacing], className)}>
      {components.map((component, index) => (
        <AgentUIRenderer
          key={component.id || `${component.type}-${index}`}
          component={component}
          onAction={
            onAction ? (action) => onAction(action, component) : undefined
          }
        />
      ))}
    </div>
  )
}
