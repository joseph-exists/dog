/**
 * AgentBadge Component
 *
 * Displays agent metadata as small, informative badges.
 * - Scope badge: System (🌐) vs Personal (👤)
 * - Mode badge: Always, On Mention (@), Manual
 * - Status badge: Enabled/Disabled
 */

import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

type AgentScope = "system" | "personal"
type ParticipationMode = "always" | "on_mention" | "manual"

interface ScopeBadgeProps {
  scope: AgentScope
  className?: string
}

/**
 * Badge showing agent scope (system vs personal)
 */
export function AgentScopeBadge({ scope, className }: ScopeBadgeProps) {
  const config = {
    system: {
      label: "System",
      icon: "🌐",
      variant: "secondary" as const,
    },
    personal: {
      label: "Personal",
      icon: "👤",
      variant: "outline" as const,
    },
  }

  const { label, icon, variant } = config[scope]

  return (
    <Badge variant={variant} className={cn("gap-1", className)}>
      <span>{icon}</span>
      <span>{label}</span>
    </Badge>
  )
}

interface ModeBadgeProps {
  mode: ParticipationMode
  className?: string
}

/**
 * Badge showing participation mode
 */
export function AgentModeBadge({ mode, className }: ModeBadgeProps) {
  const config = {
    always: {
      label: "Always Active",
      icon: "⚡",
      title: "Responds to all messages",
    },
    on_mention: {
      label: "On Mention",
      icon: "@",
      title: "Responds when mentioned",
    },
    manual: {
      label: "Manual",
      icon: "🎯",
      title: "Must be explicitly invoked",
    },
  }

  const { label, icon, title } = config[mode]

  return (
    <Badge variant="outline" className={cn("gap-1", className)} title={title}>
      <span>{icon}</span>
      <span>{label}</span>
    </Badge>
  )
}

interface StatusBadgeProps {
  isEnabled: boolean
  className?: string
}

/**
 * Badge showing enabled/disabled status
 */
export function AgentStatusBadge({ isEnabled, className }: StatusBadgeProps) {
  return (
    <Badge
      variant={isEnabled ? "default" : "secondary"}
      className={cn(
        isEnabled
          ? "bg-green-600 hover:bg-green-600"
          : "bg-muted text-muted-foreground",
        className,
      )}
    >
      {isEnabled ? "Active" : "Inactive"}
    </Badge>
  )
}

interface AgentBadgeProps {
  /** What type of badge to display */
  type: "scope" | "mode" | "status"
  /** Scope value (required if type="scope") */
  scope?: AgentScope
  /** Mode value (required if type="mode") */
  mode?: ParticipationMode
  /** Enabled status (required if type="status") */
  isEnabled?: boolean
  className?: string
}

/**
 * Unified AgentBadge component that renders the appropriate badge type.
 * For convenience when you want a single component interface.
 */
export default function AgentBadge({
  type,
  scope,
  mode,
  isEnabled,
  className,
}: AgentBadgeProps) {
  switch (type) {
    case "scope":
      if (!scope) return null
      return <AgentScopeBadge scope={scope} className={className} />
    case "mode":
      if (!mode) return null
      return <AgentModeBadge mode={mode} className={className} />
    case "status":
      if (isEnabled === undefined) return null
      return <AgentStatusBadge isEnabled={isEnabled} className={className} />
    default:
      return null
  }
}

// Type exports for consumers
export type { AgentScope, ParticipationMode }
