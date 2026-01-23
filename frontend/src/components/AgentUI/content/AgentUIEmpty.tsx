import { Blocks } from "lucide-react"
import { cn } from "@/lib/utils"

interface AgentUIEmptyProps {
  className?: string
  title?: string
  description?: string
}

export function AgentUIEmpty({
  className,
  title = "No agent UI components",
  description = "Structured UI components from agent tool calls will appear here as agents interact in this room.",
}: AgentUIEmptyProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-12 px-4 text-center",
        className,
      )}
    >
      <Blocks className="h-10 w-10 text-muted-foreground/50 mb-3" />
      <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
      <p className="text-xs text-muted-foreground/70 mt-1 max-w-[240px]">
        {description}
      </p>
    </div>
  )
}
