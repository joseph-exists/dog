// src/components/Persona/primitives/PersonaBadges.tsx
import { Badge } from "@/components/ui/badge"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

interface PersonaBadgesProps {
  traits?: Array<{ id: string; name: string }>
  qualities?: Array<{ id: string; name: string }>
  domains?: string[]
  variant?: "compact" | "expanded"
  maxVisible?: number
  className?: string
}

export function PersonaBadges({
  traits = [],
  qualities = [],
  domains = [],
  variant = "compact",
  maxVisible = 3,
  className,
}: PersonaBadgesProps) {
  if (variant === "compact") {
    const parts: string[] = []
    if (traits.length) parts.push(`${traits.length} traits`)
    if (qualities.length) parts.push(`${qualities.length} qualities`)
    if (domains.length) parts.push(domains.join(", "))

    if (parts.length === 0) return null

    return (
      <span className={cn("text-xs text-muted-foreground", className)}>
        {parts.join(" \u00B7 ")}
      </span>
    )
  }

  // Expanded variant
  const allBadges = [
    ...traits.map((t) => ({ ...t, color: "blue" as const })),
    ...qualities.map((q) => ({ ...q, color: "purple" as const })),
  ]

  const visible = allBadges.slice(0, maxVisible)
  const hidden = allBadges.slice(maxVisible)

  return (
    <div className={cn("flex flex-wrap gap-1", className)}>
      {visible.map((badge) => (
        <Badge
          key={badge.id}
          variant="secondary"
          className={cn(
            "text-xs",
            badge.color === "blue" &&
              "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
            badge.color === "purple" &&
              "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
          )}
        >
          {badge.name}
        </Badge>
      ))}
      {hidden.length > 0 && (
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge variant="outline" className="text-xs cursor-default">
              +{hidden.length} more
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            <div className="space-y-1">
              {hidden.map((b) => (
                <div key={b.id} className="text-xs">
                  {b.name}
                </div>
              ))}
            </div>
          </TooltipContent>
        </Tooltip>
      )}
      {domains.map((domain) => (
        <Badge key={domain} variant="outline" className="text-xs">
          {domain}
        </Badge>
      ))}
    </div>
  )
}
