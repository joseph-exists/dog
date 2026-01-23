// src/components/Persona/content/PersonaEmpty.tsx
import { Smile } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

type EmptyContext = "no-personas" | "no-results" | "no-matches"

interface PersonaEmptyProps {
  context?: EmptyContext
  onAction?: () => void
  actionLabel?: string
  className?: string
}

const messages: Record<EmptyContext, { title: string; description: string }> = {
  "no-personas": {
    title: "No Personas",
    description: "This library is empty. Add personas to get started.",
  },
  "no-results": {
    title: "No Results",
    description: "No personas match your search. Try a different query.",
  },
  "no-matches": {
    title: "No Matches",
    description: "No personas match the current filters.",
  },
}

export function PersonaEmpty({
  context = "no-personas",
  onAction,
  actionLabel = "Add Persona",
  className,
}: PersonaEmptyProps) {
  const message = messages[context]

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-8 px-4 text-center",
        className,
      )}
    >
      <Smile className="h-10 w-10 text-muted-foreground/50 mb-3" />
      <h3 className="text-sm font-medium">{message.title}</h3>
      <p className="text-xs text-muted-foreground mt-1 max-w-[200px]">
        {message.description}
      </p>
      {onAction && context === "no-personas" && (
        <Button variant="outline" size="sm" className="mt-4" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  )
}
